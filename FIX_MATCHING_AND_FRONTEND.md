# Fix Matching Service and Frontend Issues

## Issue 1: Matching Service Not Creating Matches

### Problem
- Matching service can't connect to RabbitMQ
- Error: `gaierror(-3, 'Temporary failure in name resolution')`
- Messages accumulating in queues (3 rider requests, 4 driver proximity events)
- No consumers on queues

### Root Cause
The matching service pod can't resolve the `rabbitmq` hostname, likely due to:
- DNS not working in the pod
- Pod needs restart to pick up service DNS
- Network policy blocking connections

### Solution

**Option 1: Restart Matching Service (Quick Fix)**
```bash
kubectl -n lastmile rollout restart deployment/matching-service
kubectl -n lastmile rollout status deployment/matching-service
```

**Option 2: Check RabbitMQ Service**
```bash
# Verify RabbitMQ is running
kubectl -n lastmile get pods -l app=rabbitmq

# Check service DNS
kubectl -n lastmile exec -it deployment/matching-service -- nslookup rabbitmq

# Test connection from matching service
kubectl -n lastmile exec -it deployment/matching-service -- ping -c 2 rabbitmq
```

**Option 3: Check Logs After Restart**
```bash
kubectl -n lastmile logs -l app=matching-service --tail=50 | grep -E "consuming|RIDER|DRIVER|MATCH|ERROR"
```

### Verify Fix
```bash
# Check if matching service is consuming
python3 scripts/fix_matching_issues.py

# Should show:
# rider.requests - Consumers: 1 (not 0)
# driver.near_station - Consumers: 1 (not 0)
```

## Issue 2: Frontend Blank Page

### Problem
Frontend shows blank page - likely due to:
- Backend not running
- CORS issues
- JavaScript errors
- Missing API connection

### Solution

**Step 1: Check Backend is Running**
```bash
# Check if backend is running
curl http://localhost:8081/api/health

# Should return: {"status":"ok"}
```

**Step 2: Start Backend if Not Running**
```bash
cd backend
python3 app.py
```

**Step 3: Check Frontend Console**
1. Open browser DevTools (F12)
2. Check Console tab for errors
3. Check Network tab for failed API calls

**Step 4: Verify Frontend is Running**
```bash
cd frontend
npm run dev

# Should show:
# VITE v5.x.x  ready in xxx ms
# ➜  Local:   http://localhost:3000/
```

**Step 5: Check Browser Console**
Common errors:
- `Failed to fetch` → Backend not running
- `CORS error` → Backend CORS not configured
- `Cannot read property` → JavaScript error in code

### Quick Test
```bash
# Test backend API
curl http://localhost:8081/api/stations
curl http://localhost:8081/api/trips

# Test frontend can reach backend
curl http://localhost:3000/api/stations
```

## Complete Fix Workflow

### 1. Fix Matching Service
```bash
# Restart matching service
kubectl -n lastmile rollout restart deployment/matching-service

# Wait for it to start
kubectl -n lastmile rollout status deployment/matching-service

# Check logs
kubectl -n lastmile logs -l app=matching-service --tail=20 | grep -E "consuming|started"
```

### 2. Verify RabbitMQ Connection
```bash
# Check queues
python3 scripts/fix_matching_issues.py

# Should show consumers > 0
```

### 3. Start Backend
```bash
cd backend
python3 app.py
# Keep this running in a terminal
```

### 4. Start Frontend
```bash
cd frontend
npm run dev
# Keep this running in another terminal
```

### 5. Test End-to-End
```bash
# Run demo simulation
python3 scripts/demo_simulation.py

# Should now see matches being created
```

## Troubleshooting

### Matching Service Still Not Working

**Check DNS:**
```bash
kubectl -n lastmile exec -it deployment/matching-service -- nslookup rabbitmq
```

**Check RabbitMQ:**
```bash
kubectl -n lastmile get pods -l app=rabbitmq
kubectl -n lastmile logs -l app=rabbitmq --tail=20
```

**Check Network Policies:**
```bash
kubectl -n lastmile get networkpolicies
```

### Frontend Still Blank

**Check Browser Console:**
- Open http://localhost:3000
- Press F12 → Console tab
- Look for red errors

**Check Network Tab:**
- F12 → Network tab
- Refresh page
- Look for failed requests (red)

**Check Backend:**
```bash
# Test backend directly
curl http://localhost:8081/api/stations
curl http://localhost:8081/api/trips

# Check backend logs
# Look for errors in the terminal where backend is running
```

## Expected Behavior After Fix

### Matching Service
- Logs show: `MatchingService consuming rider.requests, driver.near_station, trip.updated`
- Queues show consumers > 0
- Matches are created when riders and drivers match

### Frontend
- Shows map with stations
- Displays active trips
- Updates every 5 seconds
- No console errors

## Summary

**Matching Service:**
1. Restart: `kubectl -n lastmile rollout restart deployment/matching-service`
2. Verify: Check logs for "consuming" message
3. Test: Run demo simulation

**Frontend:**
1. Start backend: `cd backend && python3 app.py`
2. Start frontend: `cd frontend && npm run dev`
3. Check browser console for errors
4. Test API: `curl http://localhost:8081/api/stations`

