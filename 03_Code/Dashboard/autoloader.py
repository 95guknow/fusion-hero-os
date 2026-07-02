# -*- coding: utf-8 -*-
"""
Fusion AutoLoader — Treiber + Prozesse staged laden (fusioniert, ersetzt nichts).
Aussehen 2026 · Effizienz 1996-core: Fast-Boot zuerst, Heavy deferred.
"""
from __future__ import annotations

import asyncio
import os
import subprocess
import threading
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

from boot_optimizer import boot_plan, FULL_BOOT_STEPS, FAST_BOOT_STEPS
from fusion_profile import get_active_profile_name, set_profile, profile_status
from hyperthreading_config import is_hyperthreading_enabled, status as ht_status
from meta_layer_windows import (
    attach_meta_layer,
    get_meta_layer_status,
    scan_fusion_processes,
    scan_windows_substrate,
    set_internal_backend_context,
)
from module_registry import get_registry

BOOT_N = int(os.getenv("FUSION_BOOT_N", "12"))
BOOT_STEPS = int(os.getenv("FUSION_BOOT_STEPS", str(FAST_BOOT_STEPS)))
AUTO_ENABLED = os.getenv("FUSION_AUTO_LOAD", "1") != "0"

_AUTOLOAD_LOCK = threading.Lock()

_STATE: Dict[str, Any] = {
    "phase": "idle",
    "started_at": None,
    "finished_at": None,
    "drivers": {},
    "processes": {},
    "errors": [],
    "deferred_scheduled": False,
}


@dataclass
class DriverSpec:
    id: str
    name: str
    tier: int
    deps: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ProcessSpec:
    id: str
    name: str
    role: str
    probe: str  # self | http | pool | scan

    def to_dict(self) -> dict:
        return asdict(self)


DRIVER_CATALOG: List[DriverSpec] = [
    DriverSpec("profile", "Fusion Profil", 0),
    DriverSpec("windows_perf", "Windows Performance Tuner", 0),
    DriverSpec("windows_skin", "Windows Substrat-Skin", 0),
    DriverSpec("hyperthreading", "HT / SMP Treiber", 0),
    DriverSpec("worker_pools", "Worker-Pool Treiber", 0),
    DriverSpec("signal_network", "Layered Signal Network", 1, ["profile"]),
    DriverSpec("grok_bridge", "Grok-intern Bridge", 1),
    DriverSpec("mainframe", "HEROIC Mainframe / QUBO", 2, ["hyperthreading", "worker_pools"]),
    DriverSpec("registry_modules", "Registry Module-Bundle", 2, ["mainframe"]),
    DriverSpec("meta_layer", "Windows Meta-Layer", 3, ["mainframe"]),
    DriverSpec("medienserver", "Medienserver Sync", 4, ["registry_modules"]),
]

PROCESS_CATALOG: List[ProcessSpec] = [
    ProcessSpec("backend", "FastAPI Backend", "api", "self"),
    ProcessSpec("workspace", "NiceGUI Workspace", "gui", "http"),
    ProcessSpec("worker_proc", "Worker-Prozess-Pool", "worker", "pool"),
    ProcessSpec("worker_io", "Worker-IO-Pool", "worker", "pool"),
    ProcessSpec("fusion_scan", "Fusion Python Prozesse", "scan", "scan"),
]


def catalog() -> dict:
    return {
        "drivers": [d.to_dict() for d in DRIVER_CATALOG],
        "processes": [p.to_dict() for p in PROCESS_CATALOG],
        "auto_enabled": AUTO_ENABLED,
        "boot_defaults": {"n": BOOT_N, "steps": BOOT_STEPS, "full_steps": FULL_BOOT_STEPS},
    }


def _set_driver(driver_id: str, status: str, detail: Optional[dict] = None, error: Optional[str] = None) -> None:
    _STATE["drivers"][driver_id] = {
        "status": status,
        "ts": time.time(),
        "detail": detail or {},
        "error": error,
    }


def _load_windows_skin() -> dict:
    from windows_skin import load_skin, set_preset, ensure_user_skin_template, list_presets
    preset = os.getenv("FUSION_WINDOWS_SKIN", "synthwave")
    try:
        set_preset(preset, persist=True)
        ensure_user_skin_template()
        skin = load_skin(force=True)
        _set_driver("windows_skin", "loaded", {
            "id": skin.id,
            "label": skin.label,
            "presets": len(list_presets()),
            "user_override": str(__import__("windows_skin").USER_SKIN_FILE),
        })
        return skin.to_dict()
    except Exception as exc:
        _set_driver("windows_skin", "error", error=str(exc))
        return {"error": str(exc)}


def _tune_windows_substrate() -> dict:
    from windows_perf_tuner import apply_substrate_tuning
    result = apply_substrate_tuning(power=True, dedupe=False, priority=True, env=True)
    _set_driver(
        "windows_perf",
        "loaded",
        {
            "scope": "windows_substrate",
            "applied": result.get("applied_count", 0),
            "memory_pressure": (result.get("scan") or {}).get("memory_pressure"),
            "power_plan": (result.get("scan") or {}).get("power_plan", {}).get("name"),
            "actions": [a.get("id") for a in result.get("actions", []) if a.get("applied")],
        },
    )
    return result


def _load_profile() -> dict:
    name = os.getenv("FUSION_PROFILE", "admin")
    if get_active_profile_name() != name:
        set_profile(name, source="autoloader")
    st = profile_status()
    _set_driver("profile", "loaded", st)
    return st


def _load_hyperthreading() -> dict:
    st = ht_status()
    _set_driver("hyperthreading", "loaded" if st.get("enabled") else "standby", st)
    return st


def _warm_worker_pools() -> dict:
    from process_worker import warm_pools
    detail = warm_pools()
    _set_driver("worker_pools", "loaded", detail)
    return detail


def _load_signal_network() -> dict:
    from layered_signal_network import network_stats
    st = network_stats()
    _set_driver("signal_network", "loaded", st)
    return st


def _load_grok() -> dict:
    from grok_bridge import get_grok_bridge
    bridge = get_grok_bridge()
    st = bridge.status()
    _set_driver("grok_bridge", "loaded" if bridge.skill_loaded else "standby", st)
    return st


def _load_registry_bundle(
    force: bool = False,
    phase: str = "staged",
    sync_medienserver: bool = False,
) -> dict:
    reg = get_registry()
    mf_before = bool(reg.mainframe)
    plan = boot_plan(mainframe_loaded=mf_before, force=force)
    if phase == "auto":
        phase = plan.get("phase", "staged")

    result = reg.load_all(
        boot_n=BOOT_N,
        boot_steps=BOOT_STEPS if phase != "full" else FULL_BOOT_STEPS,
        force=force,
        phase=phase,
        sync_medienserver=sync_medienserver,
    )

    mf = result.get("modules", {}).get("mainframe", {})
    mf_ok = reg.modules.get("mainframe") and reg.modules["mainframe"].status == "loaded"
    _set_driver("mainframe", "loaded" if mf_ok else "error", mf, reg.modules["mainframe"].error)

    loaded = sum(1 for m in reg.modules.values() if m.status == "loaded")
    _set_driver(
        "registry_modules",
        "loaded" if loaded > 3 else "standby",
        {"loaded": loaded, "total": len(reg.modules), "summary": result.get("summary", {})},
    )
    return result


def _load_meta_layer() -> dict:
    set_internal_backend_context(True)
    try:
        state = attach_meta_layer()
        d = state.to_dict()
        _set_driver("meta_layer", "loaded" if state.attached else "standby", d)
        return d
    finally:
        set_internal_backend_context(False)


def _probe_windows_drivers_light() -> dict:
    """Leichtgewicht: Substrat + optionale Kernel-Treiber-Zählung."""
    sub = scan_windows_substrate(use_cache=True)
    drivers_count = None
    try:
        proc = subprocess.run(
            ["driverquery", "/fo", "csv", "/nh"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=8,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        if proc.returncode == 0 and proc.stdout:
            drivers_count = max(0, len([ln for ln in proc.stdout.splitlines() if ln.strip()]) - 0)
    except Exception:
        drivers_count = None
    return {
        "substrate": sub.to_dict(),
        "windows_kernel_drivers": drivers_count,
        "note": "Substrat-Scan — Fusion ersetzt Windows-Treiber nicht",
    }


def _probe_processes(workspace_url: str = "http://127.0.0.1:8080") -> dict:
    import urllib.request
    from process_worker import pool_status

    procs: Dict[str, Any] = {}
    procs["backend"] = {"online": True, "role": "api", "pid": os.getpid()}

    ws_online = False
    try:
        with urllib.request.urlopen(workspace_url, timeout=1.5) as resp:
            ws_online = resp.status == 200
    except Exception:
        pass
    procs["workspace"] = {"online": ws_online, "role": "gui", "url": workspace_url}

    pools = pool_status()
    procs["worker_proc"] = {"online": pools.get("process_pool", {}).get("warm", False), **pools.get("process_pool", {})}
    procs["worker_io"] = {"online": pools.get("io_pool", {}).get("warm", False), **pools.get("io_pool", {})}

    scanned = [p.to_dict() for p in scan_fusion_processes(use_cache=True)]
    procs["fusion_scan"] = {
        "online": len(scanned) > 0,
        "count": len(scanned),
        "processes": scanned[:12],
    }

    _STATE["processes"] = procs
    return procs


def run_autoload_sync(
    phase: str = "staged",
    force: bool = False,
    sync_medienserver: bool = False,
    attach_meta: bool = True,
    workspace_url: str = "http://127.0.0.1:8080",
) -> dict:
    """Treiber staged laden, Prozesse sondieren."""
    with _AUTOLOAD_LOCK:
        return _run_autoload_sync_impl(
            phase, force, sync_medienserver, attach_meta, workspace_url,
        )


def _run_autoload_sync_impl(
    phase: str,
    force: bool,
    sync_medienserver: bool,
    attach_meta: bool,
    workspace_url: str,
) -> dict:
    global _STATE
    _STATE = {
        "phase": phase,
        "started_at": time.time(),
        "finished_at": None,
        "drivers": {},
        "processes": {},
        "errors": [],
        "deferred_scheduled": False,
        "substrate": {},
    }

    try:
        _STATE["substrate"] = _probe_windows_drivers_light()
        _load_windows_skin()
        win_tune = _tune_windows_substrate()
        _STATE["windows_tune"] = win_tune
        _load_profile()
        _load_hyperthreading()
        _warm_worker_pools()
        _load_signal_network()
        _load_grok()

        result = _load_registry_bundle(force=force, phase=phase, sync_medienserver=sync_medienserver)

        if attach_meta:
            _load_meta_layer()
        else:
            ml = get_meta_layer_status(light=True, mainframe_loaded=bool(get_registry().mainframe))
            _set_driver("meta_layer", "standby", ml.to_dict())

        if sync_medienserver or (phase == "full" and result.get("boot_plan", {}).get("sync")):
            ms = result.get("modules", {}).get("medienserver", {})
            _set_driver(
                "medienserver",
                "loaded" if ms.get("status") == "success" else "standby",
                ms,
            )
        else:
            _set_driver("medienserver", "deferred", {"reason": "boot_optimizer_skip"})

        _probe_processes(workspace_url)

        try:
            import app as fusion_app
            fusion_app._sync_globals_from_registry(result)
            fusion_app._invalidate_health_cache()
        except Exception:
            pass

    except Exception as exc:
        _STATE["errors"].append(str(exc))

    _STATE["finished_at"] = time.time()
    _STATE["duration_ms"] = round((_STATE["finished_at"] - _STATE["started_at"]) * 1000, 1)
    loaded_drv = sum(1 for d in _STATE["drivers"].values() if d.get("status") == "loaded")
    standby_drv = sum(1 for d in _STATE["drivers"].values() if d.get("status") == "standby")
    online_proc = sum(1 for p in _STATE["processes"].values() if p.get("online"))
    _STATE["summary"] = {
        "drivers_loaded": loaded_drv,
        "drivers_standby": standby_drv,
        "drivers_ready": loaded_drv + standby_drv,
        "drivers_total": len(DRIVER_CATALOG),
        "processes_online": online_proc,
        "processes_total": len(PROCESS_CATALOG),
        "errors": len(_STATE["errors"]),
        "ready": loaded_drv >= 4 and _STATE["processes"].get("backend", {}).get("online"),
    }
    return dict(_STATE)


async def run_autoload(
    phase: str = "staged",
    force: bool = False,
    sync_medienserver: bool = False,
    attach_meta: bool = True,
    workspace_url: str = "http://127.0.0.1:8080",
) -> dict:
    return await asyncio.to_thread(
        run_autoload_sync,
        phase,
        force,
        sync_medienserver,
        attach_meta,
        workspace_url,
    )


def autoload_status() -> dict:
    reg = get_registry()
    return {
        **catalog(),
        "state": dict(_STATE),
        "registry_mainframe": bool(reg.mainframe),
        "profile": get_active_profile_name(),
        "hyperthreading": is_hyperthreading_enabled(),
    }


async def schedule_deferred_full() -> None:
    """Heavy-Boot + Sync im Hintergrund (wie app._deferred_heavy_boot)."""
    _STATE["deferred_scheduled"] = True
    from boot_optimizer import medienserver_sync_needed
    await asyncio.to_thread(
        run_autoload_sync,
        "full",
        True,
        medienserver_sync_needed(),
        True,
        "http://127.0.0.1:8080",
    )