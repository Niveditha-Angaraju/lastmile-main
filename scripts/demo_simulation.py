"""
Complete Demo Simulation Script
Simulates a full ride matching scenario with multiple drivers and riders.

Usage:
    # With port forwarding:
    ./scripts/port_forward_services.sh &
    python scripts/demo_simulation.py

    # From within cluster:
    python scripts/demo_simulation.py --use-k8s-services
"""
import argparse
import time
import threading
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.simulate_driver_k8s import run as simulate_driver
from scripts.simulate_rider_k8s import run as simulate_rider, get_stations
from tests.e2e_test_k8s import (
    register_driver, register_rider, publish_rider_request,
    publish_driver_proximity, consume_match_found, complete_trip
)


def get_service_host(service_name, default_port, use_k8s):
    if use_k8s:
        return f"{service_name}:{default_port}"
    return f"localhost:{default_port}"


def run_demo(use_k8s=False):
    print("\n" + "="*70)
    print("🚗 LastMile Complete Demo Simulation")
    print("="*70 + "\n")

    # Get available stations
    stations = get_stations(use_k8s)
    if not stations:
        print("❌ No stations found. Please seed stations first.")
        return
    
    print(f"✅ Found {len(stations)} stations")
    for sid, sname in stations[:5]:
        print(f"   - {sid}: {sname}")
    
    if len(stations) < 3:
        print("⚠️  Need at least 3 stations for full demo")
        return
    
    station1 = stations[0][0]
    station2 = stations[1][0] if len(stations) > 1 else stations[0][0]
    station3 = stations[2][0] if len(stations) > 2 else stations[0][0]
    
    destination = "Downtown"
    
    print(f"\n📍 Using stations: {station1}, {station2}, {station3}")
    print(f"🎯 Destination: {destination}\n")

    # Register participants
    print("="*70)
    print("STEP 1: Registering Drivers and Riders")
    print("="*70)
    
    driver1 = "drv-demo-1"
    driver2 = "drv-demo-2"
    
    register_driver(driver1, "Demo Driver 1", "1111111111", "VEH-001", use_k8s)
    register_driver(driver2, "Demo Driver 2", "2222222222", "VEH-002", use_k8s)
    time.sleep(1)
    
    rider1 = "rider-demo-1"
    rider2 = "rider-demo-2"
    rider3 = "rider-demo-3"
    
    register_rider(rider1, "Demo Rider 1", "3333333333", use_k8s)
    register_rider(rider2, "Demo Rider 2", "4444444444", use_k8s)
    register_rider(rider3, "Demo Rider 3", "5555555555", use_k8s)
    time.sleep(1)

    # Scenario 1: Driver 1 picks up Rider 1 at Station 1
    print("\n" + "="*70)
    print("STEP 2: Scenario 1 - Driver 1 picks up Rider 1")
    print("="*70)
    
    print(f"\n🚴 Rider {rider1} requests pickup at {station1}")
    publish_rider_request(rider1, station1, destination, use_k8s)
    time.sleep(2)
    
    print(f"\n🚗 Driver {driver1} arrives at {station1} with 2 seats")
    publish_driver_proximity(driver1, station1, seats=2, destination=destination, use_k8s=use_k8s)
    time.sleep(3)
    
    match1 = consume_match_found(timeout=10, use_k8s=use_k8s)
    if match1:
        print(f"✅ Match created: {match1}")
        trip_id1 = match1["trip_id"]
    else:
        print("❌ No match found")
        trip_id1 = None

    # Scenario 2: Driver 1 picks up Rider 2 at Station 2 (1 seat left)
    print("\n" + "="*70)
    print("STEP 3: Scenario 2 - Driver 1 picks up Rider 2 (1 seat left)")
    print("="*70)
    
    print(f"\n🚴 Rider {rider2} requests pickup at {station2}")
    publish_rider_request(rider2, station2, destination, use_k8s)
    time.sleep(2)
    
    print(f"\n🚗 Driver {driver1} arrives at {station2} with 1 seat")
    publish_driver_proximity(driver1, station2, seats=1, destination=destination, use_k8s=use_k8s)
    time.sleep(3)
    
    match2 = consume_match_found(timeout=10, use_k8s=use_k8s)
    if match2:
        print(f"✅ Match created: {match2}")
    else:
        print("❌ No match found")

    # Scenario 3: Driver 1 is full, Rider 3 should not match
    print("\n" + "="*70)
    print("STEP 4: Scenario 3 - Driver 1 is full (no match)")
    print("="*70)
    
    print(f"\n🚴 Rider {rider3} requests pickup at {station3}")
    publish_rider_request(rider3, station3, destination, use_k8s)
    time.sleep(2)
    
    print(f"\n🚗 Driver {driver1} arrives at {station3} with 0 seats (FULL)")
    publish_driver_proximity(driver1, station3, seats=0, destination=destination, use_k8s=use_k8s)
    time.sleep(2)
    
    no_match = consume_match_found(timeout=3, use_k8s=use_k8s)
    if no_match:
        print("❌ ERROR: Match happened when driver was full!")
    else:
        print("✅ Correct: No match when driver is full")

    # Scenario 4: Complete trip and reset seats
    if trip_id1:
        print("\n" + "="*70)
        print("STEP 5: Complete Trip and Reset Seats")
        print("="*70)
        
        print(f"\n✅ Completing trip {trip_id1}")
        complete_trip(trip_id1, use_k8s)
        time.sleep(3)
        
        print(f"\n🚗 Driver {driver1} seats should be reset to 2")
        print(f"🚴 Rider {rider3} should now be able to match")
        
        publish_driver_proximity(driver1, station3, seats=2, destination=destination, use_k8s=use_k8s)
        time.sleep(3)
        
        match3 = consume_match_found(timeout=10, use_k8s=use_k8s)
        if match3:
            print(f"✅ Match created after seat reset: {match3}")
        else:
            print("❌ No match after seat reset")

    # Scenario 5: Driver 2 picks up remaining riders
    print("\n" + "="*70)
    print("STEP 6: Driver 2 picks up remaining riders")
    print("="*70)
    
    print(f"\n🚗 Driver {driver2} arrives at {station1} with 2 seats")
    publish_driver_proximity(driver2, station1, seats=2, destination=destination, use_k8s=use_k8s)
    time.sleep(2)

    print("\n" + "="*70)
    print("✅ DEMO COMPLETE")
    print("="*70 + "\n")
    
    print("Summary:")
    print(f"  - Drivers registered: {driver1}, {driver2}")
    print(f"  - Riders registered: {rider1}, {rider2}, {rider3}")
    print(f"  - Stations used: {station1}, {station2}, {station3}")
    print(f"  - Destination: {destination}")
    print("\nYou can now:")
    print("  1. View the frontend at http://localhost:3000")
    print("  2. Run individual simulations:")
    print(f"     python scripts/simulate_driver_k8s.py --driver-id {driver1} --station-id {station1}")
    print(f"     python scripts/simulate_rider_k8s.py --rider-id {rider1} --station-id {station1}")
    print("  3. Run E2E tests:")
    print("     python tests/e2e_test_k8s.py")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Complete LastMile Demo Simulation")
    parser.add_argument("--use-k8s-services", action="store_true",
                       help="Connect directly to Kubernetes services")
    args = parser.parse_args()
    
    run_demo(use_k8s=args.use_k8s_services)

