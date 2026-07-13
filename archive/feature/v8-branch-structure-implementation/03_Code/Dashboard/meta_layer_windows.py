# -*- coding: utf-8 -*-
"""Fusion Hero OS Meta-Layer über Windows — Substrat-Host + Meta-Orchestrierung."""
from __future__ import annotations

import json
import os
import platform
import subprocess
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

FUSION_VERSION = "v1.2"
CORE_VERSION = "v7.5"
META_LAYER_ROLE = "meta_layer_over_windows"
STATE_DIR = Path(os.getenv("FUSION_META_STATE", Path.home() / ".fusion-hero-os"))
STATE_FILE = STATE_DIR / "meta_layer_state.json"
_SUBSTRATE_TTL = 120.0
_PROCESS_TTL = 8.0


@dataclass
class WindowsSubstrate:
    """Windows als Host-Substrat — Fusion ersetzt Windows nicht."""
    platform: str = "Windows"
    edition: str = ""
    release: str = ""
    version: str = ""
    build: str = ""
    hostname: str = ""
    username: str = ""
    arch: str = ""
    logical_cpus: int = 0
    physical_cpus: int = 0
    ram_gb: float = 0.0
    boot_time: Optional[float] = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class MetaLayerProcess:
    name: str
    pid: int
    role: str
    cmdline: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class MetaLayerState:
    attached: bool = False
    role: str = META_LAYER_ROLE
    fusion_os: str = FUSION_VERSION
    core: str = CORE_VERSION
    attached_at: Optional[float] = None
    last_heartbeat: Optional[float] = None
    substrate: Optional[WindowsSubstrate] = None
    fusion_processes: List[MetaLayerProcess] = field(default_factory=list)
    stack: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = {
            "attached": self.attached,
            "role": self.role,
            "fusion_os": self.fusion_os,
            "core": self.core,
            "attached_at": self.attached_at,
            "last_heartbeat": self.last_heartbeat,
            "substrate": self.substrate.to_dict() if self.substrate else None,
            "fusion_processes": [p.to_dict() for p in self.fusion_processes],
            "stack": self.stack,
            "architecture": {
                "substrate": "Windows NT (Host)",
                "meta_layer": "Fusion Hero OS v1.2",
                "pattern": "Meta-Layer über Substrat — kein Ersatz von Windows",
            },
        }
        return d


_SUBSTRATE_CACHE: Optional[WindowsSubstrate] = None
_SUBSTRATE_TS: float = 0.0
_PROCESS_CACHE: List[MetaLayerProcess] = []
_PROCESS_TS: float = 0.0
_internal_backend = False


def set_internal_backend_context(active: bool) -> None:
    global _internal_backend
    _internal_backend = active


def _read_state_file() -> dict:
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_state_file(data: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    existing = _read_state_file()
    merged = {**existing, **data, "updated_at": time.time()}
    STATE_FILE.write_text(json.dumps(merged, indent=2, default=str), encoding="utf-8")


def scan_windows_substrate(use_cache: bool = True) -> WindowsSubstrate:
    global _SUBSTRATE_CACHE, _SUBSTRATE_TS
    now = time.time()
    if use_cache and _SUBSTRATE_CACHE and (now - _SUBSTRATE_TS) < _SUBSTRATE_TTL:
        return _SUBSTRATE_CACHE

    import psutil

    uname = platform.uname()
    vm = psutil.virtual_memory()
    logical = psutil.cpu_count(logical=True) or 0
    physical = psutil.cpu_count(logical=False) or logical

    prev = _read_state_file()
    cached_sub = prev.get("substrate") or {}
    edition = cached_sub.get("edition", "")
    build = cached_sub.get("build", "")
    if not edition:
        edition = platform.platform()

    boot_time = None
    try:
        boot_time = psutil.boot_time()
    except Exception:
        pass

    substrate = WindowsSubstrate(
        platform=uname.system or "Windows",
        edition=edition,
        release=uname.release or "",
        version=uname.version or "",
        build=build,
        hostname=uname.node or "",
        username=os.getenv("USERNAME", ""),
        arch=uname.machine or "",
        logical_cpus=logical,
        physical_cpus=physical,
        ram_gb=round(vm.total / (1024 ** 3), 2),
        boot_time=boot_time,
    )
    _SUBSTRATE_CACHE = substrate
    _SUBSTRATE_TS = now
    return substrate


def scan_fusion_processes(use_cache: bool = True) -> List[MetaLayerProcess]:
    global _PROCESS_CACHE, _PROCESS_TS
    now = time.time()
    if use_cache and _PROCESS_CACHE and (now - _PROCESS_TS) < _PROCESS_TTL:
        return _PROCESS_CACHE

    import psutil

    patterns = {
        "backend": "uvicorn app:app",
        "workspace": "workspace.py",
        "mainframe_boot": "heroic_core_mainframe",
    }
    found: List[MetaLayerProcess] = []
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            cmdline = " ".join(proc.info.get("cmdline") or [])
            if "fusion-hero-os" not in cmdline.lower() and "dashboard" not in cmdline.lower():
                if not any(p in cmdline for p in patterns.values()):
                    continue
            role = "fusion"
            for r, pat in patterns.items():
                if pat in cmdline:
                    role = r
                    break
            found.append(MetaLayerProcess(
                name=proc.info.get("name") or "python",
                pid=proc.info.get("pid") or 0,
                role=role,
                cmdline=cmdline[:240],
            ))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    _PROCESS_CACHE = found
    _PROCESS_TS = now
    return found


def probe_stack_health(
    backend_url: str = "http://127.0.0.1:8000",
    workspace_url: str = "http://127.0.0.1:8080",
    mainframe_loaded: bool = False,
    skip_http: bool = False,
) -> Dict[str, Any]:
    stack: Dict[str, Any] = {
        "backend_url": backend_url,
        "workspace_url": workspace_url,
        "backend_online": False,
        "workspace_online": False,
        "mainframe_loaded": mainframe_loaded,
    }
    if skip_http or _internal_backend:
        stack["backend_online"] = True
        return stack

    import urllib.request
    try:
        with urllib.request.urlopen(f"{backend_url}/api/metrics", timeout=1) as resp:
            stack["backend_online"] = resp.status == 200
    except Exception:
        pass
    try:
        with urllib.request.urlopen(workspace_url, timeout=1) as resp:
            stack["workspace_online"] = resp.status == 200
    except Exception:
        pass
    return stack


def attach_meta_layer(
    backend_url: str = "http://127.0.0.1:8000",
    workspace_url: str = "http://127.0.0.1:8080",
    tune_substrate: bool = True,
) -> MetaLayerState:
    """Registriert Fusion als Meta-Layer über dem Windows-Substrat."""
    prev = _read_state_file()
    now = time.time()
    substrate_tune = None
    if tune_substrate:
        try:
            from windows_perf_tuner import apply_substrate_tuning
            substrate_tune = apply_substrate_tuning(power=True, dedupe=False, priority=True, env=True)
        except Exception:
            substrate_tune = {"error": "substrate_tune_failed"}
    substrate = scan_windows_substrate()
    processes = scan_fusion_processes()
    stack = probe_stack_health(backend_url, workspace_url, skip_http=_internal_backend)
    if substrate_tune:
        stack["substrate_tune"] = {
            "applied": substrate_tune.get("applied_count", 0),
            "power": (substrate_tune.get("scan") or {}).get("power_plan", {}).get("name"),
        }

    state = MetaLayerState(
        attached=True,
        attached_at=prev.get("attached_at") or now,
        last_heartbeat=now,
        substrate=substrate,
        fusion_processes=processes,
        stack=stack,
    )
    _write_state_file(state.to_dict())
    return state


def get_meta_layer_status(
    backend_url: str = "http://127.0.0.1:8000",
    workspace_url: str = "http://127.0.0.1:8080",
    light: bool = False,
    mainframe_loaded: bool = False,
) -> MetaLayerState:
    prev = _read_state_file()
    if light:
        cached_sub = prev.get("substrate")
        substrate = None
        if cached_sub:
            substrate = WindowsSubstrate(
                **{k: cached_sub.get(k) for k in WindowsSubstrate.__dataclass_fields__}
            )
        if substrate is None:
            substrate = scan_windows_substrate(use_cache=True)
        processes = prev.get("fusion_processes") or []
        proc_objs = [
            MetaLayerProcess(**{k: p.get(k) for k in MetaLayerProcess.__dataclass_fields__})
            for p in processes[:6]
        ] if processes else []
        stack = probe_stack_health(
            backend_url, workspace_url,
            mainframe_loaded=mainframe_loaded,
            skip_http=True,
        )
    else:
        substrate = scan_windows_substrate(use_cache=True)
        processes = scan_fusion_processes(use_cache=True)
        proc_objs = processes
        stack = probe_stack_health(
            backend_url, workspace_url,
            mainframe_loaded=mainframe_loaded,
            skip_http=_internal_backend,
        )

    attached = bool(
        prev.get("attached")
        or stack.get("backend_online")
        or len(proc_objs) > 0
    )
    return MetaLayerState(
        attached=attached,
        attached_at=prev.get("attached_at"),
        last_heartbeat=time.time(),
        substrate=substrate,
        fusion_processes=proc_objs if light else processes,
        stack=stack,
    )


_meta_singleton: Optional[MetaLayerState] = None


def heartbeat_meta_layer() -> MetaLayerState:
    global _meta_singleton
    _meta_singleton = attach_meta_layer()
    return _meta_singleton