# -*- coding: utf-8 -*-
"""Zentrale Fusion Hero OS Einstellungen — Schema, Persistenz, Anwendung.

Binäre (bool) und diskrete (enum) Optionen für alle Hauptfunktionen.
Werte werden in ~/.fusion-hero-os/fusion_settings.json gespeichert und beim
Start sowie per API auf os.environ angewendet.
"""

from __future__ import annotations

import json
import os
import time
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional

STATE_DIR = Path(os.getenv("FUSION_META_STATE", Path.home() / ".fusion-hero-os"))
SETTINGS_FILE = STATE_DIR / "fusion_settings.json"

GROUPS = {
    "performance": {"label": "Leistung & Ressourcen", "order": 1},
    "modules": {"label": "Module & Bridge", "order": 2},
    "llm": {"label": "LLM & Provider", "order": 3},
    "agents": {"label": "Agenten & Kontrolle", "order": 4},
    "dashboard": {"label": "Dashboard & UI", "order": 5},
    "context": {"label": "Kontext & Mathematik", "order": 6},
}

# type: bool | enum | multi_enum
SETTINGS_SCHEMA: List[Dict[str, Any]] = [
    # --- performance ---
    {
        "key": "FUSION_PROFILE",
        "label": "Leistungsprofil",
        "description": "Admin = voll, Eco = sparsam. Steuert Worker-Anteile und Signal-Layer.",
        "type": "enum",
        "group": "performance",
        "default": "admin",
        "options": [
            {"value": "admin", "label": "Admin (100%)"},
            {"value": "two_thirds", "label": "2/3 Leistung"},
            {"value": "balanced", "label": "Balanced"},
            {"value": "eco", "label": "Eco"},
        ],
    },
    {
        "key": "FUSION_HYPERTHREADING",
        "label": "Hyperthreading",
        "description": "Parallele Worker-Skalierung über logische CPUs.",
        "type": "bool",
        "group": "performance",
        "default": "1",
    },
    {
        "key": "FUSION_HT_ADAPTIVE",
        "label": "HT adaptiv",
        "description": "Spectrum selbstregulierend an CPU-Last anpassen.",
        "type": "bool",
        "group": "performance",
        "default": "1",
    },
    {
        "key": "FUSION_HT_SPECTRUM",
        "label": "HT-Spektrum",
        "description": "0 = aus, 1 = Standard, 2 = aggressiv (virtuelle Threads).",
        "type": "enum",
        "group": "performance",
        "default": "1.0",
        "options": [
            {"value": "0.0", "label": "0.0 — minimal"},
            {"value": "0.5", "label": "0.5 — sparsam"},
            {"value": "1.0", "label": "1.0 — Standard"},
            {"value": "1.5", "label": "1.5 — erhöht"},
            {"value": "2.0", "label": "2.0 — maximal"},
        ],
    },
    {
        "key": "FUSION_USE_GPU",
        "label": "GPU nutzen",
        "description": "CUDA/GPU-Pfade für virtuelles HT und Llama.",
        "type": "bool",
        "group": "performance",
        "default": "1",
    },
    {
        "key": "FUSION_VIRTUAL_HT_GPU",
        "label": "Virtuelles GPU-HT",
        "description": "Zustände im GPU-VRAM cachen für parallele Tracks.",
        "type": "bool",
        "group": "performance",
        "default": "1",
    },
    {
        "key": "FUSION_VIRTUAL_THREADS",
        "label": "Virtuelle Threads",
        "description": "Obergrenze paralleler virtueller Tracks.",
        "type": "enum",
        "group": "performance",
        "default": "64",
        "options": [
            {"value": "8", "label": "8"},
            {"value": "16", "label": "16"},
            {"value": "32", "label": "32"},
            {"value": "64", "label": "64"},
            {"value": "128", "label": "128"},
        ],
    },
    {
        "key": "FUSION_CPU_TUNER_AUTO",
        "label": "CPU-Tuner auto",
        "description": "Temperatur/Last-basierte Performance-Ratio.",
        "type": "bool",
        "group": "performance",
        "default": "1",
    },
    {
        "key": "FUSION_RESOURCE_COUPLER_AUTO",
        "label": "Ressourcen-Koppler",
        "description": "RAM/VRAM/Compute automatisch koppeln.",
        "type": "bool",
        "group": "performance",
        "default": "1",
    },
    # --- modules ---
    {
        "key": "FUSION_AUTO_LOAD",
        "label": "Auto-Load beim Start",
        "description": "Alle Module/Agenten beim Dashboard-Start laden (0 = Fast Boot).",
        "type": "bool",
        "group": "modules",
        "default": "0",
    },
    {
        "key": "FUSION_ALL_MODULES",
        "label": "Alle Module aktiv",
        "description": "Vollständige Modul-Registry statt Minimal-Set.",
        "type": "bool",
        "group": "modules",
        "default": "0",
    },
    {
        "key": "FUSION_DISABLED_MODULES",
        "label": "Deaktivierte Core-Module",
        "description": "Module vom Dispatcher ausschließen (Mehrfachauswahl).",
        "type": "multi_enum",
        "group": "modules",
        "default": "",
        "options_from": "core_modules",
    },
    # --- llm ---
    {
        "key": "FUSION_LLM_BACKEND",
        "label": "LLM-Backend",
        "description": "Primärer Inferenz-Backend für Orchestrator.",
        "type": "enum",
        "group": "llm",
        "default": "grok-intern",
        "options": [
            {"value": "grok-intern", "label": "Grok intern"},
            {"value": "llama-local", "label": "Llama lokal"},
            {"value": "claude-science", "label": "Claude Science"},
            {"value": "fusion-hero", "label": "Fusion Hero"},
        ],
    },
    {
        "key": "FUSION_PROVIDER_AUTO",
        "label": "Provider Auto-Routing",
        "description": "Automatisch besten verfügbaren Provider wählen.",
        "type": "bool",
        "group": "llm",
        "default": "1",
    },
    {
        "key": "FUSION_LLAMA_QUBO",
        "label": "Llama + QUBO",
        "description": "QUBO-Augmentierung bei lokaler Llama-Generierung.",
        "type": "bool",
        "group": "llm",
        "default": "1",
    },
    {
        "key": "FUSION_MODEL_MAX_TOKENS",
        "label": "Max. Tokens",
        "description": "Obergrenze generierter Tokens pro Anfrage.",
        "type": "enum",
        "group": "llm",
        "default": "1024",
        "options": [
            {"value": "256", "label": "256"},
            {"value": "512", "label": "512"},
            {"value": "1024", "label": "1024"},
            {"value": "2048", "label": "2048"},
            {"value": "4096", "label": "4096"},
        ],
    },
    {
        "key": "FUSION_CLAUDE_SCIENCE",
        "label": "Claude Science",
        "description": "Heroik-Wissenschaft über Claude Science erlauben.",
        "type": "bool",
        "group": "llm",
        "default": "1",
    },
    # --- agents ---
    {
        "key": "FUSION_AGENT_CONTROL",
        "label": "Agent Control",
        "description": "Pre/Post-Dispatch Geltungsprüfung für Agenten.",
        "type": "bool",
        "group": "agents",
        "default": "0",
    },
    {
        "key": "FUSION_ORCH_DUAL_AGENT",
        "label": "Dual-Agent Orchestrator",
        "description": "Zwei-Agenten-Pfad in Dynamic Orchestration.",
        "type": "bool",
        "group": "agents",
        "default": "1",
    },
    {
        "key": "FUSION_GUI_SIGNAL",
        "label": "Signal-Layer",
        "description": "Netzwerk-Polling-Strategie für Monitor-GUI.",
        "type": "enum",
        "group": "agents",
        "default": "pulse",
        "options": [
            {"value": "pulse", "label": "Pulse (sparsam)"},
            {"value": "batch", "label": "Batch"},
            {"value": "delta", "label": "Delta (schnell)"},
        ],
    },
    # --- dashboard (UI scope) ---
    {
        "key": "ui.phone_link_panel",
        "label": "Phone-Link-Panel",
        "description": "SMS-Spiegel im Dashboard anzeigen.",
        "type": "bool",
        "group": "dashboard",
        "scope": "ui",
        "default": "1",
    },
    {
        "key": "ui.bridge_panel",
        "label": "Bridge-Panel",
        "description": "IPC-Bridge-Status und Test-Dispatch anzeigen.",
        "type": "bool",
        "group": "dashboard",
        "scope": "ui",
        "default": "1",
    },
    {
        "key": "ui.poll_bridge_ms",
        "label": "Bridge-Polling",
        "description": "Aktualisierungsintervall Bridge-Status.",
        "type": "enum",
        "group": "dashboard",
        "scope": "ui",
        "default": "4000",
        "options": [
            {"value": "2000", "label": "2 s"},
            {"value": "4000", "label": "4 s"},
            {"value": "8000", "label": "8 s"},
            {"value": "15000", "label": "15 s"},
        ],
    },
    {
        "key": "ui.poll_phone_ms",
        "label": "Phone-Link-Polling",
        "description": "Aktualisierungsintervall Phone-Link.",
        "type": "enum",
        "group": "dashboard",
        "scope": "ui",
        "default": "8000",
        "options": [
            {"value": "4000", "label": "4 s"},
            {"value": "8000", "label": "8 s"},
            {"value": "15000", "label": "15 s"},
            {"value": "30000", "label": "30 s"},
        ],
    },
    {
        "key": "ui.poll_metrics_ms",
        "label": "Metriken-Polling",
        "description": "CPU/RAM-Aktualisierung.",
        "type": "enum",
        "group": "dashboard",
        "scope": "ui",
        "default": "1200",
        "options": [
            {"value": "800", "label": "0.8 s"},
            {"value": "1200", "label": "1.2 s"},
            {"value": "3000", "label": "3 s"},
            {"value": "6000", "label": "6 s"},
        ],
    },
    {
        "key": "ui.event_stream_max",
        "label": "Event-Stream Limit",
        "description": "Maximale Events im Live-Stream.",
        "type": "enum",
        "group": "dashboard",
        "scope": "ui",
        "default": "500",
        "options": [
            {"value": "100", "label": "100"},
            {"value": "250", "label": "250"},
            {"value": "500", "label": "500"},
            {"value": "1000", "label": "1000"},
        ],
    },
    # --- context ---
    {
        "key": "FUSION_CONTEXT_WINDOW",
        "label": "Kontext-Fenster",
        "description": "Banach-Kontraktion für Gesprächskontext.",
        "type": "bool",
        "group": "context",
        "default": "1",
    },
    {
        "key": "FUSION_BANACH_LAMBDA",
        "label": "Banach λ",
        "description": "Kontraktionsfaktor (muss < 1 für Fixpunkt).",
        "type": "enum",
        "group": "context",
        "default": "0.74",
        "options": [
            {"value": "0.50", "label": "0.50 — stark"},
            {"value": "0.74", "label": "0.74 — Standard"},
            {"value": "0.85", "label": "0.85 — locker"},
            {"value": "0.92", "label": "0.92 — minimal"},
        ],
    },
]


def _bool_str(val: Any) -> str:
    if isinstance(val, bool):
        return "1" if val else "0"
    s = str(val).strip().lower()
    return "1" if s in ("1", "true", "yes", "on") else "0"


def _read_file() -> dict:
    if not SETTINGS_FILE.exists():
        return {}
    try:
        return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_file(data: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    prev = _read_file()
    merged = {**prev, **data, "updated_at": time.time()}
    SETTINGS_FILE.write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8")


def _core_module_options() -> List[Dict[str, str]]:
    try:
        from fusion_hero_os.modules import ALL_CORE_MODULES
        return [{"value": cls.__name__, "label": cls.__name__} for cls in ALL_CORE_MODULES]
    except Exception:
        return []


def _resolve_options(spec: dict) -> List[Dict[str, str]]:
    if spec.get("options_from") == "core_modules":
        return _core_module_options()
    return spec.get("options") or []


def _current_value(spec: dict, stored: dict) -> Any:
    key = spec["key"]
    scope = spec.get("scope", "env")
    if scope == "ui":
        ui = stored.get("ui") or {}
        if key in ui:
            return ui[key]
        if key.startswith("ui."):
            short = key[3:]
            if short in ui:
                return ui[short]
        return spec.get("default", "")
    if key in stored.get("env", {}):
        return stored["env"][key]
    return os.getenv(key, spec.get("default", ""))


def get_schema() -> Dict[str, Any]:
    groups = sorted(GROUPS.items(), key=lambda x: x[1]["order"])
    items = []
    for spec in SETTINGS_SCHEMA:
        entry = {**spec, "options": _resolve_options(spec)}
        items.append(entry)
    return {
        "groups": [{"id": gid, **meta} for gid, meta in groups],
        "settings": items,
        "file": str(SETTINGS_FILE),
    }


def get_values() -> Dict[str, Any]:
    stored = _read_file()
    env_out: Dict[str, Any] = {}
    ui_out: Dict[str, Any] = {}
    for spec in SETTINGS_SCHEMA:
        val = _current_value(spec, stored)
        key = spec["key"]
        if spec.get("scope") == "ui":
            ui_key = key[3:] if key.startswith("ui.") else key
            if spec["type"] == "bool":
                ui_out[ui_key] = _bool_str(val) == "1"
            elif spec["type"] == "multi_enum":
                ui_out[ui_key] = [x.strip() for x in str(val or "").split(",") if x.strip()]
            else:
                ui_out[ui_key] = str(val)
        else:
            if spec["type"] == "bool":
                env_out[key] = _bool_str(val) == "1"
            elif spec["type"] == "multi_enum":
                env_out[key] = [x.strip() for x in str(val or "").split(",") if x.strip()]
            else:
                env_out[key] = str(val)
    return {"env": env_out, "ui": ui_out, "updated_at": stored.get("updated_at")}


def _as_bool(val: Any) -> bool:
    if isinstance(val, bool):
        return val
    return _bool_str(val) == "1"


def _apply_side_effects(updates: Dict[str, Any]) -> List[str]:
    applied = []
    if "FUSION_PROFILE" in updates:
        try:
            from fusion_profile import set_profile
            set_profile(str(updates["FUSION_PROFILE"]), set_by="settings")
            applied.append("profile")
        except Exception:
            os.environ["FUSION_PROFILE"] = str(updates["FUSION_PROFILE"])
    if "FUSION_HYPERTHREADING" in updates or "FUSION_HT_SPECTRUM" in updates:
        try:
            from core import hyperthreading_config as ht
            if "FUSION_HYPERTHREADING" in updates:
                ht.enable(_as_bool(updates["FUSION_HYPERTHREADING"]))
                applied.append("hyperthreading")
            if "FUSION_HT_SPECTRUM" in updates:
                ht.set_ht_spectrum(float(updates["FUSION_HT_SPECTRUM"]))
                applied.append("ht_spectrum")
        except Exception:
            pass
    return applied


def apply_settings(values: Dict[str, Any], set_by: str = "api") -> Dict[str, Any]:
    """Wendet env + ui Werte an und persistiert."""
    stored = _read_file()
    env_store = dict(stored.get("env") or {})
    ui_store = dict(stored.get("ui") or {})
    env_updates: Dict[str, Any] = {}
    ui_updates: Dict[str, Any] = {}

    schema_by_key = {s["key"]: s for s in SETTINGS_SCHEMA}

    for raw_key, raw_val in values.items():
        spec = schema_by_key.get(raw_key)
        if not spec:
            continue
        key = spec["key"]
        if spec["type"] == "bool":
            norm = _bool_str(raw_val)
            parsed: Any = norm == "1"
            store_val = norm
        elif spec["type"] == "multi_enum":
            if isinstance(raw_val, list):
                store_val = ",".join(str(x).strip() for x in raw_val if str(x).strip())
            else:
                store_val = str(raw_val or "").strip()
            parsed = [x.strip() for x in store_val.split(",") if x.strip()]
        else:
            store_val = str(raw_val)
            parsed = store_val

        if spec.get("scope") == "ui":
            ui_key = key[3:] if key.startswith("ui.") else key
            ui_store[ui_key] = store_val
            ui_updates[ui_key] = parsed
        else:
            env_store[key] = store_val
            os.environ[key] = store_val
            env_updates[key] = parsed

    _write_file({"env": env_store, "ui": ui_store, "set_by": set_by})
    side = _apply_side_effects(env_updates)
    values = get_values()
    try:
        import supabase_store as store

        if store.cloud_sync_enabled():
            store.save_settings_cloud(values, set_by=set_by)
    except Exception:
        pass
    return {
        "status": "ok",
        "applied_env": list(env_updates.keys()),
        "applied_ui": list(ui_updates.keys()),
        "side_effects": side,
        "values": values,
    }


def boot_load() -> Dict[str, Any]:
    """Beim Dashboard-Start gespeicherte Einstellungen laden."""
    if os.getenv("FUSION_SETTINGS_CLOUD_PULL", "0") == "1":
        try:
            import supabase_store as store

            store.pull_settings_from_cloud(merge_if_newer=True)
        except Exception:
            pass
    stored = _read_file()
    env_store = stored.get("env") or {}
    for spec in SETTINGS_SCHEMA:
        if spec.get("scope") == "ui":
            continue
        key = spec["key"]
        if key in env_store:
            os.environ[key] = str(env_store[key])
        elif spec.get("default") is not None and key not in os.environ:
            os.environ.setdefault(key, str(spec["default"]))
    _apply_side_effects({k: v for k, v in env_store.items()})
    return get_values()


def reset_defaults(set_by: str = "reset") -> Dict[str, Any]:
    defaults: Dict[str, Any] = {}
    for spec in SETTINGS_SCHEMA:
        defaults[spec["key"]] = spec.get("default", "")
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    if SETTINGS_FILE.exists():
        SETTINGS_FILE.unlink()
    return apply_settings(defaults, set_by=set_by)