# -*- coding: utf-8 -*-
"""Tests fuer das Inference-Scheduling-QUBO (Kodierungs-Satz + Greedy-Garantie)."""
import itertools
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from fusion_hero_os.core.inference_scheduler_qubo import (
    ScheduleProblem,
    build_qubo,
    greedy_schedule,
    random_problem,
    solve_schedule,
)

rng = np.random.default_rng(20260705)


# ---- SCHED-QUBO-ENCODING-EXAKT ------------------------------------------------

def test_qubo_encoding_matches_direct_cost_property_sweep():
    """SATZ: x^T Q x + offset == H(x) fuer alle x — Sweep ueber Zufallsinstanzen
    und Zufallszuweisungen, 0 Verletzungen."""
    for _ in range(150):
        n = int(rng.integers(2, 12))
        prob = random_problem(n, rng)
        Q, offset = build_qubo(prob)
        assert np.linalg.norm(Q - Q.T) < 1e-12  # Solver-Kontrakt: symmetrisch
        for _ in range(10):
            x = rng.integers(0, 2, n).astype(np.float64)
            e_qubo = float(x @ Q @ x) + offset
            assert abs(e_qubo - prob.total_cost(x)) < 1e-8


def test_qubo_encoding_exhaustive_small_n():
    """Erschoepfend fuer n<=6: Kodierung exakt auf ALLEN 2^n Zuweisungen."""
    for n in (2, 3, 4, 5, 6):
        prob = random_problem(n, rng)
        Q, offset = build_qubo(prob)
        for bits in itertools.product((0.0, 1.0), repeat=n):
            x = np.array(bits)
            assert abs(float(x @ Q @ x) + offset - prob.total_cost(x)) < 1e-8


def test_asymmetric_or_selfcontention_penalties_rejected():
    P_bad = np.array([[0.0, 2.5], [0.0, 0.0]])  # das 3x3-Review-Muster: unsymmetrisch
    with pytest.raises(ValueError, match="symmetrisch"):
        ScheduleProblem(np.ones(2), np.ones(2), P_bad, np.zeros((2, 2)))
    P_diag = np.array([[1.0, 0.0], [0.0, 0.0]])
    with pytest.raises(ValueError, match="Diagonale"):
        ScheduleProblem(np.ones(2), np.ones(2), P_diag, np.zeros((2, 2)))


# ---- SCHED-QUBO-NIE-SCHLECHTER-GREEDY -------------------------------------------

def test_solver_never_worse_than_greedy_property_sweep():
    """BY CONSTRUCTION: solve_schedule waehlt min(SA, Greedy) — Sweep bestaetigt
    total_cost <= Greedy-Kosten auf jeder Instanz."""
    for k in range(25):
        n = int(rng.integers(3, 20))
        prob = random_problem(n, rng)
        out = solve_schedule(prob, steps=1500, n_restarts=2, base_seed=k)
        cost_greedy = prob.total_cost(greedy_schedule(prob))
        assert out["total_cost"] <= cost_greedy + 1e-9
        # Rueckgabe-Konsistenz: assignment reproduziert total_cost
        assert abs(prob.total_cost(out["assignment"]) - out["total_cost"]) < 1e-8


def test_sa_reaches_bruteforce_optimum_small_n():
    """Auf kleinen Instanzen (n<=8) findet der Solver das globale Optimum."""
    for k in range(10):
        n = int(rng.integers(3, 9))
        prob = random_problem(n, rng)
        out = solve_schedule(prob, steps=3000, n_restarts=4, base_seed=100 + k)
        best = min(prob.total_cost(np.array(b))
                   for b in itertools.product((0, 1), repeat=n))
        assert abs(out["total_cost"] - best) < 1e-8


def test_sa_strictly_beats_greedy_on_some_instances():
    """Nicht-Trivialitaet: SA ist auf einem Sweep MINDESTENS EINMAL strikt
    besser als Greedy (sonst waere das QUBO wertlos). Kein Universal-Claim."""
    strictly_better = 0
    for k in range(20):
        prob = random_problem(12, rng, contention_density=0.5)
        out = solve_schedule(prob, steps=3000, n_restarts=4, base_seed=200 + k)
        if out["sa_strictly_better"]:
            strictly_better += 1
    assert strictly_better >= 1
