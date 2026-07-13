# -*- coding: utf-8 -*-
"""Cyber Layer über Windows-Substrat — sichtbarer Optimierungs-Indikator."""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

FUSION_VERSION = "v1.2"
CYBER_LAYER_ROLE = "cyber_layer_over_windows_substrate"
STATE_DIR = Path(os.getenv("FUSION_META_STATE", Path.home() / ".fusion-hero-os"))
STATE_FILE = STATE_DIR / "cyber_layer_state.json"


@dataclass
class CyberSignal:
    id: str
    label: str
    active: bool
    detail: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class CyberLayerState:
    active: bool = False
    role: str = CYBER_LAYER_ROLE
    fusion_os: str = FUSION_VERSION
    activated_at: Optional[float] = None
    last_pulse: Optional[float] = None
    substrate_scope: str = "windows_substrate"
    optimization_score: int = 0
    signals: List[CyberSignal] = field(default_factory=list)
    visual: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "active": self.active,
            "role": self.role,
            "fusion_os": self.fusion_os,
            "activated_at": self.activated_at,
            "last_pulse": self.last_pulse,
            "substrate_scope": self.substrate_scope,
            "optimization_score": self.optimization_score,
            "signals": [s.to_dict() for s in self.signals],
            "visual": self.visual,
            "architecture": {
                "pattern": "Cyber Layer über Windows-Substrat",
                "decoupled_from": "fusion_performance_ratio",
            },
        }


_STATE: Optional[CyberLayerState] = None


def _read_file() -> dict:
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_file(data: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    merged = {**_read_file(), **data, "updated_at": time.time()}
    STATE_FILE.write_text(json.dumps(merged, indent=2, default=str), encoding="utf-8")


def _build_signals(substrate_result: Optional[dict] = None) -> List[CyberSignal]:
    signals: List[CyberSignal] = []
    scan = (substrate_result or {}).get("scan") or {}
    actions = {a.get("id"): a for a in (substrate_result or {}).get("actions", [])}

    power = scan.get("power_plan") or {}
    power_ok = not scan.get("power_saver_active", True)
    signals.append(CyberSignal(
        "power_substrate",
        "Power Substrat",
        power_ok,
        power.get("name", "?"),
    ))

    enc = actions.get("substrate_env", {})
    signals.append(CyberSignal(
        "encoding",
        "UTF-8 Pipeline",
        enc.get("applied") or bool(os.getenv("PYTHONUTF8")),
        enc.get("detail", "PYTHONUTF8"),
    ))

    prio = actions.get("priority_boost", {})
    signals.append(CyberSignal(
        "priority",
        "Prozess-Priorität",
        prio.get("applied", False),
        prio.get("detail", ""),
    ))

    dedupe = actions.get("dedupe_backend", {})
    if dedupe:
        signals.append(CyberSignal(
            "dedupe",
            "Backend-Singularity",
            dedupe.get("applied", False),
            dedupe.get("detail", ""),
        ))

    pressure = scan.get("memory_pressure", "low")
    signals.append(CyberSignal(
        "ram_watch",
        "RAM-Wächter",
        pressure in ("low", "medium"),
        f"Druck: {pressure} · {scan.get('ram_percent', '?')}%",
    ))

    signals.append(CyberSignal(
        "meta_layer",
        "Meta-Layer Host",
        True,
        "Windows NT · Fusion v1.2",
    ))

    return signals


def _score(signals: List[CyberSignal]) -> int:
    if not signals:
        return 0
    active = sum(1 for s in signals if s.active)
    return max(0, min(100, int(40 + (active / len(signals)) * 60)))


def activate_cyber_layer(substrate_result: Optional[dict] = None) -> CyberLayerState:
    """Aktiviert Cyber Layer nach Substrat-Tuning."""
    global _STATE
    now = time.time()
    prev = _read_file()
    signals = _build_signals(substrate_result)
    score = _score(signals)
    active = score >= 50 or any(s.id == "power_substrate" and s.active for s in signals)

    try:
        from windows_skin import load_skin
        skin = load_skin()
        badge_on = skin.tokens.get("badge_active", "OPTIMIZATION ACTIVE")
        badge_off = skin.tokens.get("badge_standby", "CYBER STANDBY")
        skin_id = skin.id
        accent = skin.tokens.get("accent", "#00ffd5")
        accent2 = skin.tokens.get("accent2", "#a855f7")
    except Exception:
        skin = None
        badge_on, badge_off, skin_id = "OPTIMIZATION ACTIVE", "CYBER STANDBY", "cyber_neon"
        accent, accent2 = "#00ffd5", "#a855f7"

    state = CyberLayerState(
        active=active,
        activated_at=prev.get("activated_at") or now,
        last_pulse=now,
        optimization_score=score,
        signals=signals,
        visual={
            "mode": "cyber_active" if active else "cyber_standby",
            "frame": "hud_corners",
            "scanline": active and (skin.features.get("scanline", True) if skin else True),
            "grid_density": "high" if active else "normal",
            "accent": accent,
            "accent2": accent2,
            "skin_id": skin_id,
            "skin_label": skin.label if skin else "Cyber Neon",
            "badge": badge_on if active else badge_off,
        },
    )
    _STATE = state
    _write_file(state.to_dict())
    return state


def pulse_cyber_layer() -> CyberLayerState:
    """Heartbeat — hält Cyber Layer sichtbar aktuell."""
    global _STATE
    try:
        from windows_perf_tuner import substrate_status
        sub = substrate_status()
        last_apply = sub.get("last_apply") or {}
        if last_apply:
            return activate_cyber_layer(last_apply)
    except Exception:
        pass
    if _STATE:
        _STATE.last_pulse = time.time()
        return _STATE
    return activate_cyber_layer()


def get_cyber_layer_status(refresh: bool = False) -> CyberLayerState:
    global _STATE
    if refresh or _STATE is None:
        data = _read_file()
        if data.get("active"):
            signals = [
                CyberSignal(**{k: s.get(k) for k in CyberSignal.__dataclass_fields__})
                for s in data.get("signals", [])
            ]
            _STATE = CyberLayerState(
                active=data.get("active", False),
                activated_at=data.get("activated_at"),
                last_pulse=data.get("last_pulse"),
                optimization_score=data.get("optimization_score", 0),
                signals=signals,
                visual=data.get("visual", {}),
            )
        else:
            _STATE = pulse_cyber_layer()
    return _STATE