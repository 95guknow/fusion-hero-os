# -*- coding: utf-8 -*-
"""resource_guardian_routes.py — API + GUI-Anbindung fuer local_infrastructure_kernel.

Vertrag: workstation/contracts/local_infrastructure_kernel.v1.json
Kernlogik (Probing/Schwellenwerte/Eskalation): src/normal_os/core/local_infrastructure_kernel.py
(lokal implementiert, siehe IDE/GUI-Zustaendigkeitstrennung - diese Datei ist
nur die API/GUI-Schicht, analog api_extensions.py/vr_routes.py).

Transport gemaess Contract: bevorzugt python_import (live, direkter Aufruf);
faellt auf status_file zurueck (~/.fusion/local-infrastructure-kernel/status.json),
falls das Modul in diesem Prozess nicht importierbar ist (z.B. anderer Host/
andere PYTHONPATH als der Windows-Mainframe) - liefert dann den letzten
persistierten Zyklus statt "nicht verfuegbar", wo moeglich.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel

BASE = Path(__file__).parent

# Contract: PYTHONPATH=src/normal_os/core (bare "import local_infrastructure_kernel")
_CORE_DIR = str(Path(__file__).resolve().parents[2] / "core")
if _CORE_DIR not in sys.path:
    sys.path.insert(0, _CORE_DIR)

try:
    import local_infrastructure_kernel as lik
except Exception:
    lik = None

router = APIRouter()


@router.get("/resources", response_class=HTMLResponse)
async def resources_page():
    """GUI fuer den local_infrastructure_kernel (RAM/Disk C:/Tailscale/Services)."""
    path = BASE / "templates" / "resources.html"
    if path.exists():
        return FileResponse(path)
    return HTMLResponse("<h1>resources.html not found</h1>", status_code=404)


def _status_file_fallback() -> Optional[Dict[str, Any]]:
    """Status-File-Transport gemaess Contract, falls python_import nicht verfuegbar ist."""
    custom = os.getenv("FUSION_LOCAL_KERNEL_STATE")
    base = Path(custom) if custom else Path.home() / ".fusion" / "local-infrastructure-kernel"
    status_file = base / "status.json"
    if not status_file.exists():
        return None
    try:
        return json.loads(status_file.read_text(encoding="utf-8"))
    except Exception:
        return None


def _unavailable() -> Dict[str, Any]:
    cached = _status_file_fallback()
    if cached:
        return {**cached, "note": "python_import fehlgeschlagen, status_file-Fallback verwendet"}
    return {
        "available": False,
        "reason": "nicht verfügbar",
        "module": "local_infrastructure_kernel",
        "contract_version": "1.0",
        "expected_module": "src/normal_os/core/local_infrastructure_kernel.py",
        "expected_status_file": "~/.fusion/local-infrastructure-kernel/status.json",
        "spec": "workstation/contracts/local_infrastructure_kernel.v1.json",
    }


@router.get("/api/resources/status")
async def resources_status():
    if not lik:
        return _unavailable()
    return lik.status()


@router.get("/api/resources/probe")
async def resources_probe(timeout: float = 4.0):
    if not lik:
        return _unavailable()
    return lik.probe(timeout=timeout)


@router.get("/api/resources/evaluate")
async def resources_evaluate(timeout: float = 4.0):
    if not lik:
        return _unavailable()
    return lik.evaluate(lik.probe(timeout=timeout))


class RunCyclePayload(BaseModel):
    timeout: float = 4.0
    apply_actions: bool = False


@router.post("/api/resources/run-cycle")
async def resources_run_cycle(payload: RunCyclePayload):
    if not lik:
        return _unavailable()
    return lik.run_cycle(timeout=payload.timeout, apply_actions=payload.apply_actions)


@router.get("/api/resources/cached")
async def resources_cached():
    """Letzter persistierter Zyklus (status.json), ohne einen neuen Probe/Cycle auszuloesen."""
    if lik:
        cached = lik.read_cached_state()
        if cached:
            return cached
        return {"available": True, "cached": False, "note": "noch kein Zyklus gelaufen"}
    fallback = _status_file_fallback()
    return fallback or _unavailable()


@router.get("/api/resources/thresholds")
async def resources_thresholds():
    if not lik:
        return _unavailable()
    return lik.load_thresholds()
