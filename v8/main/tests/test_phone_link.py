"""Tests für Phone Link read-only Integration."""

from __future__ import annotations

from fusion_hero_os.integrations.phone_link.reader import (
    PhoneLinkReader,
    _discover_database,
    _filetime_to_iso,
    _mask_address,
    phone_link_status,
)
from fusion_hero_os.modules.phone_link import PhoneLinkCoreModule


def test_mask_address():
    assert _mask_address("+4917012345678").endswith("5678")
    assert _mask_address("2202") == "2202"
    assert _mask_address("Telekom") == "Telekom"


def test_filetime_to_iso():
    iso = _filetime_to_iso(134277278027900000)
    assert iso is not None
    assert "T" in iso


def test_discover_database_on_windows():
    path = _discover_database("phone.db")
    # Auf CI ohne Phone Link kann None zurückkommen
    if path is not None:
        assert path.name == "phone.db"
        assert path.exists()


def test_phone_link_status_shape():
    st = phone_link_status()
    assert "connected" in st
    assert "recent_messages" in st
    assert "limitations" in st
    assert isinstance(st["limitations"], list)


def test_phone_link_module_actions():
    mod = PhoneLinkCoreModule()
    status = mod.process({"action": "status"})
    assert status is not None
    assert "message_count" in status
    msgs = mod.process({"action": "messages", "limit": 3})
    assert "messages" in msgs
    convs = mod.process({"action": "conversations", "limit": 3})
    assert "conversations" in convs


def test_reader_counts_when_db_present():
    reader = PhoneLinkReader()
    if reader.database_path and reader.database_path.exists():
        counts = reader.counts()
        assert counts["messages"] >= 0
        assert counts["conversations"] >= 0