"""Tests für Watch Together."""

from __future__ import annotations

import sys
import time
from pathlib import Path

_DASHBOARD = Path(__file__).resolve().parents[1] / "03_Code" / "Dashboard"
if str(_DASHBOARD) not in sys.path:
    sys.path.insert(0, str(_DASHBOARD))

from watch_party import WatchPartyManager, join_url_for_room, render_watch_page


def test_extract_video_id():
    mgr = WatchPartyManager()
    assert mgr.extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert mgr.extract_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert mgr.extract_video_id("dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert mgr.extract_video_id("") is None


def test_room_play_pause_position():
    mgr = WatchPartyManager()
    room = mgr.create_room("https://youtu.be/dQw4w9WgXcQ")
    rid = room.room_id
    mgr.apply_command(rid, "play", position=10.0)
    room = mgr.get_room(rid)
    assert room.playing is True
    assert room.position == 10.0
    time.sleep(0.05)
    mgr.apply_command(rid, "pause")
    room = mgr.get_room(rid)
    assert room.playing is False
    assert room.position >= 10.0


def test_load_video():
    mgr = WatchPartyManager()
    room = mgr.create_room()
    mgr.apply_command(room.room_id, "load", video_id="https://youtu.be/jNQXAC9IVRw")
    updated = mgr.get_room(room.room_id)
    assert updated.video_id == "jNQXAC9IVRw"
    assert updated.playing is False


def test_render_watch_page():
    html = render_watch_page("abc12345", "dQw4w9WgXcQ", lan_base="http://192.168.1.50:8000")
    assert "abc12345" in html
    assert "dQw4w9WgXcQ" in html
    assert "192.168.1.50" in html


def test_join_url_for_room():
    url = join_url_for_room("deadbeef", "http://192.168.0.10:8000")
    assert url == "http://192.168.0.10:8000/watch/deadbeef"


def test_room_info_has_qr_fields():
    mgr = WatchPartyManager()
    room = mgr.create_room()
    info = mgr.room_info(room.room_id, base_url="http://10.0.0.5:8000")
    assert info["ok"] is True
    assert "qr_url" in info
    assert info["join_url"].endswith(f"/watch/{room.room_id}")