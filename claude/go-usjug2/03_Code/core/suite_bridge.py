"""Bridge to cherry-picked suite tools (fusion, gpu, qubo) — status without side effects."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List

_SUITE = Path(__file__).resolve().parent.parent / "suite"
_CODE = Path(__file__).resolve().parent.parent


def _count_py(folder: Path) -> int:
    if not folder.is_dir():
        return 0
    return len(list(folder.glob("*.py")))


def suite_inventory() -> Dict[str, Any]:
    """Filesystem inventory of integrated suite modules."""
    areas = {
        "layers": "8-layer COEVO pipeline",
        "qubo": "QUBO miner/solver",
        "gpu": "GPU acceleration",
        "fusion": "Fusion experiments",
        "ghosthunting": "Geisterjagd hooks",
        "audio-bridge": "PC-to-phone audio",
        "tools": "Benchmarks/stress tests",
        "tests": "Suite tests",
    }
    modules: List[Dict[str, Any]] = []
    for name, desc in areas.items():
        path = _SUITE / name
        modules.append({
            "name": name,
            "description": desc,
            "path": str(path),
            "py_files": _count_py(path),
            "available": path.exists(),
        })
    return {
        "suite_root": str(_SUITE),
        "modules": modules,
        "total_py": sum(m["py_files"] for m in modules),
    }


def gpu_status() -> Dict[str, Any]:
    """Best-effort GPU probe (CuPy / PyTorch), no prints."""
    out: Dict[str, Any] = {"cupy": None, "torch": None, "fusion_env": {}}
    for k, v in sorted(os.environ.items()):
        if k.startswith("FUSION"):
            out["fusion_env"][k] = v
    try:
        import cupy as cp  # type: ignore

        out["cupy"] = {
            "version": cp.__version__,
            "cuda_available": bool(cp.cuda.is_available()),
        }
        if cp.cuda.is_available():
            out["cupy"]["device_count"] = int(cp.cuda.runtime.getDeviceCount())
    except Exception as exc:
        out["cupy"] = {"error": str(exc)[:120]}
    try:
        import torch  # type: ignore

        out["torch"] = {
            "cuda_available": bool(torch.cuda.is_available()),
        }
        if torch.cuda.is_available():
            out["torch"]["device"] = torch.cuda.get_device_name(0)
    except Exception as exc:
        out["torch"] = {"error": str(exc)[:120]}
    return out


def fusion_health(base_url: str = "http://127.0.0.1:8000", timeout: float = 4.0) -> Dict[str, Any]:
    """Probe local dashboard health (fusion_status pattern)."""
    result: Dict[str, Any] = {"base_url": base_url, "reachable": False}
    paths = ["/api/health", "/api/gui/status", "/api/autoload/status"]
    for path in paths:
        try:
            with urllib.request.urlopen(base_url + path, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            result[path] = data
            result["reachable"] = True
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
            result[path] = {"error": str(exc)[:120]}
    return result


def suite_status() -> Dict[str, Any]:
    """Combined suite + gpu + fusion health snapshot."""
    return {
        "inventory": suite_inventory(),
        "gpu": gpu_status(),
        "fusion_health": fusion_health(),
    }