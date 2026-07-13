#!/usr/bin/env python3
"""Test for springloop_energy (middle-out core)."""
import sys
sys.path.insert(0, ".")
from core.qb_qubo import springloop_energy, energy, make_Q
import numpy as np

def test_springloop_reduces_energy():
    """Springloop should reduce or maintain energy (contraction)."""
    np.random.seed(42)
    Q = make_Q(5)
    x = np.random.randint(0, 2, 5).astype(float)
    initial_e = energy(Q, x)
    xs, final_e = springloop_energy(Q, x, steps=50)
    print(f"Initial: {initial_e:.4f}, Final: {final_e:.4f}")
    assert final_e <= initial_e + 1e-6, "Springloop should not increase energy"
    print("test_springloop_reduces_energy: PASS")

if __name__ == "__main__":
    test_springloop_reduces_energy()
