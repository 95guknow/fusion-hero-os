"""PhoneLinkCoreModule — read-only Phone Link Integration für den Dispatcher."""

from __future__ import annotations

from typing import Any, Dict, Optional

from fusion_hero_os.core.base_module import BaseModule
from fusion_hero_os.integrations.phone_link.reader import PhoneLinkReader


class PhoneLinkCoreModule(BaseModule):
    """``process(payload)`` Aktionen:

    - ``status`` (default) — Verbindungs- und Sync-Übersicht
    - ``messages`` — letzte SMS (``limit`` optional)
    - ``conversations`` — letzte Konversationen (``limit`` optional)
    """

    def __init__(self) -> None:
        super().__init__()
        self._reader = PhoneLinkReader()

    def process(self, payload: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        payload = payload or {}
        action = payload.get("action", "status")
        limit = int(payload.get("limit", 10))

        if action == "status":
            return self._reader.snapshot().to_dict()
        if action == "messages":
            return {"messages": self._reader.recent_messages(limit=limit)}
        if action == "conversations":
            return {"conversations": self._reader.recent_conversations(limit=limit)}
        raise ValueError(f"Unbekannte action: {action!r}")