# LastMile Quick Start Guide

Complete step-by-step guide to run the LastMile demo system.

## Prerequisites Check

```bash
# Check if services are running in Kubernetes
kubectl -n lastmile get pods

# All pods should be in "Running" state
```

## Step-by-Step Startup

### Step 0: Seed Stations (One-time setup)

**IMPORTANT:** You need to seed stations before running simulations!

```bash
# Make sure port forwarding is running first
./scripts/port_forward_services.sh

# Then in another terminal, seed stations
python3 scripts/seed_stations_local.py
```

Or use the automatic script:
```bash
./scripts/seed_stations.sh
```

### Step 1: Port Forward Services (Terminal 1)

```bash
cd /home/niveditha/lastmile-main
./scripts/port_forward_services.sh
```

**Keep this terminal open!** This forwards all services to localhost.

**Alternative:** Run in background:
```bash
./scripts/port_forward_services.sh > /tmp/portforward.log 2>&1 &
```

To stop later:
```bash
pkill -f 'kubectl.*port-forward'
```

### Step 2: Start Backend API (Terminal 2)

```bash
cd /home/niveditha/lastmile-main/backend
pip3 install -r requirements.txt  # Only needed first time
python3 app.py
```

The API will run on **http://localhost:8081**

**To use a different port:**
```bash
PORT=8082 python3 app.py
```

### Step 3: Start Frontend (Terminal 3)

**Option A - React Frontend (Recommended):**
```bash
cd /home/niveditha/lastmile-main/frontend
npm install  # Only needed first time
npm run dev
```

Frontend will be at **http://localhost:3000**

**Option B - Simple HTML (No build needed):**
```bash
# Just open in browser:
# file:///home/niveditha/lastmile-main/frontend/simple.html
# Or use a simple HTTP server:
cd /home/niveditha/lastmile-main/frontend
python3 -m http.server 3000
# Then open: http://localhost:3000/simple.html
```

### Step 4: Run Demo Simulation (Terminal 4)

```bash
cd /home/niveditha/lastmile-main

# Complete demo with multiple scenarios
python3 scripts/demo_simulation.py

# Or run individual simulations:
# Simulate driver
python3 scripts/simulate_driver_k8s.py --driver-id drv-1 --station-id ST101 --destination "Downtown"

# Simulate rider
python3 scripts/simulate_rider_k8s.py --rider-id rider-1 --station-id ST101 --destination "Downtown"

# List available stations
python3 scripts/simulate_rider_k8s.py --list-stations
```

### Step 5: Run Tests (Optional)

```bash
cd /home/niveditha/lastmile-main

# E2E test
python3 tests/e2e_test_k8s.py

# Verify setup
python3 scripts/verify_setup.py
```

## Complete Command List

### One-Time Setup

```bash
# 1. Install backend dependencies
cd backend
pip3 install -r requirements.txt

# 2. Install frontend dependencies
cd ../frontend
npm install
```

### Daily Startup (4 Terminals)

**Terminal 1 - Port Forwarding:**
```bash
cd /home/niveditha/lastmile-main
./scripts/port_forward_services.sh
```

**Terminal 2 - Backend API:**
```bash
cd /home/niveditha/lastmile-main/backend
python3 app.py
```

**Terminal 3 - Frontend:**
```bash
cd /home/niveditha/lastmile-main/frontend
npm run dev
```

**Terminal 4 - Run Simulations/Tests:**
```bash
cd /home/niveditha/lastmile-main

# Demo simulation
python3 scripts/demo_simulation.py

# Or individual commands
python3 scripts/simulate_driver_k8s.py --driver-id drv-1 --station-id ST101
python3 scripts/simulate_rider_k8s.py --rider-id rider-1 --station-id ST101
python3 tests/e2e_test_k8s.py
```

## Helper Scripts

### Quick Start Script
```bash
./scripts/quick_start.sh
```
This checks prerequisites and starts port forwarding automatically.

### Run Demo Helper
```bash
# Use the helper script for easier command execution
./scripts/run_demo.sh demo_simulation
./scripts/run_demo.sh e2e_test
./scripts/run_demo.sh driver --driver-id drv-1 --station-id ST101
./scripts/run_demo.sh rider --rider-id rider-1 --station-id ST101
```

## Port Reference

| Service | Port | URL |
|---------|------|-----|
| Frontend | 3000 | http://localhost:3000 |
| Backend API | 8081 | http://localhost:8081 |
| Station Service | 50051 | localhost:50051 |
| Driver Service | 50052 | localhost:50052 |
| Location Service | 50053 | localhost:50053 |
| Matching Service | 50054 | localhost:50054 |
| Trip Service | 50055 | localhost:50055 |
| Notification Service | 50056 | localhost:50056 |
| Rider Service | 50057 | localhost:50057 |
| User Service | 50058 | localhost:50058 |
| RabbitMQ | 5672 | localhost:5672 |
| PostgreSQL | 5432 | localhost:5432 |

## Troubleshooting

### Port Already in Use

**Backend API (8081):**
```bash
# Find what's using the port
lsof -i :8081
# Or use a different port
PORT=8082 python3 backend/app.py
```

**Frontend (3000):**
```bash
# Find what's using the port
lsof -i :3000
# Vite will automatically try next available port
```

### Services Not Accessible

1. **Check port forwarding:**
   ```bash
   ps aux | grep port-forward
   kubectl -n lastmile get svc
   ```

2. **Restart port forwarding:**
   ```bash
   pkill -f 'kubectl.*port-forward'
   ./scripts/port_forward_services.sh
   ```

3. **Verify services are running:**
   ```bash
   kubectl -n lastmile get pods
   python3 scripts/verify_setup.py
   ```

### Import Errors

If you see protobuf/grpc import errors:
```bash
# Run the fix scripts
python3 scripts/fix_protobuf_imports.py
python3 scripts/fix_grpc_final.py
```

## Quick Reference Card

```bash
# START EVERYTHING
Terminal 1: ./scripts/port_forward_services.sh
Terminal 2: cd backend && python3 app.py
Terminal 3: cd frontend && npm run dev
Terminal 4: python3 scripts/demo_simulation.py

# STOP EVERYTHING
pkill -f 'kubectl.*port-forward'  # Stop port forwarding
# Ctrl+C in other terminals

# VERIFY
python3 scripts/verify_setup.py
kubectl -n lastmile get pods
```

## Next Steps After Startup

1. **Open Frontend:** http://localhost:3000
2. **View Stations:** Stations appear on the map
3. **Register Participants:** Use "Quick Actions" in frontend
4. **Request Pickups:** Select station and request pickup
5. **Run Simulations:** Use Terminal 4 to simulate drivers/riders
6. **Monitor Matches:** Watch trips appear in frontend sidebar

## Tips

- Keep port forwarding running in a separate terminal
- Use `--use-k8s-services` flag if running from within Kubernetes cluster
- Check logs: `kubectl -n lastmile logs <pod-name>`
- Frontend auto-refreshes every 5 seconds (can be toggled)

