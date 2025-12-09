#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT_DIR="$REPO_ROOT/infra/k8s/generated"
SERVICES_DIR="$REPO_ROOT/services"
NAMESPACE="${NAMESPACE:-lastmile}"

mkdir -p "$OUT_DIR"
rm -f "$OUT_DIR"/* || true

echo "Collecting service k8s manifests..."
for svc in "$SERVICES_DIR"/*; do
  svcname=$(basename "$svc")
  kdir="$svc/k8s"
  if [ -d "$kdir" ]; then
    for f in "$kdir"/*; do
      [ -f "$f" ] || continue
      outf="$OUT_DIR/$(basename "$f")"
      if grep -q "namespace:" "$f"; then
        cp "$f" "$outf"
      else
        awk -v ns="$NAMESPACE" '
          BEGIN{printed=0}
          /metadata:/{print; getline; if($0 ~ /^[[:space:]]*labels:/){print "  namespace: " ns; print $0; next} else {print "  namespace: " ns; print $0; next}}
          {print}
        ' "$f" > "$outf"
      fi
      echo " - wrote $outf"
    done
  fi
done

echo "Also adding gateway manifest (if present)"
if [ -f "$REPO_ROOT/services/gateway_service/k8s/gateway-deployment.yaml" ]; then
  cp "$REPO_ROOT/services/gateway_service/k8s/gateway-deployment.yaml" "$OUT_DIR/gateway-deployment.yaml"
  echo " - gateway-deployment.yaml"
fi

echo "Generated manifests in $OUT_DIR"
