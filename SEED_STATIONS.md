# How to Seed Stations

Stations need to be seeded into the database before running simulations or tests.

## Quick Method (Recommended)

If you have port forwarding active:

```bash
# Make sure port forwarding is running
./scripts/port_forward_services.sh

# In another terminal, seed stations
python3 scripts/seed_stations_local.py
```

## Automatic Method

The script will try both methods:

```bash
./scripts/seed_stations.sh
```

## Manual Methods

### Method 1: Local (with port forwarding)

```bash
# 1. Start port forwarding (if not already running)
./scripts/port_forward_services.sh

# 2. Seed stations
python3 scripts/seed_stations_local.py
```

**Requirements:**
- PostgreSQL port-forwarded to `localhost:5432`
- SQLAlchemy installed: `pip3 install --user sqlalchemy psycopg2-binary geoalchemy2`

### Method 2: Kubernetes Pod

```bash
./scripts/seed_stations_k8s.sh
```

**Requirements:**
- Kubernetes cluster access
- Station service image available: `saniyaismail999/lastmile-station:1.0`

### Method 3: Direct Database Access

If you have direct database access:

```bash
# Connect to database
psql -h <postgres-host> -U lastmile -d lastmile

# Run SQL
CREATE EXTENSION IF NOT EXISTS postgis;

INSERT INTO stations (station_id, name, lat, lng, geom) VALUES
('ST101', 'MG Road', 12.975, 77.605, ST_SetSRID(ST_MakePoint(77.605, 12.975), 4326)),
('ST102', 'Cubbon Park', 12.9759, 77.601, ST_SetSRID(ST_MakePoint(77.601, 12.9759), 4326)),
('ST103', 'Trinity Circle', 12.9718, 77.6380, ST_SetSRID(ST_MakePoint(77.6380, 12.9718), 4326)),
('ST104', 'Indiranagar', 12.9786, 77.6408, ST_SetSRID(ST_MakePoint(77.6408, 12.9786), 4326)),
('ST105', 'Koramangala', 12.9352, 77.6245, ST_SetSRID(ST_MakePoint(77.6245, 12.9352), 4326));
```

## Verify Stations

After seeding, verify stations are available:

```bash
# Using the demo script
python3 scripts/demo_simulation.py

# Or using the rider script
python3 scripts/simulate_rider_k8s.py --list-stations

# Or via backend API (if running)
curl http://localhost:8081/api/stations
```

## Stations Included

The seed script creates these stations (Bangalore locations):

- **ST101**: MG Road (12.975, 77.605)
- **ST102**: Cubbon Park (12.9759, 77.601)
- **ST103**: Trinity Circle (12.9718, 77.6380)
- **ST104**: Indiranagar (12.9786, 77.6408)
- **ST105**: Koramangala (12.9352, 77.6245)
- **ST106**: Whitefield (12.9698, 77.7499)
- **ST107**: Marathahalli (12.9592, 77.6974)
- **ST108**: Electronic City (12.8456, 77.6633)

## Troubleshooting

### "connection to server failed"

**Problem:** PostgreSQL is not accessible.

**Solution:**
1. Check if port forwarding is running: `ps aux | grep port-forward`
2. Start port forwarding: `./scripts/port_forward_services.sh`
3. Verify: `kubectl -n lastmile get svc postgres`

### "password authentication failed"

**Problem:** Wrong database credentials.

**Solution:**
- Default credentials: `lastmile:lastmile`
- Check Kubernetes secrets: `kubectl -n lastmile get secret lastmile-secrets`

### "ModuleNotFoundError: No module named 'sqlalchemy'"

**Problem:** Missing Python dependencies.

**Solution:**
```bash
pip3 install --user sqlalchemy psycopg2-binary geoalchemy2
```

### "No stations found" after seeding

**Problem:** Stations table not created or PostGIS not enabled.

**Solution:**
1. Check if table exists: Connect to DB and run `\d stations`
2. Ensure PostGIS extension: `CREATE EXTENSION IF NOT EXISTS postgis;`
3. Re-run seed script

