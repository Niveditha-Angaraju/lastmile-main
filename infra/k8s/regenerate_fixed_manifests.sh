#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT_DIR="$REPO_ROOT/infra/k8s/generated"
SERVICES_DIR="$REPO_ROOT/services"
NAMESPACE="${NAMESPACE:-lastmile}"

mkdir -p "$OUT_DIR"
rm -f "$OUT_DIR"/* || true

echo "Generating fixed manifests into $OUT_DIR ..."
for svc in "$SERVICES_DIR"/*; do
  [ -d "$svc" ] || continue
  svcname="$(basename "$svc")"
  # only if service has app.py and Dockerfile
  if [ -f "$svc/app.py" ] && [ -f "$svc/Dockerfile" ]; then
    # sanitize K8s resource name (lowercase, replace _ with -)
    kname="$(echo "$svcname" | tr '[:upper:]' '[:lower:]' | tr '_' '-')"
    if [ "$kname" = "gateway-service" ] || [ "$svcname" = "gateway_service" ] || [ "$svcname" = "gateway-service" ]; then
      port=8000
    else
      port=50052
    fi
    image="lastmile/${svcname}:local"
    out="$OUT_DIR/${kname}-deployment.yaml"

    cat > "$out" <<EOF
apiVersion: v1
kind: Namespace
metadata:
  name: ${NAMESPACE}
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ${kname}
  namespace: ${NAMESPACE}
  labels:
    app: ${kname}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ${kname}
  template:
    metadata:
      labels:
        app: ${kname}
    spec:
      containers:
      - name: ${kname}
        image: ${image}
        imagePullPolicy: IfNotPresent
        env:
        - name: PORT
          value: "${port}"
        ports:
        - containerPort: ${port}
EOF

    # probes: TCP for gRPC backends, HTTP for gateway
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

    # append service (note: port is numeric)
    cat >> "$out" <<EOF
---
apiVersion: v1
kind: Service
metadata:
  name: ${kname}
  namespace: ${NAMESPACE}
spec:
  selector:
    app: ${kname}
  ports:
  - port: ${port}
    targetPort: ${port}
EOF

    echo "Wrote $out (service: ${kname}, port: ${port})"
  fi
done

echo
echo "Validating generated manifests (client-side dry-run)..."
fail=0
for f in "$OUT_DIR"/*.yaml; do
  [ -f "$f" ] || continue
  echo "---- validating: $f ----"
  if ! kubectl apply --dry-run=client -f "$f" 2>&1; then
    echo "Validation failed for $f"
    fail=1
  fi
done

if [ "$fail" -ne 0 ]; then
  echo "One or more manifests failed validation. Inspect above output."
  exit 1
fi

echo "All manifests validated successfully. Files in: $OUT_DIR"
exit 0
