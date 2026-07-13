# agent_backend_router.py — Agent → Llama, Anti-Agent → Grok

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

AGENT_BACKEND = os.getenv("FUSION_AGENT_BACKEND", "llama-local")
ANTI_AGENT_BACKEND = os.getenv("FUSION_ANTI_AGENT_BACKEND", "grok-intern")

ANTI_ROLES = frozenset({
    "anti_agent", "anti-agent", "antiagent", "verifier", "critic", "contrarian",
    "peer_challenge", "anti", "challenger",
})
AGENT_ROLES = frozenset({
    "agent", "worker", "primary", "thinker", "subagent", "proposer", "solver",
})


def is_dual_agent_enabled() -> bool:
    return os.getenv("FUSION_DUAL_AGENT", "1") == "1"


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


def backend_for_role(role: Optional[str] = None, task: Optional[Dict[str, Any]] = None) -> str:
    if is_anti_agent(role, task):
        return ANTI_AGENT_BACKEND
    return AGENT_BACKEND


def backend_for_agent_id(agent_id: str) -> str:
    aid = (agent_id or "").lower()
    if aid.startswith("anti-") or "anti" in aid and "agent" in aid:
        return ANTI_AGENT_BACKEND
    if aid.endswith("-worker") or aid in (
        "math-worker", "phil-worker", "info-worker", "science-worker",
        "general-worker", "llama-test-worker", "fusion-hero-supervisor",
    ):
        return AGENT_BACKEND
    return AGENT_BACKEND


def invoke(
    role: str,
    query: str,
    context: Optional[Dict[str, Any]] = None,
    agent_response: Optional[str] = None,
) -> Dict[str, Any]:
    """Führt Query über den rollenbasierten Backend-Pfad aus."""
    ctx = dict(context or {})
    backend = backend_for_role(role, {**ctx, "role": role})
    text = (query or "").strip()
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
    """Agent (Llama) erzeugt, Anti-Agent (Grok) prüft."""
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
    synthesis = agent_out.get("response", "")
    if anti_out and anti_out.get("ok"):
        synthesis = (
            f"{agent_out.get('response', '')}\n\n"
            f"---\n**Anti-Agent (Grok):**\n{anti_out.get('response', '')}"
        )
    return {
        "ok": agent_out.get("ok", False),
        "agent_backend": agent_out.get("backend", AGENT_BACKEND),
        "anti_agent_backend": anti_out.get("backend") if anti_out else None,
        "agent": agent_out,
        "anti_agent": anti_out,
        "synthesis": synthesis,
        "policy": policy(),
    }


def policy() -> Dict[str, Any]:
    return {
        "agent_backend": AGENT_BACKEND,
        "anti_agent_backend": ANTI_AGENT_BACKEND,
        "dual_agent_enabled": is_dual_agent_enabled(),
        "agent_roles": sorted(AGENT_ROLES),
        "anti_roles": sorted(ANTI_ROLES),
    }


def annotate_task(task: Dict[str, Any]) -> Dict[str, Any]:
    """Setzt Backend-Felder an Task/Agent-Zuweisung."""
    agent = task.get("assigned_agent") or task.get("agent_id") or "agent"
    if is_anti_agent(task=task):
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
    return pol