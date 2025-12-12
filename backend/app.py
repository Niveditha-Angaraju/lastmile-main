"""
Backend API Server for LastMile Frontend
Acts as a bridge between the frontend and gRPC services.
"""
import os
import json
import time
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
import grpc
import pika
import sys
from sqlalchemy import create_engine, text

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.common_lib.protos_generated import (
    station_pb2, station_pb2_grpc,
    driver_pb2, driver_pb2_grpc,
    rider_pb2, rider_pb2_grpc,
    trip_pb2, trip_pb2_grpc,
)

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backend_api")

# Service hosts (can be overridden via env vars)
STATION_SERVICE = os.getenv("STATION_SERVICE", "localhost:50051")
DRIVER_SERVICE = os.getenv("DRIVER_SERVICE", "localhost:50052")
RIDER_SERVICE = os.getenv("RIDER_SERVICE", "localhost:50057")
TRIP_SERVICE = os.getenv("TRIP_SERVICE", "localhost:50055")
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://lastmile:lastmile@localhost:5432/lastmile")

# Database engine for direct queries
db_engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Helper functions
def get_station_stub():
    channel = grpc.insecure_channel(STATION_SERVICE)
    return station_pb2_grpc.StationServiceStub(channel), channel

def get_driver_stub():
    channel = grpc.insecure_channel(DRIVER_SERVICE)
    return driver_pb2_grpc.DriverServiceStub(channel), channel

def get_rider_stub():
    channel = grpc.insecure_channel(RIDER_SERVICE)
    return rider_pb2_grpc.RiderServiceStub(channel), channel

def get_trip_stub():
    channel = grpc.insecure_channel(TRIP_SERVICE)
    return trip_pb2_grpc.TripServiceStub(channel), channel

def publish_to_rabbitmq(queue, message):
    try:
        conn = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
        ch = conn.channel()
        ch.queue_declare(queue=queue, durable=True)
        ch.basic_publish(
            exchange="",
            routing_key=queue,
            body=json.dumps(message),
            properties=pika.BasicProperties(delivery_mode=2)
        )
        conn.close()
        return True
    except Exception as e:
        logger.error(f"RabbitMQ publish error: {e}")
        return False

# API Routes
@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})

@app.route('/api/stations', methods=['GET'])
def get_stations():
    try:
        stub, channel = get_station_stub()
        req = station_pb2.StationListRequest()
        res = stub.ListStations(req)
        channel.close()
        
        stations = [{
            "station_id": s.station_id,
            "name": s.name,
            "lat": s.lat,
            "lng": s.lng
        } for s in res.stations]
        
        return jsonify({"stations": stations})
    except Exception as e:
        logger.error(f"Error getting stations: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/stations/<station_id>', methods=['GET'])
def get_station(station_id):
    try:
        stub, channel = get_station_stub()
        req = station_pb2.StationRequest(station_id=station_id)
        res = stub.GetStation(req)
        channel.close()
        
        if not res.station:
            return jsonify({"error": "Station not found"}), 404
        
        station = {
            "station_id": res.station.station_id,
            "name": res.station.name,
            "lat": res.station.lat,
            "lng": res.station.lng
        }
        
        return jsonify({"station": station})
    except Exception as e:
        logger.error(f"Error getting station: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/drivers/register', methods=['POST'])
def register_driver():
    try:
        data = request.json
        stub, channel = get_driver_stub()
        
        profile = driver_pb2.DriverProfile(
            driver_id=data.get("driver_id"),
            user_id=data.get("user_id", f"user-{data.get('driver_id')}"),
            name=data.get("name"),
            phone=data.get("phone"),
            vehicle_no=data.get("vehicle_no")
        )
        
        req = driver_pb2.RegisterDriverRequest(profile=profile)
        res = stub.RegisterDriver(req)
        channel.close()
        
        if res.ok:
            return jsonify({"driver_id": res.driver_id, "ok": True})
        else:
            return jsonify({"error": "Registration failed"}), 400
    except Exception as e:
        logger.error(f"Error registering driver: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/riders/register', methods=['POST'])
def register_rider():
    try:
        data = request.json
        stub, channel = get_rider_stub()
        
        profile = rider_pb2.RiderProfile(
            rider_id=data.get("rider_id"),
            user_id=data.get("user_id", f"user-{data.get('rider_id')}"),
            name=data.get("name"),
            phone=data.get("phone")
        )
        
        req = rider_pb2.RegisterRiderRequest(profile=profile)
        res = stub.RegisterRider(req)
        channel.close()
        
        if res.ok:
            return jsonify({"rider_id": res.rider_id, "ok": True})
        else:
            return jsonify({"error": "Registration failed"}), 400
    except Exception as e:
        logger.error(f"Error registering rider: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/riders/request-pickup', methods=['POST'])
def request_pickup():
    try:
        data = request.json
        stub, channel = get_rider_stub()
        
        req = rider_pb2.RequestPickupRequest(
            rider_id=data.get("rider_id"),
            station_id=data.get("station_id"),
            arrival_time=data.get("arrival_time", int(time.time() * 1000)),
            destination=data.get("destination"),
            request_id=data.get("request_id", f"req-{int(time.time()*1000)}")
        )
        
        res = stub.RequestPickup(req)
        channel.close()
        
        if res.ok:
            return jsonify({"request_id": res.request_id, "ok": True})
        else:
            return jsonify({"error": "Request failed"}), 400
    except Exception as e:
        logger.error(f"Error requesting pickup: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/trips', methods=['GET'])
def get_trips():
    trips = []
    
    # Method 1: Try to query database directly via port-forward
    try:
        with db_engine.connect() as conn:
            result = conn.execute(text("""
                SELECT trip_id, driver_id, rider_ids, origin_station, destination,
                       status, start_time, end_time, seats_reserved
                FROM trips
                WHERE status != 'completed' OR end_time > (EXTRACT(EPOCH FROM NOW()) * 1000 - 3600000)
                ORDER BY start_time DESC
                LIMIT 50
            """))
            
            for row in result:
                rider_ids = row.rider_ids.split(",") if row.rider_ids else []
                trips.append({
                    "trip_id": row.trip_id,
                    "driver_id": row.driver_id,
                    "rider_ids": rider_ids,
                    "origin_station": row.origin_station,
                    "destination": row.destination,
                    "status": row.status,
                    "start_time": row.start_time,
                    "end_time": row.end_time,
                    "seats_reserved": row.seats_reserved
                })
        
        logger.info(f"Found {len(trips)} trips from database")
        return jsonify({"trips": trips})
        
    except Exception as db_error:
        logger.warning(f"Database query failed: {db_error}")
        
        # Method 2: Try to query via kubectl exec (fallback for port-forward issues)
        try:
            import subprocess
            cmd = [
                "kubectl", "-n", "lastmile", "exec", "postgres-0", "--",
                "psql", "-U", "lastmile", "-d", "lastmile", "-t", "-A", "-F", "|",
                "-c", """
                    SELECT 
                        trip_id, driver_id, rider_ids, origin_station, destination,
                        status, start_time, end_time, seats_reserved
                    FROM trips
                    ORDER BY start_time DESC
                    LIMIT 100;
                """
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if not line or line.startswith('(') or 'rows' in line.lower():
                        continue
                    parts = line.split('|')
                    if len(parts) >= 9:
                        rider_ids = [r.strip() for r in parts[2].split(',')] if parts[2].strip() else []
                        trips.append({
                            "trip_id": parts[0].strip(),
                            "driver_id": parts[1].strip(),
                            "rider_ids": rider_ids,
                            "origin_station": parts[3].strip(),
                            "destination": parts[4].strip(),
                            "status": parts[5].strip(),
                            "start_time": int(parts[6].strip()) if parts[6].strip() else None,
                            "end_time": int(parts[7].strip()) if parts[7].strip() else None,
                            "seats_reserved": int(parts[8].strip()) if parts[8].strip() else 0
                        })
                
                if trips:
                    logger.info(f"Found {len(trips)} trips via kubectl")
                    return jsonify({"trips": trips, "source": "kubectl"})
        except Exception as k8s_error:
            logger.warning(f"Kubectl fallback failed: {k8s_error}")
        
        # Method 3: Try RabbitMQ match.found queue
        try:
            conn = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
            ch = conn.channel()
            ch.queue_declare(queue="match.found", durable=True)
            
            match_trips = []
            # Peek at messages without consuming
            for _ in range(20):  # Limit to prevent infinite loop
                method, props, body = ch.basic_get("match.found", auto_ack=False)
                if not method:
                    break
                
                try:
                    match_data = json.loads(body)
                    match_trips.append({
                        "trip_id": match_data.get("trip_id", f"trip-{int(time.time()*1000)}"),
                        "driver_id": match_data.get("driver_id", ""),
                        "rider_ids": match_data.get("rider_ids", []),
                        "origin_station": match_data.get("station_id", ""),
                        "destination": match_data.get("destination", ""),
                        "status": "scheduled",
                        "start_time": match_data.get("ts", int(time.time()*1000)),
                        "end_time": None,
                        "seats_reserved": len(match_data.get("rider_ids", []))
                    })
                except:
                    pass
                
                ch.basic_nack(method.delivery_tag, requeue=True)
            
            conn.close()
            
            if match_trips:
                logger.info(f"Found {len(match_trips)} trips from RabbitMQ")
                return jsonify({"trips": match_trips, "source": "rabbitmq"})
        except Exception as mq_error:
            logger.warning(f"RabbitMQ fallback failed: {mq_error}")
        
        # Method 4: Return empty array
        return jsonify({"trips": [], "note": "All query methods failed"})

@app.route('/api/trips/<trip_id>', methods=['GET'])
def get_trip(trip_id):
    try:
        stub, channel = get_trip_stub()
        req = trip_pb2.GetTripRequest(trip_id=trip_id)
        res = stub.GetTrip(req)
        channel.close()
        
        if not res.trip:
            return jsonify({"error": "Trip not found"}), 404
        
        trip = {
            "trip_id": res.trip.trip_id,
            "driver_id": res.trip.driver_id,
            "rider_ids": list(res.trip.rider_ids),
            "origin_station": res.trip.origin_station,
            "destination": res.trip.destination,
            "status": res.trip.status,
            "start_time": res.trip.start_time,
            "end_time": res.trip.end_time,
            "seats_reserved": res.trip.seats_reserved
        }
        
        return jsonify({"trip": trip})
    except Exception as e:
        logger.error(f"Error getting trip: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/trips/<trip_id>/start', methods=['POST'])
def start_trip(trip_id):
    """Mark trip as active (started)"""
    try:
        stub, channel = get_trip_stub()
        
        update = trip_pb2.Trip(
            trip_id=trip_id,
            status="active",
            rider_ids=[]
        )
        
        req = trip_pb2.UpdateTripRequest(trip=update)
        res = stub.UpdateTrip(req)
        channel.close()
        
        if res.ok:
            return jsonify({"ok": True, "status": "active"})
        else:
            return jsonify({"error": "Update failed"}), 400
    except Exception as e:
        logger.error(f"Error starting trip: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/trips/<trip_id>/complete', methods=['POST'])
def complete_trip(trip_id):
    """Mark trip as completed"""
    try:
        stub, channel = get_trip_stub()
        
        update = trip_pb2.Trip(
            trip_id=trip_id,
            status="completed",
            rider_ids=[]
        )
        
        req = trip_pb2.UpdateTripRequest(trip=update)
        res = stub.UpdateTrip(req)
        channel.close()
        
        if res.ok:
            return jsonify({"ok": True, "status": "completed"})
        else:
            return jsonify({"error": "Update failed"}), 400
    except Exception as e:
        logger.error(f"Error completing trip: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv("PORT", 8081))  # Changed default to 8081 to avoid conflicts
    app.run(host='0.0.0.0', port=port, debug=True)
