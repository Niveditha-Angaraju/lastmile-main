# Multi-Station Route Guide

## Overview

The LastMile system now supports drivers moving through multiple stations, with riders requesting at different stations along the route.

## Station Setup

### Extended Station List

The system now includes **12 stations** arranged in route patterns:

**Main Route (North→South):**
- ST101: MG Road (Start)
- ST102: Cubbon Park
- ST103: Trinity Circle
- ST104: Indiranagar
- ST105: Koramangala
- ST106: HSR Layout
- ST107: Electronic City
- ST108: Silk Board

**Alternative Route (East→West):**
- ST109: Whitefield
- ST110: Marathahalli
- ST111: Hebbal
- ST112: Yeshwanthpur (End)

### Seeding Stations

**Local (for testing):**
```bash
cd services/station_service
python3 seed_stations.py
```

**Kubernetes:**
```bash
kubectl -n lastmile exec -it postgres-0 -- python3 /app/seed_stations.py
```

Or use the script:
```bash
./scripts/seed_stations_k8s.sh
```

## Multi-Station Route Demo

### Basic Multi-Station Demo

```bash
python3 scripts/demo_multi_station.py
```

**What it does:**
1. Driver starts at ST101
2. Moves through 8 stations (ST101 → ST108)
3. Riders request at different stations (ST101, ST103, ST105, ST107)
4. Matches happen at each station
5. Driver seats decrease as riders are picked up

### Advanced Route Simulation

```bash
python3 scripts/simulate_multi_station_route.py
```

**Features:**
- Driver moves through all 8 stations
- Riders at every station
- Automatic seat management
- Trip completion and seat reset

## Frontend Visualization

### What You'll See

1. **Multiple Stations**: All 12 stations shown on map
2. **Route Lines**: Driver route connecting stations
3. **Car Movement**: Driver icon moves along route
4. **Matches**: Notifications when matches occur
5. **Progress**: Trip progress shown in popups

### Route Display

- **Orange Dashed**: Scheduled trip route
- **Green Solid**: Active trip route
- **Multiple Waypoints**: Route shows intermediate stations

## How It Works

### Driver Route

1. Driver registers with route through multiple stations
2. Route defined as: `[ST101, ST102, ST103, ...]`
3. Driver moves from station to station
4. At each station, checks for waiting riders

### Rider Requests

1. Riders request at specific stations
2. Requests stored in `station_waiting_riders[station_id]`
3. When driver arrives, matching service:
   - Checks available seats
   - Matches riders with same destination
   - Creates trip with matched riders
   - Decrements driver seats

### Matching Logic

```python
# When driver arrives at station:
1. Check driver seats
2. Get waiting riders at station
3. Filter by destination match
4. Match up to available seats
5. Create trip
6. Remove matched riders from waiting list
```

## Test Cases

### Test Case 1: Sequential Stations

```bash
# Driver: ST101 → ST102 → ST103
# Riders: Request at ST101, ST102, ST103
python3 scripts/demo_multi_station.py
```

### Test Case 2: Spread Out Riders

```bash
# Driver: All 8 stations
# Riders: Request at ST101, ST105, ST108 (spread out)
# Expected: Matches at each station
```

### Test Case 3: Concurrent Riders at Same Station

```bash
# Driver: Arrives at ST101
# Riders: 5 riders request at ST101 simultaneously
# Expected: All 5 matched (if driver has 5 seats)
```

### Test Case 4: Full Driver

```bash
# Driver: Picks up riders, becomes full
# Next Station: Driver arrives with 0 seats
# Expected: No match, driver continues route
```

## Configuration

### Number of Stations

Edit `services/station_service/seed_stations.py` to add/modify stations.

### Route Pattern

Stations are ordered in the seed file. Driver routes follow this order:
- Main route: Stations 1-8
- Alternative route: Stations 9-12

### Driver Seats

Default: 5 seats per driver
Configurable in: `infra/k8s/secret-configmap.yaml`

## Troubleshooting

### Routes Not Showing

- Check stations are seeded: `kubectl -n lastmile exec postgres-0 -- psql -U lastmile -d lastmile -c "SELECT * FROM stations;"`
- Check trip has `origin_station` and `destination`
- Refresh frontend

### Car Not Moving

- Click "Start Trip" button
- Check trip status is `active`
- Check browser console for errors

### No Matches

- Check riders requested before driver arrived
- Check destination matches
- Check driver has available seats
- Check matching service logs: `kubectl logs -l app=matching-service -n lastmile`

## Summary

✅ **12 Stations**: Extended station network
✅ **Multi-Station Routes**: Drivers move through multiple stations
✅ **Riders at Different Stations**: Riders request along route
✅ **Visual Routes**: Frontend shows complete route
✅ **Automatic Matching**: Matches happen at each station
✅ **Seat Management**: Seats decrease as riders picked up

The system now fully supports complex multi-station routes! 🚗

