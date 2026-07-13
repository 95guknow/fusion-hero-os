# -*- coding: utf-8 -*-
"""Ehrliche Tests für den Automatisierungs-Scheduler-Knoten (03_Code/core).

Verankert die OPTIMALITÄT der exakten Ressourcenauswahl (0/1-Knapsack, DP):
sie liefert das wert-maximale zulässige Bündel (== Brute-Force-Optimum auf
kleinen Instanzen) und hält die Gesamtkosten <= Budget. Bewusst NUR die exakte
Auswahl — der optionale QUBO-Pfad ist Heuristik und wird NICHT als optimal
behauptet (QUBO-SCHEDULER-NUTZEN bleibt in proof_registry.yaml OFFEN).
"""
import itertools
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "03_Code" / "core"))

from automation_scheduler_node import knapsack_exact  # noqa: E402


def _brute_force_optimum(costs, values, budget):
    """Referenz: bestes zulässiges Bündel per Enumeration (klein)."""
    best = 0.0
    n = len(costs)
    for r in range(n + 1):
        for combo in itertools.combinations(range(n), r):
            if sum(costs[i] for i in combo) <= budget:
                best = max(best, sum(values[i] for i in combo))
    return best


def test_knapsack_exact_matches_bruteforce_small():
    """SATZ: knapsack_exact == Brute-Force-Optimum auf kleinen Zufallsinstanzen."""
    rnd = random.Random(20260706)
    for _ in range(300):
        n = rnd.randint(1, 9)
        costs = [rnd.randint(1, 7) for _ in range(n)]
        values = [float(rnd.randint(1, 10)) for _ in range(n)]
        budget = rnd.randint(1, sum(costs))
        idx, total = knapsack_exact(costs, values, budget)
        assert abs(total - _brute_force_optimum(costs, values, budget)) < 1e-9
        # die zurückgegebene Auswahl trägt genau den gemeldeten Gesamtwert
        assert abs(sum(values[i] for i in idx) - total) < 1e-9


def test_knapsack_exact_respects_budget():
    """SATZ: die gewählte Auswahl überschreitet das Budget nie."""
    rnd = random.Random(7)
    for _ in range(300):
        n = rnd.randint(1, 11)
        costs = [rnd.randint(1, 9) for _ in range(n)]
        values = [float(rnd.randint(1, 10)) for _ in range(n)]
        budget = rnd.randint(1, sum(costs))
        idx, _total = knapsack_exact(costs, values, budget)
        assert sum(costs[i] for i in idx) <= budget


def test_knapsack_exact_edge_cases():
    """Randfälle: leer, Budget 0, alles passt."""
    assert knapsack_exact([], [], 10) == ([], 0.0)
    assert knapsack_exact([3, 4], [5.0, 6.0], 0) == ([], 0.0)
    idx, total = knapsack_exact([2, 3], [5.0, 6.0], 10)  # alles passt
    assert sorted(idx) == [0, 1] and abs(total - 11.0) < 1e-9
