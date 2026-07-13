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
CLAUDE_SCIENCE_MODEL = os.getenv("CLAUDE_SCIENCE_MODEL", "claude-sonnet-5").strip()
ANTHROPIC_API_URL = os.getenv("ANTHROPIC_API_URL", "https://api.anthropic.com/v1/messages").strip()

# --- Frontier-Backend-Fähigkeiten (opt-in per Env; koevolutionär wählbar) ------
# Prompt-Caching: markiert den System-Prompt als cache_control -> Anthropic
#   Prompt-Cache (5-Min-TTL) spart Kosten/Latenz bei wiederholten System-Prompts.
PROMPT_CACHE_ENABLED = os.getenv("FUSION_CLAUDE_PROMPT_CACHE", "1") == "1"
# Extended Thinking: Reasoning-Budget in Tokens (0 = aus).
THINKING_BUDGET = int(os.getenv("FUSION_CLAUDE_THINKING_BUDGET", "0"))

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
        "frontier_capabilities": {
            "tool_use_loop": True,
            "prompt_caching": PROMPT_CACHE_ENABLED,
            "streaming": True,
            "extended_thinking": THINKING_BUDGET > 0,
            "thinking_budget": THINKING_BUDGET,
        },
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


def _system_field(system: Optional[str], cache: bool) -> Any:
    """System-Prompt als cache-fähigen Block (cache_control) oder als String.

    Mit cache=True wird der System-Prompt als ephemeraler Cache-Breakpoint
    markiert -> wiederholte Calls mit gleichem System-Prompt lesen aus dem
    Anthropic-Prompt-Cache (5-Min-TTL) statt ihn neu zu prozessieren.
    """
    text = system or _science_system_prompt()
    if not cache:
        return text
    return [{"type": "text", "text": text, "cache_control": {"type": "ephemeral"}}]


def _build_payload(
    prompt: str,
    system: Optional[str] = None,
    *,
    cache: bool = PROMPT_CACHE_ENABLED,
    thinking_budget: int = THINKING_BUDGET,
    stream: bool = False,
    max_tokens: Optional[int] = None,
) -> Dict[str, Any]:
    """Baut das Messages-API-Payload inkl. Caching/Thinking/Streaming (opt-in)."""
    mt = max_tokens or int(os.getenv("FUSION_CLAUDE_SCIENCE_MAX_TOKENS", "1024"))
    payload: Dict[str, Any] = {
        "model": CLAUDE_SCIENCE_MODEL,
        "max_tokens": mt,
        "system": _system_field(system, cache),
        "messages": [{"role": "user", "content": prompt}],
    }
    if thinking_budget and thinking_budget > 0:
        # Extended Thinking: Reasoning-Budget muss < max_tokens sein.
        payload["max_tokens"] = max(mt, thinking_budget + 512)
        payload["thinking"] = {"type": "enabled", "budget_tokens": thinking_budget}
    if stream:
        payload["stream"] = True
    return payload


def _call_api(prompt: str, system: Optional[str] = None) -> tuple[str, Dict[str, Any]]:
    import httpx

    resp = httpx.post(
        ANTHROPIC_API_URL,
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json=_build_payload(prompt, system),
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
        "cache_creation_input_tokens": usage.get("cache_creation_input_tokens"),
        "cache_read_input_tokens": usage.get("cache_read_input_tokens"),
        "stop_reason": data.get("stop_reason"),
    }


def call_stream(
    prompt: str,
    system: Optional[str] = None,
    on_delta: Optional[Any] = None,
    *,
    iter_lines: Optional[Any] = None,
) -> tuple[str, Dict[str, Any]]:
    """Streamt die Antwort token-weise (SSE). on_delta(text) pro Delta aufgerufen.

    Returns (voller_text, meta). `iter_lines` ist injizierbar (Iterator über
    SSE-Zeilen) — damit ohne Netz testbar. Ohne Injektion wird httpx-Streaming
    gegen die Anthropic-API genutzt.

    Ehrlich: Streaming ändert nichts an der Antwortqualität — nur an der
    Latenz-Wahrnehmung (inkrementelle Ausgabe fürs Dashboard).
    """
    import json as _json

    def _consume(lines: Any) -> tuple[str, Dict[str, Any]]:
        parts: List[str] = []
        meta: Dict[str, Any] = {"model": CLAUDE_SCIENCE_MODEL, "streamed": True}
        for raw in lines:
            line = raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else str(raw)
            line = line.strip()
            if not line or not line.startswith("data:"):
                continue
            payload = line[len("data:"):].strip()
            if payload == "[DONE]":
                break
            try:
                evt = _json.loads(payload)
            except Exception:
                continue
            etype = evt.get("type")
            if etype == "content_block_delta":
                delta = (evt.get("delta") or {}).get("text", "")
                if delta:
                    parts.append(delta)
                    if on_delta:
                        on_delta(delta)
            elif etype == "message_delta":
                usage = evt.get("usage") or {}
                meta["output_tokens"] = usage.get("output_tokens")
                meta["stop_reason"] = (evt.get("delta") or {}).get("stop_reason")
            elif etype == "message_start":
                usage = ((evt.get("message") or {}).get("usage")) or {}
                meta["input_tokens"] = usage.get("input_tokens")
                meta["cache_read_input_tokens"] = usage.get("cache_read_input_tokens")
        return "".join(parts).strip(), meta

    if iter_lines is not None:
        return _consume(iter_lines)

    import httpx

    payload = _build_payload(prompt, system, stream=True)
    with httpx.stream(
        "POST",
        ANTHROPIC_API_URL,
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json=payload,
        timeout=float(os.getenv("FUSION_CLAUDE_SCIENCE_TIMEOUT", "60")),
    ) as resp:
        if resp.status_code != 200:
            raise RuntimeError(f"Anthropic API {resp.status_code}: {resp.read()[:300]!r}")
        return _consume(resp.iter_lines())


# ---------------------------------------------------------------------------
# Tool-Use-Loop (Function Calling über die Messages API)
# ---------------------------------------------------------------------------

def _default_post(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Sendet ein Messages-API-Payload; gibt das JSON der Antwort zurück."""
    import httpx

    resp = httpx.post(
        ANTHROPIC_API_URL,
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json=payload,
        timeout=float(os.getenv("FUSION_CLAUDE_SCIENCE_TIMEOUT", "60")),
    )
    if resp.status_code != 200:
        try:
            detail = resp.json().get("error", {}).get("message", resp.text)
        except Exception:
            detail = resp.text[:300]
        raise RuntimeError(f"Anthropic API {resp.status_code}: {detail}")
    return resp.json()


def run_tool_loop(
    query: str,
    tools: List[Dict[str, Any]],
    tool_executor: Any,
    system: Optional[str] = None,
    max_rounds: int = 8,
    post: Optional[Any] = None,
) -> Dict[str, Any]:
    """Echter Tool-Use-Loop: Claude ruft Tools auf, Ergebnisse fließen zurück.

    Args:
        query: Nutzeranfrage.
        tools: Tool-Definitionen im Anthropic-Format
               ({name, description, input_schema}).
        tool_executor: Callable(name: str, tool_input: dict) -> str.
                       Führt das Tool LOKAL aus (Grounding!) und gibt das
                       Ergebnis als String zurück. Exceptions werden als
                       is_error-Tool-Result zurückgemeldet, nicht verschluckt.
        system: optionaler System-Prompt (Default: Science-Prompt).
        max_rounds: harte Obergrenze an API-Runden (Endlosschleifen-Schutz).
        post: injizierbarer Transport für Tests (payload -> response-json).

    Returns dict: ok, response (finaler Text), tool_calls (Transkript),
        rounds, stop_reason, usage. Ohne API-Key: ok=False + Offline-Hinweis.

    Ehrlich: Der Loop selbst schafft kein Wissen — sein Wert entsteht durch
    die lokal ausgeführten Tools (Dateien lesen, Tests laufen lassen, ...).
    """
    query = (query or "").strip()
    if not query:
        return {"ok": False, "error": "empty query"}
    if post is None and not is_configured():
        return {
            "ok": False,
            "error": "missing ANTHROPIC_API_KEY",
            "response": "[Claude Science · Offline-Modus] Tool-Use benötigt Live-API.",
            "tool_calls": [],
            "rounds": 0,
        }

    send = post or _default_post
    messages: List[Dict[str, Any]] = [{"role": "user", "content": query}]
    tool_calls: List[Dict[str, Any]] = []
    usage_total = {"input_tokens": 0, "output_tokens": 0}
    stop_reason = None

    for round_no in range(1, max_rounds + 1):
        payload = {
            "model": CLAUDE_SCIENCE_MODEL,
            "max_tokens": int(os.getenv("FUSION_CLAUDE_SCIENCE_MAX_TOKENS", "1024")),
            "system": _system_field(system, PROMPT_CACHE_ENABLED),
            "messages": messages,
            "tools": tools,
        }
        try:
            data = send(payload)
        except Exception as exc:
            return {
                "ok": False,
                "error": str(exc),
                "tool_calls": tool_calls,
                "rounds": round_no,
            }

        usage = data.get("usage", {})
        usage_total["input_tokens"] += usage.get("input_tokens") or 0
        usage_total["output_tokens"] += usage.get("output_tokens") or 0
        stop_reason = data.get("stop_reason")
        content = data.get("content", [])

        if stop_reason != "tool_use":
            text = "\n".join(
                b.get("text", "") for b in content if b.get("type") == "text"
            ).strip()
            return {
                "ok": True,
                "response": text,
                "tool_calls": tool_calls,
                "rounds": round_no,
                "stop_reason": stop_reason,
                "usage": usage_total,
                "model": data.get("model", CLAUDE_SCIENCE_MODEL),
            }

        # Tool-Runde: alle tool_use-Blöcke ausführen, Ergebnisse zurückgeben
        messages.append({"role": "assistant", "content": content})
        results: List[Dict[str, Any]] = []
        for block in content:
            if block.get("type") != "tool_use":
                continue
            name = block.get("name", "")
            tool_input = block.get("input") or {}
            call_record = {"round": round_no, "tool": name, "input": tool_input}
            try:
                output = str(tool_executor(name, tool_input))
                call_record["ok"] = True
                call_record["output"] = output[:2000]
                results.append({
                    "type": "tool_result",
                    "tool_use_id": block.get("id"),
                    "content": output,
                })
            except Exception as exc:
                call_record["ok"] = False
                call_record["error"] = str(exc)
                results.append({
                    "type": "tool_result",
                    "tool_use_id": block.get("id"),
                    "content": f"Tool-Fehler: {exc}",
                    "is_error": True,
                })
            tool_calls.append(call_record)
        messages.append({"role": "user", "content": results})

    return {
        "ok": False,
        "error": f"max_rounds={max_rounds} erreicht ohne finale Antwort",
        "tool_calls": tool_calls,
        "rounds": max_rounds,
        "stop_reason": stop_reason,
        "usage": usage_total,
    }