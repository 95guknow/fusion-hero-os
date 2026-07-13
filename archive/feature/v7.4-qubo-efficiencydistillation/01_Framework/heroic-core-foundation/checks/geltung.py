"""Geltungskategorien-specific checks (extensible)."""
from __future__ import annotations
import re
from typing import List, Dict

GELTUNG_RE = re.compile(r"\b(Satz|Bedingt|Modell|Axiomatisch|Fragment)\b", re.I)

def check_geltung(text: str) -> Dict[str, int]:
    counts = {"Satz": 0, "Bedingt": 0, "Modell": 0, "Axiomatisch": 0, "Fragment": 0}
    for m in GELTUNG_RE.finditer(text):
        cat = m.group(1).capitalize()
        if cat in counts:
            counts[cat] += 1
    return counts
