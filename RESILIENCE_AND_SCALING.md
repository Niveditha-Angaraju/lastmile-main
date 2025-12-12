# Resilience and Scaling Documentation

## Overview

This document demonstrates how the LastMile application handles:
1. **Resilience**: Continues working when services fail
2. **Scaling**: Scales matching service from 1 to 5 replicas

## Prerequisites

- Kubernetes cluster running (Minikube)
- All services deployed
- kubectl configured

## Resilience Testing

### What is Resilience?

Resilience means the system continues operating even when some services fail. In Kubernetes:
- Pods can crash or be terminated
- Services automatically restart failed pods
- Other services continue operating independently

### Testing Service Failures

**Test a single service failure:**
```bash
./scripts/test_resilience.sh matching-service
```

**Test multiple service failures:**
```bash
./scripts/test_resilience.sh
```

**What happens:**
1. Service is scaled down to 0 replicas (simulated failure)
2. System continues operating with other services
3. Service is restored (scaled back to 1)
4. Service recovers automatically

### Example: Matching Service Failure

```bash
# Scale down matching service
kubectl scale deployment matching-service --replicas=0 -n lastmile

# System continues:
# - Drivers can still register
# - Riders can still request pickups
# - Location service still tracks drivers
# - Trip service still manages trips
# - Only matching is temporarily unavailable

# Scale back up
kubectl scale deployment matching-service --replicas=1 -n lastmile

# Service recovers automatically
```

### Resilience Features

1. **Independent Services**: Each microservice operates independently
2. **Message Queues**: RabbitMQ buffers messages during failures
3. **Automatic Restarts**: Kubernetes restarts failed pods
4. **Health Checks**: Services have health endpoints
5. **Graceful Degradation**: Non-critical services can fail without breaking core functionality

## Scaling Testing

### What is Scaling?

Scaling means increasing the number of service instances to handle more load. For matching service:
- 1 replica: Handles normal load
- 2-3 replicas: Handles moderate load
- 4-5 replicas: Handles high load

### Scaling Matching Service

**Scale to specific number:**
```bash
./scripts/scale_matching_service.sh 3
```

**Test full scaling sequence (1→2→3→4→5→1):**
```bash
./scripts/scale_matching_service.sh
```

**Manual scaling:**
```bash
# Scale to 3 replicas
kubectl scale deployment matching-service --replicas=3 -n lastmile

# Check status
kubectl get pods -l app=matching-service -n lastmile

# Scale back to 1
kubectl scale deployment matching-service --replicas=1 -n lastmile
```

### How Scaling Works

1. **Load Distribution**: Kubernetes distributes requests across all replicas
2. **RabbitMQ**: Multiple matching service instances consume from same queues
3. **State Management**: Each instance maintains its own in-memory state
4. **Coordination**: RabbitMQ ensures messages are processed by only one instance

### Scaling Demonstration

```bash
# Start with 1 replica
kubectl scale deployment matching-service --replicas=1 -n lastmile

# Run simulation (normal load)
python3 scripts/demo_simulation.py

# Scale to 3 replicas (moderate load)
kubectl scale deployment matching-service --replicas=3 -n lastmile

# Run simulation (should handle more concurrent requests)
python3 scripts/demo_multi_station.py

# Scale to 5 replicas (high load)
kubectl scale deployment matching-service --replicas=5 -n lastmile

# Run multiple simulations simultaneously
python3 scripts/demo_simulation.py &
python3 scripts/demo_multi_station.py &
```

### Monitoring Scaling

```bash
# Watch pods
kubectl get pods -l app=matching-service -n lastmile -w

# Check logs from all replicas
kubectl logs -l app=matching-service -n lastmile --tail=50

# Check resource usage
kubectl top pods -l app=matching-service -n lastmile
```

## Architecture Benefits

### Microservices Architecture

- **Isolation**: Failure in one service doesn't break others
- **Independent Scaling**: Scale only services that need it
- **Independent Deployment**: Deploy services separately

### Message Queue (RabbitMQ)

- **Buffering**: Messages queued during service failures
- **Load Distribution**: Multiple consumers process messages
- **Durability**: Messages persisted, not lost on failure

### Kubernetes Features

- **Auto-restart**: Failed pods automatically restarted
- **Health Checks**: Unhealthy pods replaced
- **Load Balancing**: Requests distributed across replicas
- **Rolling Updates**: Zero-downtime deployments

## Test Scenarios

### Scenario 1: Matching Service Failure

```bash
# 1. Start system
./scripts/port_forward_services.sh

# 2. Run simulation
python3 scripts/demo_simulation.py

# 3. Kill matching service
kubectl scale deployment matching-service --replicas=0 -n lastmile

# 4. Continue operations (other services work)
# - Drivers can register
# - Riders can request
# - Location service tracks drivers

# 5. Restore matching service
kubectl scale deployment matching-service --replicas=1 -n lastmile

# 6. System recovers, matches resume
```

### Scenario 2: Scale Under Load

```bash
# 1. Start with 1 replica
kubectl scale deployment matching-service --replicas=1 -n lastmile

# 2. Generate load
for i in {1..5}; do
    python3 scripts/demo_simulation.py &
done

# 3. Scale up to handle load
kubectl scale deployment matching-service --replicas=5 -n lastmile

# 4. Observe improved performance
kubectl logs -l app=matching-service -n lastmile --tail=100
```

### Scenario 3: Multiple Service Failures

```bash
# 1. Scale down non-critical services
kubectl scale deployment notification-service --replicas=0 -n lastmile
kubectl scale deployment user-service --replicas=0 -n lastmile

# 2. Core functionality still works
python3 scripts/demo_simulation.py

# 3. Restore services
kubectl scale deployment notification-service --replicas=1 -n lastmile
kubectl scale deployment user-service --replicas=1 -n lastmile
```

## Best Practices

1. **Health Checks**: All services have health endpoints
2. **Graceful Shutdown**: Services handle termination signals
3. **Retry Logic**: Clients retry failed requests
4. **Circuit Breakers**: Prevent cascading failures
5. **Monitoring**: Watch service health and performance

## Summary

✅ **Resilience**: System continues operating when services fail
✅ **Scaling**: Matching service scales from 1 to 5 replicas
✅ **Auto-recovery**: Kubernetes automatically restarts failed pods
✅ **Load Distribution**: Multiple replicas share load via RabbitMQ
✅ **Independent Services**: Microservices operate independently

The LastMile application demonstrates production-ready resilience and scaling capabilities!

