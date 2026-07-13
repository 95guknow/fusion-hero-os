# -*- coding: utf-8 -*-
"""Boot-Optimizer — größter Flaschenhals: synchroner Full-Boot + Robocopy."""
from __future__ import annotations

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

ROOT = Path(__file__).resolve().parents[2]
def _medienserver_path() -> Path:
    env = os.getenv("FUSION_MEDIENSERVER")
    if env:
        return Path(env)
    home = Path.home()
    rel = "Fusion_Hero_OS_v1.2"
    for parent in (
        Path(r"G:\Meine Ablage"),
        home / "Google Drive-Streaming" / "Meine Ablage",
        home / "Google Drive" / "Meine Ablage",
    ):
        if parent.exists():
            return parent / rel
    return Path(r"G:\Meine Ablage") / rel


MEDIENSERVER = _medienserver_path()
MANIFEST = MEDIENSERVER / "GROK_ONLINE_MANIFEST.json"

FAST_BOOT_STEPS = int(os.getenv("FUSION_FAST_BOOT_STEPS", "600"))
FULL_BOOT_STEPS = int(os.getenv("FUSION_BOOT_STEPS", "2000"))
SYNC_MAX_AGE_MIN = int(os.getenv("FUSION_SYNC_MAX_AGE_MIN", "60"))


def medienserver_sync_needed(max_age_min: Optional[int] = None) -> bool:
    """Robocopy nur wenn Manifest fehlt, veraltet oder FORCE."""
    if os.getenv("FUSION_FORCE_SYNC", "0") == "1":
        return True
    if not MEDIENSERVER.parent.exists():
        return False
    if not MANIFEST.exists():
        return True
    try:
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        synced_at = data.get("synced_at", "")
        if not synced_at:
            return True
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
            try:
                ts = datetime.strptime(synced_at, fmt)
                age_min = (datetime.now() - ts).total_seconds() / 60.0
                return age_min >= (max_age_min or SYNC_MAX_AGE_MIN)
            except ValueError:
                continue
    except Exception:
        return True
    return False


def sync_status() -> dict:
    needed = medienserver_sync_needed()
    last = None
    if MANIFEST.exists():
        try:
            last = json.loads(MANIFEST.read_text(encoding="utf-8")).get("synced_at")
        except Exception:
            pass
    return {
        "needed": needed,
        "last_synced_at": last,
        "max_age_min": SYNC_MAX_AGE_MIN,
        "force": os.getenv("FUSION_FORCE_SYNC", "0") == "1",
        "path": str(MEDIENSERVER),
    }


def boot_plan(mainframe_loaded: bool = False, force: bool = False) -> dict:
    """Entscheidet Fast vs Heavy Boot — API sofort, QUBO/Sync im Hintergrund."""
    if mainframe_loaded and not force:
        return {"phase": "cached", "mainframe_steps": 0, "sync": False, "note": "Registry bereits geladen"}
    if force:
        return {"phase": "full", "mainframe_steps": FULL_BOOT_STEPS, "sync": True, "note": "Erzwungener Full-Boot"}
    return {
        "phase": "staged",
        "mainframe_steps": FAST_BOOT_STEPS,
        "sync": medienserver_sync_needed(),
        "note": "Fast-Boot zuerst, Heavy optional im Hintergrund",
    }


def optimize_steps(requested: int, phase: str) -> int:
    if phase == "cached":
        return 0
    if phase == "fast" or phase == "staged":
        return min(requested, FAST_BOOT_STEPS)
    return requested