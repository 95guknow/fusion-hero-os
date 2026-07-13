"""ConversationContextCoreModule — begrenztes Konversationsfenster.

Hält die letzten ``max_turns`` Gesprächsbeiträge im Speicher (FIFO-Eviction).
Reiner In-Memory-Zustand für die Dauer des Prozesses — keine Persistenz,
kein externer Zugriff.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fusion_hero_os.core.base_module import BaseModule


@dataclass
class ConversationTurn:
    role: str
    content: str
    ts: str


class ConversationContextCoreModule(BaseModule):
    """``process(payload)`` erwartet ``{"action": "add" | "window" | "clear", ...}``.

    - ``add``: ``{"role": str, "content": str}`` -> hängt einen Turn an.
    - ``window``: optional ``{"n": int}`` -> liefert die letzten ``n`` Turns.
    - ``clear``: leert das Fenster.
    """

    def __init__(self, max_turns: int = 50) -> None:
        super().__init__()
        self.max_turns = max_turns
        self._turns: List[ConversationTurn] = []

    def process(self, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload = payload or {}
        action = payload.get("action", "add")

        if action == "add":
            turn = ConversationTurn(
                role=payload.get("role", "user"),
                content=payload.get("content", ""),
                ts=datetime.now(timezone.utc).isoformat(),
            )
            self._turns.append(turn)
            if len(self._turns) > self.max_turns:
                self._turns = self._turns[-self.max_turns:]
            return {"turns": len(self._turns)}

        if action == "window":
            n = int(payload.get("n", self.max_turns))
            return {"window": [asdict(t) for t in self._turns[-n:]]}

        if action == "clear":
            self._turns.clear()
            return {"turns": 0}

        raise ValueError(f"Unbekannte action: {action!r}")
