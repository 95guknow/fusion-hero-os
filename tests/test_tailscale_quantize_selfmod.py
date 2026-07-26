# -*- coding: utf-8 -*-
from fusion_hero_os.core.tailscale_quantize_selfmod import (
    ensure_assist_nodes,
    load_config,
    run_full_cycle,
    run_quantize,
    self_modulate,
    status,
)


def test_config_loads():
    c = load_config()
    assert c.get("platform_version") == "12.0.0"
    assert (c.get("self_mod") or {}).get("enabled") is True
    assert len(c.get("assist_roles") or []) >= 3


def test_ensure_assist_nodes():
    r = ensure_assist_nodes()
    assert r.get("ok") is True
    assert len(r.get("nodes") or []) >= 3
    for n in r["nodes"]:
        assert "tag" in n
        assert 0.0 < float(n["capacity"]) <= 1.0
        assert "virtual" in n


def test_self_modulate_bounds():
    m = self_modulate(heroic_boost=0.5)
    assert m.get("ok") is True
    p = m["params"]
    assert 2 <= p["bit_depth"] <= 8
    assert 200 <= p["anneal_steps"] <= 8000
    assert 1 <= p["workers"] <= 16
    assert 1 <= p["partitions"] <= 8


def test_run_quantize_metrics():
    m = self_modulate()
    r = run_quantize(params=m["params"])
    assert r.get("ok") is True
    met = r["metrics"]
    assert "quantization_mse" in met
    assert "energy_quantized" in met
    assert "integrity_gap" in met
    assert r["honest"]["remote_peer_execution"] is False


def test_full_cycle():
    s = run_full_cycle(heroic_boost=0.2)
    assert s.get("ok") is True
    assert s.get("nodes_count", 0) >= 3
    assert s.get("metrics")
    st = status()
    assert st.get("ok") is True
    assert st.get("self_mod_enabled") is True
