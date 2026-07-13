# claude_science.py — Claude Science Workbench-Bridge (Anthropic API)

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parents[1] / "Dashboard" / ".env")
except Exception:
    pass

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
CLAUDE_SCIENCE_MODEL = os.getenv("CLAUDE_SCIENCE_MODEL", "claude-sonnet-4-20250514").strip()
ANTHROPIC_API_URL = os.getenv("ANTHROPIC_API_URL", "https://api.anthropic.com/v1/messages").strip()

SCIENCE_DOMAINS = (
    "biology",
    "genomics",
    "proteomics",
    "cheminformatics",
    "structural biology",
    "single-cell",
    "crispr",
    "epidemiology",
    "chemistry",
    "medicine",
    "healthcare",
    "physics",
    "environmental",
    "neuroscience",
    "bioinformatics",
    "drug discovery",
    "protein",
    "rna",
    "dna",
    "sequencing",
    "molecular",
)

# Wissenschaft der Heroik — Fusion Hero OS / ALTE_Frau_95g Domäne
HEROIC_SCIENCE_TERMS = (
    "heroik",
    "heroisch",
    "heroismus",
    "heroic science",
    "wissenschaft der heroik",
    "alte_frau",
    "alte frau 95g",
    "fusion hero",
    "fusion hero os",
    "mer matrix",
    "geisteskrankheiten",
    "4d matrix",
    "neurotheologie",
    "heroische mathematik",
    "heroische informatik",
    "kompendium der heroik",
    "masterseed",
    "eudaimonia",
    "geltungskategorie",
    "geltungskategorien",
    "peer-review",
    "peer review",
    "konzeptraum",
    "z*",
    "z-star",
    "dissertation hero",
    "psychiatrie 4d",
    "hospitalismus",
    "entkategorisierung",
    "modal-kollaps",
    "schicht ü",
    "schicht u",
    "heroic core",
    "heroic philosophy",
    "heroische philosophie",
    "qubo hero",
    "trajektorie",
    "pi_kg",
    "pi_sn",
)

_UNCLEAR_RESPONSE_MARKERS = (
    "[merged v7",
    "[llama-fallback]",
    "[llama error",
    "[heroic orchestration] dom=",
    "[heroic orchestration]",
    "placeholder",
    "orchestrated for",
    "could not",
    "keine ahnung",
    "nicht sicher",
    "unbekannt",
    "unclear",
    "tbd",
    "unvollständig",
    "unvollstaendig",
    "ich weiss nicht",
    "ich weiß nicht",
    "no clear",
    "kein klares ergebnis",
    "keine klare antwort",
)

SCIENCE_SKILLS = (
    "literature_review",
    "pubmed_search",
    "genomics_pipeline",
    "single_cell_rna",
    "protein_structure",
    "cheminformatics",
    "citation_audit",
    "reproducible_figures",
    "manuscript_draft",
    "evidence_database",
    "heroic_formal_math_audit",
    "heroic_science_domain_review",
    "geltungskategorie_check",
)

SCIENCE_CONNECTORS = (
    "UniProt",
    "PDB",
    "Ensembl",
    "Reactome",
    "ClinVar",
    "ChEMBL",
    "GEO",
    "PubMed",
    "BioNeMo",
)


def is_configured() -> bool:
    return bool(ANTHROPIC_API_KEY)


def is_enabled() -> bool:
    return os.getenv("FUSION_CLAUDE_SCIENCE", "1") == "1"


def is_escalation_enabled() -> bool:
    return os.getenv("FUSION_CLAUDE_SCIENCE_ESCALATE", "1") == "1"


def is_available() -> bool:
    """Modul nutzbar (Live-API oder Offline-Fallback)."""
    return is_enabled()


def is_heroic_science_query(query: str) -> bool:
    """Erkennt Anfragen zur Wissenschaft der Heroik."""
    q = (query or "").lower()
    if "[heroic-science]" in q or "[heroik]" in q or "wissenschaft der heroik" in q:
        return True
    return any(term in q for term in HEROIC_SCIENCE_TERMS)


def is_science_query(query: str) -> bool:
    q = (query or "").lower()
    if "[science]" in q or "claude science" in q:
        return True
    if is_heroic_science_query(query):
        return True
    return any(term in q for term in SCIENCE_DOMAINS)


def is_unclear_response(response: str, min_len: int = 80) -> bool:
    """Heuristik: Antwort liefert kein klares, substanzielles Ergebnis."""
    if not response or not str(response).strip():
        return True
    r = str(response).strip()
    low = r.lower()
    if len(low) < min_len:
        return True
    if any(m in low for m in _UNCLEAR_RESPONSE_MARKERS):
        return True
    if low.startswith("[heroic orchestration]") and "agent=" in low:
        return True
    if low.count("[") >= 3 and len(low) < 220:
        return True
    return False


def should_use_claude_science(
    query: str,
    prior_response: Optional[str] = None,
) -> tuple[bool, str]:
    """
    Entscheidet ob Anthropic Claude Science eingesetzt werden soll.

    Returns:
        (should_use, reason) — reason: science_domain | heroic_science | unclear_result | disabled | not_applicable
    """
    if not is_available():
        return False, "disabled"
    if is_heroic_science_query(query):
        return True, "heroic_science"
    if is_science_query(query):
        return True, "science_domain"
    if is_escalation_enabled() and prior_response is not None and is_unclear_response(prior_response):
        return True, "unclear_result"
    return False, "not_applicable"


def _science_system_prompt(subdomain: str = "general_science") -> str:
    base = (
        "Du bist Claude Science — ein wissenschaftliches AI-Workbench für Fusion Hero OS. "
        "Fokus: reproduzierbare Analysen, nachvollziehbare Artefakte, Zitationsprüfung, "
        "Domänen Genomics/Single-Cell/Proteomics/Strukturbiologie/Cheminformatics. "
        "Antworte präzise, mit Methodik, Annahmen und Limitationen. "
        "Markiere unsichere Aussagen. Keine erfundenen DOIs oder Messwerte."
    )
    if subdomain == "heroic_science":
        base += (
            " Zusätzlicher Fokus: Wissenschaft der Heroik (ALTE_Frau_95g / Fusion Hero OS). "
            "Verbinde philosophische, mathematische, neurotheologische und psychiatrische Konzepte "
            "mit evidenzbasierter Methodik: MER-Matrix, Geltungskategorien (Satz/Bedingt/Modell/Fragment), "
            "Peer-Review 5D, Z*-Attraktor, Konzeptraum, Schicht Ü-Warnungen. "
            "Unterscheide explizit Modell von Satz. Liefere klare, strukturierte Ergebnisse."
        )
    if subdomain == "heroic_formal_math":
        base += (
            " Modus: Formale Mathematik der Heroik — strikte Geltungsprüfung. "
            "Prüfe q∘b, Banach-Fixpunkt (λ<1), Simplex-Balance, MER-Index, QUBO, Harmonisierung H. "
            "Erkenne epistemische Drift (Modell→Satz-Upgrade). Keine Metapher als Beweis. "
            "Verdict: PASS/WARN/FAIL mit empfohlener Kategorie."
        )
    return base


def status() -> Dict[str, Any]:
    return {
        "module": "claude_science",
        "product": "Claude Science (Anthropic)",
        "enabled": is_enabled(),
        "configured": is_configured(),
        "escalation_enabled": is_escalation_enabled(),
        "model": CLAUDE_SCIENCE_MODEL,
        "api_url": ANTHROPIC_API_URL,
        "native_app_platforms": ["macOS", "Linux"],
        "windows_mode": "api_bridge",
        "skills": list(SCIENCE_SKILLS),
        "connectors": list(SCIENCE_CONNECTORS),
        "domains": list(SCIENCE_DOMAINS),
        "heroic_science_terms": len(HEROIC_SCIENCE_TERMS),
        "routing": {
            "science_domain": "primary",
            "heroic_science": "primary",
            "unclear_result": "escalation" if is_escalation_enabled() else "off",
        },
        "docs": "https://claude.com/science",
    }


def probe(timeout: float = 4.0) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "reachable": False,
        "key_accepted": False,
        "http_status": None,
        "latency_ms": None,
        "error": None,
    }
    if not is_configured():
        result["error"] = "missing ANTHROPIC_API_KEY"
        return result
    try:
        import httpx
    except Exception as exc:
        result["error"] = f"httpx not available: {exc}"
        return result

    start = time.perf_counter()
    try:
        resp = httpx.post(
            ANTHROPIC_API_URL,
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": CLAUDE_SCIENCE_MODEL,
                "max_tokens": 32,
                "messages": [{"role": "user", "content": "ping"}],
            },
            timeout=timeout,
        )
        result["http_status"] = resp.status_code
        result["latency_ms"] = round((time.perf_counter() - start) * 1000, 1)
        result["reachable"] = resp.status_code < 500
        result["key_accepted"] = resp.status_code == 200
        if not result["key_accepted"]:
            try:
                result["error"] = resp.json().get("error", {}).get("message", resp.text[:200])
            except Exception:
                result["error"] = resp.text[:200]
    except Exception as exc:
        result["latency_ms"] = round((time.perf_counter() - start) * 1000, 1)
        result["error"] = str(exc)
    return result


def _build_escalation_prompt(query: str, context: Optional[Dict[str, Any]] = None) -> str:
    """Reichert Query an wenn vorherige Antwort unklar war."""
    if not context:
        return query
    prior = context.get("prior_response") or context.get("prior")
    reason = context.get("escalation") or context.get("escalation_reason")
    if not prior:
        return query
    return (
        f"Ursprüngliche Anfrage:\n{query}\n\n"
        f"Vorherige unklare/unzureichende Antwort ({reason or 'escalation'}):\n{prior[:2000]}\n\n"
        "Bitte liefere eine klarere, wissenschaftlich fundierte und strukturierte Antwort. "
        "Nenne Methodik, Annahmen, Limitationen und Geltungskategorie (Modell/Bedingt/Satz)."
    )


def escalate_to_science(
    query: str,
    prior_response: str,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Eskaliert unklare Ergebnisse an Anthropic Claude Science."""
    ctx = dict(context or {})
    ctx["prior_response"] = prior_response
    ctx["escalation"] = ctx.get("escalation") or "unclear_result"
    return analyze(query, context=ctx)


def analyze(query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Wissenschaftliche Analyse mit reproduzierbarem Artefakt-Metadaten-Block."""
    query = (query or "").strip()
    if not query:
        return {"ok": False, "error": "empty query"}

    subdomain = _detect_subdomain(query)
    if is_heroic_science_query(query):
        subdomain = "heroic_science"

    use, route_reason = should_use_claude_science(
        query,
        (context or {}).get("prior_response") or (context or {}).get("prior"),
    )

    meta: Dict[str, Any] = {
        "artifact_type": "science_analysis",
        "reproducible": True,
        "skills_used": [],
        "connectors_considered": list(SCIENCE_CONNECTORS[:6]),
        "reviewer": "citation_and_calculation_check",
        "subdomain": subdomain,
        "route_reason": route_reason if use else "direct_call",
    }
    if context:
        meta["context"] = {k: context[k] for k in list(context.keys())[:12]}

    prompt = _build_escalation_prompt(query, context)
    system = _science_system_prompt(subdomain)

    if not is_configured():
        heroic_note = " [Heroik-Wissenschaft]" if subdomain == "heroic_science" else ""
        esc_note = ""
        if context and context.get("prior_response"):
            esc_note = " Eskalation wegen unklarer Vorantwort."
        return {
            "ok": True,
            "backend": "claude-science-fallback",
            "query": query,
            "response": (
                f"[Claude Science · Offline-Modus]{heroic_note}{esc_note} "
                f"Setze ANTHROPIC_API_KEY in 03_Code/Dashboard/.env für Live-API. "
                f"Domäne: {subdomain}. Route: {route_reason}. Query: {query[:240]}"
            ),
            "meta": meta,
            "configured": False,
            "route_reason": route_reason,
        }

    try:
        text, api_meta = _call_api(prompt, system=system)
        meta.update(api_meta)
        backend = "claude-science"
        if context and context.get("prior_response"):
            backend = "claude-science-escalated"
        return {
            "ok": True,
            "backend": backend,
            "query": query,
            "response": text,
            "meta": meta,
            "configured": True,
            "route_reason": route_reason,
        }
    except Exception as exc:
        return {
            "ok": False,
            "backend": "claude-science",
            "query": query,
            "error": str(exc),
            "meta": meta,
            "route_reason": route_reason,
        }


def chat(message: str, system: Optional[str] = None) -> str:
    result = analyze(message)
    if result.get("ok"):
        return str(result.get("response", ""))
    raise RuntimeError(result.get("error", "claude science failed"))


def _detect_subdomain(query: str) -> str:
    q = query.lower()
    if is_heroic_science_query(query):
        return "heroic_science"
    for label, terms in (
        ("genomics", ("genom", "rna-seq", "dna", "ensembl", "crispr")),
        ("proteomics", ("protein", "uniprot", "pdb", "fold")),
        ("cheminformatics", ("chem", "molecule", "drug", "compound")),
        ("epidemiology", ("epidem", "cohort", "glioma", "clinical")),
        ("neuroscience", ("neuro", "brain", "allen institute")),
        ("heroic_science", ("heroik", "heroismus", "mer matrix", "neurotheologie")),
    ):
        if any(t in q for t in terms):
            return label
    return "general_science"


def _call_api(prompt: str, system: Optional[str] = None) -> tuple[str, Dict[str, Any]]:
    import httpx

    resp = httpx.post(
        ANTHROPIC_API_URL,
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": CLAUDE_SCIENCE_MODEL,
            "max_tokens": int(os.getenv("FUSION_CLAUDE_SCIENCE_MAX_TOKENS", "1024")),
            "system": system or _science_system_prompt(),
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=float(os.getenv("FUSION_CLAUDE_SCIENCE_TIMEOUT", "60")),
    )
    if resp.status_code != 200:
        try:
            detail = resp.json().get("error", {}).get("message", resp.text)
        except Exception:
            detail = resp.text[:300]
        raise RuntimeError(f"Anthropic API {resp.status_code}: {detail}")

    data = resp.json()
    parts = []
    for block in data.get("content", []):
        if block.get("type") == "text":
            parts.append(block.get("text", ""))
    text = "\n".join(parts).strip()
    usage = data.get("usage", {})
    return text, {
        "model": data.get("model", CLAUDE_SCIENCE_MODEL),
        "input_tokens": usage.get("input_tokens"),
        "output_tokens": usage.get("output_tokens"),
        "stop_reason": data.get("stop_reason"),
    }