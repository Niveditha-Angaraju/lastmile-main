#!/usr/bin/env python3
"""
Gateway HTTP demo for LastMile:
- Listens on PORT (default 8000)
- Exposes /health, /status, /request-ride, /move-driver
- Tries to call gRPC backends (driver-service, rider-service), but falls back to mock responses.
This is intentionally small and dependency-light so it runs easily inside the repo.
"""
import os
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
import logging
LOG = logging.getLogger("gateway_service")
logging.basicConfig(level=logging.INFO)

PORT = int(os.getenv("PORT", "8000"))

# Try to import grpc and generated protos if present
GRPC_OK = False
try:
    import grpc
    from services.common_lib.protos_generated import driver_pb2, driver_pb2_grpc  # may raise if not present
    from services.common_lib.protos_generated import rider_pb2, rider_pb2_grpc
    GRPC_OK = True
except Exception:
    LOG.info("gRPC stubs not fully available or grpc not installed; gateway will return mock responses.")

def mock_request_ride(payload):
    return {"ride_id": "mock-ride-123", "status": "assigned", "driver_id": "driver-mock-1"}

def mock_move_driver(payload):
    return {"ok": True, "driver_id": payload.get("driver_id", "d-mock")}

class Handler(BaseHTTPRequestHandler):
    def _json(self, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self._json(200)
            self.wfile.write(json.dumps({"status": "ok"}).encode())
            return
        if parsed.path == "/status":
            self._json(200)
            self.wfile.write(json.dumps({"status": "running", "grpc_available": GRPC_OK}).encode())
            return
        self._json(404)
        self.wfile.write(json.dumps({"error": "not found"}).encode())

    def do_POST(self):
        parsed = urlparse(self.path)
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw.decode() or "{}")
        except Exception:
            payload = {}

        if parsed.path == "/request-ride":
            # Try to forward to rider service via gRPC if available
            if GRPC_OK:
                try:
                    channel = grpc.insecure_channel("rider-service:50052")
                    stub = rider_pb2_grpc.RiderStub(channel)
                    if hasattr(rider_pb2, "RideRequest"):
                        req = rider_pb2.RideRequest(user_id=payload.get("user_id", "u1"))
                        resp = stub.RequestRide(req, timeout=5)
                        # best-effort conversion
                        reply = {}
                        try:
                            for fld, val in resp.ListFields():
                                reply[fld.name] = getattr(resp, fld.name)
                        except Exception:
                            reply = {"reply": str(resp)}
                        self._json(200)
                        self.wfile.write(json.dumps(reply).encode())
                        return
                except Exception as e:
                    LOG.exception("gRPC call to rider-service failed; falling back to mock: %s", e)

            resp = mock_request_ride(payload)
            self._json(200)
            self.wfile.write(json.dumps(resp).encode())
            return

        if parsed.path == "/move-driver":
            if GRPC_OK:
                try:
                    channel = grpc.insecure_channel("driver-service:50052")
                    stub = driver_pb2_grpc.DriverStub(channel)
                    if hasattr(driver_pb2, "MoveRequest"):
                        req = driver_pb2.MoveRequest(driver_id=payload.get("driver_id","d1"),
                                                     lat=payload.get("lat",0.0),
                                                     lon=payload.get("lon",0.0))
                        resp = stub.MoveDriver(req, timeout=5)
                        reply = {}
                        try:
                            for fld, val in resp.ListFields():
                                reply[fld.name] = getattr(resp, fld.name)
                        except Exception:
                            reply = {"reply": str(resp)}
                        self._json(200)
                        self.wfile.write(json.dumps(reply).encode())
                        return
                except Exception as e:
                    LOG.exception("gRPC call to driver-service failed; falling back to mock: %s", e)

            resp = mock_move_driver(payload)
            self._json(200)
            self.wfile.write(json.dumps(resp).encode())
            return

        self._json(404)
        self.wfile.write(json.dumps({"error": "not found"}).encode())

def run():
    httpd = HTTPServer(("0.0.0.0", PORT), Handler)
    LOG.info("Gateway listening on 0.0.0.0:%s (grpc_ok=%s)", PORT, GRPC_OK)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()

if __name__ == "__main__":
    run()
