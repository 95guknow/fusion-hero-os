# -*- coding: utf-8 -*-
"""
Autoload Controller — status surface for post-reboot load orchestration.

Heavy lifting lives in ``scripts/autoload_controller.ps1`` and
``scripts/prepare_reboot_autoload.ps1``. This module only reads/writes
operator-local state and reports readiness (public-safe).

Geltung: Spezifikation (controller contract)
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

__all__ = ["STATE_PATH", "status", "public_status", "mark_ready"]

OP = Path.home() / ".fusion"
STATE_PATH = OP / "autoload_controller.json"
PLATFORM = "12.1.0"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load() -> Dict[str, Any]:
    if not STATE_PATH.is_file():
        return {
            "ok": False,
            "ready_for_reboot": False,
            "phase": "uninitialized",
            "platform_version": PLATFORM,
        }
    try:
        raw = STATE_PATH.read_text(encoding="utf-8-sig")
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {"ok": False, "error": "unreadable_state"}


def mark_ready(**extra: Any) -> Dict[str, Any]:
    OP.mkdir(parents=True, exist_ok=True)
    body = {
        "ok": True,
        "controller": "autoload_controller_v1",
        "platform_version": PLATFORM,
        "ready_for_reboot": True,
        "phase": "pre_reboot_ready",
        "hostname": os.environ.get("COMPUTERNAME") or "",
        "updated_at": _now(),
        **extra,
    }
    STATE_PATH.write_text(
        json.dumps(body, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return body


def public_status() -> Dict[str, Any]:
    d = _load()
    return {
        "ok": bool(d.get("ok", True)),
        "module": "autoload_controller",
        "platform_version": d.get("platform_version") or PLATFORM,
        "phase": d.get("phase"),
        "ready_for_reboot": bool(d.get("ready_for_reboot") or d.get("ready")),
        "ready": bool(d.get("ready") or d.get("ready_for_reboot")),
        "hostname": d.get("hostname"),
        "prepared_at": d.get("prepared_at") or d.get("updated_at"),
        "health_ok": d.get("health_ok"),
        "task_name": d.get("task_name"),
        "controller": d.get("controller") or "autoload_controller_v1",
        "state_path": str(STATE_PATH),
        "scripts": {
            "prepare": "scripts/prepare_reboot_autoload.ps1",
            "controller": "scripts/autoload_controller.ps1",
        },
    }


def status() -> Dict[str, Any]:
    return public_status()


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="Autoload controller status")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--mark-ready", action="store_true")
    args = ap.parse_args()
    if args.mark_ready:
        print(json.dumps(mark_ready(), indent=2, ensure_ascii=False))
        return 0
    print(json.dumps(status(), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
