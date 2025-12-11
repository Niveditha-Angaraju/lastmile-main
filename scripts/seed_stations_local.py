"""
Seed stations into the database for local development.
Works with port-forwarded PostgreSQL.
"""
import os
import sys
from sqlalchemy import create_engine, text

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Use localhost when port forwarding, or postgres when in cluster
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://lastmile:lastmile@localhost:5432/lastmile")

def seed_stations():
    """Seed stations into the database."""
    print("🌱 Seeding stations into database...")
    print(f"   Database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else DATABASE_URL}")
    
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    
    try:
        with engine.connect() as conn:
            # First, ensure PostGIS extension exists
            try:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
                conn.commit()
                print("✅ PostGIS extension ensured")
            except Exception as e:
                print(f"⚠️  PostGIS extension check: {e}")
                # Continue anyway - might already exist
            
            # Create stations table if it doesn't exist
            try:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS stations (
                        id SERIAL PRIMARY KEY,
                        station_id VARCHAR(64) UNIQUE NOT NULL,
                        name VARCHAR(256) NOT NULL,
                        lat FLOAT NOT NULL,
                        lng FLOAT NOT NULL,
                        geom geometry(POINT, 4326)
                    );
                """))
                conn.commit()
                print("✅ Stations table ensured")
            except Exception as e:
                print(f"⚠️  Table creation: {e}")
                # Continue anyway - might already exist
            
            # Define stations (Bangalore locations)
            stations = [
                ("ST101", "MG Road", 12.975, 77.605),
                ("ST102", "Cubbon Park", 12.9759, 77.601),
                ("ST103", "Trinity Circle", 12.9718, 77.6380),
                ("ST104", "Indiranagar", 12.9786, 77.6408),
                ("ST105", "Koramangala", 12.9352, 77.6245),
                ("ST106", "Whitefield", 12.9698, 77.7499),
                ("ST107", "Marathahalli", 12.9592, 77.6974),
                ("ST108", "Electronic City", 12.8456, 77.6633),
            ]
            
            seeded_count = 0
            for sid, name, lat, lng in stations:
                try:
                    # Use ON CONFLICT to handle duplicates
                    conn.execute(text("""
                        INSERT INTO stations (station_id, name, lat, lng, geom) 
                        VALUES (:sid, :name, :lat, :lng, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326))
                        ON CONFLICT (station_id) DO UPDATE 
                        SET name = EXCLUDED.name, lat = EXCLUDED.lat, lng = EXCLUDED.lng, 
                            geom = EXCLUDED.geom
                    """), {"sid": sid, "name": name, "lat": lat, "lng": lng})
                    seeded_count += 1
                    print(f"   ✅ Seeded: {sid} - {name} ({lat}, {lng})")
                except Exception as e:
                    print(f"   ⚠️  Error seeding {sid}: {e}")
            
            conn.commit()
            print(f"\n✅ Successfully seeded {seeded_count} stations!")
            return True
            
    except Exception as e:
        print(f"\n❌ Error connecting to database: {e}")
        print(f"   Make sure PostgreSQL is running and port-forwarded to localhost:5432")
        print(f"   Run: kubectl -n lastmile port-forward svc/postgres 5432:5432")
        return False

if __name__ == '__main__':
    success = seed_stations()
    sys.exit(0 if success else 1)

