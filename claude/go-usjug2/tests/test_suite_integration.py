"""Integration tests for suite → core merge."""
from __future__ import annotations

import sys
from pathlib import Path

_CORE = Path(__file__).resolve().parents[1] / "03_Code" / "core"
if str(_CORE) not in sys.path:
    sys.path.insert(0, str(_CORE))


def test_qb_qubo_shim_exports_springloop():
    from qb_qubo import springloop_energy, make_Q
    import numpy as np

    Q = make_Q(4)
    x = np.random.randint(0, 2, 4).astype(float)
    _, e = springloop_energy(Q, x, steps=3)
    assert isinstance(e, (float, np.floating))


def test_ghosthunt_hook_returns_coevo():
    from ghosthunt_hook import ghosthunt_hook

    snap, coevo = ghosthunt_hook("test-layer", context={"events": 5}, steps=3, verbose=False)
    assert "distance" in snap
    assert "emerged" in coevo
    assert "springloop_energy" in coevo


def test_suite_bridge_inventory():
    from suite_bridge import suite_inventory

    inv = suite_inventory()
    assert inv["total_py"] > 0
    names = {m["name"] for m in inv["modules"]}
    assert "layers" in names
    assert "qubo" in names


def test_suite_pipeline_status():
    from suite_pipeline import pipeline_status

    st = pipeline_status()
    assert st["layer_count"] == 8
    assert "00_middle" in st["layers"][0] or any("middle" in l for l in st["layers"])


def test_heroic_orchestration_apply_ghosthunt():
    sys.path.insert(0, str(_CORE))
    from heroic_orchestration import apply_ghosthunt_coevo

    snap, coevo = apply_ghosthunt_coevo("orch-test", steps=2)
    assert coevo.get("layer") == "orch-test"