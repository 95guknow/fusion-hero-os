# heroic_orchestration.py
# Fusion Hero OS - Consolidated orchestration layer
# Merges: classification (HERO-GUIDE), agent loading/assignment, task orchestration,
# and thin wrapper around DynamicOrchestration + agents.Supervisor.
#
# Goal: Avoid duplication of "immer prüfen + auto zuordnen" logic between
# workspace.py, app.py, and future consumers.
#
# Usage:
#   from heroic_orchestration import (
#       load_guide, classify_and_normalize, ensure_agents_loaded,
#       assign_task_to_agent, get_orchestrator
#   )

from __future__ import annotations
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))  # allow sibling imports for core modules
import json
from typing import Any, Dict, List, Optional, Tuple

# --- Paths ---
_HERE = os.path.dirname(__file__)
_GUIDE_PATH = os.path.join(_HERE, '..', '02_Mathematik', 'hero-guide_geltungsstand.json')
_V22_AGENTS_PATH = os.path.join(_HERE, 'FusionHeroOS_v2.2')

# --- Cache ---
_GUIDE_CACHE: Optional[List[Dict[str, Any]]] = None
_AGENT_SUPERVISOR: Any = None
_LOADED_AGENTS: Dict[str, Dict[str, Any]] = {}
_AGENTS_LOADED: bool = False

# Optional import of real agents framework
_AGENTS_MODULE = None
try:
    if _V22_AGENTS_PATH not in sys.path:
        sys.path.insert(0, _V22_AGENTS_PATH)
    import agents as _AGENTS_MODULE  # type: ignore
except Exception:
    _AGENTS_MODULE = None

# Thin wrapper for the existing dynamic orchestrator
_ORCHESTRATOR: Any = None
try:
    from dynamic_orchestration_core import DynamicOrchestrationCoreModule
    _ORCHESTRATOR = DynamicOrchestrationCoreModule()
except Exception:
    _ORCHESTRATOR = None


def load_guide() -> List[Dict[str, Any]]:
    """Load HERO-GUIDE once."""
    global _GUIDE_CACHE
    if _GUIDE_CACHE is None:
        try:
            with open(_GUIDE_PATH, encoding='utf-8') as f:
                _GUIDE_CACHE = json.load(f)
        except Exception:
            _GUIDE_CACHE = []
    return _GUIDE_CACHE or []


def classify_and_normalize(query: str) -> Tuple[str, str, Optional[Dict], str]:
    """Eingabe IMMER prüfen + auto-tag + dom detection (HERO-GUIDE)."""
    query = (query or "").strip()
    if not query:
        return query, "model", None, "General"

    cats = ['proven', 'cond', 'model', 'frag', 'over']
    has_geltung = any(f"[{c}]" in query for c in cats) or any(f"#{c}" in query for c in cats)

    guide = load_guide()
    matched = None
    best_cat = "model"
    dom = "General"

    q_lower = query.lower()
    for entry in guide:
        name = entry.get('name', '').lower()
        if any(kw in q_lower for kw in name.split()[:3] if len(kw) > 3) or \
           entry.get('dom', '').lower() in q_lower:
            matched = entry
            best_cat = entry.get('cat', 'model')
            dom = entry.get('dom', 'General')
            break

    normalized = query
    if not has_geltung:
        prefix = f"[{best_cat}] "
        if not query.startswith('['):
            normalized = prefix + query

    return normalized, best_cat, matched, dom


def ensure_agents_loaded(force: bool = False) -> bool:
    """Agenten IMMER automatisch laden (bevorzugt echte Supervisor aus agents.py)."""
    global _AGENTS_LOADED, _AGENT_SUPERVISOR, _LOADED_AGENTS

    if _AGENTS_LOADED and not force:
        return True

    _LOADED_AGENTS = {}

    if _AGENTS_MODULE is not None:
        try:
            if _AGENT_SUPERVISOR is None or force:
                _AGENT_SUPERVISOR = _AGENTS_MODULE.Supervisor(
                    name="fusion-hero-supervisor",
                    min_workers=2,
                    max_workers=12,
                )
                _AGENT_SUPERVISOR.start()
            _AGENTS_LOADED = True
            _LOADED_AGENTS["supervisor"] = {
                "name": _AGENT_SUPERVISOR.name,
                "role": "supervisor",
                "state": getattr(_AGENT_SUPERVISOR, "state", "running"),
            }
            for child in getattr(_AGENT_SUPERVISOR, "children", lambda: [])():
                _LOADED_AGENTS[child.name] = {
                    "name": child.name,
                    "role": getattr(child, "role", "worker"),
                    "state": "running",
                }
            return True
        except Exception:
            pass

    # Robust fallback (domain-aware workers)
    _AGENTS_LOADED = True
    _AGENT_SUPERVISOR = None
    _LOADED_AGENTS = {
        "supervisor": {"name": "fusion-hero-supervisor", "role": "supervisor", "state": "running", "children": 4},
        "math-worker": {"name": "math-worker", "role": "worker", "dom": "Math"},
        "phil-worker": {"name": "phil-worker", "role": "worker", "dom": "Phil"},
        "info-worker": {"name": "info-worker", "role": "worker", "dom": "Info"},
        "general-worker": {"name": "general-worker", "role": "worker"},
    }
    return True


def get_loaded_agents() -> Dict[str, Dict[str, Any]]:
    return dict(_LOADED_AGENTS)


def get_agent_supervisor():
    return _AGENT_SUPERVISOR


def assign_task_to_agent(task: Dict[str, Any]) -> str:
    """Auto-assign agent based on dom/geltung. Respects hyperthreading worker scaling."""
    ensure_agents_loaded()
    dom = task.get("dom", "General")
    agent_name = {
        "Math": "math-worker",
        "Phil": "phil-worker",
        "Info": "info-worker",
    }.get(dom, "general-worker")

    # HT scaling hint (more parallel tracks when enabled)
    try:
        import hyperthreading_config as _htc
        if _htc.status().get("enabled"):
            task["ht_workers"] = _htc.parallel_workers()
    except Exception:
        pass

    # Wire to qubo_miner external if available for QUBO tasks
    if "qubo" in str(task.get("dom", "")).lower() or "qubo" in str(task.get("query", "")).lower():
        try:
            if EXTERNAL_QUBO_SOLVER:
                task["external_solver"] = "qubo_miner"
                # pass vht cache if set
                try:
                    from virtual_gpu_hyperthreading import get_virtual_gpu_ht_cache
                    if hasattr(EXTERNAL_QUBO_SOLVER, 'vht_cache') and not getattr(EXTERNAL_QUBO_SOLVER, 'vht_cache', None):
                        EXTERNAL_QUBO_SOLVER.vht_cache = get_virtual_gpu_ht_cache()
                except:
                    pass
        except:
            pass

    sup = _AGENT_SUPERVISOR
    if sup and hasattr(sup, "task_queue"):
        try:
            if _AGENTS_MODULE:
                t = _AGENTS_MODULE.Task(name=f"task-{task.get('id')}", payload=task)
                sup.task_queue.put(t)
        except Exception:
            pass

    task["assigned_agent"] = agent_name
    return agent_name


def get_orchestrator():
    """Return the (possibly enhanced) orchestrator."""
    global _ORCHESTRATOR
    return _ORCHESTRATOR

# === Full consolidation and wiring of virtual HT + external projects ===
EXTERNAL_QUBO_SOLVER = None

def _try_load_external_qubo_solver():
    """Try to load from qubo_miner project for better GPU/QUBO with vHT. Wire virtual cache."""
    global EXTERNAL_QUBO_SOLVER
    if EXTERNAL_QUBO_SOLVER is not None:
        return EXTERNAL_QUBO_SOLVER
    try:
        import sys
        qubo_path = r"C:\Users\Admin\qubo_miner"
        if qubo_path not in sys.path:
            sys.path.insert(0, qubo_path)
        from qubo_solver import QUBOSolver
        solver = QUBOSolver(solver="gpu" if os.getenv("FUSION_USE_GPU") == "1" else "neal")
        # wire vht cache from our virtual system
        try:
            from virtual_gpu_hyperthreading import get_virtual_gpu_ht_cache
            solver.vht_cache = get_virtual_gpu_ht_cache()
        except Exception:
            pass
        EXTERNAL_QUBO_SOLVER = solver
        return solver
    except Exception:
        return None

def get_best_qubo_solver():
    """Return the best available QUBO solver, preferring external qubo_miner with vHT wiring."""
    solver = _try_load_external_qubo_solver()
    if solver:
        return solver
    # Fallback to internal if needed
    return None

# Pre-wire from C: searched projects (qubo_miner cache, FusionHero SSD)
try:
    import sys, os, json
    qubo_path = r"C:\Users\Admin\qubo_miner"
    if qubo_path not in sys.path:
        sys.path.insert(0, qubo_path)
    from cache_integration import CacheManager
    fusion_cache = r"C:\FusionHero\QuboCache\miner_optimizer_state.json"
    if os.path.exists(fusion_cache):
        with open(fusion_cache) as f:
            QUBO_CACHE_STATE = json.load(f)  # available for auto assignment optimization
except Exception:
    QUBO_CACHE_STATE = {}

# Wire virtual HT into QUBO solving
def solve_qubo(Q, bias=None, **kwargs):
    """Solve QUBO using best wired solver (qubo_miner if available, with virtual threads)."""
    solver = get_best_qubo_solver()
    if solver:
        try:
            return solver.solve(Q, bias or {}, **kwargs)
        except Exception:
            pass
    # Internal fallback using virtual update if possible
    try:
        from virtual_gpu_hyperthreading import gpu_virtual_energy_update, get_virtual_gpu_ht_cache
        cache = get_virtual_gpu_ht_cache()
        tid = cache.allocate_virtual_thread()
        if tid:
            gpu_virtual_energy_update([tid], Q)
            cache.free(tid)
            # dummy result for now
            n = len(Q) if hasattr(Q, '__len__') else 10
            return {"solution": {i: 0 for i in range(n)}, "energy": 0.0, "vht_used": True}
    except:
        pass
    return {"solution": {}, "energy": 0.0, "note": "fallback"}

# General AutoLoad for orchestration layer
def auto_load(phase: str = "staged", force: bool = False) -> Dict[str, Any]:
    """Generelle AutoLoad Logik für alles was passt: Agents, HT, Factors etc."""
    results = {"loaded": [], "errors": []}
    try:
        ensure_agents_loaded(force=force)
        results["loaded"].append("agents")
    except Exception as e:
        results["errors"].append(f"agents: {e}")
    try:
        import hyperthreading_config as htc
        if force or not htc.status().get("enabled"):
            htc.enable(True)
        results["loaded"].append("hyperthreading")
    except Exception as e:
        results["errors"].append(f"hyperthreading: {e}")
    # Could add more: core modules, etc.
    results["phase"] = phase
    return results


# Convenience for task creation (used by check_and_assign)
def create_classified_task(raw_query: str, **extra) -> Dict[str, Any]:
    normalized, cat, matched, dom = classify_and_normalize(raw_query)
    auto_load(phase="staged")  # general auto load
    agent = assign_task_to_agent({"dom": dom, "geltung": cat, "id": extra.get("id", 0)})

    task = {
        "query": normalized,
        "original": raw_query,
        "geltung": cat,
        "dom": dom,
        "matched": matched.get("name") if matched else None,
        "assigned_agent": agent,
        "status": "pending",
        **extra,
    }

    # If QUBO-related, pre-wire the best solver + virtual threads
    if "qubo" in (dom or "").lower() or "qubo" in normalized.lower():
        q_data = extra.get("Q") or task.get("payload", {}).get("Q")
        if q_data:
            result = solve_qubo(q_data, extra.get("bias"))
            task["qubo_result"] = result
            task["solver"] = "qubo_miner+vht" if EXTERNAL_QUBO_SOLVER else "internal_vht"

    return task
