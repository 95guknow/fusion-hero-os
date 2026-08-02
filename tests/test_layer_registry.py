# -*- coding: utf-8 -*-
"""Tests für die v8.3 Layer-Registry: alle Layer aus fusion_unified.yaml
liefern einen Status, die in der Konsolidierung ergänzten Layer sind
vorhanden, und der Layer-Graph ist konsistent verdrahtet."""

from __future__ import annotations

import yaml

from fusion_hero_os.core.layer_registry import (
    REPO_ROOT,
    UNIFIED_CONFIG,
    LayerStatus,
    get_all_layer_status,
    get_layer_status,
)

V83_LAYERS = {"kernel", "ascension", "tarnkappe", "android", "knowledge"}


def _unified() -> dict:
    return yaml.safe_load(UNIFIED_CONFIG.read_text(encoding="utf-8")) or {}


def test_every_unified_layer_has_module_and_health():
    layers = _unified().get("layers") or {}
    assert layers, "fusion_unified.yaml: keine Layer definiert"
    for lid, cfg in layers.items():
        assert (cfg or {}).get("module"), f"Layer '{lid}' ohne module"
        assert (cfg or {}).get("health"), f"Layer '{lid}' ohne health"


def test_v83_layers_registered():
    layers = set((_unified().get("layers") or {}).keys())
    missing = V83_LAYERS - layers
    assert not missing, f"v8.3-Layer fehlen in fusion_unified.yaml: {sorted(missing)}"


def test_registry_reports_every_layer():
    result = get_all_layer_status()
    layers = _unified().get("layers") or {}
    assert result["layer_count"] == len(layers)
    assert set(result["layers"].keys()) == set(layers.keys())
    for lid, status in result["layers"].items():
        assert status["layer"] == lid
        assert isinstance(status["present"], bool)
        assert isinstance(status["config_ok"], bool)


def test_all_layers_present_and_config_ok():
    """v8.3-Konsolidierungsziel: der komplette Layer-Graph ist lokal verifizierbar."""
    result = get_all_layer_status()
    broken = {
        lid: s["detail"]
        for lid, s in result["layers"].items()
        if not (s["present"] and s["config_ok"])
    }
    assert not broken, f"Layer nicht ok: {broken}"
    assert result["overall"] == "complete"


def test_layer_edges_reference_known_layers():
    unified = _unified()
    layers = set((unified.get("layers") or {}).keys())
    nodes = set((unified.get("nodes") or {}).keys())
    edges = unified.get("layer_edges") or []
    assert edges, "fusion_unified.yaml: layer_edges fehlen"
    known = layers | nodes
    for edge in edges:
        assert edge.get("from") in known, f"layer_edge from unbekannt: {edge}"
        assert edge.get("to") in known, f"layer_edge to unbekannt: {edge}"


def test_knowledge_layer_ties_registries_together():
    status = get_layer_status("knowledge")
    assert isinstance(status, LayerStatus)
    detail = status.detail
    assert detail["proof_claims"] > 0, "proof_registry.yaml nicht gelesen"
    assert detail["geltungsstand_entries"] >= 0
    assert detail["erkenntnisse_index"]["ok"] is True
    assert detail["erkenntnisse_index"]["open_conflicts"] == 0


def test_ascension_layer_importable():
    """Ascension layer import + version pin.

    Historically the core carried the aspirational track id ``9.x-aspirational``.
    Final discharge (PR #112) aligned ``AscensionCore.version`` with the platform
    kanon (root ``VERSION``). Accept that pin; keep importability as the hard
    contract. Aspirational track identity remains in docs/assets (v9.10 labels),
    not in this status field.
    """
    status = get_layer_status("ascension")
    assert status is not None
    assert status.detail.get("importable") is True, status.detail
    platform = (REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip()
    reported = str(status.detail.get("version", ""))
    assert reported == platform, (
        f"ascension layer version {reported!r} must match root VERSION {platform!r} "
        f"(discharge pin; was startswith('9.') pre-v14/v15)"
    )


def test_unknown_layer_returns_none():
    assert get_layer_status("gibt_es_nicht") is None


def test_config_paths_are_repo_relative():
    result = get_all_layer_status()
    for lid, s in result["layers"].items():
        for rel in s["detail"].get("config_paths", []):
            assert not rel.startswith("/"), f"{lid}: absoluter Pfad im Status: {rel}"
            assert ".." not in rel, f"{lid}: Pfad verlaesst Repo: {rel}"
    assert (REPO_ROOT / "fusion_unified.yaml").exists()
