#!/usr/bin/env bash
set -euo pipefail

OUTDIR=infra/k8s/lastmile
mkdir -p "$OUTDIR"

# Namespace manifest
cat > "$OUTDIR/00-namespace.yml" <<NS
apiVersion: v1
kind: Namespace
metadata:
  name: lastmile
NS

# Service list and port mapping.
# If a service uses a different internal port, change the number below.
declare -A SERVICES
SERVICES=(
  [gateway]=8000
  [user-service]=8001
  [station-service]=8002
  [location-service]=8003
  [matching-service]=8004
  [driver-service]=8005
  [notification-service]=8006
  [trip-service]=8007
  [rider-service]=8008
)

# Template generator
for svc in "${!SERVICES[@]}"; do
  port="${SERVICES[$svc]}"
  # normalize k8s resource names (deployment/service)
  name="${svc}"
  image="lastmile/${svc}:latest"

  # Deployment
  cat > "$OUTDIR/DEPLOY_${name}.yml" <<DEP
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ${name}
  namespace: lastmile
  labels:
    app: ${name}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ${name}
  template:
    metadata:
      labels:
        app: ${name}
    spec:
      # If you're pulling from a private registry add imagePullSecrets here
      containers:
        - name: ${name}
          image: ${image}
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: ${port}
          env:
            - name: PORT
              value: "${port}"
          readinessProbe:
            httpGet:
              path: /healthz
              port: ${port}
            initialDelaySeconds: 5
            periodSeconds: 5
            failureThreshold: 3
          livenessProbe:
            httpGet:
              path: /healthz
              port: ${port}
            initialDelaySeconds: 10
            periodSeconds: 10
            failureThreshold: 5
          resources:
            requests:
              cpu: "100m"
              memory: "128Mi"
            limits:
              cpu: "500m"
              memory: "512Mi"
DEP

  # Service
  cat > "$OUTDIR/SVC_${name}.yml" <<SVC
apiVersion: v1
kind: Service
metadata:
  name: ${name}
  namespace: lastmile
  labels:
    app: ${name}
spec:
  type: ClusterIP
  selector:
    app: ${name}
  ports:
    - protocol: TCP
      port: ${port}
      targetPort: ${port}
SVC

done

echo "Manifests generated in $OUTDIR"
echo ""
echo "Files:"
ls -1 infra/k8s/lastmile
