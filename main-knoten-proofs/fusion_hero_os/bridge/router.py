"""IPC request router — dispatches to fusion_hero_os + v8 core."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger("fusion_hero_os.bridge.router")

REPO_ROOT = Path(__file__).resolve().parents[2]
CODE_DIR = REPO_ROOT / "03_Code"

# Protocol constants (mirrored from kernel/bridge/protocol.py)
MSG_PING = 0x01
MSG_DISPATCH = 0x10
MSG_MATH_STATUS = 0x20
MSG_ORCHESTRATOR_STATUS = 0x21
MSG_LIST_MODULES = 0x22


def _json_safe(obj: Any) -> Any:
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if hasattr(obj, "to_dict") and callable(obj.to_dict):
        return _json_safe(obj.to_dict())
    if hasattr(obj, "__dataclass_fields__"):
        from dataclasses import asdict
        return _json_safe(asdict(obj))
    if isinstance(obj, dict):
        return {str(k): _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(v) for v in obj]
    if hasattr(obj, "value"):  # Enum
        return obj.value
    return str(obj)


def route_dispatch(module: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    from fusion_hero_os.core.dispatcher import build_default_dispatcher

    dispatcher = build_default_dispatcher()
    available = dispatcher.list_modules()
    if module not in available:
        return {
            "ok": False,
            "error": f"module not registered: {module}",
            "available": available,
        }
    try:
        result = _json_safe(dispatcher.dispatch(module, payload or {}))
        return {"ok": True, "module": module, "result": result}
    except Exception as exc:
        logger.exception("dispatch failed for %s", module)
        return {"ok": False, "module": module, "error": str(exc)}


def _v8_import(fn_name: str) -> Dict[str, Any]:
    if str(CODE_DIR) not in sys.path:
        sys.path.insert(0, str(CODE_DIR))
    from core import v8_core_bridge

    return getattr(v8_core_bridge, fn_name)()


def route_list_modules() -> Dict[str, Any]:
    from fusion_hero_os.core.dispatcher import build_default_dispatcher

    return {"ok": True, "modules": build_default_dispatcher().list_modules()}


def handle_ipc_message(msg_type: int, payload: bytes) -> Dict[str, Any]:
    body: Dict[str, Any] = {}
    if payload:
        try:
            body = json.loads(payload.decode("utf-8"))
        except json.JSONDecodeError:
            body = {"raw": payload.decode("utf-8", errors="replace")}

    if msg_type == MSG_PING:
        return {"ok": True, "pong": True, "transport": "fhos_ipc_v1"}

    if msg_type == MSG_LIST_MODULES:
        return route_list_modules()

    if msg_type == MSG_MATH_STATUS:
        return _v8_import("math_status")

    if msg_type == MSG_ORCHESTRATOR_STATUS:
        return _v8_import("orchestrator_status")

    if msg_type == MSG_DISPATCH:
        module = str(body.get("module", ""))
        return route_dispatch(module, body.get("payload"))

    return {"ok": False, "error": f"unknown msg_type: 0x{msg_type:02X}"}