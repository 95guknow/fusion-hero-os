# windows_substrate.py — Meta-Layer, Substrat-Tuning, Cyber Layer

from __future__ import annotations

import json
import os
import platform
import socket
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List

_STATE_DIR = Path(os.getenv("FUSION_STATE_DIR", Path.home() / ".fusion-hero-os"))
_STATE_FILE = _STATE_DIR / "meta_layer_state.json"


class WindowsSubstrate:
    def __init__(self) -> None:
        self.attached = False
        self.cyber_active = False
        self._load_state()

    def _load_state(self) -> None:
        if _STATE_FILE.exists():
            try:
                data = json.loads(_STATE_FILE.read_text(encoding="utf-8"))
                self.attached = bool(data.get("attached"))
                self.cyber_active = bool(data.get("cyber_active"))
            except Exception:
                pass

    def _save_state(self) -> None:
        _STATE_DIR.mkdir(parents=True, exist_ok=True)
        _STATE_FILE.write_text(json.dumps({
            "attached": self.attached,
            "cyber_active": self.cyber_active,
            "updated": time.time(),
        }, indent=2), encoding="utf-8")

    def scan(self) -> Dict[str, Any]:
        import psutil
        power = "unknown"
        try:
            r = subprocess.run(
                ["powercfg", "/getactivescheme"],
                capture_output=True, text=True, timeout=5,
            )
            power = r.stdout.strip() or "unknown"
        except Exception:
            pass
        return {
            "hostname": socket.gethostname(),
            "os": platform.platform(),
            "python": platform.python_version(),
            "logical_cpus": psutil.cpu_count(logical=True),
            "ram_total_gb": round(psutil.virtual_memory().total / (1024 ** 3), 2),
            "power_plan": {"name": power},
            "fusion_profile": os.getenv("FUSION_PROFILE", "admin"),
            "fusion_env": {k: v for k, v in os.environ.items() if k.startswith("FUSION_")},
        }

    def attach(self) -> Dict[str, Any]:
        self.attached = True
        self._save_state()
        scan = self.scan()
        return {
            "status": "attached",
            "substrate": scan,
            "meta_layer": "Fusion Hero OS v8",
            "stack": ["windows_nt", "fusion_hero_os", "heroic_core", "grok_intern"],
        }

    def tune_substrate(self) -> Dict[str, Any]:
        applied: List[str] = []
        try:
            subprocess.run(
                ["powercfg", "/setactive", "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"],
                capture_output=True, timeout=8,
            )
            applied.append("high_performance_power_plan")
        except Exception:
            pass
        os.environ["FUSION_PROFILE"] = "admin"
        os.environ["FUSION_PERFORMANCE_RATIO"] = "1.0"
        os.environ["FUSION_HYPERTHREADING"] = "1"
        applied.append("fusion_profile_admin")
        return {
            "status": "ok",
            "scan": self.scan(),
            "applied": applied,
            "applied_count": len(applied),
        }

    def activate_cyber_layer(self) -> Dict[str, Any]:
        self.cyber_active = True
        self._save_state()
        score = 72 + (10 if self.attached else 0) + (8 if os.getenv("FUSION_USE_GPU") == "1" else 0)
        return {
            "status": "active",
            "optimization_score": min(100, score),
            "visual": {"badge": "CYBER-LAYER-ON", "skin": os.getenv("FUSION_WINDOWS_SKIN", "synthwave")},
            "layers": ["substrate", "meta", "cyber", "heroic_core"],
        }

    def status(self) -> Dict[str, Any]:
        return {
            "attached": self.attached,
            "cyber_active": self.cyber_active,
            "substrate": self.scan(),
            "state_file": str(_STATE_FILE),
        }


_substrate: WindowsSubstrate | None = None


def get_substrate() -> WindowsSubstrate:
    global _substrate
    if _substrate is None:
        _substrate = WindowsSubstrate()
    return _substrate