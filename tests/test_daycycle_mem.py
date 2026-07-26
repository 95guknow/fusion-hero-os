# -*- coding: utf-8 -*-
from pathlib import Path

from fusion_hero_os.core.daycycle_mem import (
    check_wake_word,
    is_agent_awake,
    load_config,
    log_instance_traffic,
    minute_tick,
    protocol_event,
    status,
    wake_agent,
)


def test_config_v121():
    c = load_config()
    assert c.get("platform_version") == "12.1.0"
    assert (c.get("agent_protocol") or {}).get("wake_word") == "testtest"
    assert (c.get("private_repo") or {}).get("name") == "fusion-hero-os-daily-plans"


def test_minute_tick_writes_mem():
    r = minute_tick(note="unit-test")
    assert r.get("ok") is True
    p = Path(r["path"])
    assert p.exists()
    text = p.read_text(encoding="utf-8")
    assert "unit-test" in text or "daycycle" in text


def test_protocol_and_wake():
    protocol_event("test", "hello")
    assert check_wake_word("please testtest now") is True
    assert is_agent_awake() is True
    w = wake_agent("unit")
    assert w.get("kind") == "wake"


def test_traffic_log():
    rec = log_instance_traffic("primary", dest="https://example.invalid", bytes_n=42, note="lab")
    assert rec["bytes"] == 42
    assert rec["instance_id"] == "primary"


def test_status():
    st = status()
    assert st.get("ok") is True
    assert st.get("platform") == "12.1.0"
