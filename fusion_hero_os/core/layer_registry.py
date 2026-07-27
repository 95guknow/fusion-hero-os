"""Fusion Hero OS v8.3 — Layer-Registry (alles mit allem).

Liest die Konfigurations-Registries des Repos maschinell ein und liefert
einen einheitlichen Status je Layer aus fusion_unified.yaml — inklusive der
in v8.3 ergaenzten Layer kernel, ascension, tarnkappe, android, knowledge.

Design: reine Datei-/Struktur-Checks, kein Netzwerkzwang. Live-Probes
(Tailscale, LLM-Keys) macht weiterhin fusion_integration_hub; diese Registry
beantwortet die Frage "ist der Layer im Repo vorhanden, konfiguriert und
konsistent verdrahtet?" deterministisch und offline.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]

UNIFIED_CONFIG = REPO_ROOT / "fusion_unified.yaml"
MESH_CONFIG = REPO_ROOT / "mesh_connectors.yaml"
LLM_CONFIG = REPO_ROOT / "llm_frameworks.yaml"
PMS_CONFIG = REPO_ROOT / "PMS.yaml"
PROOF_REGISTRY = REPO_ROOT / "proof_registry.yaml"
GELTUNGSSTAND = REPO_ROOT / "hero-guide_geltungsstand.json"
ERKENNTNISSE_INDEX = REPO_ROOT / "docs" / "v8" / "erkenntnisse_index.yaml"
PUSH_LAYER_GUARD = REPO_ROOT / "push_layer_guard.yaml"


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError:
        return {}
    try:
        if path.exists():
            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return data if isinstance(data, dict) else {}
    except Exception:
        pass
    return {}


def _load_json(path: Path) -> Any:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return None


@dataclass
class LayerStatus:
    """Einheitlicher Status eines Layers aus fusion_unified.yaml."""

    layer: str
    present: bool
    config_ok: bool
    module: str = ""
    health: str = ""
    detail: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "layer": self.layer,
            "present": self.present,
            "config_ok": self.config_ok,
            "module": self.module,
            "health": self.health,
            "detail": dict(self.detail),
        }


def _paths_from_config(config: Any) -> list[Path]:
    """Normalisiert das config-Feld eines Layers auf Repo-Pfade."""
    if config is None:
        return []
    entries = config if isinstance(config, list) else [config]
    return [REPO_ROOT / str(e).rstrip("/") for e in entries]


def _check_mesh_layer(status: LayerStatus) -> None:
    mesh = _load_yaml(MESH_CONFIG)
    connectors = mesh.get("connectors") or {}
    status.detail["connector_count"] = len(connectors)
    status.config_ok = status.config_ok and len(connectors) > 0


def _check_intelligence_layer(status: LayerStatus) -> None:
    llm = _load_yaml(LLM_CONFIG)
    frameworks = llm.get("frameworks") or llm.get("providers") or {}
    status.detail["framework_count"] = len(frameworks)
    status.config_ok = status.config_ok and len(frameworks) > 0


def _check_vr_layer(status: LayerStatus) -> None:
    assets_root = REPO_ROOT / "03_VR_Assets"
    assets = list(assets_root.glob("*.jpg")) if assets_root.is_dir() else []
    status.detail["assets_found"] = len(assets)


def _check_kernel_layer(status: LayerStatus) -> None:
    bridge_dir = REPO_ROOT / "kernel" / "bridge"
    sources = list(bridge_dir.glob("*.c")) + list(bridge_dir.glob("*.py")) if bridge_dir.is_dir() else []
    status.detail["bridge_sources"] = len(sources)
    status.detail["launcher"] = (REPO_ROOT / "start_fusion_hero.py").exists()
    status.config_ok = status.config_ok and len(sources) > 0


def _check_ascension_layer(status: LayerStatus) -> None:
    info: dict[str, Any] = {"importable": False}
    try:
        from ascension_os.core.ascension_core import get_ascension_core

        core = get_ascension_core()
        info["importable"] = True
        info["version"] = getattr(core, "version", "unknown")
        info["cec"] = core.cec is not None
        info["persistent_sisyphos"] = core.persistent_sisyphos is not None
        info["evolution_engine"] = core.evolution_engine is not None
    except Exception as e:
        info["error"] = str(e)[:200]
    status.detail.update(info)
    status.config_ok = status.config_ok and info["importable"]


def _check_knowledge_layer(status: LayerStatus) -> None:
    proof = _load_yaml(PROOF_REGISTRY)
    claims = proof.get("claims") or []
    by_status: dict[str, int] = {}
    for claim in claims:
        st = str((claim or {}).get("status", "?"))
        by_status[st] = by_status.get(st, 0) + 1
    status.detail["proof_claims"] = len(claims)
    status.detail["proof_by_status"] = by_status

    geltung = _load_json(GELTUNGSSTAND)
    entries = geltung.get("items") if isinstance(geltung, dict) else geltung
    status.detail["geltungsstand_entries"] = len(entries) if isinstance(entries, list) else 0

    status.detail["erkenntnisse_index"] = erkenntnisse_summary()
    index_ok = bool(status.detail["erkenntnisse_index"].get("ok"))
    status.config_ok = status.config_ok and len(claims) > 0 and index_ok


_EXTRA_CHECKS = {
    "connectors": _check_mesh_layer,
    "network": _check_mesh_layer,
    "intelligence": _check_intelligence_layer,
    "vr": _check_vr_layer,
    "kernel": _check_kernel_layer,
    "ascension": _check_ascension_layer,
    "knowledge": _check_knowledge_layer,
}


def erkenntnisse_summary() -> dict[str, Any]:
    """Zusammenfassung des Erkenntnis-Index (docs/v8/erkenntnisse_index.yaml)."""
    index = _load_yaml(ERKENNTNISSE_INDEX)
    docs = index.get("docs") or []
    if not docs:
        return {"ok": False, "error": "erkenntnisse_index.yaml fehlt oder leer",
                "path": str(ERKENNTNISSE_INDEX.relative_to(REPO_ROOT))}
    by_status: dict[str, int] = {}
    missing: list[str] = []
    for doc in docs:
        st = str((doc or {}).get("status", "?"))
        by_status[st] = by_status.get(st, 0) + 1
        rel = str((doc or {}).get("path", ""))
        if rel and not (REPO_ROOT / rel).exists():
            missing.append(rel)
    conflicts = index.get("resolved_conflicts") or []
    open_conflicts = [c for c in conflicts if str((c or {}).get("state")) != "resolved"]
    return {
        "ok": not missing and not open_conflicts,
        "doc_count": len(docs),
        "by_status": by_status,
        "missing_files": missing,
        "resolved_conflicts": len(conflicts) - len(open_conflicts),
        "open_conflicts": len(open_conflicts),
        "version": index.get("version"),
    }


def get_layer_status(layer_id: str) -> LayerStatus | None:
    unified = _load_yaml(UNIFIED_CONFIG)
    cfg = (unified.get("layers") or {}).get(layer_id)
    if cfg is None:
        return None
    return _build_status(layer_id, cfg)


def _build_status(layer_id: str, cfg: dict[str, Any]) -> LayerStatus:
    paths = _paths_from_config(cfg.get("config"))
    existing = [p for p in paths if p.exists()]
    remote = bool(cfg.get("remote"))
    status = LayerStatus(
        layer=layer_id,
        present=bool(existing) or not paths or remote,
        # Remote-Layer (z.B. Windows-Workstation) werden nicht am lokalen
        # Dateisystem gemessen - ihre Configs leben auf einem anderen Knoten.
        config_ok=remote or len(existing) == len(paths),
        module=str(cfg.get("module", "")),
        health=str(cfg.get("health", "")),
        detail={
            "config_paths": [str(p.relative_to(REPO_ROOT)) for p in paths],
            "config_missing": [
                str(p.relative_to(REPO_ROOT)) for p in paths if not p.exists()
            ],
            **({"remote": True} if remote else {}),
        },
    )
    extra = _EXTRA_CHECKS.get(layer_id)
    if extra:
        extra(status)
    return status


def get_all_layer_status() -> dict[str, Any]:
    """Status ALLER Layer aus fusion_unified.yaml + Layer-Kanten."""
    unified = _load_yaml(UNIFIED_CONFIG)
    layers = unified.get("layers") or {}
    statuses = {lid: _build_status(lid, cfg or {}) for lid, cfg in layers.items()}
    ok_count = sum(1 for s in statuses.values() if s.present and s.config_ok)
    push_guard = _load_yaml(PUSH_LAYER_GUARD) if PUSH_LAYER_GUARD.exists() else {}
    return {
        "layer_count": len(statuses),
        "layers_ok": ok_count,
        "layers": {lid: s.to_dict() for lid, s in statuses.items()},
        "layer_edges": unified.get("layer_edges") or [],
        "principle": unified.get("principle"),
        "overall": "complete" if ok_count == len(statuses) else "partial",
        # Weave: push structure known IDs + path→layer map (blocks unwanted pushes)
        "push_layer_guard": {
            "present": PUSH_LAYER_GUARD.exists(),
            "policy": push_guard.get("policy"),
            "freemium": push_guard.get("freemium", False),
            "identities": push_guard.get("identities"),
            "layer_ids": list((push_guard.get("layers") or {}).keys()),
            "config": str(PUSH_LAYER_GUARD.relative_to(REPO_ROOT))
            if PUSH_LAYER_GUARD.exists()
            else None,
        },
    }


if __name__ == "__main__":
    print(json.dumps(get_all_layer_status(), indent=2, ensure_ascii=False))
