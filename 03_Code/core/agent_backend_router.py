# agent_backend_router.py — Agent → Llama, Anti-Agent → Grok

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

AGENT_BACKEND = os.getenv("FUSION_AGENT_BACKEND", "llama-local")
ANTI_AGENT_BACKEND = os.getenv("FUSION_ANTI_AGENT_BACKEND", "grok-intern")
QUANTIZER_BACKEND = os.getenv("FUSION_QUANTIZER_BACKEND", "local")

ANTI_ROLES = frozenset({
    "anti_agent", "anti-agent", "antiagent", "verifier", "critic", "contrarian",
    "peer_challenge", "anti", "challenger",
})
AGENT_ROLES = frozenset({
    "agent", "worker", "primary", "thinker", "subagent", "proposer", "solver",
})
QUANTIZER_ROLES = frozenset({
    "quantizer", "string_quantizer", "string-quantizer", "q-agent", "phrase_quantizer",
})


def is_dual_agent_enabled() -> bool:
    return os.getenv("FUSION_DUAL_AGENT", "1") == "1"


def is_quantizer_enabled() -> bool:
    """3. Agent (String-Quantisierer) — default an, begleitet jede Verhandlung."""
    return os.getenv("FUSION_QUANTIZER_AGENT", "1") == "1"


def is_anti_agent(role: Optional[str] = None, task: Optional[Dict[str, Any]] = None) -> bool:
    if task:
        if task.get("anti_agent") or task.get("is_anti_agent"):
            return True
        role = role or task.get("role") or task.get("agent_role") or task.get("mode")
        name = str(task.get("assigned_agent") or task.get("agent_id") or "").lower()
        if name.startswith("anti-") or "anti-agent" in name or "anti_agent" in name:
            return True
    r = (role or "").lower().replace("_", "-")
    return r in ANTI_ROLES or r.startswith("anti-")


def is_quantizer_agent(role: Optional[str] = None, task: Optional[Dict[str, Any]] = None) -> bool:
    if task:
        if task.get("quantizer") or task.get("is_quantizer") or task.get("agent_kind") == "quantizer":
            return True
        role = role or task.get("role") or task.get("agent_role") or task.get("mode")
        name = str(task.get("assigned_agent") or task.get("agent_id") or "").lower()
        if "quantizer" in name or name in ("string-quantizer", "q-agent"):
            return True
    r = (role or "").lower().replace("-", "_")
    return r in QUANTIZER_ROLES or r.startswith("quantiz")


def backend_for_role(role: Optional[str] = None, task: Optional[Dict[str, Any]] = None) -> str:
    if is_quantizer_agent(role, task):
        return QUANTIZER_BACKEND
    if is_anti_agent(role, task):
        return ANTI_AGENT_BACKEND
    return AGENT_BACKEND


def backend_for_agent_id(agent_id: str) -> str:
    aid = (agent_id or "").lower()
    if "quantizer" in aid or aid in ("string-quantizer", "q-agent"):
        return QUANTIZER_BACKEND
    if aid.startswith("anti-") or "anti" in aid and "agent" in aid:
        return ANTI_AGENT_BACKEND
    if aid.endswith("-worker") or aid in (
        "math-worker", "phil-worker", "info-worker", "science-worker",
        "general-worker", "llama-test-worker", "fusion-hero-supervisor",
        "string-quantizer",
    ):
        return AGENT_BACKEND if "quantizer" not in aid else QUANTIZER_BACKEND
    return AGENT_BACKEND


def invoke(
    role: str,
    query: str,
    context: Optional[Dict[str, Any]] = None,
    agent_response: Optional[str] = None,
    anti_response: Optional[str] = None,
) -> Dict[str, Any]:
    """Führt Query über den rollenbasierten Backend-Pfad aus."""
    ctx = dict(context or {})
    backend = backend_for_role(role, {**ctx, "role": role})
    text = (query or "").strip()

    # 3. Agent: String-Quantisierer — ganze Strings, Wiederholungen quantisieren
    if is_quantizer_agent(role, {**ctx, "role": role}):
        return _invoke_quantizer(
            query or "",
            agent_response=agent_response or "",
            anti_response=anti_response or ctx.get("anti_response") or "",
            context=ctx,
            backend=backend,
        )

    if not text:
        return {"ok": False, "backend": backend, "role": role, "error": "empty query"}

    if is_anti_agent(role, ctx) and agent_response:
        text = (
            f"[anti-agent] Prüfe die folgende Agent-Antwort (Llama) kritisch auf "
            f"Lücken, Widersprüche und epistemische Inflation.\n\n"
            f"**Nutzeranfrage:** {query}\n\n**Agent-Antwort:**\n{agent_response[:6000]}"
        )

    if backend == "llama-local":
        return _invoke_llama(text, role, backend)
    if backend == "grok-intern":
        return _invoke_grok(text, role, backend, ctx)
    return {"ok": False, "backend": backend, "role": role, "error": f"unknown backend {backend}"}


def _invoke_quantizer(
    query: str,
    agent_response: str = "",
    anti_response: str = "",
    context: Optional[Dict[str, Any]] = None,
    backend: str = "local",
) -> Dict[str, Any]:
    try:
        from string_quantizer_agent import accompany, is_enabled

        if not is_enabled():
            return {
                "ok": False,
                "backend": backend,
                "role": "quantizer",
                "skipped": True,
                "error": "quantizer disabled",
            }
        out = accompany(query, agent_response, anti_response, context)
        out["backend"] = backend
        return out
    except Exception as exc:
        return {"ok": False, "backend": backend, "role": "quantizer", "error": str(exc)}


def _invoke_llama(prompt: str, role: str, backend: str) -> Dict[str, Any]:
    try:
        from local_llama import get_local_llama

        llama = get_local_llama()
        if not llama.active:
            return {"ok": False, "backend": backend, "role": role, "error": "llama not active"}
        use_qubo = os.getenv("FUSION_LLAMA_QUBO", "1") == "1" and role not in ANTI_ROLES
        if use_qubo:
            out = llama.generate_qubo(prompt)
            return {
                "ok": bool(out.get("response", "").strip()),
                "backend": out.get("backend", backend),
                "role": role,
                "response": out.get("response", ""),
                "qubo_applied": out.get("qubo_applied"),
            }
        response = llama.generate(prompt, use_qubo=False)
        return {"ok": bool(response.strip()), "backend": backend, "role": role, "response": response}
    except Exception as exc:
        return {"ok": False, "backend": backend, "role": role, "error": str(exc)}


def _invoke_grok(prompt: str, role: str, backend: str, ctx: Dict[str, Any]) -> Dict[str, Any]:
    try:
        from model_connectors import invoke_model, pick_verifier_model

        pool = ["grok", "claude", "gpt"]
        model = pick_verifier_model(pool, "llama")
        result = invoke_model(model, prompt, role="verifier")
        if result.ok and result.response.strip():
            return {
                "ok": True,
                "backend": f"grok-api/{model}",
                "role": role,
                "response": result.response,
                "latency_ms": result.latency_ms,
            }
    except Exception:
        pass

    try:
        import sys
        from pathlib import Path

        dash = Path(__file__).resolve().parents[1] / "Dashboard"
        if str(dash) not in sys.path:
            sys.path.insert(0, str(dash))
        from grok_bridge import get_grok_bridge

        gr = get_grok_bridge().chat(prompt, health=ctx.get("health"))
        response = gr.response if hasattr(gr, "response") else str(gr)
        return {"ok": bool(response.strip()), "backend": backend, "role": role, "response": response}
    except Exception as exc:
        return {"ok": False, "backend": backend, "role": role, "error": str(exc)}


def dual_run(query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Verhandlungstriade:
      1) Agent (Llama) erzeugt
      2) Anti-Agent (Grok) prüft
      3) Quantisierer — ganze Strings logisch, Wiederholungen quantisieren
    """
    ctx = dict(context or {})
    agent_out = invoke("agent", query, ctx)
    anti_out = None
    if is_dual_agent_enabled() and agent_out.get("ok"):
        anti_out = invoke(
            "anti_agent",
            query,
            ctx,
            agent_response=agent_out.get("response", ""),
        )

    # Whole-string policy auf Agent-Antwort anwenden (kein Char-Stream)
    agent_text = agent_out.get("response", "") or ""
    anti_text = (anti_out or {}).get("response", "") or ""
    try:
        from string_quantizer_agent import emit_logical

        if agent_text.strip():
            agent_text = emit_logical(agent_text)
            agent_out = {**agent_out, "response": agent_text, "whole_string_emit": True}
        if anti_text.strip():
            anti_text = emit_logical(anti_text)
            if anti_out:
                anti_out = {**anti_out, "response": anti_text, "whole_string_emit": True}
    except Exception:
        pass

    quant_out = None
    if is_quantizer_enabled():
        quant_out = invoke(
            "quantizer",
            query,
            {**ctx, "anti_response": anti_text},
            agent_response=agent_text,
            anti_response=anti_text,
        )

    synthesis = agent_text
    if anti_out and anti_out.get("ok"):
        synthesis = (
            f"{agent_text}\n\n"
            f"---\n**Anti-Agent (Grok):**\n{anti_text}"
        )
    if quant_out and quant_out.get("ok"):
        compact = quant_out.get("compact") or ""
        synthesis = (
            f"{synthesis}\n\n"
            f"---\n**Quantisierer (3. Agent — whole-string / Q-Table):**\n"
            f"{compact[:4000]}"
        )

    return {
        "ok": agent_out.get("ok", False),
        "agent_backend": agent_out.get("backend", AGENT_BACKEND),
        "anti_agent_backend": anti_out.get("backend") if anti_out else None,
        "quantizer_backend": quant_out.get("backend") if quant_out else None,
        "agent": agent_out,
        "anti_agent": anti_out,
        "quantizer": quant_out,
        "synthesis": synthesis,
        "triad": True,
        "policy": policy(),
    }


def triple_run(query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Alias: explizite Triade Agent + Anti-Agent + Quantisierer."""
    return dual_run(query, context)


def policy() -> Dict[str, Any]:
    return {
        "agent_backend": AGENT_BACKEND,
        "anti_agent_backend": ANTI_AGENT_BACKEND,
        "quantizer_backend": QUANTIZER_BACKEND,
        "dual_agent_enabled": is_dual_agent_enabled(),
        "quantizer_agent_enabled": is_quantizer_enabled(),
        "triad": "agent + anti_agent + quantizer",
        "emit_policy": "whole_string_logical_never_char_stream",
        "agent_roles": sorted(AGENT_ROLES),
        "anti_roles": sorted(ANTI_ROLES),
        "quantizer_roles": sorted(QUANTIZER_ROLES),
    }


def annotate_task(task: Dict[str, Any]) -> Dict[str, Any]:
    """Setzt Backend-Felder an Task/Agent-Zuweisung."""
    agent = task.get("assigned_agent") or task.get("agent_id") or "agent"
    if is_quantizer_agent(task=task):
        task["backend"] = QUANTIZER_BACKEND
        task["agent_kind"] = "quantizer"
    elif is_anti_agent(task=task):
        task["backend"] = ANTI_AGENT_BACKEND
        task["agent_kind"] = "anti_agent"
    else:
        task["backend"] = backend_for_agent_id(str(agent))
        task["agent_kind"] = "agent"
    return task


def status() -> Dict[str, Any]:
    pol = policy()
    pol["module"] = "agent_backend_router"
    pol["llama_active"] = False
    pol["grok_bridge"] = False
    pol["quantizer"] = {}
    try:
        from local_llama import get_local_llama

        pol["llama_active"] = get_local_llama().active
    except Exception:
        pass
    try:
        import sys
        from pathlib import Path

        dash = Path(__file__).resolve().parents[1] / "Dashboard"
        if str(dash) not in sys.path:
            sys.path.insert(0, str(dash))
        from grok_bridge import get_grok_bridge

        pol["grok_bridge"] = get_grok_bridge().skill_loaded
    except Exception:
        pass
    try:
        from string_quantizer_agent import get_quantizer

        pol["quantizer"] = get_quantizer().status()
    except Exception as exc:
        pol["quantizer"] = {"error": str(exc)}
    return pol