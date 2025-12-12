# Build and Deploy Rider Service

## Quick Start

### 1. Build Docker Image

```bash
cd /home/niveditha/lastmile-main

# Use the build script (recommended)
./services/rider_service/build_and_push.sh 1.1 saniyaismail999

# Or build manually
docker build -f services/rider_service/Dockerfile -t saniyaismail999/lastmile-rider:1.1 .
```

### 2. Login to DockerHub

```bash
docker login
# Enter your DockerHub credentials
```

### 3. Push to DockerHub

```bash
# Push specific version
docker push saniyaismail999/lastmile-rider:1.1

# Push as latest
docker tag saniyaismail999/lastmile-rider:1.1 saniyaismail999/lastmile-rider:latest
docker push saniyaismail999/lastmile-rider:latest
```

### 4. Update Kubernetes Deployment

```bash
# Update deployment to use new image
kubectl -n lastmile set image deployment/rider-service rider-service=saniyaismail999/lastmile-rider:1.1

# Wait for rollout
kubectl -n lastmile rollout status deployment/rider-service

# Verify
kubectl -n lastmile get pods -l app=rider-service
```

## Detailed Steps

### Step 1: Verify Code is Fixed

```bash
cd /home/niveditha/lastmile-main
python3 -c "from services.rider_service.app import RiderService; print('✅ Code is valid')"
```

### Step 2: Build Image

The Dockerfile builds:
- Python 3.11 base image
- Installs dependencies from `requirements.txt`
- Copies rider service code
- Copies protobuf generated files
- Sets up environment

```bash
docker build -f services/rider_service/Dockerfile -t saniyaismail999/lastmile-rider:1.1 .
```

### Step 3: Test Image Locally (Optional)

```bash
# Run container locally to test
docker run -it --rm \
  -e DATABASE_URL="postgresql://lastmile:lastmile@host.docker.internal:5432/lastmile" \
  -e RABBITMQ_URL="amqp://guest:guest@host.docker.internal:5672/" \
  saniyaismail999/lastmile-rider:1.1
```

### Step 4: Push to DockerHub

```bash
docker login
docker push saniyaismail999/lastmile-rider:1.1
docker push saniyaismail999/lastmile-rider:latest
```

### Step 5: Update Kubernetes

```bash
# Method 1: kubectl set image (quickest)
kubectl -n lastmile set image deployment/rider-service rider-service=saniyaismail999/lastmile-rider:1.1

# Method 2: Edit YAML
vim services/rider_service/k8s/rider-deployment.yaml
# Change image: saniyaismail999/lastmile-rider:1.0
# To:     image: saniyaismail999/lastmile-rider:1.1
kubectl -n lastmile apply -f services/rider_service/k8s/rider-deployment.yaml

# Wait for rollout
kubectl -n lastmile rollout status deployment/rider-service
```

### Step 6: Verify

```bash
# Check pod is running
kubectl -n lastmile get pods -l app=rider-service

# Check logs
kubectl -n lastmile logs -l app=rider-service --tail=20

# Test registration
python3 scripts/demo_simulation.py
# Should see: [TEST] Registered rider rider-demo-1: True
```

## Troubleshooting

### Build Fails

```bash
# Check Dockerfile syntax
docker build -f services/rider_service/Dockerfile -t test-rider . 2>&1 | tail -20

# Check if protobuf files exist
ls services/common_lib/protos_generated/rider_pb2.py
```

### Push Fails

```bash
# Verify login
docker login

# Check image exists
docker images | grep lastmile-rider

# Try pushing again
docker push saniyaismail999/lastmile-rider:1.1
```

### Deployment Fails

```bash
# Check pod status
kubectl -n lastmile describe pod -l app=rider-service

# Check events
kubectl -n lastmile get events --sort-by='.lastTimestamp' | grep rider

# Check logs
kubectl -n lastmile logs -l app=rider-service
```

### Old Image Still Running

```bash
# Force delete pod
kubectl -n lastmile delete pod -l app=rider-service

# Or restart deployment
kubectl -n lastmile rollout restart deployment/rider-service
```

## Version Management

### Current Version
- **Image**: `saniyaismail999/lastmile-rider:1.0` (old)
- **New Version**: `saniyaismail999/lastmile-rider:1.1` (with your fix)

### Versioning Strategy
- **Major version** (1.x): Breaking changes
- **Minor version** (x.1): New features, fixes
- **Patch version** (x.x.1): Bug fixes

### Updating Other Services

Same process for any service:
```bash
# Build
docker build -f services/<service>/Dockerfile -t saniyaismail999/lastmile-<service>:1.1 .

# Push
docker push saniyaismail999/lastmile-<service>:1.1

# Deploy
kubectl -n lastmile set image deployment/<service>-service <service>-service=saniyaismail999/lastmile-<service>:1.1
```

