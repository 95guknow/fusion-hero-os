#!/usr/bin/env python3
"""Test for ghosthunt_hook."""
import sys
sys.path.insert(0, ".")
from ghosthunting.hook import ghosthunt_hook

def test_ghosthunt_hook_returns_state():
    """Hook should return snapshot and coevo_state with expected keys."""
    snap, coevo = ghosthunt_hook("test-layer", context={"events": 5}, use_springloop=True, steps=5)
    assert snap is not None
    assert "distance" in snap
    assert coevo is not None
    assert "emerged" in coevo
    assert "springloop_energy" in coevo
    print(f"emerged={coevo['emerged']}, energy={coevo['springloop_energy']}")
    print("test_ghosthunt_hook_returns_state: PASS")

if __name__ == "__main__":
    test_ghosthunt_hook_returns_state()
