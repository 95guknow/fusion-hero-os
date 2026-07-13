# -*- coding: utf-8 -*-
"""Worker-Tasks — Ausfuehrung ausserhalb des Eingabe-Layers."""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from grok_bridge import get_grok_bridge
from module_registry import get_registry
from fusion_profile import set_profile
from meta_layer_windows import attach_meta_layer
from hyperthreading_config import status as ht_status, is_hyperthreading_enabled
from layered_signal_network import emit_signal

BOOT_N = 12
BOOT_STEPS = 2000

_REVIEW_CHECKS = (
    ("Evidenz/Quellen", r"(quelle|source|ref|http|doi|zitat)"),
    ("Logische Kette", r"(→|=>|daher|because|weil|therefore|deshalb|folgt)"),
    ("Alternativen", r"(alternativ|gegenargument|jedoch|stattdessen|abwägung)"),
    ("Implikationen", r"(implikation|folge|handlungsempfehl|nächst|next step)"),
    ("Risiken/Lücken", r"(risik|unsicher|lücke|tbd|todo|offen)"),
)


def _load_all(force: bool = False, phase: str = "auto", sync: bool = False) -> dict:
    result = get_registry().load_all(
        boot_n=BOOT_N, boot_steps=BOOT_STEPS, force=force, phase=phase, sync_medienserver=sync,
    )
    try:
        import app as fusion_app
        fusion_app._sync_globals_from_registry(result)
        fusion_app._invalidate_health_cache()
    except Exception:
        pass
    return result


def _solve_qubo(n: int = 12, steps: int = 2000, parallel: bool = True) -> dict:
    import heroic_core_mainframe as hc
    reg = get_registry()
    if reg.mainframe:
        Q = hc.make_Q(n, submodular=False, scale=2.5)
        if parallel and is_hyperthreading_enabled():
            out = reg.mainframe.execute_parallel_run(
                Q, steps=steps, T0=2.5, n_restarts=ht_status().get("workers"),
            )
            return {
                "energy": round(float(out["energy"]), 6),
                "engine": "mainframe_parallel",
                "workers": out["workers"],
                "time_ms": round(out["runtime_seconds"] * 1000, 2),
            }
        cfg = hc.QUBOSolverConfig(backend="simulated_annealing", steps=steps, T0=2.5)
        res = reg.mainframe.execute_secure_run(Q, config=cfg)
        return {"energy": round(float(res.energy), 6), "engine": "mainframe", "time_ms": round(res.runtime_seconds * 1000, 2)}
    return {"error": "mainframe offline"}


def _health_light() -> dict:
    reg = get_registry()
    return {
        "mainframe_loaded": bool(reg.mainframe),
        "modules": len(reg.modules),
        "agents": len(reg.agents),
        "hyperthreading": ht_status(),
    }


def execute_intent(intent: str, payload: Optional[dict] = None) -> dict:
    payload = payload or {}
    reg = get_registry()
    try:
        if intent == "load_all":
            r = _load_all(force=False, phase="auto", sync=False)
            return {"intent": intent, "status": "ok", "summary": r.get("summary", {})}
        if intent == "mainframe_load":
            r = _load_all(force=False, phase="staged", sync=False)
            return {"intent": intent, "status": "ok", "summary": r.get("summary", {})}
        if intent == "benchmark":
            return {"intent": intent, "status": "ok", "result": _solve_qubo(14, 6000, True)}
        if intent == "sync":
            if reg.google_sync:
                r = reg.google_sync.sync_horkrux("fusion-hero-os-v1.2", list(reg.google_sync.sync_targets))
            else:
                r = reg._sync_medienserver(force=True)
            return {"intent": intent, "status": "ok", "result": r}
        if intent == "pipeline":
            pipe = reg.mainframe_pipeline_status()
            pipe["hyperthreading"] = ht_status()
            return {"intent": intent, "status": "ok", "result": pipe}
        if intent == "layer4":
            return {"intent": intent, "status": "ok", "result": reg.layer4_status()}
        if intent == "ht_on":
            return {"intent": intent, "status": "ok", "result": reg.set_hyperthreading(True)}
        if intent == "ht_off":
            return {"intent": intent, "status": "ok", "result": reg.set_hyperthreading(False)}
        if intent == "qubo":
            return {"intent": intent, "status": "ok", "result": _solve_qubo(
                payload.get("n", BOOT_N), payload.get("steps", BOOT_STEPS), payload.get("parallel", True),
            )}
        if intent == "health":
            return {"intent": intent, "status": "ok", "result": _health_light()}
        if intent == "agents":
            return {"intent": intent, "status": "ok", "agents": reg.list_agents(enrich_resources=True)}
        if intent == "meta_layer":
            return {"intent": intent, "status": "ok", "result": attach_meta_layer().to_dict()}
        if intent == "profile_admin":
            return {"intent": intent, "status": "ok", "result": set_profile("admin", "worker")}
        if intent == "resources":
            return {"intent": intent, "status": "ok", "result": reg.resource_plan(force=True)}
        if intent == "signal_network":
            snap = {"backend": "online", "mainframe": {"loaded": bool(reg.mainframe)}, "metrics": {}}
            sig = emit_signal(snap, "delta", "worker", False)
            return {"intent": intent, "status": "ok", "result": sig.to_dict()}
        if intent in ("autoload", "autoloader", "auto_load"):
            from autoloader import run_autoload_sync
            phase = payload.get("phase", "staged")
            return {
                "intent": intent,
                "status": "ok",
                "result": run_autoload_sync(
                    phase=phase,
                    force=bool(payload.get("force")),
                    sync_medienserver=bool(payload.get("sync")),
                    attach_meta=payload.get("attach_meta", True),
                ),
            }
        if intent in ("substrate_tune", "windows_substrate", "windows_tune"):
            from windows_perf_tuner import apply_substrate_tuning, apply_windows_tuning
            fn = apply_windows_tuning if intent == "windows_tune" else apply_substrate_tuning
            return {"intent": intent, "status": "ok", "result": fn(
                power=True,
                dedupe=(intent == "windows_tune"),
                priority=True,
                env=True,
            )}
        if intent == "orchestrate":
            if not reg.orchestrator:
                return {"intent": intent, "status": "error", "error": "Orchestrator nicht geladen"}
            plan = reg.resource_plan(force=False)
            return {
                "intent": intent,
                "status": "ok",
                "result": reg.orchestrator.orchestrate(
                    payload.get("query", ""),
                    payload.get("models") or plan.get("model_pool"),
                    {
                        "orchestrator_workers": plan.get("orchestrator_workers"),
                        "resource_plan": plan,
                        "routing": "worker_intent",
                    },
                ),
            }
        return {"intent": intent, "status": "unknown"}
    except Exception as exc:
        return {"intent": intent, "status": "error", "error": str(exc)}


def execute_job(job: dict) -> dict:
    intents: List[str] = list(job.get("intents") or [])
    kind = job.get("kind", "command")
    message = job.get("message", "")
    code = job.get("code", "")
    payload = job.get("payload") or {}
    history = job.get("history") or []

    if not intents and kind not in ("chat", "command", "peer_review", "foundation", "hero_guide", "agent", "orchestrate"):
        intents = [kind.replace("-", "_")]

    executed = [execute_intent(i, payload) for i in intents]

    if kind == "peer_review" or (code and not intents):
        checks = [{"name": n, "ok": bool(re.search(p, code, re.I))} for n, p in _REVIEW_CHECKS]
        passed = sum(c["ok"] for c in checks)
        return {"kind": "peer_review", "checks": checks, "passed": passed, "accepted": passed >= 3, "executed": executed}

    if kind == "foundation":
        try:
            from foundation import check_foundation_gate
            report = check_foundation_gate(code or message, payload.get("require_explicit", False))
            return {
                "kind": "foundation", "passed": report.passed,
                "findings": [{"kind": f.kind} for f in report.findings[:8]], "executed": executed,
            }
        except Exception as exc:
            return {"kind": "foundation", "error": str(exc), "executed": executed}

    if kind == "hero_guide":
        try:
            from audit_agent import audit_claim, audit_before_write
            text = payload.get("text") or message or code
            if payload.get("persist"):
                result = audit_before_write({
                    "text": text,
                    "kategorie": payload.get("kategorie", "FRAGMENT"),
                    "praemissen": payload.get("praemissen") or [],
                    "praemissen_erfuellt": bool(payload.get("praemissen_erfuellt", False)),
                    "fehlende_praemisse": payload.get("fehlende_praemisse", ""),
                })
            else:
                result = audit_claim(
                    text,
                    kategorie=payload.get("kategorie", "FRAGMENT"),
                    praemissen=payload.get("praemissen"),
                    praemissen_erfuellt=bool(payload.get("praemissen_erfuellt", False)),
                    fehlende_praemisse=payload.get("fehlende_praemisse", ""),
                    persist=False,
                )
            return {"kind": "hero_guide", **result, "executed": executed}
        except Exception as exc:
            return {"kind": "hero_guide", "error": str(exc), "executed": executed}

    if kind == "agent":
        return {
            "kind": "agent",
            "result": get_registry().use_agent(payload.get("agent_id", ""), payload.get("query", message)),
            "executed": executed,
        }

    orchestrator_result = None
    if kind == "orchestrate" or payload.get("orchestrate"):
        reg = get_registry()
        if reg.orchestrator:
            plan = reg.resource_plan(force=False)
            orchestrator_result = reg.orchestrator.orchestrate(
                payload.get("query", message),
                payload.get("models") or plan.get("model_pool"),
                {
                    "orchestrator_workers": plan.get("orchestrator_workers"),
                    "resource_plan": plan,
                    "routing": "worker_orchestrate",
                    "history_len": len(history),
                },
            )

    health = _health_light()
    chat = get_grok_bridge().chat(message, history=history, health={"metrics": {}, "v12": {}, "mainframe": health}, orchestrator_result=orchestrator_result)
    out = chat.to_dict()
    out["executed"] = executed
    out["processed_by"] = "worker"
    return out