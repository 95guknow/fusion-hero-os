"""SelfModifyCoreModule (BaseModule-Adapter).

Wichtig — Sicherheitsprinzip: dieses Modul verändert NIEMALS selbstständig
Code. ``propose_evolution()`` erzeugt einen strukturierten, rein deklarativen
:class:`~fusion_hero_os.core.base_module.EvolutionProposal` (Text/Diff-Vorschlag).
Das tatsächliche Anwenden ist ausdrücklich NICHT Teil dieses Moduls — ein
Vorschlag wird erst wirksam, wenn ein Mensch (oder eine reguläre CI-Pipeline,
z.B. via PR-Review) ihn prüft und den zugehörigen Diff normal committet.
Es gibt hier keinen Mechanismus für unbeaufsichtigte Laufzeit-Selbstmodifikation.

Wrapt :class:`fusion_hero_os.engine.mainframe.SelfModifyCoreModule`, das
bereits als reiner Vorschlags-Sammler (Audit-Hooks + Historie-Liste, wendet
nichts an) implementiert ist.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fusion_hero_os.core.base_module import BaseModule, EvolutionProposal
from fusion_hero_os.engine.mainframe import SelfModifyCoreModule as _SelfModifyImpl


class SelfModifyCoreModule(BaseModule):
    """``process(payload)`` erwartet ``{"summary": str, "rationale": str,
    "diff": str | None}``, hängt den Vorschlag an die Historie an und gibt
    ihn als :class:`EvolutionProposal` zurück. Nichts wird angewendet.
    """

    def __init__(self) -> None:
        super().__init__()
        self._impl = _SelfModifyImpl()

    def process(self, payload: Optional[Dict[str, Any]] = None) -> EvolutionProposal:
        return self._record_proposal(payload or {})

    def propose_evolution(self, context: Optional[Dict[str, Any]] = None) -> Optional[EvolutionProposal]:
        if not context:
            return None
        return self._record_proposal(context)

    def _record_proposal(self, payload: Dict[str, Any]) -> EvolutionProposal:
        proposal = EvolutionProposal(
            module=payload.get("target_module", "unspecified"),
            summary=payload.get("summary", ""),
            rationale=payload.get("rationale", ""),
            diff=payload.get("diff"),
            requires_review=True,
        )
        self._impl.modification_history.append(
            {
                "ts": datetime.now(timezone.utc).isoformat(),
                "module": proposal.module,
                "summary": proposal.summary,
                "rationale": proposal.rationale,
                "diff": proposal.diff,
                "status": "pending_review",
            }
        )
        return proposal

    def history(self) -> List[Dict[str, Any]]:
        """Alle bisher gesammelten Vorschläge (nur Lesezugriff)."""
        return list(self._impl.modification_history)
