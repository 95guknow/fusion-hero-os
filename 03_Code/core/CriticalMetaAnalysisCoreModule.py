# core/CriticalMetaAnalysisCoreModule.py
# Version: v5.22

from __future__ import annotations

import re
from typing import Any, Dict, List


class CriticalMetaAnalysisCoreModule:
    """Epistemische Meta-Analyse: erkennt Absolutismus, Übergeneralisation und fehlende Evidenz."""

    _ABSOLUTIST = re.compile(
        r"\b(immer|nie|garantiert|universell|beweislich sicher|ohne ausnahme|"
        r"alle\s+\w+\s+sind|jeder\s+\w+\s+ist|100\s*%|vollständig bewiesen)\b",
        re.IGNORECASE,
    )
    _INFLATION = re.compile(
        r"\b(offensichtlich|selbstverständlich|unbestreitbar|zweifellos|"
        r"eindeutig bewiesen|wissenschaftlich erwiesen ohne)\b",
        re.IGNORECASE,
    )
    _HEDGE_MISSING = re.compile(
        r"\b(muss sein|kann nur|ist die wahrheit|definitiv|absolut)\b",
        re.IGNORECASE,
    )

    def analyze(self, text: str) -> List[Dict[str, Any]]:
        if not (text or "").strip():
            return []

        issues: List[Dict[str, Any]] = []
        lower = text.lower()

        for match in self._ABSOLUTIST.finditer(text):
            issues.append({
                "type": "epistemic_inflation",
                "severity": "high",
                "token": match.group(0),
                "message": "Mögliche epistemische Inflation (Absolutismus)",
            })

        for match in self._INFLATION.finditer(text):
            issues.append({
                "type": "rhetorical_certainty",
                "severity": "medium",
                "token": match.group(0),
                "message": "Rhetorische Gewissheit ohne explizite Evidenz",
            })

        if self._HEDGE_MISSING.search(text) and not re.search(
            r"\b(vielleicht|möglicherweise|tendenz|hypothese|modell|heuristik)\b", lower
        ):
            issues.append({
                "type": "missing_hedge",
                "severity": "medium",
                "message": "Starke Behauptung ohne epistemische Abschwächung",
            })

        if len(text.split()) > 40 and text.count(".") < 2 and issues:
            issues.append({
                "type": "monolithic_claim",
                "severity": "low",
                "message": "Lange Monolith-Aussage — Peer-Review empfohlen",
            })

        seen = set()
        deduped: List[Dict[str, Any]] = []
        for item in issues:
            key = (item.get("type"), item.get("token"), item.get("message"))
            if key not in seen:
                seen.add(key)
                deduped.append(item)
        return deduped

    def peer_review_passed(self, text: str) -> bool:
        return len(self.analyze(text)) == 0