"""Epistemic hygiene helpers (metaphor-as-proof, modal collapse, unlabeled claims)."""
from __future__ import annotations
import re
from typing import List
from dataclasses import dataclass

@dataclass
class HygieneIssue:
    kind: str
    line: int
    text: str

PATTERNS = {
    "metaphor_proof": [
        r"\b(wie|als ob|quasi|gleichsam)\b.*\b(beweist|zeigt|impliziert|belegt)\b",
    ],
    "modal_collapse": [
        r"\b(könnte|could|might|may)\b[^.]{0,60}\b(ist|bedeutet|zeigt sich)\b",
    ],
}

def check_hygiene(text: str) -> List[HygieneIssue]:
    issues: List[HygieneIssue] = []
    for i, line in enumerate(text.splitlines(), 1):
        l = line.lower()
        for kind, pats in PATTERNS.items():
            for p in pats:
                if re.search(p, l):
                    issues.append(HygieneIssue(kind, i, line[:120]))
                    break
    return issues
