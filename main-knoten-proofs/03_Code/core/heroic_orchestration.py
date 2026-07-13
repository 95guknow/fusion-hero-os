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
import re
from typing import Any, Dict, List, Optional, Tuple

# --- Paths ---
_HERE = os.path.dirname(__file__)
_GUIDE_PATH = os.path.join(_HERE, '..', '02_Mathematik', 'hero-guide_geltungsstand.json')
_V22_AGENTS_PATH = os.path.abspath(os.path.join(_HERE, '..', 'reference'))

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


# Sprach-bewusste Schlüsselwörter je Domäne/Modus (Deutsch + Englisch).
# Bewusst editierbar/erweiterbar — die "feinere Einstellung" der Domänen-Erkennung.
# Greift nur als Fallback, wenn weder claude_science noch der HERO-GUIDE eine
# Domäne zuweisen; überschreibt diese also nie.
DOMAIN_KEYWORDS: Dict[str, List[str]] = {
    "Math": [
        "mathe", "mathematik", "gleichung", "beweis", "formel", "matrix",
        "optimierung", "qubo", "ising", "annealing", "algorithmus", "wahrscheinlichkeit",
        "math", "equation", "proof", "formula", "optimization", "algorithm", "probability",
    ],
    "Phil": [
        "philosoph", "ethik", "moral", "tugend", "sinn", "bewusstsein",
        "gerechtigkeit", "eudaimonie", "heroisch", "existenz",
        "philosophy", "ethic", "virtue", "meaning", "consciousness", "justice",
    ],
    "Info": [
        "information", "quelle", "recherche", "fakt", "beleg", "referenz", "wissen",
        "definition", "erkläre", "erklär",
        "source", "research", "fact", "reference", "knowledge", "explain",
    ],
}


_DOMAIN_KEYWORDS_CACHE: Optional[Dict[str, List[str]]] = None


def _domain_keywords_file() -> str:
    """Pfad der optionalen Laufzeit-Override-Datei (JSON)."""
    env = os.getenv("FUSION_DOMAIN_KEYWORDS_FILE", "").strip()
    if env:
        return env
    state = os.getenv("FUSION_META_STATE", os.path.join(os.path.expanduser("~"), ".fusion-hero-os"))
    return os.path.join(state, "domain_keywords.json")


def get_domain_keywords(reload: bool = False) -> Dict[str, List[str]]:
    """Effektive Domänen-Keywords = Builtins + optionale JSON-Overrides (gemerged).

    Laufzeit-Konfiguration OHNE Code-Änderung: eine JSON-Datei (Pfad via env
    FUSION_DOMAIN_KEYWORDS_FILE, sonst <FUSION_META_STATE>/domain_keywords.json)
    erweitert die Builtins. Format: {"Math": ["..."], "NeuerModus": ["..."]}.
    Pro Domäne werden die Keywords zu den Builtins hinzugefügt (dedupliziert,
    lowercased); komplett neue Domänen/Modi sind erlaubt. Top-Level
    "__replace__": true ersetzt die Builtins vollständig durch die Datei.
    Fehlt oder defekt die Datei, gelten nur die Builtins (defensiv, kein Crash).
    """
    global _DOMAIN_KEYWORDS_CACHE
    if _DOMAIN_KEYWORDS_CACHE is not None and not reload:
        return _DOMAIN_KEYWORDS_CACHE
    eff: Dict[str, List[str]] = {d: list(kws) for d, kws in DOMAIN_KEYWORDS.items()}
    path = _domain_keywords_file()
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, dict):
                if data.pop("__replace__", False):
                    eff = {}
                for d, kws in data.items():
                    if not isinstance(kws, list):
                        continue
                    lows = [str(k).lower() for k in kws if str(k).strip()]
                    base = eff.get(d, [])
                    seen = set(base)
                    eff[d] = base + [k for k in lows if k not in seen]
    except Exception:
        pass  # defekte Datei -> nur Builtins
    _DOMAIN_KEYWORDS_CACHE = eff
    return eff


def reload_domain_keywords() -> Dict[str, List[str]]:
    """Override-Datei neu einlesen (nach Änderung zur Laufzeit)."""
    return get_domain_keywords(reload=True)


def _kw_matches(kw: str, text: str) -> bool:
    """Treffer, wenn kw an mind. einer Wortgrenze steht.

    Fängt deutsche Komposita ("Differentialgleichung" -> "gleichung",
    "QUBO-Optimierung" -> "optimierung") UND vermeidet Mid-Word-Fehltreffer
    wie "fact" in "refactor" (dort steht "fact" an keiner Wortgrenze).
    """
    esc = re.escape(kw)
    return re.search(r'\b' + esc + r'|' + esc + r'\b', text) is not None


def detect_domain_by_language(q_lower: str) -> Tuple[str, int]:
    """Sprach-bewusste Domänen-Erkennung (DE+EN) per get_domain_keywords().

    Gibt (Domäne, Treffer-Anzahl) zurück; ("General", 0) wenn nichts passt.
    Die Domäne mit den meisten (wortgrenzen-)Treffern gewinnt.
    """
    kw = get_domain_keywords()
    scores = {d: sum(1 for k in kws if _kw_matches(k, q_lower)) for d, kws in kw.items()}
    best = max(scores, key=scores.get) if scores else "General"
    return (best, scores[best]) if scores and scores[best] > 0 else ("General", 0)


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
    science_dom = False
    heroic_science = False
    try:
        from claude_science import is_science_query, is_heroic_science_query
        if is_heroic_science_query(query):
            science_dom = True
            heroic_science = True
            dom = "Science"
            best_cat = "cond"
        elif is_science_query(query):
            science_dom = True
            dom = "Science"
            best_cat = "cond"
    except Exception:
        pass

    for entry in guide:
        name = entry.get('name', '').lower()
        if any(kw in q_lower for kw in name.split()[:3] if len(kw) > 3) or \
           entry.get('dom', '').lower() in q_lower:
            matched = entry
            best_cat = entry.get('cat', 'model')
            if not science_dom:
                dom = entry.get('dom', 'General')
            break

    # Sprach-bewusster Fallback: nur wenn oben nichts zugewiesen wurde.
    # Macht deutsche Eingaben ohne HERO-GUIDE-Treffer modus-fähig (Math/Phil/Info).
    if dom == "General" and not science_dom:
        lang_dom, hits = detect_domain_by_language(q_lower)
        if hits > 0:
            dom = lang_dom

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
            executor = None
            try:
                from agent_control import is_enabled, wrap_executor, register_message_bus_hooks
                _default_executor = getattr(_AGENTS_MODULE, "default_executor", None)
                if is_enabled() and _default_executor is not None:
                    executor = wrap_executor(_default_executor)
            except Exception:
                executor = None

            if _AGENT_SUPERVISOR is None or force:
                sup_kwargs: Dict[str, Any] = {
                    "name": "fusion-hero-supervisor",
                    "min_workers": 2,
                    "max_workers": 12,
                }
                if executor is not None:
                    sup_kwargs["executor"] = executor
                _AGENT_SUPERVISOR = _AGENTS_MODULE.Supervisor(**sup_kwargs)
                _AGENT_SUPERVISOR.start()
                if executor is not None:
                    try:
                        register_message_bus_hooks(_AGENT_SUPERVISOR.bus)
                    except Exception:
                        pass
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
        "supervisor": {"name": "fusion-hero-supervisor", "role": "supervisor", "state": "running", "children": 5},
        "math-worker": {"name": "math-worker", "role": "worker", "dom": "Math"},
        "phil-worker": {"name": "phil-worker", "role": "worker", "dom": "Phil"},
        "info-worker": {"name": "info-worker", "role": "worker", "dom": "Info"},
        "science-worker": {"name": "science-worker", "role": "worker", "dom": "Science", "backend": "claude-science"},
        "llama-test-worker": {
            "name": "llama-test-worker",
            "role": "subagent",
            "dom": "LLM",
            "backend": "llama-local",
            "action": "llama_subagent_tests",
        },
        "general-worker": {"name": "general-worker", "role": "worker", "backend": "llama-local"},
        "anti-general-worker": {"name": "anti-general-worker", "role": "anti_agent", "backend": "grok-intern"},
        "anti-math-worker": {"name": "anti-math-worker", "role": "anti_agent", "backend": "grok-intern", "dom": "Math"},
        "anti-phil-worker": {"name": "anti-phil-worker", "role": "anti_agent", "backend": "grok-intern", "dom": "Phil"},
    }
    return True


def get_loaded_agents() -> Dict[str, Dict[str, Any]]:
    return dict(_LOADED_AGENTS)


def get_agent_supervisor():
    return _AGENT_SUPERVISOR


def assign_task_to_agent(task: Dict[str, Any]) -> str:
    """Auto-assign agent based on dom/geltung. Respects hyperthreading worker scaling."""
    ensure_agents_loaded()

    try:
        from agent_control import is_enabled, pre_dispatch
        if is_enabled() and (task.get("query") or task.get("original")) and not task.get("control_pre"):
            pre = pre_dispatch(task)
            if pre.blocked:
                task["assigned_agent"] = "control-gate"
                task["status"] = "control_blocked"
                return "control-gate"
    except Exception:
        pass

    dom = task.get("dom", "General")
    q_lower = str(task.get("query") or task.get("original") or "").lower()

    try:
        from agent_backend_router import is_anti_agent as _is_anti

        if _is_anti(task=task):
            dom_key = dom.lower().replace(" ", "-")
            agent_name = task.get("assigned_agent") or f"anti-{dom_key}-worker"
            if agent_name not in _LOADED_AGENTS:
                agent_name = "anti-general-worker"
            task["agent_kind"] = "anti_agent"
            task["backend"] = "grok-intern"
            task["assigned_agent"] = agent_name
            return agent_name
    except Exception:
        pass

    llama_test = (
        task.get("subagent_action") == "llama_subagent_tests"
        or task.get("type") == "llama_subagent_test"
        or any(k in q_lower for k in ("llama test", "llama-test", "subagent llama", "teste llama", "llama subagent"))
    )
    if llama_test:
        agent_name = "llama-test-worker"
        task["subagent_action"] = "llama_subagent_tests"
        try:
            from llama_subagent_tester import run as llama_subagent_run

            include_gen = task.get("include_generate")
            task["llama_subagent_result"] = llama_subagent_run(
                subagents=task.get("subagents"),
                max_workers=task.get("max_workers"),
                include_generate=include_gen,
            )
        except Exception as exc:
            task["llama_subagent_result"] = {"status": "error", "error": str(exc)}
    else:
        agent_name = {
            "Math": "math-worker",
            "Phil": "phil-worker",
            "Info": "info-worker",
            "Science": "science-worker",
        }.get(dom, "general-worker")
        task["agent_kind"] = "agent"
        task["backend"] = "llama-local"

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

    try:
        from agent_backend_router import annotate_task, is_dual_agent_enabled, dual_run, is_anti_agent

        annotate_task(task)
        if (
            is_dual_agent_enabled()
            and task.get("dual_agent")
            and not is_anti_agent(task=task)
        ):
            q = task.get("query") or task.get("original") or ""
            if q.strip():
                task["dual_agent_result"] = dual_run(q, task)
    except Exception:
        pass

    try:
        from conversation_context_core import allocate_subagent, is_enabled

        if is_enabled():
            weight = "heavy" if task.get("subagent_action") else "medium"
            ctx = allocate_subagent(agent_name, task_weight=weight, seed_fragment=task.get("query"))
            task["subagent_context_window"] = ctx.get("subagent_window")
            task["context_prompt_block"] = ctx.get("prompt_block", "")[:500]
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

    task = {
        "query": normalized,
        "original": raw_query,
        "geltung": cat,
        "dom": dom,
        "matched": matched.get("name") if matched else None,
        "status": "pending",
        "id": extra.get("id", 0),
        **extra,
    }

    try:
        from conversation_context_core import init_root, is_enabled

        if is_enabled():
            root = init_root(raw_query, {"dom": dom, "geltung": cat, "task_weight": extra.get("task_weight", "medium")})
            task["start_context_window"] = root.get("root")
            # Selbstadaptiv: Kontext-Fäden nach aktueller Stärke neu gewichten +
            # veraltete Fäden prunen (orientiert an den Faden-Stärken).
            try:
                from conversation_context_core import rebalance_by_strength
                rb = rebalance_by_strength(prune=True)
                task["context_rebalance"] = {"rebalanced": rb.get("rebalanced"), "pruned": len(rb.get("pruned", []))}
            except Exception:
                pass
    except Exception:
        pass

    try:
        from agent_control import is_enabled, pre_dispatch
        if is_enabled():
            pre = pre_dispatch(task)
            if pre.blocked:
                task["assigned_agent"] = "control-gate"
                task["status"] = "control_blocked"
                return task
    except Exception:
        pass

    agent = assign_task_to_agent(task)
    task["assigned_agent"] = agent

    # If QUBO-related, pre-wire the best solver + virtual threads
    if "qubo" in (dom or "").lower() or "qubo" in normalized.lower():
        q_data = extra.get("Q") or task.get("payload", {}).get("Q")
        if q_data:
            result = solve_qubo(q_data, extra.get("bias"))
            task["qubo_result"] = result
            task["solver"] = "qubo_miner+vht" if EXTERNAL_QUBO_SOLVER else "internal_vht"

    try:
        from agent_control import is_enabled, pre_dispatch, post_dispatch
        if is_enabled():
            pre_dispatch(task)
            synth = task.get("synthesised_response") or task.get("response")
            if synth:
                post_dispatch(task, {"response": synth})
    except Exception:
        pass

    return task
