#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
SERVICES_DIR="$REPO_ROOT/services"
MANIFEST_DIR="$REPO_ROOT/infra/k8s/generated"
NAMESPACE="${NAMESPACE:-lastmile}"

# ensure minikube is running
minikube status || (echo "Start minikube first (minikube start)"; exit 2)

echo "Using minikube docker daemon for builds..."
eval "$(minikube docker-env)"

# Build images for each service folder that contains a Dockerfile and an app.py
for svc in "$SERVICES_DIR"/*; do
  svcname=$(basename "$svc")
  if [ -f "$svc/Dockerfile" ] && [ -f "$svc/app.py" ]; then
    echo "Building image lastmile/${svcname}:local"
    docker build -t "lastmile/${svcname}:local" -f "$svc/Dockerfile" "$REPO_ROOT"
  else
    echo "Skipping ${svcname} (no Dockerfile+app.py)"
  fi
done

# Build gateway if present and not already built
if [ -d "$SERVICES_DIR/gateway_service" ]; then
  if [ -f "$SERVICES_DIR/gateway_service/Dockerfile" ]; then
    echo "Building gateway image lastmile/gateway_service:local"
    docker build -t "lastmile/gateway_service:local" -f "$SERVICES_DIR/gateway_service/Dockerfile" "$REPO_ROOT"
  fi
fi

# ensure manifests are generated (call generator)
bash "$REPO_ROOT/infra/k8s/generate_manifests.sh"

# Apply namespace first
kubectl apply -f "$REPO_ROOT/infra/k8s/namespace.yaml"

# Apply every manifest from generated folder
kubectl apply -f "$MANIFEST_DIR"

echo "Waiting for deployments to become ready (namespace: $NAMESPACE)..."
kubectl -n "$NAMESPACE" wait --for=condition=available --timeout=180s deploy --all || true

echo "Pods status:"
kubectl -n "$NAMESPACE" get pods -o wide

# Print gateway URL (if NodePort created)
if kubectl -n "$NAMESPACE" get svc gateway-service >/dev/null 2>&1; then
  echo "Gateway service URL (minikube):"
  minikube service gateway-service -n "$NAMESPACE" --url || true
fi

echo "Done. If anything failed, check 'kubectl -n $NAMESPACE get pods' and 'kubectl -n $NAMESPACE logs <pod>'"
