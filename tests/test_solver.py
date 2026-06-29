# -*- coding: utf-8 -*-
"""Korrektheits-Gates für den QUBO-Solver (engine/mainframe.py).

Die zentrale Eigenschaft: der Annealer muss den per Brute-Force ermittelten
Grundzustand treffen. parallel_anneal ist deterministisch (jeder Restart wird
mit base_seed+k geseedet), daher sind diese Tests reproduzierbar.
"""
import itertools

import numpy as np

from engine.mainframe import (
    parallel_anneal,
    simulated_annealing,
    local_search,
    make_Q,
)


def _brute_force_min(Q):
    """Exakter Grundzustand über alle 2^n Zustände (nur für kleine n)."""
    n = Q.shape[0]
    best_e, best_x = np.inf, None
    for bits in itertools.product([0, 1], repeat=n):
        x = np.asarray(bits, dtype=float)
        e = float(x @ Q @ x)
        if e < best_e:
            best_e, best_x = e, x
    return best_x, best_e


def _fixed_Q(n, seed):
    """Deterministische, symmetrische Testmatrix (unabhängig vom Modul-RNG)."""
    r = np.random.default_rng(seed)
    Q = np.zeros((n, n))
    for i in range(n):
        Q[i, i] = r.normal(0, 1)
    for i in range(n):
        for j in range(i + 1, n):
            v = r.normal(0, 1) / 2.0
            Q[i, j] = Q[j, i] = v
    return Q


def test_make_Q_is_symmetric():
    Q = make_Q(10, scale=1.5)
    assert np.allclose(Q, Q.T), "make_Q muss symmetrische Matrizen liefern"


def test_diagonal_ground_state_is_exact():
    # Q = -I  ->  Minimum bei x=(1,...,1), Energie = -n
    n = 6
    Q = -np.eye(n)
    out = parallel_anneal(Q, steps=2000, n_restarts=8)
    assert abs(out["energy"] - (-n)) < 1e-9
    assert list(np.asarray(out["solution"], dtype=int)) == [1] * n


def test_parallel_anneal_matches_bruteforce():
    for seed in (1, 2, 3):
        Q = _fixed_Q(8, seed)
        _, be = _brute_force_min(Q)
        out = parallel_anneal(Q, steps=8000, n_restarts=16)
        assert abs(out["energy"] - be) < 1e-6, (
            f"seed={seed}: Annealer {out['energy']:.6f} != Brute-Force {be:.6f}"
        )


def test_simulated_annealing_reaches_bruteforce():
    Q = _fixed_Q(7, 4)
    _, be = _brute_force_min(Q)
    _, se = simulated_annealing(Q, steps=12000, T0=2.0)
    assert abs(se - be) < 1e-6, f"SA {se:.6f} != Brute-Force {be:.6f}"


def test_local_search_returns_local_minimum():
    Q = _fixed_Q(8, 5)
    x, e = local_search(Q, iters=500)
    # An einem lokalen Minimum darf kein einzelner Bit-Flip die Energie senken.
    x = np.asarray(x, dtype=float)
    for i in range(len(x)):
        xt = x.copy()
        xt[i] = 1 - xt[i]
        assert float(xt @ Q @ xt) >= e - 1e-9
