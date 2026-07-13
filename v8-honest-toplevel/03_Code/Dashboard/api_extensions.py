# api_extensions.py — fehlende Endpunkte freigeben (alle Module)

from __future__ import annotations

import asyncio
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class ProfilePayload(BaseModel):
    name: str = "admin"


class GatePayload(BaseModel):
    text: str = ""


class ChatPayload(BaseModel):
    message: str = ""


class ValidatePayload(BaseModel):
    text: str = ""


class AgentControlPayload(BaseModel):
    text: str = ""
    query: str = ""
    dom: str = "General"
    geltung: str = "model"
    strategies: Optional[List[str]] = None


class AutoLoadPayload(BaseModel):
    phase: str = "staged"
    force: bool = False
    sync: bool = False
    attach_meta: bool = True


class HeroGuideResolvePayload(BaseModel):
    text: str = ""
    kategorie: str = "FRAGMENT"
    praemissen: List[str] = []
    praemissen_erfuellt: bool = False
    fehlende_praemisse: str = ""
    persist: bool = False


class CodeValidatePayload(BaseModel):
    code: str = ""


def _orch():
    from core.dynamic_orchestration_core import DynamicOrchestrationCoreModule
    return DynamicOrchestrationCoreModule()


@router.post("/api/load-all")
async def api_load_all(force: bool = False):
    from core.module_registry import load_all
    return await asyncio.to_thread(load_all, force)


@router.get("/api/modules")
async def api_modules():
    from core.module_registry import list_modules
    return {"modules": list_modules(), "all_enabled": os.getenv("FUSION_ALL_MODULES", "1") == "1"}


@router.post("/api/agents/{agent_id}/use")
async def api_agent_use(agent_id: str, payload: dict = None):
    from core.heroic_orchestration import assign_task_to_agent
    from core.agent_control import is_enabled, post_dispatch

    task = {"dom": "General", "id": agent_id, **(payload or {})}
    agent = assign_task_to_agent(task)
    status = "ok"
    if task.get("status") == "control_blocked":
        status = "control_blocked"
    elif is_enabled() and task.get("control_pre", {}).get("passed") is False:
        status = "control_warning"
    if is_enabled() and task.get("result"):
        post_dispatch(task, task.get("result"))
    return {
        "status": status,
        "agent_id": agent_id,
        "assigned": agent,
        "control_pre": task.get("control_pre"),
        "control_post": task.get("control_post"),
    }


@router.get("/api/agent-control/status")
async def api_agent_control_status():
    from core.agent_control import status as control_status
    return control_status()


@router.get("/api/agent-control/history")
async def api_agent_control_history(limit: int = 20):
    from core.agent_control import history
    return {"history": history(limit)}


@router.post("/api/agent-control/verify")
async def api_agent_control_verify(payload: AgentControlPayload):
    from core.agent_control import verify_text, strategy_order

    text = (payload.text or payload.query or "").strip()
    if not text:
        return {"status": "error", "error": "empty text"}
    ctx = {"dom": payload.dom, "geltung": payload.geltung, "query": text}
    if payload.strategies:
        os.environ["FUSION_AGENT_CONTROL_STRATEGIES"] = ",".join(payload.strategies)
    result = await asyncio.to_thread(verify_text, text, ctx)
    result["status"] = "ok" if result.get("passed") else "failed"
    result["strategies_configured"] = strategy_order()
    return result


@router.post("/api/agent-control/pre-check")
async def api_agent_control_pre_check(payload: AgentControlPayload):
    from core.agent_control import pre_dispatch

    text = (payload.text or payload.query or "").strip()
    task = {
        "query": text,
        "dom": payload.dom,
        "geltung": payload.geltung,
        "id": "api-pre-check",
    }
    cr = await asyncio.to_thread(pre_dispatch, task)
    return {"status": "ok" if cr.passed else "blocked", **cr.to_dict()}


@router.post("/api/mainframe/load")
async def api_mainframe_load():
    from core.module_registry import load_all
    result = await asyncio.to_thread(load_all, True)
    return {"status": "loaded", "version": "v7.4/v7.5", "boot_phase": "full", **result}


@router.get("/api/layer4/status")
async def api_layer4_status():
    try:
        import sys
        from pathlib import Path
        p = Path(r"C:\Users\Admin\heroic-highest-layer")
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))
        from highest_layer import load  # type: ignore
        return load().status()
    except Exception as exc:
        return {"status": "fallback", "error": str(exc)}


@router.post("/api/foundation/gate")
async def api_foundation_gate(payload: GatePayload):
    try:
        from core.foundation_loader import ensure_foundation_on_path, foundation_report_to_dict, load_check_foundation_gate

        if ensure_foundation_on_path() is None:
            return {"passed": False, "error": "heroic-core-foundation not found"}
        check = load_check_foundation_gate()
        return foundation_report_to_dict(check(payload.text))
    except Exception as exc:
        return {"passed": False, "error": str(exc)}


@router.post("/api/v12/sync")
async def api_v12_sync():
    try:
        from core.google_multi_account_sync_core import GoogleMultiAccountSyncCoreModule
        mod = GoogleMultiAccountSyncCoreModule()
        if hasattr(mod, "sync_all"):
            return mod.sync_all()
        return {"status": "ok", "note": "sync module loaded", "module": type(mod).__name__}
    except Exception as exc:
        return {"status": "fallback", "error": str(exc)}


@router.post("/api/mod/validate")
async def api_mod_validate(payload: ValidatePayload):
    from core.CriticalMetaAnalysisCoreModule import CriticalMetaAnalysisCoreModule
    from core.SelfModifyCoreModule import SelfModifyCoreModule
    issues = CriticalMetaAnalysisCoreModule().analyze(payload.text)
    proposal = None
    if issues:
        proposal = SelfModifyCoreModule().propose_modification(
            description="PeerReview finding", diff="", risk_level="low",
        )
    return {
        "status": "ok",
        "issues": issues,
        "peer_review_passed": len(issues) == 0,
        "proposal": proposal,
        "dimensions": 5,
    }


@router.get("/api/grok/status")
async def api_grok_status():
    from core.local_llama import get_local_llama, default_model_pool
    from core.claude_science import status as science_status
    llama = get_local_llama().status()
    return {
        "bridge": "grok-intern",
        "skill": "fusion-hero-os",
        "llama_local": llama,
        "claude_science": science_status(),
        "default_model_pool": default_model_pool(),
        "endpoints": [
            "/api/grok/chat",
            "/api/v12/orchestrate",
            "/api/claude-science/analyze",
            "/api/input",
        ],
    }


@router.get("/api/claude-science/heroic-audit/status")
async def api_heroic_audit_status():
    from core.heroic_science_audit import status as audit_status, load_last_report
    last = load_last_report()
    return {
        "audit": audit_status(),
        "last_run": {
            "ts": last.get("ts") if last else None,
            "summary": last.get("summary") if last else None,
            "configured": last.get("configured") if last else None,
        },
    }


@router.post("/api/claude-science/heroic-audit/run")
async def api_heroic_audit_run(payload: dict = None):
    from core.heroic_science_audit import run_audit

    payload = payload or {}
    approach_ids = payload.get("approach_ids")
    max_workers = int(payload.get("max_workers", 2))
    return await asyncio.to_thread(
        run_audit,
        approach_ids=approach_ids,
        include_items=payload.get("include_items", True),
        include_domains=payload.get("include_domains", True),
        max_workers=max_workers,
        save=payload.get("save", True),
        desktop_copy=payload.get("desktop_copy", True),
    )


@router.get("/api/claude-science/heroic-audit/report")
async def api_heroic_audit_report(format: str = "json"):
    from pathlib import Path
    from core.heroic_science_audit import load_last_report, render_markdown_report

    report = load_last_report()
    if not report:
        return {"status": "not_found", "hint": "POST /api/claude-science/heroic-audit/run zuerst"}
    if format == "md":
        from fastapi.responses import PlainTextResponse
        md_path = Path(__file__).resolve().parents[1] / "core" / "knowledge" / "Heroik_Wissenschaft_Claude_Science_Audit.md"
        if md_path.exists():
            return PlainTextResponse(md_path.read_text(encoding="utf-8"), media_type="text/markdown")
        return PlainTextResponse(render_markdown_report(report), media_type="text/markdown")
    return report


@router.get("/api/claude-science/status")
async def api_claude_science_status(probe: bool = False):
    from core.claude_science import probe as science_probe, status as science_status

    info = science_status()
    if probe:
        info["probe"] = await asyncio.to_thread(science_probe)
    return info


@router.post("/api/claude-science/analyze")
async def api_claude_science_analyze(payload: ChatPayload):
    from core.claude_science import analyze

    msg = (payload.message or "").strip()
    if not msg:
        return {"status": "error", "error": "empty message"}
    result = await asyncio.to_thread(analyze, msg)
    return {"status": "ok" if result.get("ok") else "error", **result}


@router.post("/api/claude-science/chat")
async def api_claude_science_chat(payload: ChatPayload):
    from core.claude_science import analyze

    msg = (payload.message or "").strip()
    if not msg:
        return {"status": "error", "error": "empty message"}
    result = await asyncio.to_thread(analyze, msg)
    return {
        "status": "ok" if result.get("ok") else "error",
        "response": result.get("response", ""),
        "backend": result.get("backend", "claude-science"),
        "meta": result.get("meta"),
        "error": result.get("error"),
    }


@router.get("/api/provider/status")
async def api_provider_status():
    from core.provider_switcher import status

    return status()


@router.post("/api/provider/select")
async def api_provider_select():
    from core.provider_switcher import select_provider, status

    active = await asyncio.to_thread(select_provider, True)
    return {"active_backend": active, **status()}


@router.get("/api/first-install/status")
async def api_first_install_status():
    from core.first_install_bootstrap import is_first_install_pending, _MARKER_FILE

    return {
        "pending": is_first_install_pending(),
        "marker": str(_MARKER_FILE),
        "marker_exists": _MARKER_FILE.exists(),
    }


@router.post("/api/first-install/run")
async def api_first_install_run(force: bool = False):
    from core.first_install_bootstrap import run

    return await asyncio.to_thread(run, force)


@router.post("/api/internal/optimize-parallel")
async def api_internal_optimize_parallel(payload: dict = None):
    from core.parallel_internal_optimizer import run

    payload = payload or {}
    tracks = payload.get("tracks")
    max_workers = payload.get("max_workers")
    return await asyncio.to_thread(run, tracks, max_workers)


@router.post("/api/grok/chat")
async def api_grok_chat(payload: ChatPayload):
    msg = (payload.message or "").strip()
    if not msg:
        return {"status": "error", "error": "empty message"}
    from core.heroic_orchestration import classify_and_normalize
    from core.local_llama import get_local_llama, default_model_pool
    from core.provider_switcher import select_provider_for_query
    from core.claude_science import (
        analyze as science_analyze,
        should_use_claude_science,
        is_unclear_response,
        escalate_to_science,
        is_heroic_science_query,
    )
    normalized, cat, _, dom = classify_and_normalize(msg)
    llama = get_local_llama()
    response = ""
    route_reason = None
    backend = await asyncio.to_thread(select_provider_for_query, normalized)
    use_science, route_reason = should_use_claude_science(normalized)

    if backend == "claude-science" or dom == "Science" or use_science:
        sci = await asyncio.to_thread(science_analyze, normalized)
        if sci.get("ok"):
            response = sci.get("response", "")
            backend = sci.get("backend", "claude-science")
            route_reason = sci.get("route_reason", route_reason)

    if not response and route_reason not in ("science_domain", "heroic_science"):
        if backend == "llama-local" and llama.active:
            try:
                response = await asyncio.to_thread(llama.generate, normalized)
            except Exception as exc:
                response = f"[Llama error: {exc}]"
                backend = "fusion-hero"
        if not response:
            pool = default_model_pool(normalized)
            result = await asyncio.to_thread(_orch().orchestrate, normalized, pool)
            response = result.get("synthesised_response", "")
            backend = result.get("backend", backend or "fusion-hero")
            route_reason = result.get("route_reason", route_reason)

    # Eskalation bei unklaren Ergebnissen oder Heroik-Wissenschaft ohne klare Antwort
    esc_use, esc_reason = should_use_claude_science(normalized, response)
    if esc_use and esc_reason == "unclear_result" and is_unclear_response(response):
        sci = await asyncio.to_thread(escalate_to_science, normalized, response)
        if sci.get("ok") and sci.get("response"):
            response = sci.get("response", "")
            backend = sci.get("backend", "claude-science-escalated")
            route_reason = esc_reason

    return {
        "status": "ok",
        "query": normalized,
        "response": response,
        "backend": backend,
        "route_reason": route_reason,
        "heroic_science": is_heroic_science_query(normalized),
        "category": cat,
        "dom": dom,
        "model_pool": default_model_pool(normalized),
        "provider_auto": os.getenv("FUSION_PROVIDER_AUTO", "1") == "1",
    }


@router.get("/api/meta-layer/status")
async def api_meta_layer_status():
    from core.windows_substrate import get_substrate
    return get_substrate().status()


@router.get("/api/meta-layer/windows")
async def api_meta_layer_windows():
    from core.windows_substrate import get_substrate
    return get_substrate().scan()


@router.post("/api/meta-layer/attach")
async def api_meta_layer_attach():
    from core.windows_substrate import get_substrate
    return get_substrate().attach()


@router.post("/api/windows/substrate/tune")
async def api_windows_substrate_tune():
    from core.windows_substrate import get_substrate
    return get_substrate().tune_substrate()


@router.post("/api/windows/cyber-layer/activate")
async def api_windows_cyber_activate():
    from core.windows_substrate import get_substrate
    return get_substrate().activate_cyber_layer()


@router.get("/api/profile/status")
async def api_profile_status():
    return {
        "name": os.getenv("FUSION_PROFILE", "admin"),
        "performance_ratio": float(os.getenv("FUSION_PERFORMANCE_RATIO", "1.0")),
        "hyperthreading": os.getenv("FUSION_HYPERTHREADING", "1") == "1",
        "all_modules": os.getenv("FUSION_ALL_MODULES", "1") == "1",
    }


@router.post("/api/profile/set")
async def api_profile_set(payload: ProfilePayload):
    name = payload.name.lower()
    os.environ["FUSION_PROFILE"] = name
    ratio = {"admin": 1.0, "balanced": 0.67, "eco": 0.5}.get(name, 0.67)
    os.environ["FUSION_PERFORMANCE_RATIO"] = str(ratio)
    return {"status": "ok", "profile": name, "performance_ratio": ratio}


@router.get("/api/resources/plan")
async def api_resources_plan():
    from core.module_registry import resource_plan
    return resource_plan()


@router.get("/api/resources/workflow")
async def api_resources_workflow(task_weight: str = "medium"):
    from core.resource_workflow import recommend_workers

    return recommend_workers(task_weight)


@router.get("/api/v8/math/status")
async def api_v8_math_status():
    from core.v8_core_bridge import math_status

    return math_status()


@router.post("/api/v8/math/verify")
async def api_v8_math_verify():
    from core.v8_core_bridge import run_math_verification

    return await asyncio.to_thread(run_math_verification)


@router.get("/api/v8/orchestrator/status")
async def api_v8_orchestrator_status():
    from core.v8_core_bridge import orchestrator_status

    return orchestrator_status()


@router.post("/api/v8/orchestrator/bootstrap")
async def api_v8_orchestrator_bootstrap():
    from core.v8_core_bridge import bootstrap_orchestrator

    return await asyncio.to_thread(bootstrap_orchestrator)


@router.post("/api/v8/orchestrator/query")
async def api_v8_orchestrator_query(payload: dict = None):
    from core.v8_core_bridge import process_query

    payload = payload or {}
    domain = payload.get("domain", "GESTALT")
    operator_id = payload.get("operator_id", "OP_Q_B_CIRC")
    return await asyncio.to_thread(process_query, domain, operator_id, payload.get("payload"))


@router.get("/api/viz/geisterjagd-banach")
async def api_viz_geisterjagd_banach(tick: bool = True):
    from core.geisterjagd_banach_viz import get_viz, build_hints_from_system

    viz = get_viz()
    hints: Dict[str, Any] = {"event_rate": 0.3, "queue_pressure": 0.1, "heuristic_score": 0.5}
    if tick:
        try:
            from app import events, TASK_QUEUE, PERFORMANCE_TRACKING

            recent = [e.get("type", "") for e in list(events)[-8:]]
            cpu = 50.0
            try:
                import psutil
                cpu = psutil.cpu_percent(interval=None)
            except Exception:
                pass
            blocked = 0
            try:
                from core.agent_control import status as ac_status
                blocked = ac_status().get("blocked_total", 0)
            except Exception:
                pass
            hints = build_hints_from_system(
                event_count=len(events),
                recent_types=recent,
                queue_len=len(TASK_QUEUE) if TASK_QUEUE else 0,
                cpu_pct=cpu,
                agent_blocked=blocked,
            )
        except Exception:
            pass
        await asyncio.to_thread(viz.tick, hints)
    return viz.snapshot()


@router.get("/api/signal/health")
async def api_signal_health(layer: str = "full"):
    from core.module_registry import signal_health
    return signal_health(layer)


@router.get("/api/jobs/{job_id}")
async def api_job_get(job_id: str):
    from app import JOBS, TASK_QUEUE
    job = JOBS.get(job_id)
    if job:
        return {"status": "ok", "job": job}
    for t in TASK_QUEUE:
        if t.get("id") == job_id:
            return {"status": "ok", "job": t}
    return {"status": "not_found", "job_id": job_id}


@router.get("/api/llama/status")
async def api_llama_status():
    from local_llama import get_local_llama
    return get_local_llama().status()


@router.post("/api/llama/chat")
async def api_llama_chat(payload: ChatPayload):
    from local_llama import get_local_llama
    llama = get_local_llama()
    msg = (payload.message or "").strip()
    if not msg:
        return {"status": "error", "error": "empty message"}
    use_qubo = os.getenv("FUSION_LLAMA_QUBO", "1") == "1"
    if use_qubo:
        result = await asyncio.to_thread(llama.generate_qubo, msg)
        return {
            "status": "ok",
            "response": result.get("response", ""),
            "backend": result.get("backend", "llama-local"),
            "qubo_applied": result.get("qubo_applied", False),
            "qubo_result": result.get("qubo_result"),
            "candidate_scores": result.get("candidate_scores"),
        }
    response = await asyncio.to_thread(llama.generate, msg, None, False)
    return {"status": "ok", "response": response, "backend": "llama-local"}


@router.get("/api/llama/qubo/status")
async def api_llama_qubo_status():
    from core.qubo_llama_bridge import status as qubo_status
    from local_llama import get_local_llama
    return {"llama": get_local_llama().status(), "qubo_bridge": qubo_status()}


@router.get("/api/llama/subagent-tests/status")
async def api_llama_subagent_tests_status():
    from core.llama_subagent_tester import status

    return status()


@router.post("/api/llama/subagent-tests/run")
async def api_llama_subagent_tests_run(payload: dict = None):
    from core.llama_subagent_tester import run

    payload = payload or {}
    subagents = payload.get("subagents")
    max_workers = payload.get("max_workers")
    include_generate = payload.get("include_generate")
    return await asyncio.to_thread(run, subagents, max_workers, include_generate)


@router.get("/api/agent-backend/policy")
async def api_agent_backend_policy():
    from core.agent_backend_router import policy, status

    return {"policy": policy(), "status": status()}


@router.post("/api/agent-backend/dual-run")
async def api_agent_backend_dual_run(payload: ChatPayload):
    from core.agent_backend_router import dual_run

    msg = (payload.message or "").strip()
    if not msg:
        return {"status": "error", "error": "empty message"}
    return await asyncio.to_thread(dual_run, msg, {})


@router.post("/api/agent-backend/invoke")
async def api_agent_backend_invoke(payload: dict = None):
    from core.agent_backend_router import invoke

    payload = payload or {}
    role = payload.get("role", "agent")
    query = (payload.get("query") or payload.get("message") or "").strip()
    if not query:
        return {"status": "error", "error": "empty query"}
    result = await asyncio.to_thread(
        invoke, role, query, payload.get("context"), payload.get("agent_response"),
    )
    return {"status": "ok" if result.get("ok") else "error", **result}


@router.post("/api/subagents/llama-test")
async def api_subagents_llama_test(payload: dict = None):
    """Alias: Subagenten führen Llama-Test-Tracks parallel aus."""
    from core.llama_subagent_tester import run

    payload = payload or {}
    return await asyncio.to_thread(
        run,
        payload.get("subagents"),
        payload.get("max_workers"),
        payload.get("include_generate"),
        payload.get("seed_context"),
    )


@router.get("/api/context/window/status")
async def api_context_window_status():
    from core.conversation_context_core import status

    return status()


@router.post("/api/context/window/init")
async def api_context_window_init(payload: dict = None):
    from core.conversation_context_core import init_root

    payload = payload or {}
    seed = (payload.get("seed_text") or payload.get("query") or payload.get("message") or "").strip()
    if not seed:
        return {"status": "error", "error": "empty seed_text"}
    return await asyncio.to_thread(
        init_root,
        seed,
        payload.get("task_meta"),
        bool(payload.get("force_new")),
    )


@router.post("/api/context/window/subagent")
async def api_context_window_subagent(payload: dict = None):
    from core.conversation_context_core import allocate_subagent

    payload = payload or {}
    name = (payload.get("subagent_name") or payload.get("name") or "").strip()
    if not name:
        return {"status": "error", "error": "empty subagent_name"}
    return await asyncio.to_thread(
        allocate_subagent,
        name,
        payload.get("task_weight", "medium"),
        payload.get("seed_fragment"),
    )


@router.post("/api/context/window/feedback")
async def api_context_window_feedback(payload: dict = None):
    from core.conversation_context_core import feedback

    payload = payload or {}
    wid = (payload.get("window_id") or payload.get("subagent_id") or "").strip()
    text = (payload.get("result_text") or payload.get("result") or payload.get("message") or "").strip()
    if not wid or not text:
        return {"status": "error", "error": "window_id and result_text required"}
    return await asyncio.to_thread(feedback, wid, text, payload.get("metadata"))


@router.get("/api/medienserver/status")
async def api_medienserver_status():
    from core.medienserver_bridge import status as ms_status

    return ms_status()


@router.get("/api/autoload/status")
async def api_autoload_status():
    from autoloader import autoload_status

    return autoload_status()


@router.post("/api/autoload/run")
async def api_autoload_run(payload: AutoLoadPayload):
    from autoloader import run_autoload

    return await run_autoload(
        phase=payload.phase,
        force=payload.force,
        sync_medienserver=payload.sync,
        attach_meta=payload.attach_meta,
    )


@router.get("/api/hero-guide/status")
async def api_hero_guide_status():
    import sys
    from pathlib import Path

    code_root = Path(__file__).resolve().parents[1]
    if str(code_root) not in sys.path:
        sys.path.insert(0, str(code_root))
    from hero_guide_ide import status as hg_status
    from audit_agent import status as audit_status

    return {"hero_guide": hg_status(), "audit_agent": audit_status()}


@router.get("/api/hero-guide/audit")
async def api_hero_guide_audit(limit: int = 50):
    import sys
    from pathlib import Path

    code_root = Path(__file__).resolve().parents[1]
    if str(code_root) not in sys.path:
        sys.path.insert(0, str(code_root))
    from hero_guide_ide import get_workbench

    wb = get_workbench(with_graph=False)
    return {"audit_log": wb.audit_log[-limit:], "total": len(wb.audit_log)}


@router.post("/api/hero-guide/resolve")
async def api_hero_guide_resolve(payload: HeroGuideResolvePayload):
    import sys
    from pathlib import Path

    code_root = Path(__file__).resolve().parents[1]
    if str(code_root) not in sys.path:
        sys.path.insert(0, str(code_root))
    from audit_agent import audit_claim

    return await asyncio.to_thread(
        audit_claim,
        payload.text,
        payload.kategorie,
        payload.praemissen,
        payload.praemissen_erfuellt,
        payload.fehlende_praemisse,
        persist=payload.persist,
    )


@router.get("/api/knowledge-graph/status")
async def api_knowledge_graph_status():
    import sys
    from pathlib import Path

    code_root = Path(__file__).resolve().parents[1]
    if str(code_root) not in sys.path:
        sys.path.insert(0, str(code_root))
    from knowledge_graph import get_knowledge_graph

    return get_knowledge_graph().status()


@router.get("/api/knowledge-graph/nodes")
async def api_knowledge_graph_nodes(limit: int = 50):
    import sys
    from pathlib import Path

    code_root = Path(__file__).resolve().parents[1]
    if str(code_root) not in sys.path:
        sys.path.insert(0, str(code_root))
    from knowledge_graph import get_knowledge_graph

    return {"nodes": get_knowledge_graph().list_nodes(limit)}


@router.post("/api/knowledge-graph/write")
async def api_knowledge_graph_write(payload: HeroGuideResolvePayload):
    import sys
    from pathlib import Path

    code_root = Path(__file__).resolve().parents[1]
    if str(code_root) not in sys.path:
        sys.path.insert(0, str(code_root))
    from audit_agent import audit_before_write

    body = payload.model_dump()
    body["persist"] = True
    return await asyncio.to_thread(audit_before_write, body)


@router.post("/api/mod/validate-code")
async def api_mod_validate_code(payload: CodeValidatePayload):
    import re
    import sys
    from pathlib import Path

    code_root = Path(__file__).resolve().parents[1]
    if str(code_root) not in sys.path:
        sys.path.insert(0, str(code_root))

    checks = [
        ("Alternativen", r"(alternativ|gegenargument|jedoch|stattdessen|abwägung)"),
        ("Implikationen", r"(implikation|folge|handlungsempfehl|nächst|next step)"),
        ("Risiken/Lücken", r"(risik|unsicher|lücke|tbd|todo|offen)"),
    ]
    review = [{"name": n, "ok": bool(re.search(p, payload.code, re.I))} for n, p in checks]
    passed = sum(c["ok"] for c in review)
    hero_guide_scan = []
    try:
        from audit_agent import scan_code_claims

        hero_guide_scan = scan_code_claims(payload.code)
    except Exception:
        pass
    return {
        "checks": review,
        "passed": passed,
        "total": len(review),
        "accepted": passed >= 2,
        "hero_guide_scan": hero_guide_scan,
    }