# -*- coding: utf-8 -*-
"""Tests fuer layer_distance_crosscheck: BFS-Distanzsemantik auf einem
synthetischen Pfadgraphen UND auf dem echten fusion_unified.yaml-Graphen.
Proof-Registry-Anker: LAYER-DISTANCE-CROSSCHECK."""

from __future__ import annotations

import pytest

from fusion_hero_os.core.layer_distance_crosscheck import (
    build_adjacency,
    build_adjacency_from_fusion_unified,
    crosscheck_all,
    crosscheck_real_layers,
    distance_n_neighbors,
    find_blind_spot_candidates,
)
from fusion_hero_os.core.layer_registry import get_all_layer_status


def _path_graph():
    # A - B - C - D
    return build_adjacency([
        {"from": "A", "to": "B"},
        {"from": "B", "to": "C"},
        {"from": "C", "to": "D"},
    ])


def test_build_adjacency_is_undirected():
    g = build_adjacency([{"from": "A", "to": "B"}])
    assert g["A"] == {"B"}
    assert g["B"] == {"A"}


def test_build_adjacency_skips_malformed_edges():
    g = build_adjacency([{"from": "A"}, {"to": "B"}, {}, {"from": "A", "to": "B"}])
    assert g == {"A": {"B"}, "B": {"A"}}


def test_distance_0_is_start_node():
    g = _path_graph()
    assert distance_n_neighbors(g, "A", 0) == {"A"}


def test_distance_1_2_3_on_path_graph():
    g = _path_graph()
    assert distance_n_neighbors(g, "A", 1) == {"B"}
    assert distance_n_neighbors(g, "A", 2) == {"C"}
    assert distance_n_neighbors(g, "A", 3) == {"D"}


def test_distance_1_and_distance_2_are_always_disjoint_on_path_graph():
    g = _path_graph()
    for node in g:
        assert distance_n_neighbors(g, node, 1) & distance_n_neighbors(g, node, 2) == set()


def test_distance_1_and_distance_2_are_always_disjoint_on_real_graph():
    g = build_adjacency_from_fusion_unified()
    assert g, "fusion_unified.yaml layer_edges leer — Graph fehlt"
    for node in g:
        assert distance_n_neighbors(g, node, 1) & distance_n_neighbors(g, node, 2) == set()


def test_isolated_node_has_no_positive_distance_neighbors():
    g = build_adjacency([{"from": "A", "to": "B"}])
    assert distance_n_neighbors(g, "isolated", 1) == set()
    assert distance_n_neighbors(g, "isolated", 2) == set()


def test_negative_n_raises_value_error():
    g = _path_graph()
    with pytest.raises(ValueError):
        distance_n_neighbors(g, "A", -1)


def test_find_blind_spot_candidates_flags_correlated_blind_spot():
    g = _path_graph()
    health = {"A": True, "B": True, "C": False, "D": True}
    candidates = find_blind_spot_candidates(g, health, "A")
    assert len(candidates) == 1
    assert candidates[0].unhealthy_distance_2 == "C"
    assert candidates[0].healthy_distance_1 == ["B"]


def test_find_blind_spot_candidates_silent_when_direct_neighbor_already_unhealthy():
    # Distanz-1-Problem ist Sache der Adjazenz-Pruefung, nicht des n±2-Checks.
    g = _path_graph()
    health = {"A": True, "B": False, "C": False, "D": True}
    assert find_blind_spot_candidates(g, health, "A") == []


def test_find_blind_spot_candidates_empty_when_all_healthy():
    g = _path_graph()
    health = {"A": True, "B": True, "C": True, "D": True}
    assert find_blind_spot_candidates(g, health, "A") == []


def test_crosscheck_all_runs_over_every_node_in_graph():
    g = _path_graph()
    health = {"A": True, "B": True, "C": False, "D": True}
    result = crosscheck_all(g, health)
    assert any(c.origin == "A" and c.unhealthy_distance_2 == "C" for c in result)


def test_build_adjacency_from_real_fusion_unified_layer_edges():
    """Hand-verifiziertes Beispiel gegen die echten layer_edges (siehe A13)."""
    g = build_adjacency_from_fusion_unified()
    assert g["knowledge"] == {"kernel", "ascension", "intelligence", "connectors", "vr"}
    assert distance_n_neighbors(g, "knowledge", 2) == {"orchestration"}


def test_tarnkappe_reaches_android_only_at_distance_2():
    """Hyper-Tarnkappe/Poly-Mesh-Beispiel: tarnkappe-Adjazenz ist nur {network};
    android liegt auf Distanz 2 (via network) — sichtbar erst per n±2-Crosscheck."""
    g = build_adjacency_from_fusion_unified()
    assert distance_n_neighbors(g, "tarnkappe", 1) == {"network"}
    assert "android" in distance_n_neighbors(g, "tarnkappe", 2)


def test_crosscheck_real_layers_reports_no_false_positives_when_layer_graph_is_healthy():
    result = get_all_layer_status()
    if result["overall"] != "complete":
        pytest.skip("Layer-Graph aktuell nicht durchgehend gesund (umgebungsabhaengig)")
    assert crosscheck_real_layers() == []
