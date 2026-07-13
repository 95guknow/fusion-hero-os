# -*- coding: utf-8 -*-
"""
Audit-Agent (Gatekeeper ALTE_FRAU_95g) — epistemische Schleuse vor Graph-Writes.
Jede Behauptung durchläuft die HERO-GUIDE Geltungs-Werkbank.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from hero_guide_ide import Behauptung, GeltungsKategorie, HeroGuideWorkbench, get_workbench, parse_kategorie

GATEKEEPER_ID = "ALTE_FRAU_95g"
GATEKEEPER_ROLE = "epistemic_gatekeeper"


def audit_claim(
    text: str,
    kategorie: str = "FRAGMENT",
    praemissen: Optional[List[str]] = None,
    praemissen_erfuellt: bool = False,
    fehlende_praemisse: str = "",
    *,
    persist: bool = False,
) -> dict:
    """Prüft eine Aussage: wird Autorität ohne Prämisse projiziert?"""
    wb = get_workbench(with_graph=persist)
    payload = {
        "text": text,
        "kategorie": kategorie,
        "praemissen": praemissen or [],
        "praemissen_erfuellt": praemissen_erfuellt,
        "fehlende_praemisse": fehlende_praemisse,
    }
    result = wb.resolve_from_payload(payload, persist=persist)
    result["gatekeeper"] = GATEKEEPER_ID
    result["role"] = GATEKEEPER_ROLE
    result["authority_projection"] = _detect_authority_projection(text, parse_kategorie(kategorie))
    return result


def audit_before_write(payload: dict) -> dict:
    """Pflicht-Gate für jeden Wissensgraph-Write."""
    from knowledge_graph import get_knowledge_graph
    graph = get_knowledge_graph()
    wb = HeroGuideWorkbench(graph)
    clean = {k: v for k, v in payload.items() if k != "persist"}
    out = wb.resolve_from_payload(clean, persist=True)
    out["gatekeeper"] = GATEKEEPER_ID
    return out


def scan_code_claims(code: str) -> List[dict]:
    """Heuristik: SATZ-Behauptungen in Code/Kommentaren markieren."""
    import re
    findings: List[dict] = []
    patterns = [
        (r"(?i)\b(beweis|theorem|satz|kontraktion|fixpunkt)\b", "SATZ"),
        (r"(?i)\b(metapher|wie ein|als ob|symbolisch)\b", "METAPHER_ALS_BEWEIS"),
        (r"(?i)\b(modell|heuristik|approximation)\b", "MODELL"),
        (r"(?i)\b(todo|tbd|fragment|unfertig)\b", "FRAGMENT"),
    ]
    for line_no, line in enumerate(code.splitlines(), 1):
        for pat, kat in patterns:
            if re.search(pat, line):
                findings.append({
                    "line": line_no,
                    "snippet": line.strip()[:120],
                    "suggested_kategorie": kat,
                })
                break
    return findings[:20]


def _detect_authority_projection(text: str, suggested: GeltungsKategorie) -> bool:
    """True wenn starke Autorität ohne bescheidene Markierung suggeriert wird."""
    import re
    strong = bool(re.search(r"(?i)\b(beweis|definitiv|immer|garantiert|satz)\b", text))
    humble = suggested in (
        GeltungsKategorie.MODELL,
        GeltungsKategorie.FRAGMENT,
        GeltungsKategorie.BEDINGT,
    )
    return strong and not humble and suggested == GeltungsKategorie.SATZ


def status() -> dict:
    wb = get_workbench(with_graph=True)
    return {
        "gatekeeper": GATEKEEPER_ID,
        "role": GATEKEEPER_ROLE,
        "audit_entries": len(wb.audit_log),
        "workbench": "HERO-GUIDE Geltungs-Werkbank",
    }