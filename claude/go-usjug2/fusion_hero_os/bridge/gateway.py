"""High-level IPC Gateway for Dashboard and launcher."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger("fusion_hero_os.bridge.gateway")

REPO_ROOT = Path(__file__).resolve().parents[2]
_BRIDGE_DIR = REPO_ROOT / "kernel" / "bridge"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

_gateway: Optional["IPCGateway"] = None


class IPCGateway:
    """Unified access: TCP IPC server, C unix server, or in-process."""

    def __init__(self) -> None:
        self._client = None
        self._transport = "unknown"
        self._connect()

    def _connect(self) -> None:
        from kernel.bridge.fhos_ipc_client import FusionHeroIPCClient, Transport, auto_client

        try:
            self._client = auto_client()
            self._transport = (
                "in_process"
                if self._client.transport.value == "in_process"
                else self._client.transport.value
            )
        except Exception as exc:
            logger.warning("IPC connect failed, in-process fallback: %s", exc)
            self._client = FusionHeroIPCClient(transport=Transport.IN_PROCESS)
            self._transport = "in_process"

    def status(self) -> Dict[str, Any]:
        try:
            ping = self._client.ping()
            data = ping.get("data", ping)
            modules = self._client.list_modules()
            mod_data = modules.get("data", modules)
            return {
                "ok": True,
                "transport": self._transport,
                "ping": data,
                "module_count": len(mod_data.get("modules", [])),
                "modules": mod_data.get("modules", []),
                "deepened_modules": [
                    "TimespaceTokenCoreModule",
                    "HeroicLLMEAOrchestrator",
                    "HeroicImageOrchestrator",
                ],
            }
        except Exception as exc:
            return {"ok": False, "transport": self._transport, "error": str(exc)}

    def dispatch(self, module: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            result = self._client.dispatch(module, payload)
            return result.get("data", result) if isinstance(result, dict) else result
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def math_status(self) -> Dict[str, Any]:
        r = self._client.math_status()
        return r.get("data", r)

    def orchestrator_status(self) -> Dict[str, Any]:
        r = self._client.orchestrator_status()
        return r.get("data", r)


def get_ipc_gateway() -> IPCGateway:
    global _gateway
    if _gateway is None:
        _gateway = IPCGateway()
    return _gateway