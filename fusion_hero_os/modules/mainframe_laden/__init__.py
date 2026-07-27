"""mainframe_laden — Permanent Auto-Load (P1 wiring, no longer a stub).

Loads the package registry (and optionally the 03_Code module registry)
so the Heroic Core stays addressable after process start.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

MODULE_ID = "mainframe_laden"
PLATFORM = "10.0.0"


def status() -> dict[str, Any]:
    return {
        "module": MODULE_ID,
        "stub": False,
        "platform_version": PLATFORM,
        "role": "permanent_auto_load",
        "ok": True,
    }


def load_all(include_code_registry: bool = True) -> dict[str, Any]:
    """Load fusion_hero_os Registry + optional 03_Code module_registry probe."""
    report: dict[str, Any] = {
        "module": MODULE_ID,
        "stub": False,
        "package_registry": {},
        "code_registry": None,
        "ok": True,
        "errors": [],
    }
    try:
        from fusion_hero_os.registry import Registry

        reg = Registry()
        specs = reg.load_all()
        report["package_registry"] = {
            name: {
                "status": s.status.value,
                "required": s.required,
                "error": s.error,
            }
            for name, s in specs.items()
        }
        report["package_loaded"] = sum(
            1 for s in specs.values() if s.status.value == "loaded"
        )
    except Exception as exc:  # noqa: BLE001
        report["ok"] = False
        report["errors"].append(f"package_registry: {exc}")

    if include_code_registry:
        try:
            code_root = Path(__file__).resolve().parents[3] / "03_Code"
            if str(code_root) not in __import__("sys").path:
                __import__("sys").path.insert(0, str(code_root))
            from core import module_registry as mr  # type: ignore

            if hasattr(mr, "status_all"):
                report["code_registry"] = mr.status_all()
            elif hasattr(mr, "list_modules"):
                report["code_registry"] = {"modules": mr.list_modules()}
            else:
                report["code_registry"] = {"available": True, "api": "partial"}
        except Exception as exc:  # noqa: BLE001
            report["errors"].append(f"code_registry: {exc}")

    return report


class MainframeLadenModule:
    """BaseModule-compatible adapter (dispatcher-friendly)."""

    name = MODULE_ID

    def process(self, payload: Any = None) -> dict[str, Any]:
        include = True
        if isinstance(payload, dict) and "include_code_registry" in payload:
            include = bool(payload["include_code_registry"])
        return load_all(include_code_registry=include)

    def propose_evolution(self, context: Any = None) -> None:
        return None
