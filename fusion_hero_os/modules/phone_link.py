"""PhoneLinkCoreModule — read-only Phone Link Integration für den Dispatcher.

Realwelt-Kontakt-Guard: nur der Mensch bedient das Handy und bestätigt jeden
Eingriff mit echten Kontakten. ``process()`` prüft ``FORBIDDEN_ACTIONS`` als
allererstes, vor jeder Action-Verzweigung — siehe
``fusion_hero_os.integrations.phone_link.reader`` und
``docs/ops/REALWORLD_CONTACT_GUARD.md``.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fusion_hero_os.core.base_module import BaseModule
from fusion_hero_os.integrations.phone_link.reader import (
    FORBIDDEN_ACTIONS,
    PhoneLinkReader,
    deny_realworld_contact_action,
)


class PhoneLinkCoreModule(BaseModule):
    """``process(payload)`` Aktionen:

    - ``status`` (default) — Verbindungs- und Sync-Übersicht
    - ``messages`` — letzte SMS (``limit`` optional)
    - ``conversations`` — letzte Konversationen (``limit`` optional)

    Jede Action, die einen echten Kontakt erreichen würde (senden, anrufen,
    antworten, …), wird hart abgelehnt — siehe ``FORBIDDEN_ACTIONS``.
    """

    def __init__(self) -> None:
        super().__init__()
        self._reader = PhoneLinkReader()

    def process(self, payload: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        payload = payload or {}
        action = payload.get("action", "status")
        limit = int(payload.get("limit", 10))

        if action in FORBIDDEN_ACTIONS:
            deny_realworld_contact_action(action)

        if action == "status":
            return self._reader.snapshot().to_dict()
        if action == "messages":
            return {"messages": self._reader.recent_messages(limit=limit)}
        if action == "conversations":
            return {"conversations": self._reader.recent_conversations(limit=limit)}
        raise ValueError(f"Unbekannte action: {action!r}")