"""BaseModule — gemeinsamer Vertrag für alle Core-Module.

Jedes Core-Modul, das über den :mod:`fusion_hero_os.core.dispatcher`
angesprochen werden soll, implementiert dieses Interface:

- ``process(payload)``            — die eigentliche Arbeit des Moduls.
- ``propose_evolution(context)``  — optionaler, rein deklarativer Vorschlag
  zur Weiterentwicklung des Moduls/Systems (siehe :class:`EvolutionProposal`).
  Ein Vorschlag verändert nichts von selbst; er muss von einem Menschen oder
  einer CI-Pipeline geprüft und bewusst angewendet werden (z.B. als Diff in
  einem PR). Es gibt in diesem Projekt keinen Mechanismus, der Vorschläge
  automatisch und unbeaufsichtigt in laufenden Code übernimmt.
- ``peer_review(target)``         — optionale Selbstprüfung/Fremdprüfung
  gegen ein nachvollziehbares Kriterien-Set (siehe :class:`ReviewResult`).

``propose_evolution`` und ``peer_review`` sind mit einer neutralen
Default-Implementierung versehen, damit Module, für die eine der beiden
Fähigkeiten nicht sinnvoll ist, sie nicht erzwungen bekommen.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass
class EvolutionProposal:
    """Ein strukturierter, rein deklarativer Verbesserungsvorschlag.

    Enthält absichtlich kein ausführbares Objekt — nur Text/Diff zur
    menschlichen bzw. CI-gestützten Prüfung. ``diff`` ist, wenn gesetzt,
    ein unified-diff-artiger Textblock, kein Patch, der von diesem System
    selbst angewendet wird.
    """

    module: str
    summary: str
    rationale: str
    diff: Optional[str] = None
    requires_review: bool = True


@dataclass
class ReviewCriterion:
    name: str
    passed: bool
    detail: str = ""


@dataclass
class ReviewResult:
    """Ergebnis einer Peer-Review-Prüfung gegen ein Kriterien-Set."""

    module: str
    criteria: List[ReviewCriterion] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return bool(self.criteria) and all(c.passed for c in self.criteria)

    @property
    def score(self) -> float:
        if not self.criteria:
            return 0.0
        return sum(1 for c in self.criteria if c.passed) / len(self.criteria)

    def report(self) -> str:
        lines = [f"Peer-Review: {self.module} — {'PASSED' if self.passed else 'FAILED'} "
                 f"({self.score * 100:.0f}%)"]
        for c in self.criteria:
            mark = "✓" if c.passed else "✗"
            extra = f" — {c.detail}" if c.detail else ""
            lines.append(f"  {mark} {c.name}{extra}")
        return "\n".join(lines)


class BaseModule(ABC):
    """Abstrakte Basisklasse für alle Fusion-Hero-OS Core-Module."""

    #: eindeutiger Registrierungsname (Default: Klassenname)
    name: str = ""

    def __init__(self) -> None:
        if not self.name:
            self.name = type(self).__name__

    @abstractmethod
    def process(self, payload: Any = None) -> Any:
        """Führt die Kernaufgabe des Moduls aus."""
        raise NotImplementedError

    def propose_evolution(self, context: Any = None) -> Optional[EvolutionProposal]:
        """Liefert optional einen Verbesserungsvorschlag. Default: keiner."""
        return None

    def peer_review(self, target: Any = None) -> ReviewResult:
        """Führt optional eine Selbstprüfung durch. Default: leeres Ergebnis
        (kein Kriterium definiert -> ``passed`` ist False, nicht "automatisch
        bestanden" — ein Modul ohne echte Review-Logik soll das nicht verschleiern).
        """
        return ReviewResult(module=self.name, criteria=[])
