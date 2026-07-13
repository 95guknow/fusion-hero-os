# -*- coding: utf-8 -*-
"""Korrektheits-Gates für das Profit-Switching-QUBO (engine/mining_qubo.py).

Wichtigstes Gate: im ENTKOPPELTEN Fall (keine geteilten Ressourcen) ist die
gierige Zuweisung beweisbar optimal — der Annealer MUSS sie exakt treffen.
"""
import numpy as np

from engine.mining_qubo import (
    build_profit_switching_qubo,
    decode_assignment,
    assignment_profit,
    optimize_switching,
    estimate_profit_matrix,
    ExcavatorConnector,
)


def _fixed_profit(G, A, seed):
    r = np.random.default_rng(seed)
    hr = r.uniform(20, 60, (G, A)) * r.uniform(0.7, 1.3, (G, A))
    pw = r.uniform(120, 260, (G, A))
    rev = [0.012, 0.018, 0.009, 0.015][:A]
    return estimate_profit_matrix(hr, pw, rev, energy_cost_per_kwh=0.30)


def test_qubo_onehot_structure():
    profit = _fixed_profit(4, 4, 1)
    Q, P = build_profit_switching_qubo(profit)
    G, A = profit.shape
    # Diagonale kodiert -profit - P
    for g in range(G):
        for a in range(A):
            k = g * A + a
            assert abs(Q[k, k] - (-profit[g, a] - P)) < 1e-12
    # Paare derselben GPU: +P; verschiedene GPUs: 0
    for g in range(G):
        for a in range(A):
            for b in range(a + 1, A):
                assert Q[g * A + a, g * A + b] == P
    assert Q[0 * A + 0, 1 * A + 0] == 0.0  # verschiedene GPUs ungekoppelt


def test_decode_assignment_picks_argmax_per_gpu():
    sol = np.array([0, 1, 0, 0, 1, 0, 0, 0])  # G=2, A=4
    assert decode_assignment(sol, 2, 4) == {0: 1, 1: 0}


def test_optimize_matches_greedy_when_uncoupled():
    # Ohne Kopplung ist Greedy optimal -> Annealer muss exakt gleichziehen.
    for seed in (0, 1, 2, 3):
        profit = _fixed_profit(8, 4, seed)
        greedy = {g: int(np.argmax(profit[g])) for g in range(8)}
        gp = assignment_profit(greedy, profit)
        res = optimize_switching(profit)
        assert abs(res["profit_per_hour"] - gp) < 1e-9, (
            f"seed={seed}: Annealer {res['profit_per_hour']:.6f} != Greedy {gp:.6f}"
        )


def test_estimate_profit_matrix_value():
    hr = np.array([[10.0]])
    pw = np.array([[200.0]])
    # revenue = 10*0.02 = 0.2 ; cost = 0.2 kW * 0.30 = 0.06 ; netto = 0.14
    profit = estimate_profit_matrix(hr, pw, [0.02], energy_cost_per_kwh=0.30)
    assert abs(profit[0, 0] - 0.14) < 1e-12


def test_excavator_connector_is_dry_run_by_default():
    # Sicherheits-Gate: ohne injizierten Client darf NICHTS ausgeführt werden.
    exc = ExcavatorConnector()
    res = exc.speeds()
    assert res["would_execute"] is False
    assert res["available"] is False
