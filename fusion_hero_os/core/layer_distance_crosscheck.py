# -*- coding: utf-8 -*-
"""Fusion Hero OS — Layer-Graph Distance-N Crosscheck (v2.0, axiomatisch verankert).

Operationalisiert die im Gemini-Brainstorm vom 2026-07-24 vorgeschlagene
"Layer n±2 Ghosthunting"-Idee (Skip-eine-Ebene-Cross-Check statt reiner
Adjazenz-Pruefung) als reine Graphmathematik auf dem ECHTEN Layer-Graphen
aus fusion_unified.yaml (layer_edges, gelesen ueber layer_registry).

Axiom-Anker: proof_registry.yaml LAYER-DISTANCE-CROSSCHECK (BEWIESEN).

Ehrlicher Status:
  * Real und beweisbar (SATZ-Ebene): distance_n_neighbors() liefert exakt
    die Kuerzeste-Pfad-Distanz-N-Menge per BFS; fuer jeden Knoten sind
    Distanz-1- und Distanz-2-Menge disjunkt — getestet auf einem
    synthetischen Pfadgraphen UND auf dem echten fusion_unified.yaml-Graphen.
  * NICHT bewiesen (MODELL / Design-Rationale): die allgemeine Behauptung,
    dass Skip-eine-Ebene-Pruefung in der echten Welt mehr Fehler faengt als
    reine Adjazenz-Pruefung. Das ist die Motivation aus dem Brainstorm,
    keine mathematische oder empirische Aussage, die dieser Code beweist.
  * Bewusst NICHT "ghosthunt_*" genannt: "Ghosthunt"/"Geisterjagd" traegt in
    diesem Repo bereits zwei verschiedene, echte, getestete Bedeutungen
    (ascension_os/core/geisterjagd_module.py: Banach-Fixpunkt-Konvergenz;
    src/normal_os/ascension/ghosthunt_hook.py: koevolutionaere
    Heuristik-Score-Bruecke zwischen den suite/layers 00-07, getestet in
    tests/test_suite_integration.py). Ein dritter, wieder anderer "Ghosthunt"
    waere exakt das Namenskollisions-Muster, das die Doktrin
    "Wiring + De-Dup vor Re-Import" (artifacts/2026-07-16_legacy_ghost_hunt.md)
    verhindern soll. Siehe docs/dissertation/anhaenge/A13.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Set

Graph = Dict[str, Set[str]]


def build_adjacency(layer_edges: List[Dict[str, Any]]) -> Graph:
    """Baut eine ungerichtete Adjazenzliste aus layer_edges ({from, to, ...})."""
    adjacency: Graph = {}
    for edge in layer_edges:
        a = str((edge or {}).get("from", "") or "")
        b = str((edge or {}).get("to", "") or "")
        if not a or not b:
            continue
        adjacency.setdefault(a, set()).add(b)
        adjacency.setdefault(b, set()).add(a)
    return adjacency


def distance_n_neighbors(adjacency: Graph, start: str, n: int) -> Set[str]:
    """BFS: Knoten mit Kuerzeste-Pfad-Distanz genau n von start.

    n=0 -> {start}. Knoten, die von start aus unerreichbar sind (oder n
    groesser als die maximale Distanz ab start), liefern ein leeres Set
    statt eines Fehlers.
    """
    if n < 0:
        raise ValueError("n muss >= 0 sein")
    if n == 0:
        return {start}
    visited: Dict[str, int] = {start: 0}
    frontier = [start]
    dist = 0
    while frontier and dist < n:
        nxt: List[str] = []
        for node in frontier:
            for neighbor in adjacency.get(node, ()):
                if neighbor not in visited:
                    visited[neighbor] = dist + 1
                    nxt.append(neighbor)
        frontier = nxt
        dist += 1
    return {node for node, d in visited.items() if d == n}


@dataclass
class BlindSpotCandidate:
    """origin und alle direkten Nachbarn healthy, aber ein Distanz-2-Knoten nicht."""

    origin: str
    healthy_distance_1: List[str]
    unhealthy_distance_2: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "origin": self.origin,
            "healthy_distance_1": list(self.healthy_distance_1),
            "unhealthy_distance_2": self.unhealthy_distance_2,
        }


def find_blind_spot_candidates(
    adjacency: Graph, health: Dict[str, bool], origin: str
) -> List[BlindSpotCandidate]:
    """Kern-Crosscheck: origin UND alle Distanz-1-Nachbarn healthy, aber ein
    Distanz-2-Nachbar NICHT healthy -> Blind-Spot-Kandidat. Genau der Fall,
    den reine Adjazenz-Pruefung (nur Distanz-1) niemals sieht."""
    if not health.get(origin, False):
        return []
    d1 = distance_n_neighbors(adjacency, origin, 1)
    if not all(health.get(node, False) for node in d1):
        return []
    d2 = distance_n_neighbors(adjacency, origin, 2)
    return [
        BlindSpotCandidate(
            origin=origin,
            healthy_distance_1=sorted(d1),
            unhealthy_distance_2=node,
        )
        for node in sorted(d2)
        if not health.get(node, False)
    ]


def crosscheck_all(adjacency: Graph, health: Dict[str, bool]) -> List[BlindSpotCandidate]:
    """Blind-Spot-Kandidaten fuer jeden Knoten des Graphen (deterministische Ordnung)."""
    out: List[BlindSpotCandidate] = []
    for origin in sorted(adjacency):
        out.extend(find_blind_spot_candidates(adjacency, health, origin))
    return out


def build_adjacency_from_fusion_unified() -> Graph:
    """Adjazenz direkt aus dem echten fusion_unified.yaml (via layer_registry)."""
    from fusion_hero_os.core.layer_registry import get_all_layer_status

    result = get_all_layer_status()
    return build_adjacency(result.get("layer_edges") or [])


def crosscheck_real_layers() -> List[BlindSpotCandidate]:
    """Crosscheck ueber den echten Layer-Graphen + dessen present/config_ok-Status."""
    from fusion_hero_os.core.layer_registry import get_all_layer_status

    result = get_all_layer_status()
    adjacency = build_adjacency(result.get("layer_edges") or [])
    health = {
        lid: bool(s["present"] and s["config_ok"])
        for lid, s in result["layers"].items()
    }
    return crosscheck_all(adjacency, health)


if __name__ == "__main__":
    import json

    candidates = crosscheck_real_layers()
    print(json.dumps(
        {"blind_spot_candidates": [c.to_dict() for c in candidates],
         "count": len(candidates)},
        indent=2, ensure_ascii=False,
    ))
