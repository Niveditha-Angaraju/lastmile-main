#!/bin/bash
# Build and push Rider Service Docker image
# Usage: ./build_and_push.sh [version] [dockerhub-username]

set -e

VERSION=${1:-1.1}
DOCKERHUB_USER=${2:-saniyaismail999}
IMAGE_NAME="lastmile-rider"
FULL_IMAGE_NAME="${DOCKERHUB_USER}/${IMAGE_NAME}:${VERSION}"
LATEST_IMAGE_NAME="${DOCKERHUB_USER}/${IMAGE_NAME}:latest"

echo "=========================================="
echo "Building Rider Service Docker Image"
echo "=========================================="
echo "Image: ${FULL_IMAGE_NAME}"
echo "Version: ${VERSION}"
echo ""

# Navigate to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"

echo "Building Docker image..."
docker build -f services/rider_service/Dockerfile -t "${FULL_IMAGE_NAME}" .

echo ""
echo "Tagging as latest..."
docker tag "${FULL_IMAGE_NAME}" "${LATEST_IMAGE_NAME}"

echo ""
echo "=========================================="
echo "Pushing to DockerHub"
echo "=========================================="
echo "Make sure you're logged in: docker login"
echo ""

read -p "Push to DockerHub? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Pushing ${FULL_IMAGE_NAME}..."
    docker push "${FULL_IMAGE_NAME}"
    
    echo "Pushing ${LATEST_IMAGE_NAME}..."
    docker push "${LATEST_IMAGE_NAME}"
    
    echo ""
    echo "✅ Successfully pushed to DockerHub!"
    echo ""
    echo "To update Kubernetes deployment:"
    echo "  kubectl -n lastmile set image deployment/rider-service rider-service=${FULL_IMAGE_NAME}"
    echo "  kubectl -n lastmile rollout status deployment/rider-service"
else
    echo "Skipped push. Image built locally: ${FULL_IMAGE_NAME}"
fi

echo ""
echo "=========================================="
echo "Build Complete"
echo "=========================================="

