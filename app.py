#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import signal
import socket
import threading
import time
from concurrent import futures
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import grpc
from grpc_health.v1 import health, health_pb2, health_pb2_grpc
from grpc_reflection.v1alpha import reflection

from rpcdemo.v1 import rpcdemo_pb2, rpcdemo_pb2_grpc


GRPC_PORT = int(os.environ.get("GRPC_PORT", "50051"))
HTTP_PORT = int(os.environ.get("HTTP_PORT", "8080"))
ORDER_SERVICE_ADDR = os.environ.get("ORDER_SERVICE_ADDR", "order-service:50051")
HOSTNAME = socket.gethostname()
CONTRACTS_VERSION = os.environ.get("RPC_CONTRACTS_VERSION", "0.1.0")


class UserService(rpcdemo_pb2_grpc.UserServiceServicer):
    def GetUser(self, request, context):
        user_id = request.user_id or "10001"
        return rpcdemo_pb2.GetUserResponse(
            user_id=user_id,
            nickname=f"演示用户-{user_id}",
            source_service=f"user-service/{HOSTNAME}",
        )


def call_order_service() -> dict:
    started = time.perf_counter()
    with grpc.insecure_channel(ORDER_SERVICE_ADDR) as channel:
        stub = rpcdemo_pb2_grpc.OrderServiceStub(channel)
        response = stub.ListOrders(
            rpcdemo_pb2.ListOrdersRequest(user_id="10001"), timeout=3
        )
    return {
        "flow": "rpc-user-service repository → order-service:50051",
        "target": ORDER_SERVICE_ADDR,
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
        "response": {
            "user_id": response.user_id,
            "orders": [
                {
                    "order_id": item.order_id,
                    "product_name": item.product_name,
                    "amount_cents": item.amount_cents,
                }
                for item in response.orders
            ],
            "source_service": response.source_service,
        },
    }


class Handler(BaseHTTPRequestHandler):
    def send_json(self, status: int, body: dict):
        data = json.dumps(body, ensure_ascii=False, indent=2).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/healthz":
            self.send_json(
                200,
                {
                    "status": "SERVING",
                    "service": "user-service",
                    "rpc_contracts": CONTRACTS_VERSION,
                },
            )
        elif self.path in ("/", "/demo"):
            try:
                self.send_json(200, {"success": True, **call_order_service()})
            except grpc.RpcError as exc:
                self.send_json(503, {"success": False, "grpc_code": exc.code().name, "details": exc.details()})
        else:
            self.send_json(404, {"error": "not found"})

    def log_message(self, fmt, *args):
        print(f"http {fmt % args}", flush=True)


def run_grpc(stop_event: threading.Event):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    rpcdemo_pb2_grpc.add_UserServiceServicer_to_server(UserService(), server)
    health_service = health.HealthServicer()
    health_pb2_grpc.add_HealthServicer_to_server(health_service, server)
    service_name = rpcdemo_pb2.DESCRIPTOR.services_by_name["UserService"].full_name
    health_service.set("", health_pb2.HealthCheckResponse.SERVING)
    health_service.set(service_name, health_pb2.HealthCheckResponse.SERVING)
    reflection.enable_server_reflection([service_name, health.SERVICE_NAME, reflection.SERVICE_NAME], server)
    server.add_insecure_port(f"[::]:{GRPC_PORT}")
    server.start()
    print(f"user-service gRPC listening on {GRPC_PORT}", flush=True)
    stop_event.wait()
    health_service.enter_graceful_shutdown()
    server.stop(grace=5).wait()


def main():
    stop_event = threading.Event()
    signal.signal(signal.SIGTERM, lambda *_: stop_event.set())
    signal.signal(signal.SIGINT, lambda *_: stop_event.set())
    threading.Thread(target=run_grpc, args=(stop_event,), daemon=True).start()
    httpd = ThreadingHTTPServer(("0.0.0.0", HTTP_PORT), Handler)
    httpd.timeout = 0.5
    print(f"user-service demo HTTP listening on {HTTP_PORT}", flush=True)
    while not stop_event.is_set():
        httpd.handle_request()
    httpd.server_close()


if __name__ == "__main__":
    main()
