"""PeerReviewCoreModule — Code-Review-Checkliste (BaseModule).

Nicht zu verwechseln mit ``methodology.core_modules.PeerReviewCoreModule``,
das *Fließtext* (Analysen, Berichte) gegen 5 Argumentations-Dimensionen prüft.
Dieses Modul prüft *Code-Änderungen* gegen ein festes, nachvollziehbares
Kriterien-Set — ein Quality-Gate, kein Freitext-Heuristik-Scan.

Jedes Kriterium wird über ein explizites Signal im ``payload`` bewertet
(bool oder Text). Es gibt keine automatische Quellcode-Analyse: der
Aufrufer (Mensch oder CI-Schritt) liefert die Einschätzung je Kriterium,
dieses Modul aggregiert sie nur zu einem einheitlichen, protokollierbaren
Ergebnis. Damit ist die Checkliste die gleiche, ob sie von einem Menschen
oder einem CI-Skript ausgefüllt wird.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fusion_hero_os.core.base_module import BaseModule, ReviewCriterion, ReviewResult

#: Kriterium -> Payload-Key, unter dem der Prüfstatus (bool) erwartet wird.
CRITERIA = [
    ("Korrektheit", "correctness_verified"),
    ("Tests", "tests_added"),
    ("Style", "style_checked"),
    ("Sicherheit", "security_reviewed"),
    ("Doku", "docs_updated"),
    ("Performance", "performance_considered"),
]


class PeerReviewCoreModule(BaseModule):
    """``process(payload)``/``peer_review(payload)`` sind hier identisch:
    beide erwarten ein Dict mit den Keys aus :data:`CRITERIA` (bool) sowie
    optional ``notes`` (Dict[str, str] mit Begründungen je Kriterium) und
    liefern ein :class:`ReviewResult`.
    """

    def _evaluate(self, payload: Optional[Dict[str, Any]]) -> ReviewResult:
        payload = payload or {}
        notes = payload.get("notes", {})
        criteria = [
            ReviewCriterion(
                name=label,
                passed=bool(payload.get(key, False)),
                detail=notes.get(key, ""),
            )
            for label, key in CRITERIA
        ]
        return ReviewResult(module=self.name, criteria=criteria)

    def process(self, payload: Optional[Dict[str, Any]] = None) -> ReviewResult:
        return self._evaluate(payload)

    def peer_review(self, target: Optional[Dict[str, Any]] = None) -> ReviewResult:
        return self._evaluate(target)
