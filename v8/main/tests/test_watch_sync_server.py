"""Tests für server-authoritative Watch Together (Supabase Sync)."""

from __future__ import annotations

import sys
import time
from pathlib import Path
from unittest.mock import patch

_DASHBOARD = Path(__file__).resolve().parents[1] / "03_Code" / "Dashboard"
if str(_DASHBOARD) not in sys.path:
    sys.path.insert(0, str(_DASHBOARD))

from watch_party import WatchPartyManager, WatchRoom
from watch_sync_server import (
    get_authoritative_state,
    get_realtime_client_config,
    merge_row_into_room,
    row_to_watch_state,
    server_sync_enabled,
)


def test_merge_row_newer_server_wins():
    room = WatchRoom(room_id="abc", video_id="old", position=1.0, playing=False, updated_at=10.0)
    row = {
        "room_id": "abc",
        "video_id": "newvid12345",
        "position": 42.0,
        "playing": True,
        "updated_at": 20.0,
    }
    assert merge_row_into_room(room, row) is True
    assert room.video_id == "newvid12345"
    assert room.position == 42.0
    assert room.playing is True


def test_merge_row_ignores_stale():
    room = WatchRoom(room_id="abc", video_id="keep", position=5.0, updated_at=30.0)
    row = {"video_id": "stale", "position": 0.0, "updated_at": 10.0}
    assert merge_row_into_room(room, row) is False
    assert room.video_id == "keep"


def test_authoritative_state_local_mode():
    mgr = WatchPartyManager()
    room = mgr.create_room("https://youtu.be/dQw4w9WgXcQ")
    with patch("watch_sync_server.server_sync_enabled", return_value=False):
        out = get_authoritative_state(room.room_id, mgr)
    assert out["ok"] is True
    assert out["sync_source"] == "memory"
    assert out["state"]["video_id"] == "dQw4w9WgXcQ"


def test_state_includes_updated_at():
    mgr = WatchPartyManager()
    room = mgr.create_room()
    mgr.apply_command(room.room_id, "play", position=3.0)
    st = mgr.get_room(room.room_id).to_state()
    assert "updated_at" in st
    assert st["sync_authority"] == "server"


def test_watch_room_state_api():
    from fastapi.testclient import TestClient

    from app import app

    mgr_mod = sys.modules.get("watch_party")
    if mgr_mod:
        mgr_mod._manager = None
    client = TestClient(app)
    created = client.post("/api/watch/room", json={}).json()
    rid = created["room_id"]
    r = client.get(f"/api/watch/room/{rid}/state")
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert "state" in data


def test_row_to_watch_state_playing():
    row = {
        "room_id": "abc",
        "video_id": "vid12345678",
        "position": 10.0,
        "playing": True,
        "updated_at": time.time() - 2,
    }
    st = row_to_watch_state(row)
    assert st["playing"] is True
    assert st["position"] >= 11.5
    assert st["sync_source"] == "realtime"


def test_realtime_config_api():
    from fastapi.testclient import TestClient

    from app import app

    client = TestClient(app)
    r = client.get("/api/watch/realtime/config")
    assert r.status_code == 200
    data = r.json()
    assert "enabled" in data
    assert "url" in data


def test_watch_room_cmd_api():
    from fastapi.testclient import TestClient

    from app import app

    client = TestClient(app)
    created = client.post("/api/watch/room", json={}).json()
    rid = created["room_id"]
    r = client.post(
        f"/api/watch/room/{rid}/cmd",
        json={"cmd": "load", "video_id": "https://youtu.be/jNQXAC9IVRw"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["state"]["video_id"] == "jNQXAC9IVRw"