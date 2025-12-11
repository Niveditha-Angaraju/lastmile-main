# LastMile - Complete Demo Guide

This guide will help you run tests, simulations, and the interactive frontend for the LastMile ride matching system deployed on Kubernetes.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Running Tests](#running-tests)
4. [Running Simulations](#running-simulations)
5. [Frontend Application](#frontend-application)
6. [Complete Demo Flow](#complete-demo-flow)

## Prerequisites

- Kubernetes cluster with LastMile services deployed
- `kubectl` configured to access your cluster
- Python 3.8+ with required packages
- Node.js 16+ (for frontend)
- Port forwarding access to services

## Quick Start

### 1. Port Forward Services

To access services from your local machine, port forward all services:

```bash
./scripts/port_forward_services.sh
```

This will forward:
- Station Service: `localhost:50051`
- Driver Service: `localhost:50052`
- Location Service: `localhost:50053`
- Matching Service: `localhost:50054`
- Trip Service: `localhost:50055`
- Notification Service: `localhost:50056`
- Rider Service: `localhost:50057`
- User Service: `localhost:50058`
- RabbitMQ: `localhost:5672`
- PostgreSQL: `localhost:5432`

**Note:** Keep this script running in a terminal. Press Ctrl+C to stop.

### 2. Verify Services are Running

```bash
kubectl -n lastmile get pods
```

All pods should be in `Running` state.

## Running Tests

### E2E Test (Kubernetes)

The enhanced E2E test works with your Kubernetes deployment:

```bash
# With port forwarding (default)
python tests/e2e_test_k8s.py

# From within cluster (if running from a pod)
python tests/e2e_test_k8s.py --use-k8s-services
```

This test will:
1. Register drivers and riders
2. Request pickups at different stations
3. Simulate driver proximity events
4. Verify matching logic
5. Test seat management and reset

### Original E2E Test

The original test (for local development):

```bash
python tests/e2e_test.py
```

## Running Simulations

### Simulate a Driver

Simulate a driver moving along a route and updating location:

```bash
# List available stations first
python scripts/simulate_rider_k8s.py --list-stations

# Simulate driver moving to a station
python scripts/simulate_driver_k8s.py \
  --driver-id drv-1 \
  --station-id ST101 \
  --destination "Downtown" \
  --seats 2 \
  --interval 2
```

Options:
- `--driver-id`: Driver ID (default: `drv-sim-1`)
- `--station-id`: Target station ID (required)
- `--destination`: Destination name (default: `Downtown`)
- `--seats`: Available seats (default: `2`)
- `--interval`: Update interval in seconds (default: `2`)
- `--use-k8s-services`: Use Kubernetes service names directly

### Simulate a Rider

Simulate a rider requesting a pickup:

```bash
# List available stations
python scripts/simulate_rider_k8s.py --list-stations

# Request pickup
python scripts/simulate_rider_k8s.py \
  --rider-id rider-1 \
  --station-id ST101 \
  --destination "Downtown" \
  --name "John Doe" \
  --phone "1234567890"
```

### Complete Demo Simulation

Run a full end-to-end simulation with multiple drivers and riders:

```bash
python scripts/demo_simulation.py
```

This will:
1. Register multiple drivers and riders
2. Simulate multiple matching scenarios
3. Test seat management
4. Demonstrate trip completion and seat reset

## Frontend Application

### Setup

1. Install dependencies:

```bash
cd frontend
npm install
```

2. Start the frontend:

```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

### Backend API Server

The frontend needs a backend API server to communicate with gRPC services:

1. Install Python dependencies:

```bash
cd backend
pip install -r requirements.txt
```

2. Start the API server:

```bash
# With port forwarding
python app.py
```

The API server will run on `http://localhost:8080`

**Environment Variables:**
- `STATION_SERVICE`: Station service host (default: `localhost:50051`)
- `DRIVER_SERVICE`: Driver service host (default: `localhost:50052`)
- `RIDER_SERVICE`: Rider service host (default: `localhost:50057`)
- `TRIP_SERVICE`: Trip service host (default: `localhost:50055`)
- `RABBITMQ_URL`: RabbitMQ URL (default: `amqp://guest:guest@localhost:5672/`)
- `PORT`: API server port (default: `8080`)

### Frontend Features

- **Interactive Map**: View stations on a map with proximity circles
- **Station List**: See all available stations
- **Active Trips**: Monitor active trips and their status
- **Quick Actions**: 
  - Register drivers and riders
  - Request pickups at stations
  - View trip details

## Complete Demo Flow

Here's a complete workflow to demonstrate the system:

### Step 1: Start Port Forwarding

```bash
./scripts/port_forward_services.sh
```

Keep this running in a terminal.

### Step 2: Start Backend API

```bash
cd backend
python app.py
```

Keep this running in another terminal.

### Step 3: Start Frontend

```bash
cd frontend
npm run dev
```

Open `http://localhost:3000` in your browser.

### Step 4: Run Complete Demo

In a new terminal:

```bash
python scripts/demo_simulation.py
```

This will:
- Register drivers and riders
- Create multiple matching scenarios
- Show the complete flow

### Step 5: Interact via Frontend

1. **View Stations**: Stations are shown on the map with blue markers
2. **Register Participants**: Use "Quick Actions" to register drivers/riders
3. **Request Pickups**: Select a station and request a pickup
4. **Monitor Trips**: Watch active trips in the sidebar

### Step 6: Run Individual Simulations

**Simulate Driver Movement:**

```bash
# Get station list
python scripts/simulate_rider_k8s.py --list-stations

# Simulate driver (replace ST101 with actual station ID)
python scripts/simulate_driver_k8s.py \
  --driver-id drv-demo-1 \
  --station-id ST101 \
  --destination "Downtown" \
  --interval 2
```

**Simulate Rider Request:**

```bash
python scripts/simulate_rider_k8s.py \
  --rider-id rider-demo-1 \
  --station-id ST101 \
  --destination "Downtown"
```

### Step 7: Run E2E Tests

```bash
python tests/e2e_test_k8s.py
```

## Understanding the System

### Architecture

- **Microservices**: Each service (driver, rider, matching, etc.) runs independently
- **gRPC**: Inter-service communication via gRPC
- **RabbitMQ**: Event-driven messaging for async operations
- **PostgreSQL**: Data persistence with PostGIS for geospatial queries

### Flow

1. **Rider Request**: Rider requests pickup at a station → Published to `rider.requests` queue
2. **Driver Location**: Driver streams location updates → Published to `driver.locations` queue
3. **Proximity Detection**: Location service detects driver near station → Publishes to `driver.near_station` queue
4. **Matching**: Matching service matches rider and driver → Publishes to `match.found` queue
5. **Trip Creation**: Trip service creates trip → Publishes `trip.created` event
6. **Notifications**: Notification service sends notifications to riders and driver
7. **Trip Completion**: When trip completes → Seats reset for driver

### Key Concepts

- **Stations**: Physical locations where riders wait
- **Proximity Threshold**: Default 200m - driver must be within this distance
- **Seat Management**: Drivers have limited seats, decremented on match, reset on trip completion
- **Destination Matching**: Riders must match driver's destination to be matched

## Troubleshooting

### Services Not Accessible

If you can't connect to services:

1. Verify port forwarding is active:
   ```bash
   ps aux | grep port-forward
   ```

2. Check service endpoints:
   ```bash
   kubectl -n lastmile get svc
   ```

3. Verify pods are running:
   ```bash
   kubectl -n lastmile get pods
   ```

### No Stations Available

If no stations are found:

1. Check if stations are seeded:
   ```bash
   kubectl -n lastmile exec -it <station-pod> -- python seed_stations.py
   ```

2. Or seed manually via StationService gRPC calls

### Matches Not Happening

1. Verify driver and rider destinations match
2. Check driver is within proximity threshold (200m)
3. Ensure driver has available seats
4. Check RabbitMQ queues:
   ```bash
   kubectl -n lastmile port-forward svc/rabbitmq 15672:15672
   # Open http://localhost:15672 (guest/guest)
   ```

### Frontend Not Loading

1. Verify backend API is running on port 8080
2. Check browser console for errors
3. Verify CORS is enabled in backend
4. Check API endpoints are accessible

## Next Steps

- **Add WebSocket Support**: Real-time updates in frontend
- **Enhanced Visualization**: Show driver routes, real-time location updates
- **Trip Tracking**: Track active trips on the map
- **Analytics Dashboard**: Show system metrics and statistics
- **Load Testing**: Simulate multiple concurrent drivers and riders

## Support

For issues or questions:
1. Check service logs: `kubectl -n lastmile logs <pod-name>`
2. Verify RabbitMQ queues and messages
3. Check database connectivity
4. Review service configuration in Kubernetes deployments

