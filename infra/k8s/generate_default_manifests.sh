#!/usr/bin/env bash
# Generate default k8s Deployment+Service manifests for each service that has app.py + Dockerfile.
# - backend gRPC services -> port 50052 with TCP readiness/liveness probes
# - gateway_service -> port 8000 with HTTP /health probes
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT_DIR="$REPO_ROOT/infra/k8s/generated"
SERVICES_DIR="$REPO_ROOT/services"
NAMESPACE="${NAMESPACE:-lastmile}"

mkdir -p "$OUT_DIR"

echo "Generating default manifests into $OUT_DIR ..."

for svc in "$SERVICES_DIR"/*; do
  [ -d "$svc" ] || continue
  svcname="$(basename "$svc")"
  # only generate for services that have an app.py and Dockerfile
  if [ -f "$svc/app.py" ] && [ -f "$svc/Dockerfile" ]; then
    # pick port: gateway -> 8000 else 50052
    if [ "$svcname" = "gateway_service" ]; then
      port=8000
    else
      port=50052
    fi
    image="lastmile/${svcname}:local"
    out="$OUT_DIR/${svcname}-deployment.yaml"
    cat > "$out" <<EOF
apiVersion: v1
kind: Namespace
metadata:
  name: ${NAMESPACE}
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ${svcname}
  namespace: ${NAMESPACE}
  labels:
    app: ${svcname}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ${svcname}
  template:
    metadata:
      labels:
        app: ${svcname}
    spec:
      containers:
      - name: ${svcname}
        image: ${image}
        imagePullPolicy: IfNotPresent
        env:
        - name: PORT
          value: "${port}"
        ports:
        - containerPort: ${port}
EOF
    # Add probes: TCP for gRPC backends, HTTP for gateway
    if [ "$port" -eq 50052 ]; then
      cat >> "$out" <<'EOF'
        readinessProbe:
          tcpSocket:
            port: 50052
          initialDelaySeconds: 5
          periodSeconds: 10
        livenessProbe:
          tcpSocket:
            port: 50052
          initialDelaySeconds: 20
          periodSeconds: 20
EOF
    else
      cat >> "$out" <<EOF
        readinessProbe:
          httpGet:
            path: /health
            port: ${port}
          initialDelaySeconds: 5
          periodSeconds: 10
        livenessProbe:
          httpGet:
            path: /health
            port: ${port}
          initialDelaySeconds: 20
          periodSeconds: 20
EOF
    fi
    cat >> "$out" <<'EOF'
---
apiVersion: v1
kind: Service
metadata:
  name: ${svcname}
  namespace: ${NAMESPACE}
spec:
  selector:
    app: ${svcname}
  ports:
  - port: ${port}
    targetPort: ${port}
EOF
    echo "Wrote $out"
  fi
done

echo "Done. Generated manifests in $OUT_DIR"
