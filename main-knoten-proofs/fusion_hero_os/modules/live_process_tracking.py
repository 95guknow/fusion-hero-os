"""LiveProcessTrackingCoreModule — Status-Tracking für benannte Vorgänge.

Reines In-Memory-Tracking (kein Prozess-/Thread-Management): hält für
benannte Vorgänge Start-/Ende-Zeitpunkt und Status fest, z.B. um im
Dashboard laufende Dispatcher-Aufträge sichtbar zu machen.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fusion_hero_os.core.base_module import BaseModule


@dataclass
class TrackedProcess:
    name: str
    status: str  # "running" | "completed" | "failed"
    started_at: str
    ended_at: Optional[str] = None
    meta: Dict[str, Any] = field(default_factory=dict)


class LiveProcessTrackingCoreModule(BaseModule):
    """``process(payload)`` erwartet ``{"name": str, "action": "start" |
    "complete" | "fail" | "status", "meta": dict?}``.
    """

    def __init__(self) -> None:
        super().__init__()
        self._processes: Dict[str, TrackedProcess] = {}

    def process(self, payload: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        payload = payload or {}
        name = payload.get("name")
        if not name:
            raise ValueError("payload['name'] ist erforderlich.")
        action = payload.get("action", "status")
        now = datetime.now(timezone.utc).isoformat()

        if action == "start":
            self._processes[name] = TrackedProcess(
                name=name, status="running", started_at=now, meta=payload.get("meta", {})
            )
        elif action in ("complete", "fail"):
            proc = self._processes.get(name)
            if proc is None:
                raise KeyError(f"Kein laufender Vorgang '{name}' bekannt.")
            proc.status = "completed" if action == "complete" else "failed"
            proc.ended_at = now
        elif action != "status":
            raise ValueError(f"Unbekannte action: {action!r}")

        proc = self._processes.get(name)
        return asdict(proc) if proc else None

    def snapshot(self) -> Dict[str, Dict[str, Any]]:
        """Status aller bekannten Vorgänge (nur Lesezugriff)."""
        return {name: asdict(p) for name, p in self._processes.items()}
