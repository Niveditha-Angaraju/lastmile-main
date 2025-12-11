#!/bin/bash
# Seed stations using a Kubernetes pod
# This works when you're not using port forwarding

NAMESPACE="lastmile"

echo "🌱 Seeding stations via Kubernetes pod..."

kubectl -n $NAMESPACE run station-seeder --rm -it \
  --env="DATABASE_URL=postgresql://lastmile:lastmile@postgres:5432/lastmile" \
  --image=saniyaismail999/lastmile-station:1.0 \
  --restart=Never -- \
  bash -c "python services/station_service/init_db.py && python services/station_service/seed_stations.py" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ Stations seeded successfully!"
else
    echo "❌ Failed to seed stations"
    echo "   Make sure the station service image is available"
    exit 1
fi

