"""
Complete Multi-Station Route Demo
Demonstrates driver moving through multiple stations with riders requesting at different stations.

Usage:
    python scripts/demo_multi_station.py
"""
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.e2e_test_k8s import (
    register_driver, register_rider, publish_rider_request,
    publish_driver_proximity, consume_match_found, complete_trip, get_stations
)


def run_multi_station_demo(use_k8s=False):
    """
    Complete demo showing:
    1. Driver with route through 8 stations
    2. Riders requesting at different stations
    3. Matching happening at each station
    4. Driver seats decreasing as riders are picked up
    """
    print("\n" + "="*70)
    print("🚗 LastMile Multi-Station Route Demo")
    print("="*70 + "\n")

    # Get stations
    stations = get_stations(use_k8s)
    if not stations:
        print("❌ No stations found. Please seed stations first.")
        return
    
    if len(stations) < 8:
        print(f"⚠️  Found {len(stations)} stations, need at least 8")
        print("   Please run: python scripts/seed_stations_k8s.sh")
        return
    
    print(f"✅ Found {len(stations)} stations")
    
    # Define route through 8 stations
    route_stations = [s[0] for s in stations[:8]]
    destination = "Downtown"
    
    print(f"\n📍 Route: {' → '.join(route_stations)}")
    print(f"🎯 Destination: {destination}")
    print(f"🚗 Driver seats: 5\n")

    # Register driver
    print("="*70)
    print("STEP 1: Registering Driver")
    print("="*70)
    driver_id = "drv-multi-1"
    register_driver(driver_id, "Multi-Station Driver", "1111111111", "MULTI-001", use_k8s)
    time.sleep(1)

    # Register riders for different stations
    print("\n" + "="*70)
    print("STEP 2: Registering Riders for Different Stations")
    print("="*70)
    
    # Riders at stations: ST101, ST103, ST105, ST107 (spread out)
    rider_stations = {
        route_stations[0]: "rider-multi-1",  # ST101
        route_stations[2]: "rider-multi-2",  # ST103
        route_stations[4]: "rider-multi-3",  # ST105
        route_stations[6]: "rider-multi-4",  # ST107
    }
    
    for station_id, rider_id in rider_stations.items():
        register_rider(rider_id, f"Rider at {station_id}", "9999999999", use_k8s)
        print(f"  ✅ {rider_id} (will request at {station_id})")
    time.sleep(1)

    # Simulate driver moving through route
    print("\n" + "="*70)
    print("STEP 3: Driver Moving Through Route")
    print("="*70)
    
    driver_seats = 5
    active_trips = []
    
    for i, station_id in enumerate(route_stations):
        print(f"\n{'─'*70}")
        print(f"📍 Station {i+1}/{len(route_stations)}: {station_id}")
        print(f"{'─'*70}")
        
        # Rider requests at this station (if any)
        if station_id in rider_stations:
            rider_id = rider_stations[station_id]
            print(f"\n🚴 {rider_id} requests pickup at {station_id}")
            publish_rider_request(rider_id, station_id, destination, use_k8s)
            time.sleep(1)
        
        # Driver arrives
        print(f"\n🚗 Driver arrives at {station_id}")
        print(f"   Available seats: {driver_seats}")
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
            print(f"\n✅ MATCH FOUND!")
            print(f"   Trip ID: {trip_id}")
            print(f"   Matched riders: {matched_riders}")
            print(f"   Seats used: {len(matched_riders)}")
            
            driver_seats -= len(matched_riders)
            active_trips.append(trip_id)
            print(f"   Seats remaining: {driver_seats}")
        else:
            print(f"\nℹ️  No match at {station_id}")
        
        # If driver is full, complete a trip
        if driver_seats <= 0 and active_trips:
            print(f"\n🔄 Driver full! Completing trip to free seats...")
            trip_to_complete = active_trips.pop(0)
            complete_trip(trip_to_complete, use_k8s)
            time.sleep(2)
            driver_seats = 5
            print(f"   ✅ Seats reset to 5")
        
        time.sleep(1)
    
    # Complete remaining trips
    if active_trips:
        print(f"\n{'='*70}")
        print("STEP 4: Completing Remaining Trips")
        print("="*70)
        for trip_id in active_trips:
            print(f"✅ Completing trip {trip_id}")
            complete_trip(trip_id, use_k8s)
            time.sleep(1)
    
    print("\n" + "="*70)
    print("✅ MULTI-STATION ROUTE DEMO COMPLETE")
    print("="*70)
    print(f"\nSummary:")
    print(f"  - Driver: {driver_id}")
    print(f"  - Stations visited: {len(route_stations)}")
    print(f"  - Riders matched: {len(rider_stations)}")
    print(f"  - Trips created: {len(active_trips)}")
    print(f"\n🎯 View frontend at http://localhost:3000")
    print(f"   You should see:")
    print(f"   - Driver moving through {len(route_stations)} stations")
    print(f"   - Routes connecting stations")
    print(f"   - Matches happening at different stations")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Multi-Station Route Demo")
    parser.add_argument("--use-k8s-services", action="store_true",
                       help="Connect directly to Kubernetes services")
    args = parser.parse_args()
    
    run_multi_station_demo(use_k8s=args.use_k8s_services)

