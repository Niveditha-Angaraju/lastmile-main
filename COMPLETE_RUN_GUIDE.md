# Complete Guide: Running Everything

## Overview

This guide covers running the entire LastMile system with all components working together.

## Prerequisites

- Kubernetes cluster with services deployed
- `kubectl` configured
- Docker installed (for building images)
- Python 3.8+ with dependencies
- Node.js 16+ (for frontend)

## Part 1: Build and Deploy Services

### 1.1 Build Rider Service (with your fix)

```bash
cd /home/niveditha/lastmile-main

# Build and push
./services/rider_service/build_and_push.sh 1.1 saniyaismail999

# Or manually:
docker build -f services/rider_service/Dockerfile -t saniyaismail999/lastmile-rider:1.1 .
docker login
docker push saniyaismail999/lastmile-rider:1.1
```

### 1.2 Update Kubernetes Deployment

```bash
# Update to use new image
kubectl -n lastmile set image deployment/rider-service rider-service=saniyaismail999/lastmile-rider:1.1

# Wait for rollout
kubectl -n lastmile rollout status deployment/rider-service

# Verify
kubectl -n lastmile get pods -l app=rider-service
```

### 1.3 Verify All Services Running

```bash
kubectl -n lastmile get pods
# All should be "Running"
```

## Part 2: Start Port Forwarding

### Terminal 1: Port Forward All Services

```bash
cd /home/niveditha/lastmile-main
./scripts/port_forward_services.sh
```

**Keep this terminal open!** This forwards:
- All gRPC services (50051-50058)
- RabbitMQ (5672)
- PostgreSQL (5432)

## Part 3: Seed Stations

### Terminal 2: Seed Stations

```bash
cd /home/niveditha/lastmile-main

# Automatic (tries local, then Kubernetes)
./scripts/seed_stations.sh

# Or Kubernetes method
./scripts/seed_stations_k8s.sh
```

Verify:
```bash
python3 scripts/simulate_rider_k8s.py --list-stations
```

## Part 4: Start Backend API

### Terminal 3: Backend API

```bash
cd /home/niveditha/lastmile-main/backend

# Install dependencies (first time only)
pip3 install --user -r requirements.txt

# Start backend
python3 app.py
```

Backend runs on: **http://localhost:8081**

## Part 5: Start Frontend

### Terminal 4: Frontend

```bash
cd /home/niveditha/lastmile-main/frontend

# Install dependencies (first time only)
npm install

# Start frontend
npm run dev
```

Frontend runs on: **http://localhost:3000**

## Part 6: Run Simulations

### Terminal 5: Run Demo

```bash
cd /home/niveditha/lastmile-main

# Complete demo
python3 scripts/demo_simulation.py

# Or individual simulations
python3 scripts/simulate_driver_k8s.py --driver-id drv-1 --station-id ST101
python3 scripts/simulate_rider_k8s.py --rider-id rider-1 --station-id ST101
```

## Complete Startup Sequence

### Quick Start (All Terminals)

**Terminal 1:**
```bash
./scripts/port_forward_services.sh
```

**Terminal 2:**
```bash
./scripts/seed_stations.sh
cd backend && python3 app.py
```

**Terminal 3:**
```bash
cd frontend && npm run dev
```

**Terminal 4:**
```bash
python3 scripts/demo_simulation.py
```

## What You Should See

### Frontend (http://localhost:3000)
- ✅ **Stations**: 3 stations on map (ST101, ST102, ST103)
- ✅ **Active Trips**: Shows trips as they're created
- ✅ **Map**: Interactive map with station markers
- ✅ **Real-time Updates**: Auto-refreshes every 5 seconds

### Demo Simulation
- ✅ **Rider Registration**: All riders register successfully
- ✅ **Matches Created**: Trips appear when drivers and riders match
- ✅ **Seat Management**: Seats decrement and reset correctly

### Backend API
- ✅ **Health**: `curl http://localhost:8081/api/health` → `{"status":"ok"}`
- ✅ **Stations**: `curl http://localhost:8081/api/stations` → Returns 3 stations
- ✅ **Trips**: `curl http://localhost:8081/api/trips` → Returns active trips

## Troubleshooting

### Rider Registration Still Failing

1. **Check if new image is deployed:**
   ```bash
   kubectl -n lastmile describe deployment rider-service | grep Image
   # Should show: saniyaismail999/lastmile-rider:1.1
   ```

2. **Check pod logs:**
   ```bash
   kubectl -n lastmile logs -l app=rider-service --tail=50
   ```

3. **Verify database connection:**
   ```bash
   kubectl -n lastmile logs -l app=rider-service | grep -i "database\|error"
   ```

### No Matches Created

1. **Check matching service:**
   ```bash
   kubectl -n lastmile logs -l app=matching-service --tail=100 | grep -E "RIDER|DRIVER|MATCH"
   ```

2. **Check RabbitMQ:**
   ```bash
   kubectl -n lastmile port-forward svc/rabbitmq 15672:15672
   # Open http://localhost:15672 (guest/guest)
   # Check queues: rider.requests, driver.near_station, match.found
   ```

3. **Verify services are connected:**
   ```bash
   python3 scripts/verify_setup.py
   ```

### Frontend Not Showing Trips

1. **Check backend is running:**
   ```bash
   curl http://localhost:8081/api/trips
   ```

2. **Check browser console (F12):**
   - Look for API errors
   - Check Network tab for failed requests

3. **Restart backend:**
   ```bash
   # Stop backend (Ctrl+C)
   cd backend && python3 app.py
   ```

## Daily Workflow

### Morning Startup (5 minutes)

```bash
# 1. Start port forwarding
./scripts/port_forward_services.sh

# 2. Start backend
cd backend && python3 app.py

# 3. Start frontend
cd frontend && npm run dev

# 4. Verify
python3 scripts/verify_setup.py
```

### Running Tests/Simulations

```bash
# E2E test
python3 tests/e2e_test_k8s.py

# Demo simulation
python3 scripts/demo_simulation.py

# Individual simulations
python3 scripts/simulate_driver_k8s.py --driver-id drv-1 --station-id ST101
python3 scripts/simulate_rider_k8s.py --rider-id rider-1 --station-id ST101
```

### Evening Shutdown

```bash
# Stop port forwarding
pkill -f 'kubectl.*port-forward'

# Stop backend (Ctrl+C in terminal)
# Stop frontend (Ctrl+C in terminal)
```

## Advanced: Real-time Frontend Updates

The frontend currently polls every 5 seconds. For real-time updates, you can:

1. **Add WebSocket support** (future enhancement)
2. **Reduce polling interval** (edit `frontend/src/App.jsx`)
3. **Add manual refresh button** (already exists)

## Summary

### Your Code Change
- **What**: Added `ON CONFLICT DO UPDATE` to handle duplicate rider registrations
- **Why**: Prevents errors when re-registering the same rider
- **Status**: Fixed the method signature and indentation

### Build & Deploy
```bash
./services/rider_service/build_and_push.sh 1.1 saniyaismail999
kubectl -n lastmile set image deployment/rider-service rider-service=saniyaismail999/lastmile-rider:1.1
```

### Run Everything
1. Port forward services
2. Seed stations
3. Start backend
4. Start frontend
5. Run simulations
6. Watch frontend update in real-time!

