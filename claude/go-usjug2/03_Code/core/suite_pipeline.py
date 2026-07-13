"""Programmatic 8-layer COEVO pipeline (merged from suite/process_layers.py)."""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from ghosthunt_hook import ghosthunt_hook

_SUITE = Path(__file__).resolve().parent.parent / "suite"
_LAYERS = _SUITE / "layers"
_LOG_PATH = _SUITE / "coevo_evolution_log.json"


def _run_layer_script(py_path: Path, timeout: int = 12) -> Dict[str, Any]:
    try:
        proc = subprocess.run(
            [sys.executable, str(py_path)],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(_SUITE),
        )
        return {
            "script": py_path.name,
            "returncode": proc.returncode,
            "stdout": (proc.stdout or "").strip()[:500],
            "stderr": (proc.stderr or "").strip()[:200],
            "ok": proc.returncode == 0,
        }
    except Exception as exc:
        return {"script": py_path.name, "ok": False, "error": str(exc)[:200]}


def run_full_pipeline(
    *,
    timeout_per_layer: int = 12,
    ghost_steps: int = 10,
    persist_log: bool = True,
    verbose: bool = False,
) -> Dict[str, Any]:
    """Run all suite layers with coevolutionary ghosthunt hooks between layers."""
    if not _LAYERS.exists():
        return {"ok": False, "error": f"layers dir missing: {_LAYERS}"}

    layer_names = sorted(d.name for d in _LAYERS.iterdir() if d.is_dir())
    coevo_state: Optional[Dict[str, Any]] = None
    coevo_history: List[Dict[str, Any]] = []
    layer_results: List[Dict[str, Any]] = []

    for layer_name in layer_names:
        layer_dir = _LAYERS / layer_name
        scripts = sorted(layer_dir.glob("*.py"))
        runs = [_run_layer_script(p, timeout=timeout_per_layer) for p in scripts]
        context = {
            "events": 10 + (hash(layer_name) % 15),
            "queue": 3,
            "cpu": 25 + (hash(layer_name) % 20),
        }
        snap, coevo_state = ghosthunt_hook(
            layer_name,
            context=context,
            use_springloop=True,
            steps=ghost_steps,
            coevo_state=coevo_state,
            verbose=verbose,
        )
        if coevo_state:
            coevo_state = dict(coevo_state)
            coevo_state["timestamp"] = datetime.now(timezone.utc).isoformat()
            coevo_history.append(coevo_state)
        layer_results.append({
            "layer": layer_name,
            "scripts": runs,
            "ghost_snapshot": {
                "distance": snap.get("distance"),
                "lambda": snap.get("lambda"),
                "emerged": coevo_state.get("emerged") if coevo_state else 0,
            },
        })

    total_emerged = sum(item.get("emerged", 0) for item in coevo_history)
    energies = [float(item.get("springloop_energy", 0)) for item in coevo_history]
    avg_energy = sum(energies) / len(energies) if energies else 0.0

    if persist_log and coevo_history:
        _LOG_PATH.write_text(json.dumps(coevo_history, indent=2), encoding="utf-8")

    return {
        "ok": True,
        "layers_processed": len(layer_names),
        "layer_results": layer_results,
        "coevo_history": coevo_history,
        "summary": {
            "total_emerged": total_emerged,
            "avg_springloop_energy": round(avg_energy, 4),
            "log_path": str(_LOG_PATH) if persist_log and coevo_history else None,
        },
        "ts": datetime.now(timezone.utc).isoformat(),
    }


def pipeline_status() -> Dict[str, Any]:
    """Lightweight status without running the full pipeline."""
    layer_names = []
    if _LAYERS.exists():
        layer_names = sorted(d.name for d in _LAYERS.iterdir() if d.is_dir())
    return {
        "layers_dir": str(_LAYERS),
        "layer_count": len(layer_names),
        "layers": layer_names,
        "log_exists": _LOG_PATH.exists(),
        "log_path": str(_LOG_PATH),
    }