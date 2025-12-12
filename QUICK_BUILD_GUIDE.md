# Quick Build and Deploy Guide

## Fixed Script

The `build_and_deploy_all.sh` script has been fixed to:
- ✅ Use correct directory names (with underscores: `rider_service`)
- ✅ Convert to correct image names (without "-service": `lastmile-rider`)
- ✅ Find deployment files correctly
- ✅ Handle Kubernetes deployment names (with hyphens: `rider-service`)

## Usage

### Build All Services

```bash
./scripts/build_and_deploy_all.sh
```

### Build Single Service

```bash
# Build rider service
./scripts/build_and_deploy_all.sh rider_service

# Build matching service
./scripts/build_and_deploy_all.sh matching_service
```

### Build with Custom Version

```bash
./scripts/build_and_deploy_all.sh rider_service 2.0
```

## Service Names

**Directory Names** (use these in script):
- `rider_service`
- `driver_service`
- `matching_service`
- `location_service`
- `trip_service`
- `station_service`
- `notification_service`
- `user_service`

**Docker Image Names** (generated automatically):
- `saniyaismail999/lastmile-rider:1.0`
- `saniyaismail999/lastmile-driver:1.0`
- `saniyaismail999/lastmile-matching:1.0`
- etc.

**Kubernetes Deployment Names** (used in K8s):
- `rider-service`
- `driver-service`
- `matching-service`
- etc.

## What the Script Does

1. **Checks Prerequisites**
   - Docker installed
   - kubectl installed
   - DockerHub login
   - Kubernetes connection

2. **Builds Docker Image**
   - Builds from service directory
   - Tags with DockerHub username
   - Pushes to DockerHub

3. **Updates Kubernetes**
   - Finds deployment file
   - Updates image reference
   - Applies deployment
   - Restarts deployment

## Troubleshooting

### "Service directory not found"
- Check you're using underscore names: `rider_service` not `rider-service`
- Verify directory exists: `ls services/rider_service`

### "Deployment file not found"
- Check deployment file exists: `ls services/rider_service/k8s/rider-deployment.yaml`
- File should be named with hyphens: `rider-deployment.yaml`

### "Failed to push"
- Check DockerHub login: `docker login`
- Verify image name is correct
- Check DockerHub permissions

### "Failed to apply deployment"
- Check Kubernetes connection: `kubectl cluster-info`
- Verify namespace exists: `kubectl get namespace lastmile`
- Check deployment YAML is valid

## Example Output

```
ℹ️  ==========================================
ℹ️  Processing: rider_service
ℹ️  ==========================================
ℹ️  Building rider_service...
ℹ️  Building Docker image: saniyaismail999/lastmile-rider:1.0
✅ Built and pushed rider_service
ℹ️  Updating Kubernetes deployment for rider_service...
ℹ️  Found deployment file: services/rider_service/k8s/rider-deployment.yaml
✅ Updated Kubernetes deployment for rider_service
✅ Completed: rider_service
```

## Next Steps

After building:
1. Check deployments: `kubectl get deployments -n lastmile`
2. Check pods: `kubectl get pods -n lastmile`
3. Check logs: `kubectl logs -l app=rider-service -n lastmile`

