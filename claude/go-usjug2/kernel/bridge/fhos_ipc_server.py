#!/usr/bin/env python3
"""
FHOS IPC Server (Python) — TCP transport for Windows + cross-platform.

Implements the same 16-byte header protocol as fhos_ipc_server.c.
Routes requests through fusion_hero_os.bridge.router.
"""

from __future__ import annotations

import argparse
import logging
import socket
import struct
import sys
import threading
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from kernel.bridge.protocol import (  # noqa: E402
    DEFAULT_TCP_HOST,
    DEFAULT_TCP_PORT,
    HEADER_SIZE,
    MSG_DISPATCH_RESPONSE,
    MSG_ERROR,
    MSG_PONG,
    json_payload,
    pack_message,
    unpack_header,
)
from fusion_hero_os.bridge.router import handle_ipc_message  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("fhos.ipc.server")


def _response_type(request_type: int) -> int:
    if request_type == 0x01:
        return MSG_PONG
    if request_type == 0x10:
        return MSG_DISPATCH_RESPONSE
    if request_type in (0x20, 0x21, 0x22):
        return request_type + 1
    return MSG_ERROR


def handle_client(conn: socket.socket, addr) -> None:
    try:
        while True:
            header_data = _recv_exact(conn, HEADER_SIZE)
            _, _, msg_type, _, payload_len, _ = unpack_header(header_data)
            payload = _recv_exact(conn, payload_len) if payload_len else b""
            logger.info("Request type=0x%02X len=%d from %s", msg_type, payload_len, addr)

            result = handle_ipc_message(msg_type, payload)
            status = 0 if result.get("ok", True) else 1
            resp_type = _response_type(msg_type)
            resp_body = json_payload(result)
            conn.sendall(pack_message(resp_type, resp_body, status_code=status))
    except (ConnectionError, OSError):
        pass
    except Exception as exc:
        logger.exception("client handler error: %s", exc)
        try:
            conn.sendall(
                pack_message(MSG_ERROR, json_payload({"ok": False, "error": str(exc)}), status_code=1)
            )
        except Exception:
            pass
    finally:
        conn.close()


def _recv_exact(sock: socket.socket, n: int) -> bytes:
    buf = bytearray()
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("connection closed")
        buf.extend(chunk)
    return bytes(buf)


def serve_tcp(host: str = DEFAULT_TCP_HOST, port: int = DEFAULT_TCP_PORT) -> None:
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((host, port))
    srv.listen(20)
    logger.info("FHOS Python IPC server on tcp://%s:%d", host, port)
    try:
        while True:
            conn, addr = srv.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
    except KeyboardInterrupt:
        logger.info("shutting down")
    finally:
        srv.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FHOS Python IPC Bridge Server")
    parser.add_argument("--host", default=DEFAULT_TCP_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_TCP_PORT)
    args = parser.parse_args()
    serve_tcp(args.host, args.port)