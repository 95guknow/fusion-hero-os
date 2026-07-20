"""Tests für Phone Link read-only Integration."""

from __future__ import annotations

import pytest

from fusion_hero_os.integrations.phone_link.reader import (
    FORBIDDEN_ACTIONS,
    NO_INTERMEDIARY_ROUTING,
    PhoneLinkReader,
    RealWorldContactBlocked,
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


# --- Realwelt-Kontakt-Guard ----------------------------------------------


def test_guard_policy_flag_is_hardcoded_true():
    assert NO_INTERMEDIARY_ROUTING is True


def test_reader_has_no_send_capable_attribute():
    assert PhoneLinkReader.SEND_CAPABLE is False


def test_reader_exposes_no_send_or_call_methods():
    forbidden_method_names = {
        "send_message",
        "send_sms",
        "reply",
        "forward_message",
        "place_call",
        "dial",
        "call",
        "answer_call",
        "end_call",
    }
    present = forbidden_method_names & set(dir(PhoneLinkReader))
    assert not present, f"PhoneLinkReader darf keine Sende-/Anruf-Methoden besitzen: {present}"


@pytest.mark.parametrize("action", sorted(FORBIDDEN_ACTIONS))
def test_module_blocks_every_forbidden_action(action):
    mod = PhoneLinkCoreModule()
    with pytest.raises(RealWorldContactBlocked):
        mod.process({"action": action, "to": "+491700000000", "text": "hi"})


def test_module_still_allows_read_only_actions():
    mod = PhoneLinkCoreModule()
    assert mod.process({"action": "status"}) is not None
    assert "messages" in mod.process({"action": "messages", "limit": 1})


def test_unknown_non_forbidden_action_still_raises_value_error():
    mod = PhoneLinkCoreModule()
    with pytest.raises(ValueError):
        mod.process({"action": "totally_unknown_action"})