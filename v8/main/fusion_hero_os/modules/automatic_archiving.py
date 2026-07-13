"""AutomaticArchivingCoreModule (BaseModule-Adapter).

Dünner Adapter um :class:`fusion_hero_os.methodology.core_modules.AutomaticArchivingCoreModule`.
Erzeugt ausschließlich einen Plan (Text + Dateiliste) — schreibt und zippt
nichts. Das tatsächliche Anlegen der Archivdatei ist bewusst Aufgabe des
aufrufenden Codes, nicht dieses Moduls.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, Optional

from fusion_hero_os.core.base_module import BaseModule
from fusion_hero_os.methodology.core_modules import (
    AutomaticArchivingCoreModule as _AutomaticArchivingImpl,
)


class AutomaticArchivingCoreModule(BaseModule):
    """``process(payload)`` erwartet mind. ``{"titel": str, "artefakte": list[str]}``
    (optional ``entscheidungen``, ``outputs``, ``offene_punkte``, ``chronologie``)
    und liefert den Archivierungs-Plan als Dict — ohne Seiteneffekt.
    """

    def __init__(self) -> None:
        super().__init__()
        self._impl = _AutomaticArchivingImpl()

    def process(self, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload = payload or {}
        plan = self._impl.build_plan(
            titel=payload.get("titel", "(unbenannt)"),
            artefakte=payload.get("artefakte", []),
            entscheidungen=payload.get("entscheidungen"),
            outputs=payload.get("outputs"),
            offene_punkte=payload.get("offene_punkte"),
            chronologie=payload.get("chronologie"),
        )
        return asdict(plan)
