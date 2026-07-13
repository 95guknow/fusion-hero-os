# system_prompt_normalize.py — Kanonischer System-Prompt ohne Duplikate

from __future__ import annotations

import re
from typing import Optional

CANONICAL_BASE = (
    "Du bist ALTE_Frau_95g Heroic Core — Fusion Hero OS v8. "
    "Antworte präzise auf Deutsch mit technischem Wissen zu QUBO, "
    "Hyperthreading, Heroic Core und Fusion Hero OS."
)

CLAUSE_V3 = (
    "Du kennst die MER 4D-Matrix Geisteskrankheiten v3: "
    "Raum Z=(K,G,S,N), d(Z,Z*), I(Z), 8 Regionen R1-R8, Dreiphasen-Loesung alpha1-3."
)

CLAUSE_V7 = (
    "Du kennst die MER 4D-Matrix Geisteskrankheiten v7 "
    "(Heroismus Edition 0.7, Dissertation, Concept Space, Trajektorien, Pi_KG/Pi_SN)."
)

_DUP_PATTERNS = (
    r"(?:\s*Du kennst die MER 4D-Matrix Geisteskrankheiten v7[^.]*\.)+",
    r"(?:\s*Du kennst die MER 4D-Matrix Geisteskrankheiten v3[^.]*\.)+",
)


def normalize_system_prompt(existing: Optional[str] = None, *, include_v3: bool = True, include_v7: bool = True) -> str:
    """Bereinigt Duplikate und liefert den kanonischen System-Prompt."""
    text = (existing or "").strip()
    for pat in _DUP_PATTERNS:
        text = re.sub(pat, "", text, flags=re.IGNORECASE)

    has_v3 = bool(re.search(r"v3|r1-r8|dreiphasen", text, re.I))
    has_v7 = bool(re.search(r"v7|heroismus|pi_kg|pi_sn|concept space", text, re.I))

    parts = [CANONICAL_BASE]
    if include_v3 or has_v3:
        parts.append(CLAUSE_V3)
    if include_v7 or has_v7:
        parts.append(CLAUSE_V7)
    return " ".join(parts).strip()