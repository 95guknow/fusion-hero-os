"""Tests für Access-Point-Discovery und Connectivity-API."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

DASH = Path(__file__).resolve().parents[1] / "03_Code" / "Dashboard"
if str(DASH) not in sys.path:
    sys.path.insert(0, str(DASH))


def test_list_lan_ips_prefers_192_168():
    from connectivity import _score_ip, list_lan_ips

    assert _score_ip("192.168.1.10") < _score_ip("172.23.16.1")
    ips = list_lan_ips()
    assert isinstance(ips, list)


def test_build_discovery_has_endpoints():
    from connectivity import build_discovery

    d = build_discovery()
    assert d["ok"] is True
    assert "lan_ip" in d
    assert "watch_url" in d
    assert "endpoints" in d
    assert "health" in d["endpoints"]


def test_local_network_base_uses_port_env(monkeypatch):
    from connectivity import local_network_base

    monkeypatch.setenv("FUSION_DASHBOARD_PORT", "9001")
    monkeypatch.delenv("FUSION_LAN_BASE_OVERRIDE", raising=False)
    base = local_network_base()
    assert base.endswith(":9001")


@pytest.mark.parametrize(
    "path",
    [
        "/api/discovery",
        "/api/connectivity",
        "/api/jobs?limit=5",
        "/api/faden/status",
        "/api/faden/threads",
    ],
)
def test_connectivity_routes_exist(path):
    from fastapi.testclient import TestClient

    from app import app

    client = TestClient(app)
    r = client.get(path)
    assert r.status_code == 200, path