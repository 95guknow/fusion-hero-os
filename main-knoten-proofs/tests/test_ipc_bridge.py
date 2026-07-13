"""Tests for C↔Python IPC Bridge (in-process + TCP)."""

from __future__ import annotations

import json
import socket
import threading
import time

import pytest

from fusion_hero_os.bridge.gateway import IPCGateway
from fusion_hero_os.bridge.router import handle_ipc_message, route_dispatch
from kernel.bridge.protocol import (
    DEFAULT_TCP_HOST,
    DEFAULT_TCP_PORT,
    MSG_DISPATCH,
    MSG_LIST_MODULES,
    MSG_PING,
    json_payload,
    pack_message,
)


def test_in_process_ping():
    result = handle_ipc_message(MSG_PING, b"")
    assert result["ok"] is True
    assert result["pong"] is True


def test_in_process_list_modules():
    result = handle_ipc_message(MSG_LIST_MODULES, b"")
    assert result["ok"] is True
    assert "TimespaceTokenCoreModule" in result["modules"]


def test_in_process_dispatch_timespace():
    result = route_dispatch("TimespaceTokenCoreModule", {
        "tracks": [{
            "name": "t1",
            "coordinate": {"time_index": 0, "space_depth": 0},
            "state": {
                "stability": 0.8, "latent_tension": 0.2, "depth": 1,
                "fluctuation_severity": 0.1, "bottleneck_risk": 0.1,
            },
        }],
    })
    assert result["ok"] is True
    assert "allocations" in result["result"]


def test_gateway_in_process_status():
    gw = IPCGateway()
    st = gw.status()
    assert st["ok"] is True
    assert st["transport"] in ("in_process", "tcp", "unix")
    assert "TimespaceTokenCoreModule" in st.get("modules", st.get("deepened_modules", []))


def _run_tcp_server(port: int, stop: threading.Event):
    from kernel.bridge.fhos_ipc_server import serve_tcp
    # Patch: run one-shot server in thread — use low-level handler instead
    import sys
    from pathlib import Path
    repo = Path(__file__).resolve().parents[1]
    if str(repo) not in sys.path:
        sys.path.insert(0, str(repo))

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((DEFAULT_TCP_HOST, port))
    srv.listen(1)
    srv.settimeout(2.0)
    try:
        while not stop.is_set():
            try:
                conn, _ = srv.accept()
            except socket.timeout:
                continue
            from kernel.bridge.fhos_ipc_server import handle_client
            handle_client(conn, ("test", port))
    finally:
        srv.close()


def test_tcp_roundtrip():
    port = DEFAULT_TCP_PORT + 99
    stop = threading.Event()
    thread = threading.Thread(target=_run_tcp_server, args=(port, stop), daemon=True)
    thread.start()
    time.sleep(0.3)

    from kernel.bridge.fhos_ipc_client import FusionHeroIPCClient, Transport

    client = FusionHeroIPCClient(transport=Transport.TCP, port=port)
    client.connect()
    try:
        ping = client.ping()
        data = ping.get("data", ping)
        assert data.get("pong") or data.get("ok")

        body = json_payload({"module": "HeroicImageOrchestrator", "payload": {"prompt": "test"}})
        raw = client.send_request(MSG_DISPATCH, body)
        result = raw.get("data", raw)
        assert result.get("ok") is True or "result" in result
    finally:
        client.disconnect()
        stop.set()