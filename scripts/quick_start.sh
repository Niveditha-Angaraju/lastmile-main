#!/bin/bash
# Quick Start Script for LastMile Demo
# This script helps you get started quickly with the demo

set -e

echo "=========================================="
echo "🚗 LastMile Quick Start"
echo "=========================================="
echo ""

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found. Please install kubectl first."
    exit 1
fi

# Check if namespace exists
if ! kubectl get namespace lastmile &> /dev/null; then
    echo "❌ Namespace 'lastmile' not found. Please deploy services first."
    exit 1
fi

echo "✅ Kubernetes cluster accessible"
echo ""

# Check if services are running
echo "Checking service status..."
PODS=$(kubectl -n lastmile get pods --no-headers 2>/dev/null | wc -l)
if [ "$PODS" -eq 0 ]; then
    echo "❌ No pods found in 'lastmile' namespace"
    exit 1
fi

RUNNING=$(kubectl -n lastmile get pods --no-headers 2>/dev/null | grep Running | wc -l)
echo "   Pods: $RUNNING/$PODS running"
echo ""

# Start port forwarding in background
echo "Starting port forwarding..."
./scripts/port_forward_services.sh > /tmp/lastmile_portforward.log 2>&1 &
PF_PID=$!
sleep 3

if ps -p $PF_PID > /dev/null; then
    echo "✅ Port forwarding started (PID: $PF_PID)"
    echo "   Logs: /tmp/lastmile_portforward.log"
else
    echo "❌ Failed to start port forwarding"
    exit 1
fi

echo ""
echo "=========================================="
echo "Next Steps:"
echo "=========================================="
echo ""
echo "1. Start Backend API:"
echo "   cd backend && python app.py"
echo ""
echo "2. Start Frontend (choose one):"
echo "   Option A - React (recommended):"
echo "     cd frontend && npm install && npm run dev"
echo ""
echo "   Option B - Simple HTML:"
echo "     Open frontend/simple.html in browser"
echo ""
echo "3. Run Simulations:"
echo "   python scripts/demo_simulation.py"
echo ""
echo "4. Run Tests:"
echo "   python tests/e2e_test_k8s.py"
echo ""
echo "=========================================="
echo "Services are now accessible at:"
echo "=========================================="
echo "  Station Service:    localhost:50051"
echo "  Driver Service:     localhost:50052"
echo "  Location Service:   localhost:50053"
echo "  Matching Service:   localhost:50054"
echo "  Trip Service:       localhost:50055"
echo "  Notification:       localhost:50056"
echo "  Rider Service:      localhost:50057"
echo "  User Service:       localhost:50058"
echo "  RabbitMQ:           localhost:5672"
echo "  PostgreSQL:         localhost:5432"
echo ""
echo "To stop port forwarding:"
echo "  kill $PF_PID"
echo "  or: pkill -f 'kubectl.*port-forward'"
echo ""

