# -*- coding: utf-8 -*-
"""
fusion_hero_node.py — HAUPTKNOTEN: Fusion aller dienlichen Module
=================================================================
Führt die kreative Problemlösungs-Pipeline mit der Parallel-/Hyperthreading-
Schicht und den ressourcen-, kosten- und kontextbewussten Knoten zu EINER
Pipeline zusammen. Ein Aufruf — `fuse(problem)` — orchestriert:

  1. CAPABILITY-SNAPSHOT  Alle dienlichen Module werden optional (graceful,
     try/except) geprobt: hyperthreading_config, resource_workflow,
     cost_estimator_node, conversation_context_core, provider_switcher,
     agent_backend_router, claude_science, structured_output. Nichts davon ist
     Pflicht — fehlt ein Modul, läuft der Rest weiter.

  2. WORKER-SIZING (HT + Last)  Die Zahl paralleler Worker wird NICHT blind aus
     dem HT-Spektrum übernommen (das oversubscribed absichtlich), sondern
     last-bewusst gedeckelt:
        workers = clamp( resource_workflow.recommend_workers(task_weight),
                         1, min(logical_cpus, ht.parallel_workers, n_strategien) )
     -> Hyperthreading beschleunigt, wenn Ressourcen frei sind; unter Last
        (RAM/CPU/llama-server) fällt es automatisch auf seriell zurück.

  3. PARALLELE DIVERGENZ+GENERIERUNG  Die 7 Strategie-Umformulierungen aus
     creative_problem_solving werden über einen ThreadPoolExecutor gleichzeitig
     an das Backend (Agent-Rolle) gegeben — dieselbe Mechanik wie
     parallel_internal_optimizer.run().

  4. KONVERGENZ  Scoring (lexikalisch) + Simulated-Annealing-Portfolio.

  5. ADVERSARIALE KRITIK  Anti-Agent prüft den besten Kandidaten (falls online).

  6. FEEDBACK-KOPPLUNG  Gemessene Laufzeit fließt (falls vorhanden) an
     cost_estimator_node zurück; ein Kontext-Anker wird in
     conversation_context_core registriert. Beides best-effort, nie blockierend.

Ehrlich (Code-Honesty):
  * Threads helfen hier nur bei I/O-/latenzgebundenen Backend-Calls (LLM-API,
    llama-server) — dort geben die Calls den GIL frei. Bei CPU-gebundener
    reiner Python-Arbeit oder dem Offline-Stub bringt Parallelität ~nichts;
    das wird im Ergebnis als `parallel_effective` transparent gemeldet.
  * Scores bleiben lexikalische Heuristiken (siehe creative_problem_solving).
  * Alle Kopplungen sind optional; ein Minimal-Setup (nur cps) funktioniert.

Aufruf:  python fusion_hero_node.py     # Offline-Demo (parallel, ohne Netz)
"""
from __future__ import annotations

import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Dict, List, Optional, Sequence

import creative_problem_solving as cps

BackendFn = Callable[[str, str], str]  # (prompt, role) -> antwort


# ---------------------------------------------------------------------------
# 1. Capability-Snapshot — welche dienlichen Module sind da?
# ---------------------------------------------------------------------------

def _probe(fn: Callable[[], Any]) -> Dict[str, Any]:
    """Ruft eine Probe-Funktion best-effort; kapselt Fehler als available=False."""
    try:
        return {"available": True, "info": fn()}
    except Exception as exc:  # Modul fehlt / optionales Dep / Laufzeitfehler
        return {"available": False, "error": str(exc)}


def capability_snapshot() -> Dict[str, Any]:
    """Prüft alle dienlichen Module optional und meldet ihren Status."""
    snap: Dict[str, Any] = {}

    def _ht() -> Dict[str, Any]:
        import hyperthreading_config as ht
        return {
            "enabled": ht.is_hyperthreading_enabled(),
            "logical_cpus": ht.logical_cpu_count(),
            "ht_workers": ht.parallel_workers(),
        }

    def _rw() -> Dict[str, Any]:
        import resource_workflow as rw
        return rw.recommend_workers("medium")

    snap["hyperthreading"] = _probe(_ht)
    snap["resource_workflow"] = _probe(_rw)
    snap["cost_estimator"] = _probe(lambda: __import__("cost_estimator_node").__name__)
    snap["conversation_context"] = _probe(lambda: __import__("conversation_context_core").__name__)
    snap["provider_switcher"] = _probe(lambda: __import__("provider_switcher").__name__)
    snap["agent_backend_router"] = _probe(lambda: __import__("agent_backend_router").policy())
    snap["claude_science"] = _probe(lambda: __import__("claude_science").is_available())
    snap["structured_output"] = _probe(lambda: __import__("structured_output").status()["module"])
    return snap


# ---------------------------------------------------------------------------
# 2. Worker-Sizing — Hyperthreading UND Last berücksichtigen
# ---------------------------------------------------------------------------

def resolve_workers(
    n_tasks: int,
    task_weight: str = "medium",
    override: Optional[int] = None,
) -> Dict[str, Any]:
    """Bestimmt die parallele Worker-Zahl last- und HT-bewusst.

    Reihenfolge: expliziter Override > last-bewusste Empfehlung, gedeckelt auf
    min(logische CPUs, HT-Worker, Task-Zahl). Immer >= 1.
    """
    n_tasks = max(1, int(n_tasks))
    reasons: List[str] = []

    # Obergrenze aus Hardware/HT
    logical = n_tasks
    ht_cap = n_tasks
    try:
        import hyperthreading_config as ht
        logical = max(1, ht.logical_cpu_count())
        ht_cap = max(1, ht.parallel_workers())
        reasons.append(f"logical_cpus={logical}, ht_workers={ht_cap}")
    except Exception:
        reasons.append("hyperthreading_config nicht verfügbar -> Deckel = Task-Zahl")

    ceiling = min(n_tasks, logical, ht_cap)

    if override is not None and override > 0:
        workers = min(override, n_tasks)
        reasons.append(f"override={override}")
        return {"workers": max(1, workers), "ceiling": ceiling, "mode": "override", "reasons": reasons}

    # Last-bewusste Empfehlung als Primärsignal
    recommended = ceiling
    mode = "static-ceiling"
    try:
        import resource_workflow as rw
        rec = rw.recommend_workers(task_weight)
        recommended = int(rec.get("recommended_workers", ceiling))
        mode = rec.get("mode", "load-aware")
        reasons.append(f"resource_workflow: {rec.get('reason')} -> {recommended} ({mode})")
    except Exception:
        reasons.append("resource_workflow nicht verfügbar -> nutze Ceiling")

    workers = max(1, min(recommended, ceiling))
    return {"workers": workers, "ceiling": ceiling, "mode": mode, "reasons": reasons}


# ---------------------------------------------------------------------------
# 3. Parallele Divergenz + Generierung (Hyperthreading-Fan-out)
# ---------------------------------------------------------------------------

def _select_backend(backend: Optional[BackendFn]) -> tuple[BackendFn, str, bool]:
    """Wählt das effektive Backend: injiziert > Router > Offline-Stub."""
    if backend is not None:
        return backend, "injected", False
    if cps._force_offline():
        return (lambda p, r: cps._offline_stub_backend(p, r)), "offline-stub", True
    # Router-Preflight: ein billiger Probelauf entscheidet, ob live oder Stub
    try:
        cps._router_backend("[preflight] ping", "agent")
        return (lambda p, r: cps._router_backend(p, r)), "agent_backend_router", False
    except Exception:
        return (lambda p, r: cps._offline_stub_backend(p, r)), "offline-stub", True


def parallel_generate(
    problem: str,
    backend: Optional[BackendFn] = None,
    strategy_keys: Optional[Sequence[str]] = None,
    task_weight: str = "medium",
    worker_override: Optional[int] = None,
) -> Dict[str, Any]:
    """Fan-out der Strategie-Umformulierungen über einen ThreadPoolExecutor."""
    frames = cps.diversify(problem, strategy_keys)
    if not frames:
        return {"candidates": [], "workers": 1, "parallel_effective": False, "sizing": {}}

    fn, backend_label, is_stub = _select_backend(backend)
    sizing = resolve_workers(len(frames), task_weight, worker_override)
    workers = sizing["workers"]

    def _one(frame: Dict[str, str]) -> Dict[str, Any]:
        used = backend_label
        try:
            text = fn(frame["prompt"], "agent")
        except Exception as exc:
            text = f"[backend-error] {exc}"
            used = f"{backend_label}-error"
        return {
            "strategy": frame["strategy"],
            "title": frame["title"],
            "prompt": frame["prompt"],
            "response": text,
            "backend": used,
        }

    candidates: List[Dict[str, Any]] = []
    if workers <= 1 or len(frames) <= 1:
        candidates = [_one(f) for f in frames]
    else:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(_one, f): f["strategy"] for f in frames}
            for fut in as_completed(futures):
                candidates.append(fut.result())

    # Reihenfolge nach ursprünglicher Strategie-Reihenfolge stabilisieren
    order = {f["strategy"]: i for i, f in enumerate(frames)}
    candidates.sort(key=lambda c: order.get(c["strategy"], 0))

    # Parallelität ist nur wirksam, wenn Backend latenzgebunden (nicht Stub) ist
    parallel_effective = workers > 1 and not is_stub and backend_label != "offline-stub"
    return {
        "candidates": candidates,
        "workers": workers,
        "parallel_effective": parallel_effective,
        "backend": backend_label,
        "sizing": sizing,
    }


# ---------------------------------------------------------------------------
# 6. Feedback-Kopplung (optional, best-effort)
# ---------------------------------------------------------------------------

def _observe_cost(elapsed_ms: float, n_tasks: int) -> Optional[Dict[str, Any]]:
    """Meldet die reale Laufzeit an cost_estimator_node (falls vorhanden).

    observe() ist eine Methode auf get_node(); der Wert speist die EWMA-Schätzung
    für (Portal='fusion_hero', Aktion='creative_solve') und macht künftige
    Worker-/Kostenentscheidungen datengetrieben.
    """
    try:
        import cost_estimator_node as ce
        per_task = elapsed_ms / max(1, n_tasks)
        ce.get_node().observe("fusion_hero", "creative_solve", per_task)
        return {"observed_ms_per_task": round(per_task, 1)}
    except Exception:
        return None


def _anchor_context(problem: str, portfolio: List[Dict[str, Any]]) -> Optional[str]:
    """Verankert das Problem als Root-Kontext (best-effort, nicht überschreibend).

    init_root(force_new=False) setzt nur einen Root-Anker, wenn noch keiner
    existiert — es klobbert keinen fremden Kontext. Damit hängt sich die
    Fusions-Pipeline in dieselbe Banach-Rückkopplung wie die Subagenten.
    """
    try:
        import conversation_context_core as ctx
        summary = "; ".join(f"{c['strategy']}={c.get('score')}" for c in portfolio[:3])
        anchor = f"Kreativlösung: {problem[:160]} | Portfolio: {summary}"
        res = ctx.init_root(anchor, task_meta={"source": "fusion_hero_node"}, force_new=False)
        if isinstance(res, dict) and res.get("disabled"):
            return None
        return "init_root"
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Orchestrierung: der eine Fusions-Aufruf
# ---------------------------------------------------------------------------

def fuse(
    problem: str,
    backend: Optional[BackendFn] = None,
    strategy_keys: Optional[Sequence[str]] = None,
    task_weight: str = "medium",
    portfolio_size: int = cps._PORTFOLIO_SIZE,
    with_critique: bool = True,
    worker_override: Optional[int] = None,
    seed: int = cps._SA_SEED,
) -> Dict[str, Any]:
    """Voller Fusions-Durchlauf: Snapshot → HT-Sizing → parallel → Konvergenz → Kritik → Feedback."""
    problem = (problem or "").strip()
    if not problem:
        return {"ok": False, "error": "empty problem"}

    t0 = time.perf_counter()
    caps = capability_snapshot()

    gen = parallel_generate(
        problem, backend=backend, strategy_keys=strategy_keys,
        task_weight=task_weight, worker_override=worker_override,
    )
    candidates = cps.score_candidates(gen["candidates"], problem)
    portfolio = cps.anneal_select(candidates, k=portfolio_size, seed=seed)

    offline = all(c.get("backend", "").startswith("offline-stub") for c in candidates) if candidates else True
    critique: Optional[Dict[str, Any]] = None
    if with_critique and portfolio and not offline:
        critique = cps.critique_top(problem, portfolio[0], backend=backend)

    elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)
    cost_feedback = _observe_cost(elapsed_ms, len(candidates))
    context_anchor = _anchor_context(problem, portfolio)

    return {
        "ok": True,
        "problem": problem,
        "workers": gen["workers"],
        "parallel_effective": gen["parallel_effective"],
        "worker_sizing": gen["sizing"],
        "backend": gen["backend"],
        "offline": offline,
        "n_strategies": len(candidates),
        "portfolio": portfolio,
        "all_candidates": candidates,
        "critique": critique,
        "capabilities": {k: v.get("available", False) for k, v in caps.items()},
        "capability_detail": caps,
        "cost_feedback": cost_feedback,
        "context_anchor": context_anchor,
        "elapsed_ms": elapsed_ms,
        "honesty": (
            "Threads beschleunigen nur latenzgebundene Backend-Calls (LLM/llama); "
            "Offline-Stub und CPU-gebundene Arbeit profitieren nicht (siehe parallel_effective). "
            "Scores sind lexikalische Heuristiken."
        ),
    }


def status() -> Dict[str, Any]:
    caps = capability_snapshot()
    return {
        "module": "fusion_hero_node",
        "role": "HAUPTKNOTEN — Fusion aller dienlichen Module",
        "pipeline": ["capability_snapshot", "resolve_workers(HT+Last)", "parallel_generate",
                     "score+anneal", "anti_agent_critique", "cost+context feedback"],
        "capabilities": {k: v.get("available", False) for k, v in caps.items()},
        "strategies": len(cps.STRATEGIES),
        "honesty": "Parallelität wirkt nur bei latenzgebundenen Backends; Kopplungen optional/best-effort",
    }


if __name__ == "__main__":
    os.environ.setdefault("FUSION_CREATIVE_OFFLINE", "1")  # Demo hängt nie an Backends
    demo = (
        "Der lokale Llama-Agent liefert bei mehrstufigen Aufgaben inkonsistente "
        "Zwischenergebnisse, weil Kontext zwischen Schritten verloren geht."
    )
    res = fuse(demo, with_critique=False)
    print(f"workers={res['workers']} (effektiv parallel={res['parallel_effective']}) "
          f"offline={res['offline']} {res['elapsed_ms']}ms")
    print("Capabilities:", {k: v for k, v in res["capabilities"].items() if v})
    for c in res["portfolio"]:
        print(f"  [{c['strategy']}] score={c['score']} novelty={c['novelty']} coverage={c['coverage']}")
    print("Sizing:", res["worker_sizing"]["reasons"])
