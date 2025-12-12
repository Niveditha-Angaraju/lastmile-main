#!/bin/bash
# Quick build and deploy script for Rider Service
# Usage: ./QUICK_BUILD_DEPLOY.sh [version] [dockerhub-username]

set -e

VERSION=${1:-1.1}
DOCKERHUB_USER=${2:-saniyaismail999}
IMAGE_NAME="${DOCKERHUB_USER}/lastmile-rider:${VERSION}"

echo "=========================================="
echo "Quick Build and Deploy"
echo "=========================================="
echo "Version: ${VERSION}"
echo "Image: ${IMAGE_NAME}"
echo ""

cd "$(dirname "$0")"

# Step 1: Build
echo "Step 1: Building Docker image..."
docker build -f services/rider_service/Dockerfile -t "${IMAGE_NAME}" .

# Step 2: Tag as latest
echo ""
echo "Step 2: Tagging as latest..."
docker tag "${IMAGE_NAME}" "${DOCKERHUB_USER}/lastmile-rider:latest"

# Step 3: Push
echo ""
echo "Step 3: Pushing to DockerHub..."
echo "Make sure you're logged in: docker login"
read -p "Push to DockerHub? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker push "${IMAGE_NAME}"
    docker push "${DOCKERHUB_USER}/lastmile-rider:latest"
    echo "✅ Pushed to DockerHub"
else
    echo "⏭️  Skipped push"
fi

# Step 4: Check Kubernetes cluster connectivity
echo ""
echo "Step 4: Checking Kubernetes cluster connectivity..."
if kubectl cluster-info &>/dev/null; then
    echo "✅ Kubernetes cluster is accessible"
    CLUSTER_OK=true
else
    echo "❌ Cannot connect to Kubernetes cluster"
    echo ""
    echo "The cluster appears to be stopped or unreachable."
    echo ""
    echo "To start Minikube:"
    echo "  minikube start"
    echo ""
    echo "Or if using a different cluster, check:"
    echo "  kubectl cluster-info"
    echo "  kubectl get nodes"
    echo ""
    read -p "Skip deployment? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        CLUSTER_OK=false
        echo "⏭️  Skipping deployment"
    else
        echo "Please start your cluster and run this script again."
        exit 1
    fi
fi

# Step 5: Deploy (if cluster is accessible)
if [ "$CLUSTER_OK" = true ]; then
    echo ""
    echo "Step 5: Deploying to Kubernetes..."
    kubectl -n lastmile set image deployment/rider-service rider-service="${IMAGE_NAME}"

    echo ""
    echo "Step 6: Waiting for rollout..."
    kubectl -n lastmile rollout status deployment/rider-service
fi

echo ""
echo "=========================================="
echo "✅ Deployment Complete!"
echo "=========================================="
echo ""
echo "Verify:"
echo "  kubectl -n lastmile get pods -l app=rider-service"
echo "  kubectl -n lastmile logs -l app=rider-service --tail=20"
echo ""
echo "Test:"
echo "  python3 scripts/demo_simulation.py"

