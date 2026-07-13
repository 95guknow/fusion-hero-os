# agent_control.py — Globale Kontrollfunktion für Agenten (Multi-Strategie)
#
# Alternative Lösungen (parallel nutzbar, per Env wählbar):
#   1. geltung      — HERO-GUIDE Geltungskategorien + FormalMathematicsCoreModule
#   2. peer_review  — 5-Dimensionen-Review (PeerReviewCoreModule)
#   3. meta         — Epistemische Inflation (CriticalMetaAnalysisCoreModule)
#   4. audit        — Pre/Post-Strukturprüfung (AuditAgent-Muster aus Mainframe)
#   5. foundation   — Externes Foundation-Gate (heroic-core-foundation, optional)
#   6. consensus    — Mehrheitsentscheid über aktive Strategien (fail-closed)

from __future__ import annotations

import os
import re
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

_HERE = os.path.dirname(__file__)
_REF = os.path.abspath(os.path.join(_HERE, "..", "reference"))
if _REF not in sys.path:
    sys.path.insert(0, _REF)

_DEFAULT_STRATEGIES = ("geltung", "peer_review", "meta", "audit")
_HISTORY: List[Dict[str, Any]] = []
_MAX_HISTORY = 200

# Lazy-loaded core modules
_peer_review = None
_formal_math = None
_meta = None


def is_enabled() -> bool:
    return os.getenv("FUSION_AGENT_CONTROL", "1") == "1"


def is_fail_closed() -> bool:
    return os.getenv("FUSION_AGENT_CONTROL_FAIL_CLOSED", "1") == "1"


def strategy_order() -> List[str]:
    raw = os.getenv("FUSION_AGENT_CONTROL_STRATEGIES", ",".join(_DEFAULT_STRATEGIES))
    order = [s.strip().lower() for s in raw.split(",") if s.strip()]
    return order or list(_DEFAULT_STRATEGIES)


def min_consensus_votes() -> int:
    try:
        return max(1, int(os.getenv("FUSION_AGENT_CONTROL_MIN_VOTES", "2")))
    except ValueError:
        return 2


@dataclass
class StrategyResult:
    strategy: str
    passed: bool
    score: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class ControlResult:
    passed: bool
    phase: str
    strategies: List[StrategyResult] = field(default_factory=list)
    consensus: bool = False
    blocked: bool = False
    reason: str = ""
    ts: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "phase": self.phase,
            "consensus": self.consensus,
            "blocked": self.blocked,
            "reason": self.reason,
            "ts": self.ts,
            "strategies": [
                {
                    "strategy": s.strategy,
                    "passed": s.passed,
                    "score": s.score,
                    "details": s.details,
                    "error": s.error,
                }
                for s in self.strategies
            ],
        }


def _get_peer_review():
    global _peer_review
    if _peer_review is None:
        try:
            from core_modules import PeerReviewCoreModule

            _peer_review = PeerReviewCoreModule()
        except Exception:
            _peer_review = False
    return _peer_review if _peer_review is not False else None


def _get_formal_math():
    global _formal_math
    if _formal_math is None:
        try:
            from core_modules import FormalMathematicsCoreModule

            _formal_math = FormalMathematicsCoreModule()
        except Exception:
            _formal_math = False
    return _formal_math if _formal_math is not False else None


def _get_meta():
    global _meta
    if _meta is None:
        try:
            from CriticalMetaAnalysisCoreModule import CriticalMetaAnalysisCoreModule

            _meta = CriticalMetaAnalysisCoreModule()
        except Exception:
            _meta = False
    return _meta if _meta is not False else None


def _extract_text(task: Dict[str, Any], result: Any = None) -> str:
    parts: List[str] = []
    for key in ("query", "original", "text", "message", "response"):
        val = task.get(key)
        if isinstance(val, str) and val.strip():
            parts.append(val)
    payload = task.get("payload")
    if isinstance(payload, dict):
        for key in ("query", "text", "message"):
            val = payload.get(key)
            if isinstance(val, str) and val.strip():
                parts.append(val)
    if result is not None:
        if isinstance(result, str):
            parts.append(result)
        elif isinstance(result, dict):
            for key in ("response", "synthesised_response", "text", "result"):
                val = result.get(key)
                if isinstance(val, str) and val.strip():
                    parts.append(val)
    return "\n".join(parts)


# --- Strategy implementations ---

def _strategy_geltung(task: Dict[str, Any], text: str, phase: str) -> StrategyResult:
    """Alternative 1: Geltungskategorie + FormalMathematics."""
    geltung = task.get("geltung") or task.get("category") or ""
    query = task.get("query") or task.get("original") or text
    valid_cats = {"proven", "cond", "model", "frag", "over", "satz", "bedingt", "modell", "fragment"}

    has_prefix = bool(re.search(r"\[(proven|cond|model|frag|over)\]", query or "", re.I))
    has_hash = bool(re.search(r"#(proven|cond|model|frag|over)\b", query or "", re.I))
    cat_ok = (str(geltung).lower() in valid_cats) or has_prefix or has_hash

    fm = _get_formal_math()
    classification = None
    if fm and text:
        try:
            cls = fm.classify(text[:2000])
            classification = {
                "kategorie": cls.kategorie,
                "begruendung": cls.begruendung,
            }
        except Exception as exc:
            return StrategyResult("geltung", False, 0.0, {"cat_ok": cat_ok}, str(exc))

    if phase == "pre":
        passed = bool(query and query.strip()) and (cat_ok or has_prefix)
        if not query or not query.strip():
            return StrategyResult("geltung", False, 0.0, {"reason": "empty_query"})
        if not cat_ok and not has_prefix:
            return StrategyResult(
                "geltung",
                False,
                0.3,
                {"reason": "missing_geltung", "hint": "Prefix [model] oder Geltungskategorie setzen"},
            )
        return StrategyResult("geltung", passed, 1.0 if passed else 0.3, {"cat_ok": cat_ok, "classification": classification})

    # post: text should remain categorized; inflation check via classification
    passed = bool(text.strip())
    score = 1.0 if passed and cat_ok else (0.5 if passed else 0.0)
    return StrategyResult("geltung", passed, score, {"cat_ok": cat_ok, "classification": classification})


def _strategy_peer_review(task: Dict[str, Any], text: str, phase: str) -> StrategyResult:
    """Alternative 2: 5-Dimensionen PeerReview."""
    pr = _get_peer_review()
    if not pr:
        return StrategyResult("peer_review", True, 0.5, {"skipped": True}, "PeerReviewCoreModule nicht geladen")

    if phase == "pre":
        # Pre: nur bei langen/komplexen Queries erzwingen
        q = _extract_text(task)
        if len(q) < 80:
            return StrategyResult("peer_review", True, 1.0, {"skipped": True, "reason": "short_input"})
        return StrategyResult("peer_review", True, 0.8, {"deferred": "post"})

    if not text.strip():
        return StrategyResult("peer_review", False, 0.0, {"reason": "empty_output"})

    try:
        res = pr.review(text[:8000])
        passed = bool(res.get("passed"))
        score = float(res.get("coverage", 0))
        return StrategyResult(
            "peer_review",
            passed,
            score,
            {"score": res.get("score"), "max_score": res.get("max_score"), "coverage": score},
        )
    except Exception as exc:
        return StrategyResult("peer_review", True, 0.5, {"skipped": True}, str(exc))


def _strategy_meta(task: Dict[str, Any], text: str, phase: str) -> StrategyResult:
    """Alternative 3: CriticalMetaAnalysis — epistemische Inflation."""
    meta = _get_meta()
    if not meta:
        return StrategyResult("meta", True, 0.5, {"skipped": True})

    check_text = text if phase == "post" else _extract_text(task)
    if not check_text.strip():
        return StrategyResult("meta", True, 1.0, {"skipped": True, "reason": "no_text"})

    try:
        issues = meta.analyze(check_text[:4000])
        passed = len(issues) == 0
        return StrategyResult("meta", passed, 1.0 if passed else 0.2, {"issues": issues})
    except Exception as exc:
        return StrategyResult("meta", True, 0.5, {"skipped": True}, str(exc))


def _strategy_audit(task: Dict[str, Any], text: str, phase: str) -> StrategyResult:
    """Alternative 4: AuditAgent Pre/Post-Struktur (Mainframe-Muster)."""
    if phase == "pre":
        dom = task.get("dom", "General")
        agent = task.get("assigned_agent")
        issues: List[str] = []
        if not dom:
            issues.append("missing_dom")
        payload = task.get("payload")
        if isinstance(payload, dict) and "Q" in payload:
            import math

            q = payload["Q"]
            try:
                if hasattr(q, "__iter__"):
                    flat = list(q) if not hasattr(q, "flatten") else q.flatten().tolist()
                    if any(isinstance(v, float) and (math.isnan(v) or math.isinf(v)) for v in flat[:100]):
                        issues.append("invalid_matrix_values")
            except Exception:
                pass
        passed = len(issues) == 0
        return StrategyResult("audit", passed, 1.0 if passed else 0.0, {"layer": "pre", "issues": issues, "agent": agent})

    # post
    issues = []
    if isinstance(text, str) and len(text) > 50000:
        issues.append("output_too_large")
    result_energy = None
    if isinstance(task.get("qubo_result"), dict):
        result_energy = task["qubo_result"].get("energy")
        if isinstance(result_energy, (int, float)) and result_energy > 1e6:
            issues.append("divergent_energy")
    passed = len(issues) == 0
    return StrategyResult(
        "audit",
        passed,
        1.0 if passed else 0.0,
        {"layer": "post", "issues": issues, "energy": result_energy},
    )


def _strategy_foundation(task: Dict[str, Any], text: str, phase: str) -> StrategyResult:
    """Alternative 5: Externes Foundation-Gate (optional, graceful fallback)."""
    if phase == "pre":
        return StrategyResult("foundation", True, 0.5, {"skipped": True, "reason": "pre_not_required"})

    check_text = text or _extract_text(task)
    if not check_text.strip():
        return StrategyResult("foundation", True, 0.5, {"skipped": True})

    try:
        from foundation_loader import ensure_foundation_on_path, foundation_report_to_dict, load_check_foundation_gate

        if ensure_foundation_on_path() is None:
            return StrategyResult("foundation", True, 0.5, {"skipped": True, "reason": "foundation_not_found"})
        check = load_check_foundation_gate()
        gate = check(check_text[:4000])
        passed = bool(gate.passed)
        return StrategyResult("foundation", passed, 1.0 if passed else 0.0, {"gate": foundation_report_to_dict(gate)})
    except Exception as exc:
        return StrategyResult("foundation", True, 0.5, {"skipped": True, "fallback": True}, str(exc))


_STRATEGY_FN: Dict[str, Callable[[Dict[str, Any], str, str], StrategyResult]] = {
    "geltung": _strategy_geltung,
    "peer_review": _strategy_peer_review,
    "meta": _strategy_meta,
    "audit": _strategy_audit,
    "foundation": _strategy_foundation,
}


def _run_strategies(
    task: Dict[str, Any],
    phase: str,
    text: str = "",
    strategies: Optional[List[str]] = None,
) -> ControlResult:
    if not is_enabled():
        return ControlResult(passed=True, phase=phase, reason="disabled")

    active = strategies or strategy_order()
    results: List[StrategyResult] = []

    for name in active:
        fn = _STRATEGY_FN.get(name)
        if not fn:
            results.append(StrategyResult(name, True, 0.0, {"skipped": True}, "unknown_strategy"))
            continue
        try:
            results.append(fn(task, text, phase))
        except Exception as exc:
            results.append(StrategyResult(name, True, 0.5, {"error": str(exc)}, str(exc)))

    votes_pass = sum(1 for r in results if r.passed and not r.details.get("skipped"))
    votes_total = sum(1 for r in results if not r.details.get("skipped"))
    min_votes = min_consensus_votes()

    if "consensus" in active:
        consensus_pass = votes_pass >= min_votes if votes_total > 0 else True
        passed = consensus_pass
        reason = f"consensus {votes_pass}/{max(votes_total, 1)} (min={min_votes})"
    else:
        failed_critical = [r for r in results if not r.passed and not r.details.get("skipped")]
        passed = len(failed_critical) == 0
        reason = "all_strategies_pass" if passed else f"failed: {[r.strategy for r in failed_critical]}"

    blocked = not passed and is_fail_closed()
    cr = ControlResult(
        passed=passed,
        phase=phase,
        strategies=results,
        consensus="consensus" in active,
        blocked=blocked,
        reason=reason,
    )
    _record(cr, task)
    return cr


def _record(cr: ControlResult, task: Dict[str, Any]) -> None:
    entry = cr.to_dict()
    entry["task_id"] = task.get("id") or task.get("task_id")
    entry["dom"] = task.get("dom")
    entry["agent"] = task.get("assigned_agent")
    _HISTORY.append(entry)
    if len(_HISTORY) > _MAX_HISTORY:
        del _HISTORY[: len(_HISTORY) - _MAX_HISTORY]


def pre_dispatch(task: Dict[str, Any]) -> ControlResult:
    """Pre-Agent-Kontrolle vor Zuweisung/Ausführung."""
    text = _extract_text(task)
    cr = _run_strategies(task, "pre", text)
    task["control_pre"] = cr.to_dict()
    if cr.blocked:
        task["status"] = "control_blocked"
    return cr


def post_dispatch(task: Dict[str, Any], result: Any = None) -> ControlResult:
    """Post-Agent-Kontrolle nach Ausführung."""
    text = _extract_text(task, result)
    if isinstance(result, dict):
        task = {**task, **{k: v for k, v in result.items() if k in ("response", "synthesised_response", "qubo_result")}}
    cr = _run_strategies(task, "post", text)
    if os.getenv("FUSION_DUAL_AGENT", "1") == "1" and task.get("agent_kind") != "anti_agent":
        try:
            from agent_backend_router import invoke, is_anti_agent

            if not is_anti_agent(task=task) and text.strip():
                anti = invoke(
                    "anti_agent",
                    task.get("query") or task.get("original") or text[:500],
                    task,
                    agent_response=text,
                )
                task["anti_agent_review"] = anti
        except Exception:
            pass
    try:
        from conversation_context_core import feedback_from_task, is_enabled

        if is_enabled():
            fb = feedback_from_task(task, result)
            if fb:
                task["context_feedback"] = fb
    except Exception:
        pass
    task["control_post"] = cr.to_dict()
    return cr


def verify_text(text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Explizite Verifikation eines Textes über alle aktiven Strategien."""
    task = dict(context or {})
    task["query"] = text
    task["text"] = text
    pre = _run_strategies(task, "pre", text)
    post = _run_strategies(task, "post", text)
    overall_pass = pre.passed and post.passed
    return {
        "passed": overall_pass,
        "fail_closed": is_fail_closed(),
        "pre": pre.to_dict(),
        "post": post.to_dict(),
        "strategies_active": strategy_order(),
    }


def wrap_executor(base_executor: Callable[..., Any]) -> Callable[..., Any]:
    """Alternative 6: Executor-Wrapper für agents.py MessageBus-Pfad."""

    def controlled(agent: Any, task: Any) -> Any:
        payload = task.payload if hasattr(task, "payload") else {}
        ctrl_task = payload if isinstance(payload, dict) else {"payload": payload}
        ctrl_task["assigned_agent"] = getattr(agent, "name", "unknown")
        pre = pre_dispatch(ctrl_task)
        if pre.blocked:
            return {"error": "control_blocked", "control_pre": pre.to_dict(), "task_id": getattr(task, "task_id", None)}
        try:
            result = base_executor(agent, task)
        except Exception as exc:
            result = {"error": repr(exc)}
        post = post_dispatch(ctrl_task, result)
        if isinstance(result, dict):
            result["control_pre"] = pre.to_dict()
            result["control_post"] = post.to_dict()
            if post.blocked and is_fail_closed():
                result["control_blocked"] = True
        return result

    return controlled


def register_message_bus_hooks(bus: Any) -> bool:
    """Alternative 7: MessageBus-Subscriber für task_done-Events."""
    if not is_enabled() or bus is None:
        return False

    def _on_task_done(msg: Any) -> None:
        try:
            payload = getattr(msg, "payload", {}) or {}
            task_stub = {"id": payload.get("task_id"), "assigned_agent": payload.get("worker")}
            post_dispatch(task_stub, payload)
        except Exception:
            pass

    try:
        bus.subscribe("task_done", _on_task_done)
        return True
    except Exception:
        return False


def status() -> Dict[str, Any]:
    recent = _HISTORY[-5:] if _HISTORY else []
    blocked_count = sum(1 for h in _HISTORY if h.get("blocked"))
    return {
        "enabled": is_enabled(),
        "fail_closed": is_fail_closed(),
        "strategies": strategy_order(),
        "min_consensus_votes": min_consensus_votes(),
        "alternatives": list(_STRATEGY_FN.keys()) + ["consensus"],
        "modules": {
            "peer_review": _get_peer_review() is not None,
            "formal_math": _get_formal_math() is not None,
            "meta_analysis": _get_meta() is not None,
        },
        "history_len": len(_HISTORY),
        "blocked_total": blocked_count,
        "recent": recent,
    }


def history(limit: int = 20) -> List[Dict[str, Any]]:
    return list(_HISTORY[-limit:])