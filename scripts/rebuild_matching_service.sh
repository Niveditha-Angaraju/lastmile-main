#!/bin/bash
# Rebuild and deploy matching service with the fix
# Usage: ./scripts/rebuild_matching_service.sh [version] [dockerhub-username]

set -e

VERSION=${1:-1.1}
DOCKERHUB_USER=${2:-saniyaismail999}
IMAGE_NAME="${DOCKERHUB_USER}/lastmile-matching:${VERSION}"
LATEST_IMAGE_NAME="${DOCKERHUB_USER}/lastmile-matching:latest"

echo "=========================================="
echo "Rebuilding Matching Service"
echo "=========================================="
echo "Version: ${VERSION}"
echo "Image: ${IMAGE_NAME}"
echo ""

cd "$(dirname "$0")/.."

# Step 1: Build
echo "Step 1: Building Docker image..."
docker build -f services/matching_service/Dockerfile -t "${IMAGE_NAME}" .

# Step 2: Tag as latest
echo ""
echo "Step 2: Tagging as latest..."
docker tag "${IMAGE_NAME}" "${LATEST_IMAGE_NAME}"

# Step 3: Check DockerHub login
echo ""
echo "Step 3: Checking DockerHub login..."
if docker info | grep -q "Username"; then
    echo "✅ Already logged in to DockerHub"
    LOGGED_IN=true
else
    echo "⚠️  Not logged in to DockerHub"
    echo ""
    echo "You need to login first:"
    echo "  docker login"
    echo ""
    read -p "Login now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker login
        if [ $? -eq 0 ]; then
            LOGGED_IN=true
            echo "✅ Login successful"
        else
            LOGGED_IN=false
            echo "❌ Login failed"
        fi
    else
        LOGGED_IN=false
    fi
fi

# Step 4: Push (if logged in)
if [ "$LOGGED_IN" = true ]; then
    echo ""
    echo "Step 4: Pushing to DockerHub..."
    echo "Pushing ${IMAGE_NAME}..."
    docker push "${IMAGE_NAME}"
    
    echo "Pushing ${LATEST_IMAGE_NAME}..."
    docker push "${LATEST_IMAGE_NAME}"
    
    echo "✅ Pushed to DockerHub"
else
    echo ""
    echo "⏭️  Skipping push (not logged in)"
    echo "   You can push later with:"
    echo "   docker push ${IMAGE_NAME}"
fi

# Step 5: Check Kubernetes cluster
echo ""
echo "Step 5: Checking Kubernetes cluster connectivity..."
if kubectl cluster-info &>/dev/null; then
    echo "✅ Kubernetes cluster is accessible"
    CLUSTER_OK=true
else
    echo "❌ Cannot connect to Kubernetes cluster"
    echo "   Please start your cluster (e.g., minikube start)"
    CLUSTER_OK=false
fi

# Step 6: Deploy (if cluster is accessible)
if [ "$CLUSTER_OK" = true ]; then
    echo ""
    echo "Step 6: Updating Kubernetes deployment..."
    kubectl -n lastmile set image deployment/matching-service matching-service="${IMAGE_NAME}"
    
    echo ""
    echo "Step 7: Waiting for rollout..."
    kubectl -n lastmile rollout status deployment/matching-service
    
    echo ""
    echo "✅ Deployment complete!"
    echo ""
    echo "Verify:"
    echo "  kubectl -n lastmile get pods -l app=matching-service"
    echo "  kubectl -n lastmile logs -l app=matching-service --tail=20 | grep -E 'DRIVER|SEATS|MATCH'"
else
    echo ""
    echo "⏭️  Skipping deployment (cluster not accessible)"
    echo "   You can deploy later with:"
    echo "   kubectl -n lastmile set image deployment/matching-service matching-service=${IMAGE_NAME}"
fi

echo ""
echo "=========================================="
echo "✅ Build Complete"
echo "=========================================="

