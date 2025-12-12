#!/bin/bash
#
# Comprehensive Docker Build and Deploy Script
# Builds all services, pushes to DockerHub, and deploys to Kubernetes
#
# Usage:
#   ./scripts/build_and_deploy_all.sh [service_name]
#   If service_name is provided, only that service is built/deployed
#   Otherwise, all services are built/deployed
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOCKERHUB_USER="${DOCKERHUB_USER:-saniyaismail999}"
NAMESPACE="${NAMESPACE:-lastmile}"
K8S_DIR="infra/k8s"

# Services to build (using actual directory names with underscores)
SERVICES=(
    "rider_service"
    "driver_service"
    "matching_service"
    "location_service"
    "trip_service"
    "station_service"
    "notification_service"
    "user_service"
)

# Function to print colored output
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl is not installed"
        exit 1
    fi
    
    # Check Docker login
    if ! docker info | grep -q "Username"; then
        print_warning "Not logged into DockerHub. Attempting login..."
        docker login || {
            print_error "Docker login failed. Please run: docker login"
            exit 1
        }
    fi
    
    # Check Kubernetes connection
    if ! kubectl cluster-info &> /dev/null; then
        print_error "Cannot connect to Kubernetes cluster"
        print_info "Make sure minikube is running: minikube start"
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Build and push a single service
build_and_push_service() {
    local service=$1
    local version="${2:-1.0}"
    
    print_info "Building ${service}..."
    
    local service_dir="services/${service}"
    if [ ! -d "$service_dir" ]; then
        print_error "Service directory not found: $service_dir"
        return 1
    fi
    
    # Convert service name with underscores to hyphens for Docker image name
    # Image names are like "lastmile-rider", "lastmile-driver" (no "-service" suffix)
    local service_name_hyphen=$(echo "$service" | tr '_' '-')
    # Remove trailing "-service" if it exists (rider-service -> rider)
    service_name_hyphen=${service_name_hyphen%-service}
    local image_name="${DOCKERHUB_USER}/lastmile-${service_name_hyphen}:${version}"
    
    # Build from project root so Dockerfiles can access services/ directory
    # Dockerfiles use paths like "services/rider_service/" which require root context
    print_info "Building Docker image: $image_name"
    print_info "Build context: project root (for services/ directory access)"
    
    # Get project root directory (parent of scripts/)
    local project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
    cd "$project_root" || {
        print_error "Failed to change to project root"
        return 1
    }
    
    docker build -f "$service_dir/Dockerfile" -t "$image_name" . || {
        print_error "Failed to build $service"
        return 1
    }
    
    # Push
    print_info "Pushing to DockerHub: $image_name"
    docker push "$image_name" || {
        print_error "Failed to push $service"
        return 1
    }
    
    print_success "Built and pushed $service"
    return 0
}

# Update Kubernetes deployment with new image
update_k8s_deployment() {
    local service=$1
    local version="${2:-1.0}"
    
    # Convert service name with underscores to hyphens for Docker image name
    # Remove "-service" suffix if present
    local service_name_hyphen=$(echo "$service" | tr '_' '-')
    service_name_hyphen=${service_name_hyphen%-service}
    local image_name="${DOCKERHUB_USER}/lastmile-${service_name_hyphen}:${version}"
    
    print_info "Updating Kubernetes deployment for $service..."
    
    # Find deployment file
    # Directory uses underscores (rider_service), filename uses hyphens (rider-deployment.yaml)
    local deployment_file=""
    local service_hyphen=$(echo "$service" | tr '_' '-')
    
    # Try the most common pattern: services/rider_service/k8s/rider-deployment.yaml
    # First try without "-service" suffix (rider-deployment.yaml)
    local service_name_no_suffix=$(echo "$service_hyphen" | sed 's/-service$//')
    if [ -f "services/${service}/k8s/${service_name_no_suffix}-deployment.yaml" ]; then
        deployment_file="services/${service}/k8s/${service_name_no_suffix}-deployment.yaml"
    # Try with full hyphen name
    elif [ -f "services/${service}/k8s/${service_hyphen}-deployment.yaml" ]; then
        deployment_file="services/${service}/k8s/${service_hyphen}-deployment.yaml"
    # Fallback: try underscore version
    elif [ -f "services/${service}/k8s/${service}-deployment.yaml" ]; then
        deployment_file="services/${service}/k8s/${service}-deployment.yaml"
    # Try in infra/k8s directory
    elif [ -f "${K8S_DIR}/${service_hyphen}-deployment.yaml" ]; then
        deployment_file="${K8S_DIR}/${service_hyphen}-deployment.yaml"
    elif [ -f "${K8S_DIR}/${service}-deployment.yaml" ]; then
        deployment_file="${K8S_DIR}/${service}-deployment.yaml"
    else
        print_warning "Deployment file not found for $service, skipping K8s update"
        print_info "   Searched: services/${service}/k8s/${service_hyphen}-deployment.yaml"
        return 0
    fi
    
    print_info "Found deployment file: $deployment_file"
    
    # Update image in deployment file
    # Match pattern like "lastmile-rider" or "lastmile-rider-service"
    local image_pattern=$(echo "$service_name_hyphen" | sed 's/-service$//')
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s|image:.*lastmile-${image_pattern}.*|image: ${image_name}|g" "$deployment_file"
        sed -i '' "s|image:.*lastmile-${service_hyphen}.*|image: ${image_name}|g" "$deployment_file"
    else
        # Linux
        sed -i "s|image:.*lastmile-${image_pattern}.*|image: ${image_name}|g" "$deployment_file"
        sed -i "s|image:.*lastmile-${service_hyphen}.*|image: ${image_name}|g" "$deployment_file"
    fi
    
    # Apply deployment
    kubectl apply -f "$deployment_file" -n "$NAMESPACE" || {
        print_error "Failed to apply deployment for $service"
        return 1
    }
    
    # Restart deployment to pull new image (deployment names use hyphens)
    local service_hyphen=$(echo "$service" | tr '_' '-')
    local deployment_name="${service_hyphen}"
    
    # Check if deployment exists
    if kubectl get deployment "${deployment_name}" -n "$NAMESPACE" &> /dev/null; then
        kubectl rollout restart deployment/${deployment_name} -n "$NAMESPACE" || {
            print_warning "Could not restart deployment ${deployment_name}"
        }
    else
        print_warning "Deployment ${deployment_name} does not exist yet (will be created on first apply)"
    fi
    
    print_success "Updated Kubernetes deployment for $service"
    return 0
}

# Build and deploy a service
build_and_deploy_service() {
    local service=$1
    local version="${2:-1.0}"
    
    echo ""
    print_info "=========================================="
    print_info "Processing: $service"
    print_info "=========================================="
    
    build_and_push_service "$service" "$version" || return 1
    update_k8s_deployment "$service" "$version" || return 1
    
    print_success "Completed: $service"
    return 0
}

# Main execution
main() {
    local target_service="${1:-}"
    local version="${2:-1.0}"
    
    echo ""
    print_info "=========================================="
    print_info "LastMile Docker Build & Deploy Script"
    print_info "=========================================="
    echo ""
    print_info "DockerHub User: $DOCKERHUB_USER"
    print_info "Namespace: $NAMESPACE"
    print_info "Version: $version"
    echo ""
    
    check_prerequisites
    
    if [ -n "$target_service" ]; then
        # Build single service
        print_info "Building single service: $target_service"
        build_and_deploy_service "$target_service" "$version"
    else
        # Build all services
        print_info "Building all services..."
        local failed_services=()
        
        for service in "${SERVICES[@]}"; do
            if ! build_and_deploy_service "$service" "$version"; then
                failed_services+=("$service")
            fi
            sleep 1  # Small delay between services
        done
        
        echo ""
        print_info "=========================================="
        print_info "Build Summary"
        print_info "=========================================="
        
        if [ ${#failed_services[@]} -eq 0 ]; then
            print_success "All services built and deployed successfully!"
        else
            print_error "Failed services: ${failed_services[*]}"
            exit 1
        fi
    fi
    
    echo ""
    print_info "Waiting for deployments to be ready..."
    sleep 5
    
    print_info "Checking deployment status..."
    kubectl get deployments -n "$NAMESPACE"
    
    echo ""
    print_success "Done! 🎉"
}

# Run main function
main "$@"

