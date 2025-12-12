"""
Multi-Station Route Simulation
Simulates a driver moving through multiple stations, with riders requesting at different stations along the route.

Usage:
    python scripts/simulate_multi_station_route.py
"""
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.e2e_test_k8s import (
    register_driver, register_rider, publish_rider_request,
    publish_driver_proximity, consume_match_found, get_stations
)


def simulate_multi_station_route(use_k8s=False):
    """
    Simulates a driver moving through multiple stations.
    Riders request at different stations along the route.
    """
    print("\n" + "="*70)
    print("🚗 Multi-Station Route Simulation")
    print("="*70 + "\n")

    # Get stations
    stations = get_stations(use_k8s)
    if len(stations) < 8:
        print("❌ Need at least 8 stations. Please seed stations first.")
        return
    
    # Define route: Main route through 8 stations
    route_stations = [s[0] for s in stations[:8]]  # ST101 to ST108
    destination = "Downtown"
    
    print(f"📍 Route: {' → '.join(route_stations)}")
    print(f"🎯 Destination: {destination}\n")

    # Register driver
    driver_id = "drv-route-1"
    print("="*70)
    print("STEP 1: Registering Driver")
    print("="*70)
    register_driver(driver_id, "Route Driver", "1111111111", "ROUTE-001", use_k8s)
    time.sleep(1)

    # Register riders (one for each station)
    print("\n" + "="*70)
    print("STEP 2: Registering Riders")
    print("="*70)
    riders = {}
    for i, station_id in enumerate(route_stations, 1):
        rider_id = f"rider-route-{i}"
        register_rider(rider_id, f"Rider {i}", f"9999999{i:03d}", use_k8s)
        riders[station_id] = rider_id
        print(f"  ✅ Registered {rider_id} (will request at {station_id})")
    time.sleep(1)

    # Simulate driver moving through stations
    print("\n" + "="*70)
    print("STEP 3: Driver Moving Through Stations")
    print("="*70)
    
    driver_seats = 5  # Start with 5 seats
    completed_trips = []
    
    for i, station_id in enumerate(route_stations):
        print(f"\n{'='*70}")
        print(f"📍 Station {i+1}/{len(route_stations)}: {station_id}")
        print(f"{'='*70}")
        
        # Rider at this station requests pickup
        if station_id in riders:
            rider_id = riders[station_id]
            print(f"\n🚴 {rider_id} requests pickup at {station_id}")
            publish_rider_request(rider_id, station_id, destination, use_k8s)
            time.sleep(1)
        
        # Driver arrives at station
        print(f"\n🚗 Driver {driver_id} arrives at {station_id} with {driver_seats} seats")
        publish_driver_proximity(
            driver_id, station_id, 
            seats=driver_seats, 
            destination=destination, 
            use_k8s=use_k8s
        )
        time.sleep(2)
        
        # Check for match
        match = consume_match_found(timeout=5, use_k8s=use_k8s)
        if match:
            matched_riders = match.get('rider_ids', [])
            trip_id = match.get('trip_id')
            print(f"✅ Match created!")
            print(f"   Trip: {trip_id}")
            print(f"   Riders: {matched_riders}")
            print(f"   Seats used: {len(matched_riders)}")
            
            # Update driver seats
            driver_seats -= len(matched_riders)
            print(f"   Driver seats remaining: {driver_seats}")
            
            completed_trips.append(trip_id)
        else:
            print(f"ℹ️  No match at {station_id} (no riders or no seats)")
        
        # If driver is full, complete a trip to free seats
        if driver_seats <= 0 and completed_trips:
            print(f"\n🔄 Driver is full. Completing trip to free seats...")
            trip_to_complete = completed_trips.pop(0)
            # In real system, this would be done after trip completion
            # For demo, we'll simulate seat reset
            driver_seats = 5
            print(f"   ✅ Seats reset to 5")
        
        time.sleep(1)
    
    print("\n" + "="*70)
    print("✅ Route Simulation Complete")
    print("="*70)
    print(f"\nSummary:")
    print(f"  - Driver: {driver_id}")
    print(f"  - Stations visited: {len(route_stations)}")
    print(f"  - Riders registered: {len(riders)}")
    print(f"  - Trips created: {len(completed_trips)}")
    print(f"\nView frontend at http://localhost:3000 to see the route!")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Multi-Station Route Simulation")
    parser.add_argument("--use-k8s-services", action="store_true",
                       help="Connect directly to Kubernetes services")
    args = parser.parse_args()
    
    simulate_multi_station_route(use_k8s=args.use_k8s_services)

