#!/usr/bin/env python3
"""
Fusion Hero OS — C-Kernel ↔ Python IPC Client (v1.1).

Transports:
  - AF_UNIX (Linux/WSL) — connects to fhos_ipc_server.c
  - TCP (Windows/cross-platform) — connects to fhos_ipc_server.py
  - in-process — direct router call (no socket, Code-Honesty: no real IPC)
"""

from __future__ import annotations

import json
import logging
import socket
import struct
import sys
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from kernel.bridge.protocol import (  # noqa: E402
    DEFAULT_TCP_HOST,
    DEFAULT_TCP_PORT,
    DEFAULT_UNIX_PATH,
    HEADER_FORMAT,
    HEADER_SIZE,
    MAGIC,
    MSG_DISPATCH,
    MSG_LIST_MODULES,
    MSG_MATH_STATUS,
    MSG_ORCHESTRATOR_STATUS,
    MSG_PING,
    VERSION,
    json_payload,
    pack_message,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("FusionHeroIPC")


class Transport(str, Enum):
    UNIX = "unix"
    TCP = "tcp"
    IN_PROCESS = "in_process"


class IPCProtocolError(Exception):
    pass


class IPCConnectionError(Exception):
    pass


class FusionHeroIPCClient:
    def __init__(
        self,
        transport: Transport = Transport.TCP,
        socket_path: str = DEFAULT_UNIX_PATH,
        host: str = DEFAULT_TCP_HOST,
        port: int = DEFAULT_TCP_PORT,
    ) -> None:
        self.transport = transport
        self.socket_path = socket_path
        self.host = host
        self.port = port
        self.sock: Optional[socket.socket] = None

    def connect(self) -> None:
        if self.transport == Transport.IN_PROCESS:
            return
        if self.transport == Transport.UNIX:
            if not hasattr(socket, "AF_UNIX"):
                raise IPCConnectionError("AF_UNIX not available on this platform")
            self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.sock.connect(self.socket_path)
            logger.info("Connected (unix) %s", self.socket_path)
            return
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))
        logger.info("Connected (tcp) %s:%d", self.host, self.port)

    def disconnect(self) -> None:
        if self.sock:
            self.sock.close()
            self.sock = None

    def _recv_exact(self, num_bytes: int) -> bytes:
        if not self.sock:
            raise IPCConnectionError("Not connected")
        buffer = bytearray()
        while len(buffer) < num_bytes:
            chunk = self.sock.recv(num_bytes - len(buffer))
            if not chunk:
                raise IPCConnectionError("Connection closed")
            buffer.extend(chunk)
        return bytes(buffer)

    def send_request(self, msg_type: int, payload: bytes = b"") -> Dict[str, Any]:
        if self.transport == Transport.IN_PROCESS:
            from fusion_hero_os.bridge.router import handle_ipc_message
            return handle_ipc_message(msg_type, payload)

        if not self.sock:
            raise IPCConnectionError("Not connected")

        self.sock.sendall(pack_message(msg_type, payload))
        raw_header = self._recv_exact(HEADER_SIZE)
        magic, version, resp_type, status_code, payload_len, _ = struct.unpack(
            HEADER_FORMAT, raw_header
        )
        if magic != MAGIC or version != VERSION:
            raise IPCProtocolError("invalid response header")

        body = b""
        if payload_len > 0:
            body = self._recv_exact(payload_len)

        result: Dict[str, Any] = {
            "msg_type": resp_type,
            "status_code": status_code,
            "payload_len": payload_len,
        }
        if body:
            try:
                result["data"] = json.loads(body.decode("utf-8"))
            except json.JSONDecodeError:
                result["payload"] = body
        return result

    def ping(self) -> Dict[str, Any]:
        return self.send_request(MSG_PING)

    def list_modules(self) -> Dict[str, Any]:
        r = self.send_request(MSG_LIST_MODULES)
        return r.get("data", r)

    def dispatch(self, module: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        body = json_payload({"module": module, "payload": payload or {}})
        r = self.send_request(MSG_DISPATCH, body)
        return r.get("data", r)

    def math_status(self) -> Dict[str, Any]:
        r = self.send_request(MSG_MATH_STATUS)
        return r.get("data", r)

    def orchestrator_status(self) -> Dict[str, Any]:
        r = self.send_request(MSG_ORCHESTRATOR_STATUS)
        return r.get("data", r)


def auto_client() -> FusionHeroIPCClient:
    """Pick best transport: TCP if port open, else in-process."""
    try:
        probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        probe.settimeout(0.3)
        probe.connect((DEFAULT_TCP_HOST, DEFAULT_TCP_PORT))
        probe.close()
        client = FusionHeroIPCClient(transport=Transport.TCP)
        client.connect()
        return client
    except OSError:
        logger.info("No TCP bridge — using in-process fallback")
        return FusionHeroIPCClient(transport=Transport.IN_PROCESS)


if __name__ == "__main__":
    client = auto_client()
    print("ping:", client.ping())
    print("modules:", client.list_modules())
    client.disconnect()