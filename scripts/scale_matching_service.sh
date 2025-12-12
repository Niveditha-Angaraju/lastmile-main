#!/bin/bash
#
# Matching Service Scaling Script
# Scales matching service from 1 to 5 replicas and back
#
# Usage:
#   ./scripts/scale_matching_service.sh [replicas]
#   If replicas not provided, scales 1→2→3→4→5→1
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

NAMESPACE="${NAMESPACE:-lastmile}"
SERVICE="matching-service"

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

# Scale to specific number of replicas
scale_to() {
    local replicas=$1
    
    print_info "Scaling $SERVICE to $replicas replicas..."
    kubectl scale deployment "$SERVICE" --replicas="$replicas" -n "$NAMESPACE"
    
    print_info "Waiting for pods to be ready..."
    kubectl wait --for=condition=ready pod -l app="$SERVICE" -n "$NAMESPACE" --timeout=120s || {
        print_warning "Some pods may not be ready yet"
    }
    
    print_info "Current status:"
    kubectl get pods -l app="$SERVICE" -n "$NAMESPACE"
    
    local ready_count=$(kubectl get pods -l app="$SERVICE" -n "$NAMESPACE" --field-selector=status.phase=Running --no-headers | wc -l | tr -d ' ')
    
    if [ "$ready_count" -eq "$replicas" ]; then
        print_success "All $replicas replicas are running!"
    else
        print_warning "Only $ready_count/$replicas replicas are running"
    fi
    
    return 0
}

# Test scaling sequence
test_scaling_sequence() {
    echo ""
    print_info "=========================================="
    print_info "Matching Service Scaling Test"
    print_info "=========================================="
    echo ""
    
    # Check if service exists
    if ! kubectl get deployment "$SERVICE" -n "$NAMESPACE" &> /dev/null; then
        print_error "Service $SERVICE not found"
        exit 1
    fi
    
    # Scale 1 → 2 → 3 → 4 → 5 → 1
    for replicas in 1 2 3 4 5 1; do
        echo ""
        print_info "=========================================="
        print_info "Scaling to $replicas replicas"
        print_info "=========================================="
        
        scale_to "$replicas"
        
        if [ "$replicas" -gt 1 ]; then
            print_info "Testing load distribution..."
            print_info "All $replicas instances should be processing matches"
            
            # Show pod distribution
            print_info "Pod distribution:"
            kubectl get pods -l app="$SERVICE" -n "$NAMESPACE" -o wide
        fi
        
        sleep 3
    done
    
    print_success "Scaling test complete!"
}

# Scale to specific number
scale_to_specific() {
    local replicas=$1
    
    if ! [[ "$replicas" =~ ^[0-9]+$ ]] || [ "$replicas" -lt 1 ] || [ "$replicas" -gt 5 ]; then
        print_error "Replicas must be between 1 and 5"
        exit 1
    fi
    
    echo ""
    print_info "Scaling $SERVICE to $replicas replicas..."
    scale_to "$replicas"
    
    echo ""
    print_success "Scaled to $replicas replicas! 🎉"
}

# Main
main() {
    local target_replicas="${1:-}"
    
    echo ""
    print_info "=========================================="
    print_info "LastMile Matching Service Scaling"
    print_info "=========================================="
    echo ""
    
    # Check Kubernetes connection
    if ! kubectl cluster-info &> /dev/null; then
        print_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    if [ -z "$target_replicas" ]; then
        # Run full scaling sequence
        test_scaling_sequence
    else
        # Scale to specific number
        scale_to_specific "$target_replicas"
    fi
    
    echo ""
    print_info "Current status:"
    kubectl get deployment "$SERVICE" -n "$NAMESPACE"
    kubectl get pods -l app="$SERVICE" -n "$NAMESPACE"
}

main "$@"

