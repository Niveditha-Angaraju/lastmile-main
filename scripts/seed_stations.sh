#!/bin/bash
# Seed stations - tries local first, then Kubernetes method

echo "🌱 Seeding stations..."
echo ""

# Check if port forwarding is active
if ps aux | grep -q "[k]ubectl.*port-forward.*postgres"; then
    echo "✅ PostgreSQL port-forward detected"
    echo "   Attempting local seeding..."
    python3 scripts/seed_stations_local.py
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ Stations seeded successfully!"
        exit 0
    else
        echo ""
        echo "⚠️  Local seeding failed. Trying Kubernetes method..."
    fi
else
    echo "⚠️  PostgreSQL port-forward not detected"
    echo "   Trying Kubernetes method..."
fi

# Try Kubernetes method
echo ""
echo "Attempting to seed via Kubernetes pod..."
kubectl -n lastmile run station-seeder --rm -i \
  --env="DATABASE_URL=postgresql://lastmile:lastmile@postgres:5432/lastmile" \
  --image=saniyaismail999/lastmile-station:1.0 \
  --restart=Never -- \
  bash -c "python services/station_service/init_db.py && python services/station_service/seed_stations.py" 2>/dev/null

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Stations seeded successfully!"
else
    echo ""
    echo "❌ Failed to seed stations"
    echo ""
    echo "Options:"
    echo "1. Start port forwarding: ./scripts/port_forward_services.sh"
    echo "2. Then run: python3 scripts/seed_stations_local.py"
    echo "3. Or use Kubernetes: ./scripts/seed_stations_k8s.sh"
    exit 1
fi

