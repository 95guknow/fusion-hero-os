"""QUBO-artige Bottleneck-Vorhersage für Track-Konkurrenz (ohne externe Solver-Abhängigkeit)."""

from __future__ import annotations

from typing import Dict, List, Tuple


def build_competition_qubo(
    track_names: List[str],
    bottleneck_risks: Dict[str, float],
    coupling_strength: float = 0.5,
) -> Dict[Tuple[int, int], float]:
    """
    Minimiere Σ Q_ii x_i + Σ Q_ij x_i x_j  (x_i ∈ {0,1} = Track aktiv).

    Diagonal: Bottleneck-Risiko (höher = teurer aktiv zu bleiben).
    Off-Diagonal: Kopplung zwischen konkurrierenden Tracks.
    """
    n = len(track_names)
    q: Dict[Tuple[int, int], float] = {}
    for i, name in enumerate(track_names):
        q[(i, i)] = bottleneck_risks.get(name, 0.0)
    for i in range(n):
        for j in range(i + 1, n):
            q[(i, j)] = coupling_strength * (
                bottleneck_risks.get(track_names[i], 0.0)
                + bottleneck_risks.get(track_names[j], 0.0)
            ) / 2.0
    return q


def greedy_bottleneck_assignment(
    track_names: List[str],
    bottleneck_risks: Dict[str, float],
    budget_slots: int,
) -> Dict[str, float]:
    """
    Greedy-Zuweisung: wähle ``budget_slots`` Tracks mit niedrigstem effektivem Risiko.
    Liefert Prioritäts-Multiplikatoren (0.3–2.5) — kein echter QUBO-Solver.
    """
    if not track_names:
        return {}
    ranked = sorted(track_names, key=lambda n: bottleneck_risks.get(n, 0.0))
    winners = set(ranked[: max(1, budget_slots)])
    multipliers: Dict[str, float] = {}
    for name in track_names:
        if name in winners:
            multipliers[name] = 2.5 if bottleneck_risks.get(name, 0) > 0.5 else 1.5
        else:
            multipliers[name] = max(0.3, 1.0 - bottleneck_risks.get(name, 0.0))
    return multipliers


def qubo_energy(q: Dict[Tuple[int, int], float], assignment: List[int]) -> float:
    """Energie für binäre Zuweisung x (Länge n)."""
    n = len(assignment)
    energy = 0.0
    for i in range(n):
        if assignment[i]:
            energy += q.get((i, i), 0.0)
        for j in range(i + 1, n):
            if assignment[i] and assignment[j]:
                energy += q.get((i, j), 0.0)
    return energy