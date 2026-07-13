"""Tests für Supabase Cloud-Sync (Watch, Settings, Audit, Background)."""

from __future__ import annotations

import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_DASHBOARD = Path(__file__).resolve().parents[1] / "03_Code" / "Dashboard"
if str(_DASHBOARD) not in sys.path:
    sys.path.insert(0, str(_DASHBOARD))

from watch_party import WatchPartyManager, WatchRoom


def test_watch_room_persist_called():
    mgr = WatchPartyManager()
    room = mgr.create_room("https://youtu.be/dQw4w9WgXcQ")
    with patch("supabase_store.save_watch_room") as mock_save:
        with patch("supabase_store.cloud_sync_enabled", return_value=True):
            mgr.apply_command(room.room_id, "play", position=5.0)
            assert mock_save.called


def test_watch_hydrate_from_rows():
    mgr = WatchPartyManager()
    rows = [
        {
            "room_id": "abc12345",
            "video_id": "dQw4w9WgXcQ",
            "position": 12.5,
            "playing": False,
            "title": "",
            "updated_at": time.time(),
            "created_at": time.time() - 100,
        }
    ]
    with patch("supabase_store.load_watch_rooms", return_value=rows):
        with patch("supabase_store.cloud_sync_enabled", return_value=True):
            loaded = mgr.hydrate_from_cloud()
    assert loaded == 1
    room = mgr.get_room("abc12345")
    assert room is not None
    assert room.video_id == "dQw4w9WgXcQ"


def test_save_agent_audit_skips_when_disabled():
    import supabase_store as store

    with patch.object(store, "cloud_sync_enabled", return_value=False):
        result = store.save_agent_audit("test", query="hello")
    assert result.get("skipped") is True


def test_sync_status_keys():
    import supabase_store as store

    status = store.sync_status()
    assert "cloud_sync" in status
    assert "device_id" in status
    assert "metrics_interval_sec" in status


def test_settings_cloud_on_apply(isolated_settings):
    """apply_settings spiegelt in Cloud wenn cloud_sync_enabled."""
    import fusion_settings as fs

    mock_client = MagicMock()
    mock_client.table.return_value.upsert.return_value.execute.return_value = MagicMock(data=[{}])

    with patch("supabase_store.cloud_sync_enabled", return_value=True):
        with patch("supabase_store.get_client", return_value=mock_client):
            fs.apply_settings({"FUSION_PROFILE": "eco"}, set_by="test")
    assert mock_client.table.called


@pytest.fixture
def isolated_settings(tmp_path, monkeypatch):
    path = tmp_path / "fusion_settings.json"
    monkeypatch.setattr("fusion_settings.SETTINGS_FILE", path)
    monkeypatch.setattr("fusion_settings.STATE_DIR", tmp_path)
    yield path