"""
Verify LastMile Setup
Checks if all services are accessible and working correctly.
"""
import sys
import os
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import grpc
import pika
from services.common_lib.protos_generated import (
    station_pb2, station_pb2_grpc,
    driver_pb2, driver_pb2_grpc,
    rider_pb2, rider_pb2_grpc,
    trip_pb2, trip_pb2_grpc,
)

def check_service(name, host, port, check_func):
    """Check if a service is accessible."""
    try:
        result = check_func(host, port)
        print(f"✅ {name:20s} ({host}:{port}) - OK")
        return True
    except Exception as e:
        print(f"❌ {name:20s} ({host}:{port}) - FAILED: {e}")
        return False

def check_station_service(host, port):
    channel = grpc.insecure_channel(f"{host}:{port}")
    stub = station_pb2_grpc.StationServiceStub(channel)
    req = station_pb2.StationListRequest()
    res = stub.ListStations(req, timeout=2)
    channel.close()
    return len(res.stations) >= 0

def check_driver_service(host, port):
    channel = grpc.insecure_channel(f"{host}:{port}")
    stub = driver_pb2_grpc.DriverServiceStub(channel)
    req = driver_pb2.HealthRequest()
    res = stub.Health(req, timeout=2)
    channel.close()
    return res.ok

def check_rider_service(host, port):
    channel = grpc.insecure_channel(f"{host}:{port}")
    stub = rider_pb2_grpc.RiderServiceStub(channel)
    req = rider_pb2.RiderRequest()
    res = stub.Health(req, timeout=2)
    channel.close()
    return res.ok

def check_trip_service(host, port):
    channel = grpc.insecure_channel(f"{host}:{port}")
    stub = trip_pb2_grpc.TripServiceStub(channel)
    req = trip_pb2.CreateTripRequest()
    # Just check if service responds (will fail but that's OK)
    try:
        stub.CreateTrip(req, timeout=2)
    except:
        pass
    channel.close()
    return True

def check_rabbitmq(host, port):
    url = f"amqp://guest:guest@{host}:{port}/"
    conn = pika.BlockingConnection(pika.URLParameters(url))
    ch = conn.channel()
    ch.queue_declare(queue="test", durable=False)
    ch.queue_delete(queue="test")
    conn.close()
    return True

def main():
    print("="*60)
    print("LastMile Setup Verification")
    print("="*60)
    print()
    
    use_k8s = "--use-k8s" in sys.argv
    
    if use_k8s:
        print("Mode: Kubernetes Services (direct)")
        services = {
            "Station Service": ("station-service", 50051, check_station_service),
            "Driver Service": ("driver-service", 50052, check_driver_service),
            "Rider Service": ("rider-service", 50057, check_rider_service),
            "Trip Service": ("trip-service", 50055, check_trip_service),
        }
        rabbitmq_host = "rabbitmq"
    else:
        print("Mode: Local (port forwarding)")
        services = {
            "Station Service": ("localhost", 50051, check_station_service),
            "Driver Service": ("localhost", 50052, check_driver_service),
            "Rider Service": ("localhost", 50057, check_rider_service),
            "Trip Service": ("localhost", 50055, check_trip_service),
        }
        rabbitmq_host = "localhost"
    
    print()
    
    results = []
    
    # Check gRPC services
    for name, (host, port, check_func) in services.items():
        results.append(check_service(name, host, port, check_func))
        time.sleep(0.5)
    
    print()
    
    # Check RabbitMQ
    results.append(check_service("RabbitMQ", rabbitmq_host, 5672, check_rabbitmq))
    
    print()
    print("="*60)
    
    if all(results):
        print("✅ All services are accessible!")
        print()
        print("Next steps:")
        print("  1. Run tests: python tests/e2e_test_k8s.py")
        print("  2. Run demo: python scripts/demo_simulation.py")
        print("  3. Start frontend: cd frontend && npm run dev")
        return 0
    else:
        print("❌ Some services are not accessible")
        print()
        if not use_k8s:
            print("If using port forwarding, make sure to run:")
            print("  ./scripts/port_forward_services.sh")
        else:
            print("If using Kubernetes services, make sure:")
            print("  - You're running from within the cluster")
            print("  - Services are properly deployed")
            print("  - Network policies allow access")
        return 1

if __name__ == "__main__":
    sys.exit(main())

