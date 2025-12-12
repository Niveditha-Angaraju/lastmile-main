# Station Seeding Fix

## Problem

The station seeding script was failing with:
```
duplicate key value violates unique constraint "stations_station_id_key"
DETAIL: Key (station_id)=(ST101) already exists.
```

This happens when stations are already seeded and you try to seed again.

## Solution

Updated `services/station_service/seed_stations.py` to use `ON CONFLICT DO UPDATE`, similar to the rider registration fix.

### Before (Would Fail on Duplicates)
```python
conn.execute(text(
    "INSERT INTO stations (station_id, name, lat, lng, geom) VALUES (:sid, :name, :lat, :lng, ST_SetSRID(ST_MakePoint(:lng,:lat),4326))"
), {"sid": sid, "name": name, "lat": lat, "lng": lng})
```

### After (Handles Duplicates Gracefully)
```python
conn.execute(text(
    """
    INSERT INTO stations (station_id, name, lat, lng, geom) 
    VALUES (:sid, :name, :lat, :lng, ST_SetSRID(ST_MakePoint(:lng,:lat),4326))
    ON CONFLICT (station_id) DO UPDATE 
    SET name = EXCLUDED.name, 
        lat = EXCLUDED.lat, 
        lng = EXCLUDED.lng, 
        geom = EXCLUDED.geom
    """
), {"sid": sid, "name": name, "lat": lat, "lng": lng})
```

## What This Does

- **If station_id is NEW**: Creates a new station record
- **If station_id EXISTS**: Updates the existing record instead of erroring
- **Result**: Seeding is idempotent - safe to run multiple times

## Usage

Now you can run the seeding script multiple times without errors:

```bash
# This will work even if stations already exist
./scripts/seed_stations.sh

# Or directly via Kubernetes
./scripts/seed_stations_k8s.sh
```

## Note

The local seeding script (`scripts/seed_stations_local.py`) already had this fix. The service's seed script (`services/station_service/seed_stations.py`) is now updated to match.

## Next Steps

1. **If you need to rebuild the station service image:**
   ```bash
   docker build -f services/station_service/Dockerfile -t saniyaismail999/lastmile-station:1.1 .
   docker push saniyaismail999/lastmile-station:1.1
   kubectl -n lastmile set image deployment/station-service station-service=saniyaismail999/lastmile-station:1.1
   ```

2. **Or just run the seeding again** (it will now work):
   ```bash
   ./scripts/seed_stations.sh
   ```

The fix is in the code, so if you're using the existing image, you can also just verify stations exist:

```bash
# Check if stations exist
python3 -c "
import sys
sys.path.insert(0, '.')
from tests.e2e_test_k8s import get_stations
stations = get_stations()
print(f'Found {len(stations)} stations')
for s in stations:
    print(f'  - {s.station_id}: {s.name}')
"
```

