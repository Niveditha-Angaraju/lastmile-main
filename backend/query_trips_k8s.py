"""
Helper script to query trips from Kubernetes database
Can be called from backend as a fallback
"""
import subprocess
import json
import sys

def query_trips_via_kubectl():
    """Query trips from Kubernetes PostgreSQL using kubectl exec."""
    try:
        cmd = [
            "kubectl", "-n", "lastmile", "exec", "postgres-0", "--",
            "psql", "-U", "lastmile", "-d", "lastmile", "-t", "-A", "-F", ",",
            "-c", """
                SELECT 
                    trip_id, driver_id, rider_ids, origin_station, destination,
                    status, start_time, end_time, seats_reserved
                FROM trips
                ORDER BY start_time DESC
                LIMIT 100;
            """
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            return []
        
        trips = []
        for line in result.stdout.strip().split('\n'):
            if not line or line.startswith('('):
                continue
            parts = line.split(',')
            if len(parts) >= 9:
                rider_ids = parts[2].split(',') if parts[2] else []
                trips.append({
                    "trip_id": parts[0].strip(),
                    "driver_id": parts[1].strip(),
                    "rider_ids": rider_ids,
                    "origin_station": parts[3].strip(),
                    "destination": parts[4].strip(),
                    "status": parts[5].strip(),
                    "start_time": int(parts[6].strip()) if parts[6].strip() else None,
                    "end_time": int(parts[7].strip()) if parts[7].strip() else None,
                    "seats_reserved": int(parts[8].strip()) if parts[8].strip() else 0
                })
        
        return trips
    except Exception as e:
        print(f"Error querying via kubectl: {e}", file=sys.stderr)
        return []

if __name__ == "__main__":
    trips = query_trips_via_kubectl()
    print(json.dumps({"trips": trips}, indent=2))

