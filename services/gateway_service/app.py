# services/gateway_service/app.py
import os
import asyncio
import json
from typing import List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.responses import JSONResponse
import aioredis
import httpx

# Try to import generated gRPC stubs if present (optional)
HAS_GRPC = False
try:
    # adjust import names to match your generated files
    # from services.common_lib.protos_generated import driver_pb2_grpc, driver_pb2
    # from services.common_lib.protos_generated import location_pb2_grpc, location_pb2
    HAS_GRPC = True
except Exception:
    HAS_GRPC = False

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
GATEWAY_PORT = int(os.getenv("PORT", "8000"))

app = FastAPI(title="LastMile Gateway (HTTP + WebSocket)")

# Simple in-memory store (fallback) — seeded for demo
_mock_stations = [
    {"id": "st1", "name": "Station A", "lat": 12.9716, "lon": 77.5946},
    {"id": "st2", "name": "Station B", "lat": 12.9850, "lon": 77.6050},
]
_mock_routes = [
    {"id": "r1", "name": "Route 1", "coords": [[12.9716,77.5946],[12.9850,77.6050]]}
]
_mock_drivers = [
    {"id": "d1", "name": "Driver 1", "lat": 12.9721, "lon": 77.5950}
]
_mock_riders = [
    {"id": "u1", "name": "Rider 1", "lat": 12.9730, "lon": 77.5960}
]


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active_connections.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.active_connections:
            self.active_connections.remove(ws)

    async def broadcast(self, message: dict):
        data = json.dumps(message)
        coros = [ws.send_text(data) for ws in self.active_connections]
        if coros:
            await asyncio.gather(*coros, return_exceptions=True)


manager = ConnectionManager()

# Redis subscriber background task
redis = None
redis_sub_task = None


async def redis_subscriber():
    global redis
    try:
        redis = aioredis.from_url(REDIS_URL)
        pubsub = redis.pubsub()
        await pubsub.subscribe("lastmile_events")
        # aioredis v2 uses async iterator
        async for message in pubsub.listen():
            # message structure: {'type': 'message', 'channel': b'lastmile_events', 'data': b'...'}
            if message and message.get("type") == "message":
                try:
                    payload = message.get("data")
                    if isinstance(payload, (bytes, bytearray)):
                        payload = payload.decode("utf-8")
                    data = json.loads(payload)
                except Exception:
                    # broadcast raw string if not JSON
                    data = {"type": "raw", "payload": payload}
                # broadcast to all connected websockets
                await manager.broadcast(data)
    except asyncio.CancelledError:
        return
    except Exception as e:
        # log and retry with backoff
        print("redis_subscriber error:", e)
        await asyncio.sleep(2)
        await redis_subscriber()


@app.on_event("startup")
async def startup_event():
    # start redis subscriber background task
    global redis_sub_task
    redis_sub_task = asyncio.create_task(redis_subscriber())
    print("Gateway started. Redis URL:", REDIS_URL)


@app.on_event("shutdown")
async def shutdown_event():
    global redis_sub_task, redis
    if redis_sub_task:
        redis_sub_task.cancel()
        try:
            await redis_sub_task
        except Exception:
            pass
    if redis:
        await redis.close()
    print("Gateway shutdown.")


# REST endpoints ---------------------------------------------------------
@app.get("/healthz")
async def healthz():
    return JSONResponse(content={"status": "ok"})


@app.get("/stations")
async def get_stations():
    # Try gRPC first (if you have stubs & services); otherwise return mock
    if HAS_GRPC:
        # Implement actual gRPC call here (example pseudocode)
        # with grpc_channel_to_station_service() as stub:
        #     resp = stub.ListStations(station_pb2.Empty())
        #     return resp.stations
        pass
    return _mock_stations


@app.get("/routes")
async def get_routes():
    if HAS_GRPC:
        pass
    return _mock_routes


@app.get("/drivers")
async def get_drivers():
    # For demo we return in-memory drivers; if a real service exists query it
    if HAS_GRPC:
        pass
    return _mock_drivers


@app.get("/riders")
async def get_riders():
    if HAS_GRPC:
        pass
    return _mock_riders


# WebSocket endpoint -----------------------------------------------------
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        # keep connection alive; accept pings from client
        while True:
            # receive client's messages optionally (e.g., subscribe filters)
            try:
                msg = await ws.receive_text()
                # If client sends a "ping" or subscribe request, you can handle it here
                # Example: {"action":"subscribe","channel":"driver:d1"} etc.
                # For now we ignore client messages.
                # Optionally respond
                await ws.send_text(json.dumps({"type": "ack", "msg": "ok"}))
            except Exception:
                # if client is silent, just continue to allow publisher to push updates
                await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        manager.disconnect(ws)


# Optional: helper to publish sample events to Redis for testing
@app.post("/debug/publish")
async def debug_publish(event: dict):
    """Publish arbitrary event to redis channel for testing the WS clients."""
    r = aioredis.from_url(REDIS_URL)
    payload = json.dumps(event)
    await r.publish("lastmile_events", payload)
    return {"published": True, "payload": event}


# If you want to query other HTTP services instead of gRPC, you can add httpx calls here:
# async def query_service_http(url):
#     async with httpx.AsyncClient() as client:
#         r = await client.get(url, timeout=5.0)
#         return r.json()

# Example of how your services might publish to Redis:
# driver_service: redis.publish('lastmile_events', json.dumps({"type":"position","id":"d1","lat":..,"lon":..}))
# notification_service: redis.publish('lastmile_events', json.dumps({"type":"notification","text":"..."}))

# End of file
