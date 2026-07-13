# -*- coding: utf-8 -*-
"""Regressionstests: QUBO<->Ising-Bruecke in qb_qubo.py (Claim ISING-BRIDGE).

Bisher lebte diese Verifikation nur im __main__-Selbsttest von qb_qubo.py.
Hier wird sie zum CI-gepruefen Beweis: Fuer symmetrische Q gilt
E_QUBO(x) == E_Ising(s) unter x = (1+s)/2, fuer alle Belegungen.
"""
import importlib.util
import sys
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parent.parent


def _load_qb(path: Path):
    spec = importlib.util.spec_from_file_location("qb_" + path.parent.name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod  # vor exec_module, fuer dataclass/pickle-Kompatibilitaet
    spec.loader.exec_module(mod)
    return mod


qb = _load_qb(_ROOT / "qb_qubo.py")
rng = np.random.default_rng(42)


def test_ising_bridge_energy_identity_property_sweep():
    """SATZ-Sweep: 200 zufaellige symmetrische Q x zufaellige x — Energien identisch."""
    for _ in range(200):
        n = int(rng.integers(2, 10))
        A = rng.normal(size=(n, n))
        Q = (A + A.T) / 2.0
        x = rng.integers(0, 2, n)
        s = 2 * x - 1
        J, h, c = qb.qubo_to_ising(Q)
        e_qubo = float(x @ Q @ x)
        e_ising = qb.ising_energy(J, h, c, s)
        assert abs(e_qubo - e_ising) < 1e-9


def test_ising_bridge_exhaustive_small_n():
    """Fuer n=6 ALLE 64 Belegungen — nicht nur Stichproben."""
    n = 6
    A = rng.normal(size=(n, n))
    Q = (A + A.T) / 2.0
    J, h, c = qb.qubo_to_ising(Q)
    for bits in range(2 ** n):
        x = np.array([(bits >> i) & 1 for i in range(n)], dtype=np.float64)
        s = 2 * x - 1
        assert abs(float(x @ Q @ x) - qb.ising_energy(J, h, c, s)) < 1e-9


def test_make_q_submodular_offdiagonal_nonpositive():
    """make_Q(submodular=True): Off-Diagonale <= 0, Diagonale unveraendert verteilt.

    Verankert den 2026-07-05 bereinigten Zustand (die tools/-Kopie hatte einen
    kaputten submodular-Block, der auch die Diagonale verstuemmelte).
    """
    for _ in range(50):
        n = int(rng.integers(3, 12))
        Q = qb.make_Q(n, submodular=True, scale=1.0)
        off_mask = ~np.eye(n, dtype=bool)
        assert (Q[off_mask] <= 0).all()
        assert Q.shape == (n, n)


def test_all_three_copies_are_content_identical():
    """Die drei qb_qubo.py-Kopien (root, 02_Mathematik, 03_Code/tools) duerfen
    nie wieder auseinanderlaufen (Konsolidierung 2026-07-05)."""
    canonical = (_ROOT / "02_Mathematik" / "qb_qubo.py").read_bytes().replace(b"\r\n", b"\n")
    for rel in ("qb_qubo.py", "03_Code/tools/qb_qubo.py"):
        other = (_ROOT / rel).read_bytes().replace(b"\r\n", b"\n")
        assert other == canonical, f"{rel} weicht von 02_Mathematik/qb_qubo.py ab"
