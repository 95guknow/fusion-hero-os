# medienserver_bridge.py — Grok Medienserver (Google Drive) Status & Delta-Vergleich

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

_REPO = Path(__file__).resolve().parents[2]
_DEFAULT_MS = Path(r"G:\Meine Ablage\Fusion_Hero_OS_v1.2")
_RELATIVE_MS = "Fusion_Hero_OS_v1.2"


def _resolve_default_medienserver() -> Path:
    env = os.getenv("FUSION_MEDIENSERVER")
    if env:
        return Path(env)
    home = Path.home()
    candidates = [
        Path(r"G:\Meine Ablage") / _RELATIVE_MS,
        home / "Google Drive-Streaming" / "Meine Ablage" / _RELATIVE_MS,
        home / "Google Drive" / "Meine Ablage" / _RELATIVE_MS,
    ]
    for c in candidates:
        if c.parent.exists():
            return c
    return _DEFAULT_MS


def medienserver_path() -> Path:
    return _resolve_default_medienserver()


def manifest() -> Dict[str, Any]:
    path = medienserver_path() / "GROK_ONLINE_MANIFEST.json"
    if not path.exists():
        return {"exists": False, "path": str(path)}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        data["exists"] = True
        data["path"] = str(path)
        return data
    except Exception as exc:
        return {"exists": False, "path": str(path), "error": str(exc)}


def _list_py_files(base: Path, limit: int = 200) -> List[str]:
    if not base.exists():
        return []
    out: List[str] = []
    for p in base.rglob("*.py"):
        if "__pycache__" in p.parts or "venv" in p.parts:
            continue
        try:
            out.append(str(p.relative_to(base)).replace("\\", "/"))
        except ValueError:
            continue
        if len(out) >= limit:
            break
    return sorted(out)


def compare_with_repo() -> Dict[str, Any]:
    ms = medienserver_path()
    repo = _REPO
    ms_core = _list_py_files(ms / "03_Code" / "Dashboard")
    repo_core = _list_py_files(repo / "03_Code" / "Dashboard")
    ms_only = sorted(set(ms_core) - set(repo_core))
    repo_only = sorted(set(repo_core) - set(ms_core))
    return {
        "medienserver": str(ms),
        "medienserver_available": ms.exists(),
        "dashboard_py_medienserver": len(ms_core),
        "dashboard_py_repo": len(repo_core),
        "only_on_medienserver": ms_only[:30],
        "only_in_repo": repo_only[:30],
        "qb_qubo_root": (repo / "qb_qubo.py").exists(),
        "manifest": manifest(),
    }


def status() -> Dict[str, Any]:
    ms = medienserver_path()
    return {
        "module": "medienserver_bridge",
        "path": str(ms),
        "available": ms.exists(),
        "manifest": manifest(),
        "compare": compare_with_repo(),
    }