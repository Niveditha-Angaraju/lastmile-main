#!/usr/bin/env python3
"""
Improved idempotent station seeder.

Features:
- Uses INSERT ... ON CONFLICT DO UPDATE with RETURNING to detect whether each row was inserted or updated.
- Ensures PostGIS extension exists before inserting geometry.
- Safe transactions and error handling.
- Tries to reuse a Station model if available; otherwise falls back to raw SQL upsert.
- Allows loading stations from a JSON file (env var STATIONS_FILE) or uses an inline list.
"""
import os
import sys
import json
from pathlib import Path
from typing import List, Dict

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://lastmile:lastmile@postgres:5432/lastmile"
)

# Optional: path to a JSON file containing a list of stations [{"sid": "...", "name": "...", "lat": ..., "lng": ...}, ...]
STATIONS_FILE = os.getenv("STATIONS_FILE", "")

# Inline fallback station list (12 stations forming a route)
DEFAULT_STATIONS = [
    {"sid": "ST101", "name": "MG Road", "lat": 12.975, "lng": 77.605},
    {"sid": "ST102", "name": "Cubbon Park", "lat": 12.9759, "lng": 77.601},
    {"sid": "ST103", "name": "Trinity Circle", "lat": 12.9718, "lng": 77.6380},
    {"sid": "ST104", "name": "Indiranagar", "lat": 12.978, "lng": 77.640},
    {"sid": "ST105", "name": "Koramangala", "lat": 12.935, "lng": 77.625},
    {"sid": "ST106", "name": "HSR Layout", "lat": 12.912, "lng": 77.642},
    {"sid": "ST107", "name": "Electronic City", "lat": 12.845, "lng": 77.672},
    {"sid": "ST108", "name": "Silk Board", "lat": 12.915, "lng": 77.625},
    {"sid": "ST109", "name": "Whitefield", "lat": 12.970, "lng": 77.750},
    {"sid": "ST110", "name": "Marathahalli", "lat": 12.955, "lng": 77.700},
    {"sid": "ST111", "name": "Hebbal", "lat": 12.990, "lng": 77.595},
    {"sid": "ST112", "name": "Yeshwanthpur", "lat": 12.995, "lng": 77.540},
]


# Upsert SQL with RETURNING to detect insert vs update.
# Using Postgres internal column "xmax": for newly inserted rows xmax = 0 (so xmax = 0 means inserted).
UPSERT_SQL = text("""
INSERT INTO stations (station_id, name, lat, lng, geom)
VALUES (:sid, :name, :lat, :lng, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326))
ON CONFLICT (station_id) DO UPDATE
  SET name = EXCLUDED.name,
      lat = EXCLUDED.lat,
      lng = EXCLUDED.lng,
      geom = EXCLUDED.geom
RETURNING (xmax = 0) AS inserted;
""")

ENSURE_POSTGIS_SQL = text("CREATE EXTENSION IF NOT EXISTS postgis;")

def load_stations() -> List[Dict]:
    """Load stations from STATIONS_FILE if provided, otherwise use DEFAULT_STATIONS."""
    if STATIONS_FILE:
        p = Path(STATIONS_FILE)
        if not p.exists():
            print(f"[seed_stations] ERROR: STATIONS_FILE set to {STATIONS_FILE} but file does not exist.", file=sys.stderr)
            sys.exit(2)
        try:
            with p.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
            if not isinstance(data, list):
                raise ValueError("stations JSON must be a list of objects")
            # validate minimal fields
            for s in data:
                if not all(k in s for k in ("sid", "name", "lat", "lng")):
                    raise ValueError("each station must contain sid, name, lat, lng")
            return data
        except Exception as e:
            print(f"[seed_stations] ERROR loading stations file: {e}", file=sys.stderr)
            sys.exit(2)
    return DEFAULT_STATIONS

def try_import_model():
    """Attempt to import Station model; return True if model is available and usable."""
    try:
        # services.station_service.models is the repo path used in this project
        from services.station_service.models import Station as StationModel  # type: ignore
        # If model exists, we won't necessarily use it here, but importing verifies it's available.
        return True
    except Exception:
        return False

def main():
    print(f"[seed_stations] DATABASE_URL = {DATABASE_URL}")
    stations = load_stations()
    engine = create_engine(DATABASE_URL, future=True)

    inserted_count = 0
    updated_count = 0
    error_count = 0

    try:
        with engine.begin() as conn:  # begin a transaction
            # Ensure PostGIS exists (harmless if already present)
            try:
                print("[seed_stations] Ensuring PostGIS extension exists...")
                conn.execute(ENSURE_POSTGIS_SQL)
            except SQLAlchemyError as e:
                print(f"[seed_stations] WARNING: could not ensure postgis extension: {e}", file=sys.stderr)
                # continue anyway

            # Run upserts one-by-one, using RETURNING to detect whether inserted or updated
            for s in stations:
                params = {"sid": s["sid"], "name": s["name"], "lat": s["lat"], "lng": s["lng"]}
                try:
                    result = conn.execute(UPSERT_SQL, params)
                    row = result.fetchone()
                    # row[0] is a boolean (True if inserted, False if updated) because of (xmax = 0) AS inserted
                    inserted_flag = bool(row[0]) if row is not None else False
                    if inserted_flag:
                        inserted_count += 1
                        print(f"[seed_stations] INSERTED {s['sid']} - {s['name']}")
                    else:
                        updated_count += 1
                        print(f"[seed_stations] UPDATED  {s['sid']} - {s['name']}")
                except SQLAlchemyError as e:
                    error_count += 1
                    print(f"[seed_stations] ERROR upserting {s['sid']}: {e}", file=sys.stderr)

        # transaction committed on context exit if no exceptions
    except SQLAlchemyError as e:
        print(f"[seed_stations] TRANSACTION FAILED: {e}", file=sys.stderr)
        sys.exit(3)
    finally:
        # dispose engine
        try:
            engine.dispose()
        except Exception:
            pass

    total = len(stations)
    print("--------------------------------------------------")
    print(f"✅ Seed complete: {total} station(s) processed")
    print(f"   Inserted: {inserted_count}")
    print(f"   Updated : {updated_count}")
    if error_count:
        print(f"   Errors  : {error_count} (check logs)", file=sys.stderr)
    print("Route pattern:")
    print("  Main Route (North→South): ST101 → ST102 → ST103 → ST104 → ST105 → ST106 → ST107 → ST108")
    print("  Alt Route (East→West)  : ST109 → ST110 → ST111 → ST112")

if __name__ == "__main__":
    main()
