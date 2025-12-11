#!/bin/bash
# Query trips directly from Kubernetes PostgreSQL
# This bypasses the port-forwarding database connection issues

echo "Querying trips from Kubernetes PostgreSQL..."
echo ""

kubectl -n lastmile exec -it postgres-0 -- psql -U lastmile -d lastmile -c "
SELECT 
    trip_id,
    driver_id,
    rider_ids,
    origin_station,
    destination,
    status,
    start_time,
    end_time,
    seats_reserved
FROM trips
ORDER BY start_time DESC
LIMIT 20;
"

echo ""
echo "To see more details, run:"
echo "  kubectl -n lastmile exec -it postgres-0 -- psql -U lastmile -d lastmile"

