"""FormalMathematicsCoreModule (BaseModule-Adapter).

Dünner Adapter um :class:`fusion_hero_os.methodology.core_modules.FormalMathematicsCoreModule`
(die reale Klassifikationslogik lebt dort und bleibt dort einzige Quelle der
Wahrheit — hier nur die Anbindung an den Dispatcher-Vertrag).
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fusion_hero_os.core.base_module import BaseModule
from fusion_hero_os.methodology.core_modules import (
    FormalMathematicsCoreModule as _FormalMathematicsImpl,
)


class FormalMathematicsCoreModule(BaseModule):
    """Etikettiert eine formale Aussage als Satz/Bedingt/Modell/Fragment.

    ``process(payload)`` erwartet ``{"aussage": str, "bewiesen": bool | None,
    "annahmen": list[str] | None}`` und liefert das Klassifikationsergebnis
    als Dict.
    """

    def __init__(self) -> None:
        super().__init__()
        self._impl = _FormalMathematicsImpl()

    def process(self, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload = payload or {}
        result = self._impl.classify(
            payload.get("aussage", ""),
            bewiesen=payload.get("bewiesen"),
            annahmen=payload.get("annahmen"),
        )
        return {
            "kategorie": result.kategorie,
            "begruendung": result.begruendung,
            "aussage": result.aussage,
        }
