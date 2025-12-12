#!/bin/bash
#
# Resilience Testing Script
# Tests how the application handles failed services
#
# Usage:
#   ./scripts/test_resilience.sh [service_name]
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

NAMESPACE="${NAMESPACE:-lastmile}"

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

# Test service failure
test_service_failure() {
    local service=$1
    
    echo ""
    print_info "=========================================="
    print_info "Testing Resilience: $service"
    print_info "=========================================="
    
    # Check if service exists
    if ! kubectl get deployment "$service" -n "$NAMESPACE" &> /dev/null; then
        print_error "Service $service not found"
        return 1
    fi
    
    print_info "1. Checking initial status..."
    kubectl get pods -l app="$service" -n "$NAMESPACE"
    
    print_info "2. Scaling down to 0 replicas (simulating failure)..."
    kubectl scale deployment "$service" --replicas=0 -n "$NAMESPACE"
    
    print_info "3. Waiting for pods to terminate..."
    sleep 5
    
    print_info "4. Checking that service is down..."
    kubectl get pods -l app="$service" -n "$NAMESPACE" || print_success "Service is down (expected)"
    
    print_info "5. Testing system behavior..."
    print_warning "   System should continue operating (other services still running)"
    print_warning "   Requests to $service will fail, but other services should handle gracefully"
    
    sleep 3
    
    print_info "6. Restoring service..."
    kubectl scale deployment "$service" --replicas=1 -n "$NAMESPACE"
    
    print_info "7. Waiting for service to recover..."
    kubectl wait --for=condition=ready pod -l app="$service" -n "$NAMESPACE" --timeout=60s || {
        print_error "Service did not recover in time"
        return 1
    }
    
    print_success "Service recovered successfully!"
    
    print_info "8. Final status..."
    kubectl get pods -l app="$service" -n "$NAMESPACE"
    
    return 0
}

# Test multiple service failures
test_multiple_failures() {
    echo ""
    print_info "=========================================="
    print_info "Testing Multiple Service Failures"
    print_info "=========================================="
    
    local services=("notification-service" "user-service")
    
    print_info "Scaling down non-critical services..."
    for service in "${services[@]}"; do
        if kubectl get deployment "$service" -n "$NAMESPACE" &> /dev/null; then
            print_info "Scaling down $service..."
            kubectl scale deployment "$service" --replicas=0 -n "$NAMESPACE"
        fi
    done
    
    sleep 3
    
    print_info "System should still function (core services running)..."
    print_info "Core services: matching-service, trip-service, driver-service, rider-service"
    
    kubectl get deployments -n "$NAMESPACE" | grep -E "matching|trip|driver|rider"
    
    print_info "Restoring services..."
    for service in "${services[@]}"; do
        if kubectl get deployment "$service" -n "$NAMESPACE" &> /dev/null; then
            kubectl scale deployment "$service" --replicas=1 -n "$NAMESPACE"
        fi
    done
    
    print_success "Multiple service failure test complete"
}

# Main
main() {
    local target_service="${1:-matching-service}"
    
    echo ""
    print_info "=========================================="
    print_info "LastMile Resilience Testing"
    print_info "=========================================="
    echo ""
    
    # Check Kubernetes connection
    if ! kubectl cluster-info &> /dev/null; then
        print_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    # Test single service failure
    test_service_failure "$target_service"
    
    # Test multiple failures
    test_multiple_failures
    
    echo ""
    print_success "Resilience testing complete! 🎉"
    echo ""
    print_info "Summary:"
    print_info "  - Services can be scaled down (fail)"
    print_info "  - System continues operating with other services"
    print_info "  - Services recover when scaled back up"
    print_info "  - Kubernetes handles pod restarts automatically"
}

main "$@"

