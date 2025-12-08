#!/usr/bin/env bash

set -euo pipefail

# Defaults (change via env or CLI)
REG="${REG:-lastmile}"         # registry/namespace; default "lastmile" for local use
TAG="${TAG:-latest}"          # image tag
PUSH="${PUSH:-false}"         # set to "true" to push images after build
LOAD_MINIKUBE="${LOAD_MINIKUBE:-false}"  # set to true to minikube image load


# Services to build (Dockerfile paths are relative to repo root)
declare -A SERVICES
SERVICES=(
  ["driver-service"]="services/driver_service/Dockerfile"
  ["location-service"]="services/location_service/Dockerfile"
  ["user-service"]="services/user_service/Dockerfile"
  ["rider-service"]="services/rider_service/Dockerfile"
  ["matching-service"]="services/matching_service/Dockerfile"
  ["station-service"]="services/station_service/Dockerfile"
  ["notification-service"]="services/notification_service/Dockerfile"
  ["gateway-service"]="services/gateway_service/Dockerfile"
  ["gateway-service"]="services/trip_service/Dockerfile"
)

# Helper functions
info(){ echo -e "\033[1;34m[INFO]\033[0m $*"; }
err(){ echo -e "\033[1;31m[ERROR]\033[0m $*" >&2; }

# Ensure running from repo root (simple check)
if [ ! -d "services" ] || [ ! -d "infra" ]; then
  err "Please run this script from the project root (the folder that contains 'services/' and 'infra/')."
  exit 2
fi

# Optionally enable BuildKit (faster, modern builds)
export DOCKER_BUILDKIT=${DOCKER_BUILDKIT:-1}

info "Registry: ${REG}  Tag: ${TAG}  PUSH: ${PUSH}  MINIKUBE_LOAD: ${LOAD_MINIKUBE}"

for name in "${!SERVICES[@]}"; do
  dockerfile="${SERVICES[$name]}"
  if [ ! -f "$dockerfile" ]; then
    err "Skipping $name — Dockerfile not found at $dockerfile"
    continue
  fi

  image="${REG}/${name}:${TAG}"
  info "Building ${image} from ${dockerfile} ..."
  docker build -f "$dockerfile" -t "${image}" .

  if [ "$PUSH" = "true" ]; then
    info "Pushing ${image} ..."
    docker push "${image}"
  fi

  if [ "$LOAD_MINIKUBE" = "true" ]; then
    if command -v minikube >/dev/null 2>&1; then
      info "Loading ${image} into minikube ..."
      minikube image load "${image}"
    else
      err "minikube not found; cannot load ${image}"
    fi
  fi

done

info "Done. Built images:"
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" | grep "^${REG}/" || true

cat <<EOF

USAGE NOTES:
 - Run from repo root: ./build_all.sh
 - To push to Docker Hub (or other registry), set REG and PUSH=true:
     REG=yourdockerhubusername ./build_all.sh PUSH=true TAG=0.1.0
 - To load into minikube (no push needed):
     ./build_all.sh LOAD_MINIKUBE=true
   or:
     REG=lastmile ./build_all.sh LOAD_MINIKUBE=true
 - To load into kind:
     ./build_all.sh LOAD_KIND=true KIND_CLUSTER=kind
 - If you get permission denied pushing, run: docker login
 - The script uses BuildKit by default; if you prefer legacy builder unset DOCKER_BUILDKIT.

EOF
