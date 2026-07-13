# first_install_bootstrap.py — Einmalige Erstinstallation: alle Dienste verbinden

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Callable, Dict, List

_ROOT = Path(__file__).resolve().parents[2]
_MARKER_DIR = _ROOT / ".fusion"
_MARKER_FILE = _MARKER_DIR / "first_install.done"


def is_first_install_pending() -> bool:
    if os.getenv("FUSION_FORCE_FIRST_INSTALL", "0") == "1":
        return True
    return not _MARKER_FILE.exists()


def _step(name: str, fn: Callable[[], Any]) -> Dict[str, Any]:
    try:
        result = fn()
        return {"step": name, "ok": True, "result": _safe(result)}
    except Exception as exc:
        return {"step": name, "ok": False, "error": str(exc)}


def _safe(obj: Any) -> Any:
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {str(k): _safe(v) for k, v in list(obj.items())[:40]}
    if isinstance(obj, (list, tuple)):
        return [_safe(x) for x in obj[:25]]
    return str(obj)[:300]


def run(force: bool = False) -> Dict[str, Any]:
    """Verbindet einmalig alle wichtigen Dienste (oder bei force erneut)."""
    if not force and not is_first_install_pending():
        return {
            "status": "skipped",
            "reason": "first_install already completed",
            "marker": str(_MARKER_FILE),
        }

    steps: List[Dict[str, Any]] = []
    started = time.time()

    def _autoload():
        from heroic_orchestration import auto_load, ensure_agents_loaded

        ensure_agents_loaded(force=True)
        return auto_load(phase="full", force=True)

    def _modules():
        from module_registry import load_all

        return load_all(force=True)

    def _supabase():
        import sys

        dash = _ROOT / "03_Code" / "Dashboard"
        if str(dash) not in sys.path:
            sys.path.insert(0, str(dash))
        import supabase_client as supa

        return supa.status(do_probe=True)

    def _provider():
        from provider_switcher import select_provider, status

        active = select_provider(force_probe=True)
        return {"active": active, **status()}

    def _claude_science():
        from claude_science import status as science_status, probe as science_probe

        info = science_status()
        if info.get("configured"):
            info["probe"] = science_probe()
        return info

    def _substrate():
        from windows_substrate import get_substrate

        sub = get_substrate()
        return {
            "attach": sub.attach(),
            "tune": sub.tune_substrate(),
            "cyber": sub.activate_cyber_layer(),
        }

    def _performance():
        out: Dict[str, Any] = {}
        try:
            from resource_coupler import get_resource_coupler

            coupler = get_resource_coupler()
            if coupler:
                out["coupler"] = coupler.couple_once()
        except Exception as exc:
            out["coupler_error"] = str(exc)
        try:
            from gpu_compute_booster import get_gpu_compute_booster

            booster = get_gpu_compute_booster()
            if booster:
                out["gpu_boost"] = booster.boost_once()
        except Exception as exc:
            out["gpu_boost_error"] = str(exc)
        try:
            from memory_guard import get_memory_guard

            guard = get_memory_guard()
            if guard:
                out["memory_guard"] = guard.relieve_once()
        except Exception as exc:
            out["memory_guard_error"] = str(exc)
        return out

    def _connectors():
        import sys

        ref = _ROOT / "03_Code" / "reference"
        if str(ref) not in sys.path:
            sys.path.insert(0, str(ref))
        from connectors import ConnectorRegistry

        reg = ConnectorRegistry.default()
        avail = reg.available()
        return {"connectors": avail, "any_live": any(avail.values())}

    def _agent_control():
        from agent_control import status as control_status, verify_text

        info = control_status()
        probe = verify_text("[model] Bootstrap-Kontrollprobe: System online.", {"dom": "Info", "geltung": "model"})
        return {"status": info, "probe_passed": probe.get("passed")}

    for name, fn in (
        ("autoload_full", _autoload),
        ("load_all_modules", _modules),
        ("supabase_connect", _supabase),
        ("provider_switcher", _provider),
        ("claude_science", _claude_science),
        ("agent_control", _agent_control),
        ("windows_substrate", _substrate),
        ("performance_stack", _performance),
        ("service_connectors", _connectors),
    ):
        steps.append(_step(name, fn))

    ok_count = sum(1 for s in steps if s.get("ok"))
    report = {
        "status": "completed" if ok_count == len(steps) else "partial",
        "steps_ok": ok_count,
        "steps_total": len(steps),
        "steps": steps,
        "duration_ms": round((time.time() - started) * 1000, 1),
        "ts": time.time(),
    }

    _MARKER_DIR.mkdir(parents=True, exist_ok=True)
    _MARKER_FILE.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report