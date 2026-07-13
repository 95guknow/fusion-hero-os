# -*- coding: utf-8 -*-
"""Fusion Hero OS Profile — Admin / Balanced / Eco (fusioniert, ersetzt nichts)."""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Optional

STATE_DIR = Path(os.getenv("FUSION_META_STATE", Path.home() / ".fusion-hero-os"))
PROFILE_FILE = STATE_DIR / "fusion_profile.json"

PROFILES: Dict[str, Dict[str, Any]] = {
    "admin": {
        "label": "Admin",
        "priority": 100,
        "agent_share": 0.70,
        "subagent_share": 0.20,
        "model_share": 0.10,
        "max_parallel_agents": 8,
        "max_parallel_subagents": 4,
        "network_layer_default": "delta",
        "signal_coalesce_ms": 250,
        "worker_cap_ratio": 1.0,
        "reserve_workers": 2,
    },
    "balanced": {
        "label": "Balanced",
        "priority": 50,
        "agent_share": 0.50,
        "subagent_share": 0.25,
        "model_share": 0.25,
        "max_parallel_agents": 4,
        "max_parallel_subagents": 2,
        "network_layer_default": "batch",
        "signal_coalesce_ms": 500,
        "worker_cap_ratio": 0.75,
        "reserve_workers": 1,
    },
    "two_thirds": {
        "label": "2/3 Leistung",
        "priority": 67,
        "agent_share": 0.47,
        "subagent_share": 0.13,
        "model_share": 0.067,
        "max_parallel_agents": 5,
        "max_parallel_subagents": 3,
        "network_layer_default": "batch",
        "signal_coalesce_ms": 400,
        "worker_cap_ratio": 2 / 3,
        "reserve_workers": 2,
        "trinity_max_models": 2,
    },
    "eco": {
        "label": "Eco",
        "priority": 20,
        "agent_share": 0.35,
        "subagent_share": 0.15,
        "model_share": 0.10,
        "max_parallel_agents": 2,
        "max_parallel_subagents": 1,
        "network_layer_default": "pulse",
        "signal_coalesce_ms": 1500,
        "worker_cap_ratio": 0.5,
        "reserve_workers": 1,
    },
}


@dataclass
class FusionProfileState:
    active: str = "admin"
    set_at: Optional[float] = None
    set_by: str = "system"

    def to_dict(self) -> dict:
        return asdict(self)


def _read_file() -> dict:
    if not PROFILE_FILE.exists():
        return {}
    try:
        return json.loads(PROFILE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_file(data: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    prev = _read_file()
    merged = {**prev, **data, "updated_at": time.time()}
    PROFILE_FILE.write_text(json.dumps(merged, indent=2), encoding="utf-8")


def get_active_profile_name() -> str:
    env = os.getenv("FUSION_PROFILE", "").strip().lower()
    if env and env in PROFILES:
        return env
    data = _read_file()
    name = (data.get("active") or "admin").lower()
    return name if name in PROFILES else "admin"


def get_profile_config(name: Optional[str] = None) -> dict:
    name = (name or get_active_profile_name()).lower()
    cfg = dict(PROFILES.get(name, PROFILES["admin"]))
    cfg["id"] = name
    return cfg


def set_profile(name: str, set_by: str = "api") -> dict:
    name = name.strip().lower()
    if name not in PROFILES:
        raise ValueError(f"Unbekanntes Profil: {name}. Verfuegbar: {list(PROFILES.keys())}")
    os.environ["FUSION_PROFILE"] = name
    state = FusionProfileState(active=name, set_at=time.time(), set_by=set_by)
    _write_file({**state.to_dict(), "config": get_profile_config(name)})
    return profile_status()


def profile_status() -> dict:
    name = get_active_profile_name()
    data = _read_file()
    cfg = get_profile_config(name)
    return {
        "active": name,
        "config": cfg,
        "available": list(PROFILES.keys()),
        "set_at": data.get("set_at"),
        "set_by": data.get("set_by", "system"),
        "env": os.getenv("FUSION_PROFILE", ""),
        "performance_ratio": float(os.getenv("FUSION_PERFORMANCE_RATIO", cfg.get("performance_ratio", 1.0))),
    }


def apply_performance_level(ratio: float = 2 / 3, set_by: str = "api") -> dict:
    """Fusion-Leistung auf ratio (0.1–1.0). Windows-Substrat wird nicht geändert."""
    ratio = max(0.1, min(1.0, float(ratio)))
    if ratio >= 0.95:
        name = "admin"
    elif ratio >= 0.6:
        name = "two_thirds"
    elif ratio >= 0.4:
        name = "balanced"
    else:
        name = "eco"

    os.environ["FUSION_PERFORMANCE_RATIO"] = str(round(ratio, 4))
    result = set_profile(name, set_by=set_by)
    cfg = get_profile_config(name)

    trinity = max(1, int(round(3 * ratio)))
    os.environ["FUSION_TRINITY_MAX_MODELS"] = str(cfg.get("trinity_max_models", trinity))
    tokens = max(512, int(1024 * ratio))
    os.environ["FUSION_MODEL_MAX_TOKENS"] = str(tokens)
    orch_w = max(1, int(round((os.cpu_count() or 4) * ratio * 0.5)))
    os.environ["FUSION_ORCH_EXECUTOR_WORKERS"] = str(orch_w)

    result["performance_ratio"] = ratio
    result["trinity_max_models"] = int(os.environ["FUSION_TRINITY_MAX_MODELS"])
    result["model_max_tokens"] = tokens
    result["orchestrator_executor_workers"] = orch_w
    return result


# Boot: env oder gespeichertes Profil fusionieren
_boot = os.getenv("FUSION_PROFILE", "").strip().lower()
if _boot in PROFILES:
    set_profile(_boot, set_by="env_boot")