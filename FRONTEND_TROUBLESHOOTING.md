# Frontend Troubleshooting Guide

## Issue: Frontend shows stations but no trips

### Problem
The frontend displays stations correctly on the map, but the "Active Trips" section shows 0 trips even after running simulations.

### Solutions

#### 1. Check Backend API
Make sure the backend is running and can query trips:

```bash
# Test the API directly
curl http://localhost:8081/api/trips

# Should return JSON with trips array
```

#### 2. Verify Database Connection
The backend now queries trips directly from the database. Make sure:
- PostgreSQL is port-forwarded: `kubectl -n lastmile port-forward svc/postgres 5432:5432`
- Database credentials are correct (default: `lastmile:lastmile`)
- The `trips` table exists

#### 3. Check Matching Service
If no matches are being created:

```bash
# Check matching service logs
kubectl -n lastmile logs -l app=matching-service --tail=50

# Verify RabbitMQ queues
kubectl -n lastmile port-forward svc/rabbitmq 15672:15672
# Open http://localhost:15672 (guest/guest)
# Check queues: rider.requests, driver.near_station, match.found
```

#### 4. Verify Services are Running
```bash
kubectl -n lastmile get pods
# All services should be Running
```

#### 5. Frontend Auto-Refresh
The frontend auto-refreshes every 5 seconds. You can:
- Toggle "Auto-refresh (5s)" checkbox
- Click "Refresh Trips" button manually
- Check browser console for errors (F12)

## Issue: Rider Registration Fails

### Problem
Rider registration returns `False` in the demo simulation.

### Solutions

#### 1. Check Rider Service
```bash
# Check rider service logs
kubectl -n lastmile logs -l app=rider-service --tail=50

# Look for database errors
```

#### 2. Verify Database Table
The riders table should exist. Check:
```bash
# Connect to database
kubectl -n lastmile exec -it postgres-0 -- psql -U lastmile -d lastmile

# Check table
\dt riders

# If missing, the service should create it on startup
```

#### 3. Retry Registration
Sometimes it's a timing issue. The demo script continues even if registration fails.

## Issue: No Matches Created

### Problem
Rider requests and driver proximity events are published, but no matches are found.

### Solutions

#### 1. Check Matching Service Logs
```bash
kubectl -n lastmile logs -l app=matching-service --tail=100
```

Look for:
- `[RIDER] Rider waiting at...` - confirms rider requests received
- `[DRIVER] Init seats...` - confirms driver proximity received
- `[MATCH] Match created...` - confirms match was created

#### 2. Verify RabbitMQ
```bash
# Port forward RabbitMQ management UI
kubectl -n lastmile port-forward svc/rabbitmq 15672:15672

# Open http://localhost:15672
# Login: guest/guest
# Check queues for messages
```

#### 3. Check Destination Matching
Matches only occur when:
- Driver destination matches rider destination
- Driver has available seats
- Driver is within proximity threshold (200m)

#### 4. Verify Trip Service
```bash
# Check trip service logs
kubectl -n lastmile logs -l app=trip-service --tail=50
```

## Issue: Frontend Not Updating

### Solutions

#### 1. Check Backend Connection
```bash
# Test backend health
curl http://localhost:8081/api/health

# Should return: {"status":"ok"}
```

#### 2. Check CORS
The backend has CORS enabled. If you see CORS errors:
- Make sure backend is running on port 8081
- Check browser console for errors

#### 3. Manual Refresh
- Click "Refresh Trips" button
- Toggle auto-refresh off and on
- Hard refresh browser (Ctrl+Shift+R)

#### 4. Check Browser Console
Open browser DevTools (F12) and check:
- Network tab: Are API calls successful?
- Console tab: Any JavaScript errors?

## Quick Diagnostic Commands

```bash
# 1. Check all services
kubectl -n lastmile get pods

# 2. Check port forwarding
ps aux | grep port-forward

# 3. Test backend API
curl http://localhost:8081/api/stations
curl http://localhost:8081/api/trips

# 4. Check database
kubectl -n lastmile exec -it postgres-0 -- psql -U lastmile -d lastmile -c "SELECT COUNT(*) FROM trips;"

# 5. Check RabbitMQ queues
kubectl -n lastmile exec -it $(kubectl -n lastmile get pod -l app=rabbitmq -o name | head -1 | cut -d/ -f2) -- rabbitmqctl list_queues
```

## Expected Behavior

### When Simulation Runs:
1. **Riders registered** → Should appear in rider service database
2. **Rider requests published** → Should appear in `rider.requests` queue
3. **Driver proximity published** → Should appear in `driver.near_station` queue
4. **Matches created** → Should appear in `match.found` queue and `trips` table
5. **Frontend updates** → Should show trips in "Active Trips" section

### Frontend Display:
- **Stations**: Always visible on map (blue markers)
- **Trips**: Only shows non-completed trips
- **Auto-refresh**: Updates every 5 seconds when enabled
- **Map**: Shows stations with 200m proximity circles

## Still Having Issues?

1. **Check all service logs:**
   ```bash
   for svc in driver rider matching trip location; do
     echo "=== $svc-service ==="
     kubectl -n lastmile logs -l app=$svc-service --tail=20
   done
   ```

2. **Verify RabbitMQ connectivity:**
   ```bash
   kubectl -n lastmile exec -it $(kubectl -n lastmile get pod -l app=rabbitmq -o name | head -1 | cut -d/ -f2) -- rabbitmqctl status
   ```

3. **Check database:**
   ```bash
   kubectl -n lastmile exec -it postgres-0 -- psql -U lastmile -d lastmile -c "\dt"
   ```

