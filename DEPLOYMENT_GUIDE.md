# Complete Deployment Guide

## Understanding Your Code Change

### What `ON CONFLICT DO UPDATE` Does

Your modified `RegisterRider` method uses PostgreSQL's `ON CONFLICT DO UPDATE` clause:

```sql
INSERT INTO riders (rider_id, user_id, name, phone)
VALUES (:rid, :uid, :name, :phone)
ON CONFLICT (rider_id) DO UPDATE
SET user_id = EXCLUDED.user_id,
    name = EXCLUDED.name,
    phone = EXCLUDED.phone
```

**What it does:**
- **If rider_id doesn't exist**: Creates a new rider record
- **If rider_id already exists**: Updates the existing record instead of throwing an error
- **Benefits**: 
  - Allows re-registering the same rider without errors
  - Updates rider information if they register again
  - Prevents duplicate key errors

**Why it was failing before:**
- The method signature was broken (missing `self`, wrong parameters)
- The code wasn't properly indented as a class method
- gRPC couldn't call it correctly

## Building and Pushing Docker Image

### Step 1: Build the Image

```bash
cd /home/niveditha/lastmile-main
./services/rider_service/build_and_push.sh 1.1 saniyaismail999
```

Or manually:
```bash
cd /home/niveditha/lastmile-main
docker build -f services/rider_service/Dockerfile -t saniyaismail999/lastmile-rider:1.1 .
docker tag saniyaismail999/lastmile-rider:1.1 saniyaismail999/lastmile-rider:latest
```

### Step 2: Login to DockerHub

```bash
docker login
# Enter your DockerHub username and password
```

### Step 3: Push to DockerHub

```bash
docker push saniyaismail999/lastmile-rider:1.1
docker push saniyaismail999/lastmile-rider:latest
```

Or use the script (it will prompt):
```bash
./services/rider_service/build_and_push.sh 1.1 saniyaismail999
```

## Updating Kubernetes Deployment

### Option 1: Update Image in Deployment

```bash
# Update the deployment to use new image
kubectl -n lastmile set image deployment/rider-service rider-service=saniyaismail999/lastmile-rider:1.1

# Wait for rollout to complete
kubectl -n lastmile rollout status deployment/rider-service

# Verify the pod is running
kubectl -n lastmile get pods -l app=rider-service
```

### Option 2: Edit Deployment YAML

```bash
# Edit the deployment file
vim services/rider_service/k8s/rider-deployment.yaml
# Change: image: saniyaismail999/lastmile-rider:1.0
# To:     image: saniyaismail999/lastmile-rider:1.1

# Apply the changes
kubectl -n lastmile apply -f services/rider_service/k8s/rider-deployment.yaml

# Wait for rollout
kubectl -n lastmile rollout status deployment/rider-service
```

### Option 3: Restart Deployment

```bash
# Force restart (will pull latest image if tag is 'latest')
kubectl -n lastmile rollout restart deployment/rider-service
kubectl -n lastmile rollout status deployment/rider-service
```

## Verifying the Fix

### Check Rider Registration Works

```bash
# Test rider registration
python3 -c "
import sys
sys.path.insert(0, '.')
from tests.e2e_test_k8s import register_rider
result = register_rider('test-rider-fix', 'Test Rider', '1234567890', False)
print(f'Registration result: {result}')
"
```

### Check Service Logs

```bash
# View rider service logs
kubectl -n lastmile logs -l app=rider-service --tail=50

# Look for successful registrations
kubectl -n lastmile logs -l app=rider-service | grep "Registered rider"
```

### Run Demo Again

```bash
python3 scripts/demo_simulation.py
# Should now show: [TEST] Registered rider rider-demo-1: True
```

## Complete Workflow: Build → Deploy → Test

### 1. Build and Push Image

```bash
cd /home/niveditha/lastmile-main

# Build and push (will prompt for push)
./services/rider_service/build_and_push.sh 1.1 saniyaismail999
```

### 2. Update Kubernetes

```bash
# Update deployment
kubectl -n lastmile set image deployment/rider-service rider-service=saniyaismail999/lastmile-rider:1.1

# Wait for new pod
kubectl -n lastmile rollout status deployment/rider-service

# Verify
kubectl -n lastmile get pods -l app=rider-service
```

### 3. Test

```bash
# Test registration
python3 scripts/demo_simulation.py

# Should see:
# [TEST] Registered rider rider-demo-1: True
# [TEST] Registered rider rider-demo-2: True
# [TEST] Registered rider rider-demo-3: True
```

## Building Other Services

To build other services, use the same pattern:

```bash
# Driver Service
docker build -f services/driver_service/Dockerfile -t saniyaismail999/lastmile-driver:1.1 .
docker push saniyaismail999/lastmile-driver:1.1

# Matching Service
docker build -f services/matching_service/Dockerfile -t saniyaismail999/lastmile-matching:1.1 .
docker push saniyaismail999/lastmile-matching:1.1

# etc.
```

## Quick Reference

### Build Commands
```bash
# Build rider service
docker build -f services/rider_service/Dockerfile -t saniyaismail999/lastmile-rider:1.1 .

# Tag as latest
docker tag saniyaismail999/lastmile-rider:1.1 saniyaismail999/lastmile-rider:latest

# Push
docker push saniyaismail999/lastmile-rider:1.1
docker push saniyaismail999/lastmile-rider:latest
```

### Kubernetes Commands
```bash
# Update image
kubectl -n lastmile set image deployment/rider-service rider-service=saniyaismail999/lastmile-rider:1.1

# Check status
kubectl -n lastmile rollout status deployment/rider-service

# View logs
kubectl -n lastmile logs -l app=rider-service --tail=50

# Restart if needed
kubectl -n lastmile rollout restart deployment/rider-service
```

### Verify Deployment
```bash
# Check pod status
kubectl -n lastmile get pods -l app=rider-service

# Check image being used
kubectl -n lastmile describe deployment rider-service | grep Image
```

## Troubleshooting

### Image Not Found
```bash
# Check if image exists locally
docker images | grep lastmile-rider

# Check if pushed to DockerHub
docker pull saniyaismail999/lastmile-rider:1.1
```

### Pod Not Starting
```bash
# Check pod events
kubectl -n lastmile describe pod -l app=rider-service

# Check logs
kubectl -n lastmile logs -l app=rider-service
```

### Old Image Still Running
```bash
# Force delete pod (will recreate with new image)
kubectl -n lastmile delete pod -l app=rider-service

# Or restart deployment
kubectl -n lastmile rollout restart deployment/rider-service
```

