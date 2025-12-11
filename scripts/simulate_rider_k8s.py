"""
Enhanced Rider Simulator for Kubernetes
Simulates riders requesting pickups at stations.

Usage:
    # With port forwarding:
    kubectl -n lastmile port-forward svc/rider-service 50057:50057 &
    python scripts/simulate_rider_k8s.py --rider-id rider-1 --station-id ST101

    # From within cluster:
    python scripts/simulate_rider_k8s.py --rider-id rider-1 --station-id ST101 --use-k8s-services
"""
import argparse
import time
import grpc
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.common_lib.protos_generated import rider_pb2, rider_pb2_grpc, station_pb2, station_pb2_grpc


def get_service_host(service_name, default_port, use_k8s):
    if use_k8s:
        return f"{service_name}:{default_port}"
    return f"localhost:{default_port}"


def get_stations(use_k8s=False):
    """Get list of available stations."""
    host = get_service_host("station-service", 50051, use_k8s)
    channel = grpc.insecure_channel(host)
    stub = station_pb2_grpc.StationServiceStub(channel)
    
    req = station_pb2.StationListRequest()
    try:
        res = stub.ListStations(req)
        channel.close()
        return [(s.station_id, s.name) for s in res.stations]
    except Exception as e:
        print(f"Error getting stations: {e}")
        channel.close()
        return []


def register_rider(rider_id, name, phone, use_k8s=False):
    """Register a rider."""
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
    return res.ok


def request_pickup(rider_id, station_id, destination, use_k8s=False):
    """Request a pickup."""
    host = get_service_host("rider-service", 50057, use_k8s)
    channel = grpc.insecure_channel(host)
    stub = rider_pb2_grpc.RiderServiceStub(channel)
    
    req = rider_pb2.RequestPickupRequest(
        rider_id=rider_id,
        station_id=station_id,
        arrival_time=int(time.time() * 1000),
        destination=destination,
        request_id=f"req-{int(time.time()*1000)}"
    )
    res = stub.RequestPickup(req)
    channel.close()
    return res.ok, res.request_id


def run(rider_id, station_id, destination, name, phone, use_k8s=False):
    print(f"🚴 Simulating rider: {rider_id}")
    
    # Register rider
    print(f"Registering rider {rider_id}...")
    if register_rider(rider_id, name, phone, use_k8s):
        print(f"✅ Rider registered: {rider_id}")
    else:
        print(f"⚠️  Registration failed (may already exist)")
    
    time.sleep(1)
    
    # Request pickup
    print(f"\n📍 Requesting pickup at station {station_id}")
    print(f"   Destination: {destination}")
    ok, request_id = request_pickup(rider_id, station_id, destination, use_k8s)
    
    if ok:
        print(f"✅ Pickup request submitted: {request_id}")
        print(f"   Waiting for match...")
    else:
        print(f"❌ Pickup request failed")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Simulate rider pickup request")
    parser.add_argument('--rider-id', default='rider-sim-1', help='Rider ID')
    parser.add_argument('--station-id', help='Station ID (required)')
    parser.add_argument('--destination', default='Downtown', help='Destination')
    parser.add_argument('--name', default=None, help='Rider name')
    parser.add_argument('--phone', default='0000000000', help='Rider phone')
    parser.add_argument('--list-stations', action='store_true', help='List available stations')
    parser.add_argument('--use-k8s-services', action='store_true', help='Use Kubernetes service names')
    args = parser.parse_args()
    
    if args.list_stations:
        stations = get_stations(args.use_k8s_services)
        print("\nAvailable Stations:")
        print("-" * 50)
        for sid, sname in stations:
            print(f"  {sid}: {sname}")
        print()
    elif args.station_id:
        name = args.name or f"Rider {args.rider_id}"
        run(args.rider_id, args.station_id, args.destination, name, args.phone, args.use_k8s_services)
    else:
        print("Error: --station-id is required (use --list-stations to see available stations)")
        parser.print_help()

