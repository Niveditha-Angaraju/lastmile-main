"""
Enhanced E2E Test for Kubernetes Deployment
This test script works with services deployed in Kubernetes.
It uses port forwarding or service names to connect to services.

Usage:
    # Option 1: Port forward services first
    kubectl -n lastmile port-forward svc/rider-service 50057:50057 &
    kubectl -n lastmile port-forward svc/driver-service 50052:50052 &
    kubectl -n lastmile port-forward svc/trip-service 50055:50055 &
    kubectl -n lastmile port-forward svc/rabbitmq 5672:5672 &
    
    python tests/e2e_test_k8s.py

    # Option 2: Run from within a pod that has access to services
    python tests/e2e_test_k8s.py --use-k8s-services
"""
import time
import json
import pika
import grpc
import argparse
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.common_lib.protos_generated import (
    driver_pb2, driver_pb2_grpc,
    rider_pb2, rider_pb2_grpc,
    trip_pb2, trip_pb2_grpc,
    station_pb2, station_pb2_grpc,
)

def get_rabbit_url(use_k8s):
    if use_k8s:
        return "amqp://guest:guest@rabbitmq:5672/"
    return "amqp://guest:guest@localhost:5672/"

def get_service_host(service_name, default_port, use_k8s):
    if use_k8s:
        return f"{service_name}:{default_port}"
    return f"localhost:{default_port}"

def rabbit_channel(use_k8s=False):
    url = get_rabbit_url(use_k8s)
    conn = pika.BlockingConnection(pika.URLParameters(url))
    return conn, conn.channel()

# -------------------------------------------------------------------
# 1) Publish rider request
# -------------------------------------------------------------------
def publish_rider_request(rider_id, station_id, destination, use_k8s=False):
    conn, ch = rabbit_channel(use_k8s)
    ch.queue_declare(queue="rider.requests", durable=True)

    req = {
        "rider_id": rider_id,
        "arrival_time": int(time.time() * 1000),
        "station_id": station_id,
        "destination": destination,
    }

    ch.basic_publish(
        exchange="",
        routing_key="rider.requests",
        body=json.dumps(req).encode(),
        properties=pika.BasicProperties(delivery_mode=2)
    )
    conn.close()
    print(f"[TEST] Published rider request: {req}")


# -------------------------------------------------------------------
# 2) Publish driver proximity event
# -------------------------------------------------------------------
def publish_driver_proximity(driver_id, station_id, seats, destination, use_k8s=False):
    conn, ch = rabbit_channel(use_k8s)
    ch.queue_declare(queue="driver.near_station", durable=True)

    event = {
        "driver_id": driver_id,
        "station_id": station_id,
        "available_seats": seats,
        "destination": destination,
        "ts": int(time.time()*1000)
    }

    ch.basic_publish(
        exchange="",
        routing_key="driver.near_station",
        body=json.dumps(event).encode(),
        properties=pika.BasicProperties(delivery_mode=2)
    )
    conn.close()
    print(f"[TEST] Published driver proximity: {event}")


# -------------------------------------------------------------------
# 3) Consume match.found event
# -------------------------------------------------------------------
def consume_match_found(timeout=5, use_k8s=False):
    print("[TEST] Waiting for match.found...")

    conn, ch = rabbit_channel(use_k8s)
    ch.queue_declare(queue="match.found", durable=True)

    method_frame, header, body = ch.basic_get("match.found", auto_ack=True)

    deadline = time.time() + timeout
    while not method_frame and time.time() < deadline:
        method_frame, header, body = ch.basic_get("match.found", auto_ack=True)
        time.sleep(0.2)

    conn.close()

    if not method_frame:
        print("[❌ TEST FAILED] No match event received.")
        return None

    event = json.loads(body.decode())
    print("[✅ TEST] Match Found:", event)
    return event


# -------------------------------------------------------------------
# 4) Register rider via gRPC
# -------------------------------------------------------------------
def register_rider(rider_id, name, phone, use_k8s=False):
    host = get_service_host("rider-service", 50057, use_k8s)
    channel = grpc.insecure_channel(host)
    stub = rider_pb2_grpc.RiderServiceStub(channel)
    
    profile = rider_pb2.RiderProfile(
        rider_id=rider_id,
        user_id=f"user-{rider_id}",
        name=name,
        phone=phone
    )
    req = rider_pb2.RegisterRiderRequest(profile=profile)
    res = stub.RegisterRider(req)
    channel.close()
    print(f"[TEST] Registered rider {rider_id}: {res.ok}")
    return res.ok


# -------------------------------------------------------------------
# 5) Register driver via gRPC
# -------------------------------------------------------------------
def register_driver(driver_id, name, phone, vehicle_no, use_k8s=False):
    host = get_service_host("driver-service", 50052, use_k8s)
    channel = grpc.insecure_channel(host)
    stub = driver_pb2_grpc.DriverServiceStub(channel)
    
    profile = driver_pb2.DriverProfile(
        driver_id=driver_id,
        user_id=f"user-{driver_id}",
        name=name,
        phone=phone,
        vehicle_no=vehicle_no
    )
    req = driver_pb2.RegisterDriverRequest(profile=profile)
    res = stub.RegisterDriver(req)
    channel.close()
    print(f"[TEST] Registered driver {driver_id}: {res.ok}")
    return res.ok


# -------------------------------------------------------------------
# 6) Get stations list
# -------------------------------------------------------------------
def get_stations(use_k8s=False):
    host = get_service_host("station-service", 50051, use_k8s)
    channel = grpc.insecure_channel(host)
    stub = station_pb2_grpc.StationServiceStub(channel)
    
    req = station_pb2.StationListRequest()
    res = stub.ListStations(req)
    channel.close()
    stations = [(s.station_id, s.name, s.lat, s.lng) for s in res.stations]
    print(f"[TEST] Found {len(stations)} stations")
    return stations


# -------------------------------------------------------------------
# 7) Mark trip as completed
# -------------------------------------------------------------------
def complete_trip(trip_id, use_k8s=False):
    print(f"[TEST] Completing trip {trip_id}...")
    host = get_service_host("trip-service", 50055, use_k8s)
    channel = grpc.insecure_channel(host)
    stub = trip_pb2_grpc.TripServiceStub(channel)

    update = trip_pb2.Trip(trip_id=trip_id, status="completed", rider_ids=[])
    req = trip_pb2.UpdateTripRequest(trip=update)
    res = stub.UpdateTrip(req)
    channel.close()
    print(f"[TEST] Trip completed: {res.ok}")
    return res.ok


# -------------------------------------------------------------------
# 8) Full E2E Test Flow
# -------------------------------------------------------------------
def run_e2e_test(use_k8s=False):
    print("\n" + "="*60)
    print("E2E TEST START (Kubernetes Mode)" if use_k8s else "E2E TEST START (Local Mode)")
    print("="*60 + "\n")

    # Get available stations
    stations = get_stations(use_k8s)
    if not stations:
        print("[❌ TEST FAILED] No stations found. Please seed stations first.")
        return False
    
    # Use first few stations
    station1 = stations[0][0] if len(stations) > 0 else "ST101"
    station2 = stations[1][0] if len(stations) > 1 else "ST102"
    station3 = stations[2][0] if len(stations) > 2 else "ST103"
    
    DRIVER = "drv-test-1"
    DEST = "Downtown"

    # Register driver
    register_driver(DRIVER, "Test Driver", "1234567890", "TEST-001", use_k8s)
    time.sleep(1)

    # Register riders
    register_rider("rider-1", "Rider One", "1111111111", use_k8s)
    register_rider("rider-2", "Rider Two", "2222222222", use_k8s)
    register_rider("rider-3", "Rider Three", "3333333333", use_k8s)
    register_rider("rider-4", "Rider Four", "4444444444", use_k8s)
    time.sleep(1)

    # -----------------------------------------------------------
    # Rider1 requests pickup at station1
    # -----------------------------------------------------------
    print(f"\n[STEP 1] Rider-1 requests pickup at {station1}")
    publish_rider_request("rider-1", station1, DEST, use_k8s)
    time.sleep(2)

    # -----------------------------------------------------------
    # Driver gets near station1 with 2 seats
    # -----------------------------------------------------------
    print(f"\n[STEP 2] Driver {DRIVER} arrives at {station1} with 2 seats")
    publish_driver_proximity(DRIVER, station1, seats=2, destination=DEST, use_k8s=use_k8s)
    time.sleep(2)

    event = consume_match_found(timeout=10, use_k8s=use_k8s)
    if not event:
        print("[❌ TEST FAILED] No match for rider-1")
        return False

    trip_id = event["trip_id"]
    print(f"[✅ TEST] Match created: trip_id={trip_id}")

    # -----------------------------------------------------------
    # Rider2 requests at next station
    # -----------------------------------------------------------
    print(f"\n[STEP 3] Rider-2 requests pickup at {station2}")
    publish_rider_request("rider-2", station2, DEST, use_k8s)
    time.sleep(2)

    # Driver reaches station2 with only 1 seat left
    print(f"\n[STEP 4] Driver {DRIVER} arrives at {station2} with 1 seat")
    publish_driver_proximity(DRIVER, station2, seats=1, destination=DEST, use_k8s=use_k8s)
    time.sleep(2)

    event2 = consume_match_found(timeout=10, use_k8s=use_k8s)
    if not event2:
        print("[❌ TEST FAILED] No match for rider-2")
        return False
    print(f"[✅ TEST] Match created for rider-2: trip_id={event2['trip_id']}")

    # -----------------------------------------------------------
    # Now driver should have 0 seats
    # Rider requesting again should NOT match
    # -----------------------------------------------------------
    print(f"\n[STEP 5] Rider-3 requests pickup at {station3} (should NOT match - no seats)")
    publish_rider_request("rider-3", station3, DEST, use_k8s)
    time.sleep(2)

    publish_driver_proximity(DRIVER, station3, seats=0, destination=DEST, use_k8s=use_k8s)
    time.sleep(2)

    no_match = consume_match_found(timeout=3, use_k8s=use_k8s)
    if no_match:
        print("[❌ TEST FAILED] A match happened when seats were 0!")
        return False
    else:
        print("[✅ TEST] Correct: No match with 0 seats")

    # -----------------------------------------------------------
    # COMPLETE TRIP
    # -----------------------------------------------------------
    print(f"\n[STEP 6] Completing trip {trip_id}")
    complete_trip(trip_id, use_k8s)
    time.sleep(3)

    # -----------------------------------------------------------
    # Seats should now RESET to DEFAULT_SEATS
    # New rider should be matched
    # -----------------------------------------------------------
    print(f"\n[STEP 7] Rider-4 requests pickup at {station1} (after seat reset)")
    publish_rider_request("rider-4", station1, DEST, use_k8s)
    time.sleep(2)

    publish_driver_proximity(DRIVER, station1, seats=2, destination=DEST, use_k8s=use_k8s)
    time.sleep(2)

    event3 = consume_match_found(timeout=10, use_k8s=use_k8s)
    if event3:
        print(f"[✅ TEST] Correct: New trip matched after seat reset! trip_id={event3['trip_id']}")
    else:
        print("[❌ TEST FAILED] No match after seat reset.")
        return False

    print("\n" + "="*60)
    print("✅ E2E TEST COMPLETE - ALL TESTS PASSED")
    print("="*60 + "\n")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="E2E Test for LastMile Kubernetes Deployment")
    parser.add_argument("--use-k8s-services", action="store_true",
                       help="Connect directly to Kubernetes services (run from within cluster)")
    args = parser.parse_args()

    success = run_e2e_test(use_k8s=args.use_k8s_services)
    sys.exit(0 if success else 1)

