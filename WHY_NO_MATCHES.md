# Why No Matches Are Created

## Issue from Demo Simulation

The demo simulation shows:
```
[❌ TEST FAILED] No match event received.
```

This means the matching service is not creating matches even though:
- Rider requests are published ✅
- Driver proximity events are published ✅

## Common Causes

### 1. Matching Service Not Processing Events

**Check matching service logs:**
```bash
kubectl -n lastmile logs -l app=matching-service --tail=100
```

**Look for:**
- `[RIDER] Rider waiting at...` - confirms rider requests received
- `[DRIVER] Init seats...` - confirms driver proximity received  
- `[MATCH] Match created...` - confirms match was created

**If missing, the service might not be consuming from RabbitMQ queues.**

### 2. RabbitMQ Queue Issues

**Check if queues exist and have messages:**
```bash
# Port forward RabbitMQ management
kubectl -n lastmile port-forward svc/rabbitmq 15672:15672

# Open http://localhost:15672 (guest/guest)
# Check queues:
# - rider.requests (should have messages)
# - driver.near_station (should have messages)
# - match.found (should receive messages when matches created)
```

### 3. Destination Mismatch

**Matches only occur when destinations match:**
- Rider destination must exactly match driver destination
- Default in demo: "Downtown"
- Check that both rider request and driver proximity use same destination

### 4. Proximity Threshold

**Driver must be within 200m of station:**
- Location service publishes `driver.near_station` only when within 200m
- If driver location updates aren't being processed, proximity won't be detected

### 5. Seat Availability

**Driver must have available seats:**
- If driver has 0 seats, no match will occur
- Check driver seat state in matching service logs

## Debugging Steps

### Step 1: Check Matching Service
```bash
kubectl -n lastmile logs -l app=matching-service --tail=50 | grep -E "RIDER|DRIVER|MATCH"
```

### Step 2: Check Location Service
```bash
kubectl -n lastmile logs -l app=location-service --tail=50 | grep -i proximity
```

### Step 3: Verify RabbitMQ
```bash
# Check queue status
kubectl -n lastmile exec -it $(kubectl -n lastmile get pod -l app=rabbitmq -o name | head -1 | cut -d/ -f2) -- rabbitmqctl list_queues name messages
```

### Step 4: Test Manually
```bash
# Publish a rider request
python3 -c "
import pika, json, time
conn = pika.BlockingConnection(pika.URLParameters('amqp://guest:guest@localhost:5672/'))
ch = conn.channel()
ch.queue_declare(queue='rider.requests', durable=True)
ch.basic_publish('', 'rider.requests', json.dumps({
    'rider_id': 'test-rider',
    'station_id': 'ST101',
    'destination': 'Downtown',
    'arrival_time': int(time.time()*1000)
}))
conn.close()
print('Published rider request')
"

# Publish driver proximity
python3 -c "
import pika, json, time
conn = pika.BlockingConnection(pika.URLParameters('amqp://guest:guest@localhost:5672/'))
ch = conn.channel()
ch.queue_declare(queue='driver.near_station', durable=True)
ch.basic_publish('', 'driver.near_station', json.dumps({
    'driver_id': 'test-driver',
    'station_id': 'ST101',
    'available_seats': 2,
    'destination': 'Downtown',
    'ts': int(time.time()*1000)
}))
conn.close()
print('Published driver proximity')
"

# Check for match
python3 -c "
import pika, json, time
conn = pika.BlockingConnection(pika.URLParameters('amqp://guest:guest@localhost:5672/'))
ch = conn.channel()
ch.queue_declare(queue='match.found', durable=True)
method, props, body = ch.basic_get('match.found', auto_ack=True)
if body:
    print('Match found:', json.loads(body))
else:
    print('No match found')
conn.close()
"
```

## Quick Fix: Restart Matching Service

Sometimes the service needs a restart:
```bash
kubectl -n lastmile rollout restart deployment/matching-service
kubectl -n lastmile rollout status deployment/matching-service
```

## Expected Flow

1. **Rider Request** → `rider.requests` queue
2. **Matching Service** receives request → stores in `station_waiting_riders`
3. **Driver Proximity** → `driver.near_station` queue  
4. **Matching Service** receives proximity → checks for waiting riders
5. **Match Created** → `match.found` queue + Trip created
6. **Frontend** queries trips → displays in UI

If any step fails, matches won't be created.

