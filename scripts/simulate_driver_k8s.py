"""
Enhanced Driver Simulator for Kubernetes
Simulates a driver moving along a route, updating location in real-time.
Works with Kubernetes deployment.

Usage:
    # With port forwarding:
    kubectl -n lastmile port-forward svc/driver-service 50052:50052 &
    python scripts/simulate_driver_k8s.py --driver-id drv-1 --station-id ST101

    # From within cluster:
    python scripts/simulate_driver_k8s.py --driver-id drv-1 --station-id ST101 --use-k8s-services
"""
import argparse
import time
import grpc
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.common_lib.protos_generated import driver_pb2, driver_pb2_grpc, station_pb2, station_pb2_grpc


def get_service_host(service_name, default_port, use_k8s):
    if use_k8s:
        return f"{service_name}:{default_port}"
    return f"localhost:{default_port}"


def generate_route_points(start_lat, start_lng, end_lat, end_lng, steps=20):
    """Generate points along a route from start to end."""
    pts = []
    lat_step = (end_lat - start_lat) / steps
    lng_step = (end_lng - start_lng) / steps
    
    for i in range(steps + 1):
        lat = start_lat + (lat_step * i)
        lng = start_lng + (lng_step * i)
        pts.append((lat, lng))
    return pts


def get_station_coords(station_id, use_k8s=False):
    """Get station coordinates via StationService."""
    host = get_service_host("station-service", 50051, use_k8s)
    channel = grpc.insecure_channel(host)
    stub = station_pb2_grpc.StationServiceStub(channel)
    
    req = station_pb2.StationRequest(station_id=station_id)
    try:
        res = stub.GetStation(req)
        channel.close()
        if res.station:
            return res.station.lat, res.station.lng
    except:
        pass
    channel.close()
    return None, None


def run(driver_id, host, port, station_id, destination, interval, available_seats, use_k8s=False):
    target = f"{host}:{port}" if not use_k8s else get_service_host("driver-service", 50052, True)
    print(f"Connecting to DriverService at {target}")
    
    channel = grpc.insecure_channel(target)
    stub = driver_pb2_grpc.DriverServiceStub(channel)

    # Register driver
    print(f"Registering driver {driver_id}...")
    profile = driver_pb2.DriverProfile(
        driver_id=driver_id,
        user_id=f"user-{driver_id}",
        name=f"Driver {driver_id}",
        phone="0000000000",
        vehicle_no=f"VEH-{driver_id}"
    )
    reg_res = stub.RegisterDriver(driver_pb2.RegisterDriverRequest(profile=profile))
    if not reg_res.ok:
        print(f"Failed to register driver: {reg_res}")
        return
    print(f"✅ Driver registered: {driver_id}")

    # Get station coordinates
    station_lat, station_lng = get_station_coords(station_id, use_k8s)
    if not station_lat or not station_lng:
        print(f"⚠️  Could not get station coordinates, using default")
        station_lat, station_lng = 12.9710, 77.5940  # Default: Bangalore

    # Generate route points (start 2km away, move towards station)
    start_lat = station_lat - 0.018  # ~2km south
    start_lng = station_lng - 0.018  # ~2km west
    
    route_points = generate_route_points(start_lat, start_lng, station_lat, station_lng, steps=30)
    print(f"Generated route with {len(route_points)} points from ({start_lat:.4f}, {start_lng:.4f}) to ({station_lat:.4f}, {station_lng:.4f})")

    # Update route
    route = driver_pb2.Route(
        route_id=f"route-{driver_id}",
        station_ids=[station_id],
        waypoints=[f"{lat},{lng}" for lat, lng in route_points]
    )
    route_res = stub.UpdateRoute(driver_pb2.DriverRouteRequest(
        driver_id=driver_id,
        route=route,
        destination=destination,
        available_seats=available_seats
    ))
    print(f"✅ Route updated: {route_res.ok}")

    # Stream location updates
    print(f"\n🚗 Starting location stream (updating every {interval}s)...")
    print(f"   Moving from ({start_lat:.4f}, {start_lng:.4f}) towards station {station_id}")
    print(f"   Destination: {destination}, Available seats: {available_seats}")
    print("   Press Ctrl+C to stop\n")

    def location_generator():
        ts_base = int(time.time() * 1000)
        for i, (lat, lng) in enumerate(route_points):
            # Determine if near station (last 3 points)
            is_near_station = i >= len(route_points) - 3
            current_station = station_id if is_near_station else ""
            
            # Calculate ETA (decreasing as we approach)
            remaining_steps = len(route_points) - i
            eta_seconds = remaining_steps * interval
            eta_ms = eta_seconds * 1000

            loc = driver_pb2.LocationUpdate(
                driver_id=driver_id,
                lat=lat,
                lng=lng,
                timestamp=int(time.time() * 1000),
                status="enroute" if not is_near_station else "arriving",
                station_id=current_station,
                available_seats=available_seats,
                destination=destination,
                eta_ms=eta_ms,
            )
            
            status_icon = "📍" if is_near_station else "🚗"
            print(f"{status_icon} [{i+1}/{len(route_points)}] Lat: {lat:.6f}, Lng: {lng:.6f}, ETA: {eta_seconds}s, Station: {current_station or 'N/A'}")
            yield loc
            time.sleep(interval)

    try:
        ack = stub.StreamLocation(location_generator())
        print(f"\n✅ Stream completed, ack: {ack}")
    except KeyboardInterrupt:
        print("\n⚠️  Stream interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during stream: {e}")
    finally:
        channel.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Simulate driver location updates")
    parser.add_argument('--driver-id', default='drv-sim-1', help='Driver ID')
    parser.add_argument('--host', default='localhost', help='Driver service host')
    parser.add_argument('--port', default=50052, type=int, help='Driver service port')
    parser.add_argument('--station-id', default='ST101', help='Target station ID')
    parser.add_argument('--destination', default='Downtown', help='Destination')
    parser.add_argument('--interval', default=2, type=int, help='Update interval in seconds')
    parser.add_argument('--seats', default=2, type=int, help='Available seats')
    parser.add_argument('--use-k8s-services', action='store_true', help='Use Kubernetes service names')
    args = parser.parse_args()
    
    run(args.driver_id, args.host, args.port, args.station_id, args.destination, 
        args.interval, args.seats, args.use_k8s_services)

