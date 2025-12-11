#!/bin/bash
# Port forward all LastMile services for local testing
# This allows you to connect to services running in Kubernetes from your local machine

NAMESPACE="lastmile"

echo "Setting up port forwarding for LastMile services..."
echo "Press Ctrl+C to stop all port forwards"
echo ""

# Function to port forward a service
port_forward() {
    local service=$1
    local local_port=$2
    local target_port=$3
    
    echo "Port forwarding $service: localhost:$local_port -> $service:$target_port"
    kubectl -n $NAMESPACE port-forward svc/$service $local_port:$target_port > /dev/null 2>&1 &
    sleep 1
}

# Port forward all services
port_forward station-service 50051 50051
port_forward driver-service 50052 50052
port_forward location-service 50053 50053
port_forward matching-service 50054 50054
port_forward trip-service 50055 50055
port_forward notification-service 50056 50056
port_forward rider-service 50057 50057
port_forward user-service 50058 50058
port_forward rabbitmq 5672 5672
port_forward postgres 5432 5432

echo ""
echo "✅ All services port forwarded!"
echo ""
echo "Services available at:"
echo "  - Station Service:    localhost:50051"
echo "  - Driver Service:     localhost:50052"
echo "  - Location Service:   localhost:50053"
echo "  - Matching Service:   localhost:50054"
echo "  - Trip Service:       localhost:50055"
echo "  - Notification Service: localhost:50056"
echo "  - Rider Service:      localhost:50057"
echo "  - User Service:       localhost:50058"
echo "  - RabbitMQ:           localhost:5672"
echo "  - PostgreSQL:         localhost:5432"
echo ""
echo "To stop port forwarding, press Ctrl+C or run:"
echo "  pkill -f 'kubectl.*port-forward'"

# Wait for interrupt
trap "echo ''; echo 'Stopping port forwards...'; pkill -f 'kubectl.*port-forward'; exit" INT
wait

