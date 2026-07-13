# resource_workflow.py — Ressourcenbewusste Parallel-Steuerung für Subagent-/Track-Workflows

from __future__ import annotations

import os
from typing import Any, Dict, List

_RAM_SOFT = float(os.getenv("FUSION_RAM_SOFT_PCT", "78"))
_RAM_HARD = float(os.getenv("FUSION_RAM_HARD_PCT", "85"))
_CPU_HIGH = float(os.getenv("FUSION_CPU_LOAD_HIGH_PCT", "85"))


def snapshot() -> Dict[str, Any]:
    """Aktueller System-Snapshot (CPU, RAM, schwere Prozesse)."""
    out: Dict[str, Any] = {"cpu_pct": None, "ram_pct": None, "ram_avail_gb": None, "heavy_procs": []}
    try:
        import psutil

        out["cpu_pct"] = round(psutil.cpu_percent(interval=0.3), 1)
        mem = psutil.virtual_memory()
        out["ram_pct"] = round(mem.percent, 1)
        out["ram_avail_gb"] = round(mem.available / 1e9, 2)
        heavy: List[Dict[str, Any]] = []
        for p in psutil.process_iter(["name", "memory_info"]):
            info = p.info
            name = (info.get("name") or "").lower()
            if name not in ("python.exe", "llama-server.exe", "uvicorn"):
                continue
            rss_mb = round((info.get("memory_info").rss or 0) / 1e6, 0)
            if rss_mb >= 80 or name == "llama-server.exe":
                heavy.append({"name": info.get("name"), "rss_mb": rss_mb})
        out["heavy_procs"] = sorted(heavy, key=lambda x: x["rss_mb"], reverse=True)[:8]
    except Exception as exc:
        out["error"] = str(exc)
    return out


def recommend_workers(task_weight: str = "medium") -> Dict[str, Any]:
    """
    Empfiehlt parallele Worker/Subagents basierend auf Last.

    task_weight: light | medium | heavy
    """
    snap = snapshot()
    ram = snap.get("ram_pct") or 50.0
    cpu = snap.get("cpu_pct") or 30.0
    llama = any("llama" in (p.get("name") or "").lower() for p in snap.get("heavy_procs", []))

    if ram >= _RAM_HARD or cpu >= _CPU_HIGH:
        workers = 1
        mode = "serial"
        reason = "RAM/CPU Hard-Limit"
    elif ram >= _RAM_SOFT or llama:
        workers = 2 if task_weight == "light" else 1
        mode = "conservative"
        reason = "RAM soft oder llama-server aktiv"
    elif task_weight == "heavy":
        workers = 2
        mode = "balanced"
        reason = "schwere Tasks, Ressourcen OK"
    else:
        workers = 3 if task_weight == "light" else 2
        mode = "parallel"
        reason = "Ressourcen frei"

    return {
        "recommended_workers": workers,
        "mode": mode,
        "reason": reason,
        "snapshot": snap,
        "limits": {"ram_soft": _RAM_SOFT, "ram_hard": _RAM_HARD, "cpu_high": _CPU_HIGH},
    }


def status() -> Dict[str, Any]:
    rec = recommend_workers("medium")
    return {"module": "resource_workflow", **rec}