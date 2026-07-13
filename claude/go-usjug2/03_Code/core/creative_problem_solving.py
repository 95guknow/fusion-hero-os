# -*- coding: utf-8 -*-
"""
creative_problem_solving.py — HAUPTKNOTEN: Kreative Problemlösungs-Strategien
==============================================================================
Divergenz→Konvergenz-Pipeline für kreative Problemlösung, angelehnt an die
Strategien moderner Frontier-Harnesses (Perspektiven-Diversität, Judge-Panel,
adversariale Prüfung) — umgesetzt mit den vorhandenen Fusion-Hero-Backends.

Ablauf:
  1. DIVERGENZ:  Das Problem wird durch Strategie-Operatoren umformuliert
                 (Inversion, Analogie, Dekomposition, Constraint-Relaxation,
                 First Principles, Perspektivwechsel, Rekombination).
  2. GENERIERUNG: Jede Umformulierung geht an ein Backend (Agent-Rolle über
                 agent_backend_router; injizierbar für Tests/Offline).
  3. KONVERGENZ: Kandidaten werden bewertet (lexikalische Neuheit + Problem-
                 abdeckung) und per Simulated Annealing zu einem möglichst
                 diversen Portfolio ausgewählt (Anschluss an das Annealing-
                 Thema des Heroic-QUBO-Stacks).
  4. PRÜFUNG:    Optional prüft der Anti-Agent (Kritiker-Rolle) den besten
                 Kandidaten adversarial.

Ehrlich (Code-Honesty):
  * Die Neuheits-/Abdeckungs-Scores sind LEXIKALISCHE Heuristiken (Token-
    Jaccard), KEINE semantische Bewertung. Sie messen Verschiedenheit der
    Formulierungen, nicht Qualität der Ideen.
  * Ohne erreichbares Backend läuft ein deterministischer Offline-Stub, der
    als solcher markiert ist ([offline-stub]) — nützlich für Tests/CI, aber
    ohne inhaltlichen Wert.
  * Simulated Annealing optimiert hier eine kleine Portfolio-Zielfunktion
    (Score + Diversitätsbonus); das ist reale SA-Mechanik, aber kein QUBO.

Aufruf:  python creative_problem_solving.py   # Demo: Offline-Durchlauf
"""
from __future__ import annotations

import json
import math
import os
import random
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

_PORTFOLIO_SIZE = int(os.getenv("FUSION_CREATIVE_PORTFOLIO", "3"))
_SA_STEPS = int(os.getenv("FUSION_CREATIVE_SA_STEPS", "400"))
_SA_T0 = float(os.getenv("FUSION_CREATIVE_SA_T0", "1.0"))
_SA_SEED = int(os.getenv("FUSION_CREATIVE_SA_SEED", "95"))
_DIVERSITY_WEIGHT = float(os.getenv("FUSION_CREATIVE_DIVERSITY_WEIGHT", "0.5"))


def _force_offline() -> bool:
    """FUSION_CREATIVE_OFFLINE=1 erzwingt den Stub (Tests/CI, kein Backend-Probe)."""
    return os.getenv("FUSION_CREATIVE_OFFLINE", "0") == "1"

BackendFn = Callable[[str, str], str]  # (prompt, role) -> antwort


def _state_root() -> Path:
    root = Path(os.getenv("FUSION_STATE_DIR", os.path.expanduser("~/.fusion-hero-os")))
    return root / "creative_solving"


# ---------------------------------------------------------------------------
# 1. DIVERGENZ — Strategie-Operatoren
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Strategy:
    """Ein Divergenz-Operator: formuliert das Problem gezielt um."""

    key: str
    title: str
    description: str
    template: str  # {problem} wird eingesetzt

    def reframe(self, problem: str) -> str:
        return self.template.format(problem=problem.strip())


STRATEGIES: Tuple[Strategy, ...] = (
    Strategy(
        "inversion",
        "Inversion",
        "Das Problem umkehren: Wie würde man es garantiert verschlimmern? "
        "Die Negation der Verschlimmerer ergibt Lösungskandidaten.",
        "Problem: {problem}\n\nBearbeite es per INVERSION: Liste zuerst 3-5 Wege, "
        "wie man das Problem sicher VERSCHLIMMERN würde. Leite dann aus jeder "
        "Verschlimmerung die konkrete Gegenmaßnahme ab. Antworte mit den "
        "Gegenmaßnahmen als nummerierte Lösungsansätze.",
    ),
    Strategy(
        "analogy",
        "Analogie-Transfer",
        "Eine strukturell ähnliche, gelöste Aufgabe aus einer fremden Domäne "
        "suchen und deren Lösungsprinzip übertragen.",
        "Problem: {problem}\n\nBearbeite es per ANALOGIE-TRANSFER: Nenne ein "
        "strukturell ähnliches, bereits gelöstes Problem aus einer ganz anderen "
        "Domäne (Biologie, Logistik, Musik, Städtebau ...). Beschreibe dessen "
        "Lösungsprinzip und übertrage es Schritt für Schritt auf das Problem.",
    ),
    Strategy(
        "decomposition",
        "Dekomposition",
        "Das Problem in unabhängig lösbare Teilprobleme zerlegen und das "
        "kleinste blockierende Teilproblem zuerst angehen.",
        "Problem: {problem}\n\nBearbeite es per DEKOMPOSITION: Zerlege es in "
        "3-6 möglichst unabhängige Teilprobleme. Markiere das kleinste "
        "Teilproblem, das alle anderen blockiert, und skizziere dafür eine "
        "konkrete Lösung zuerst.",
    ),
    Strategy(
        "constraint_relaxation",
        "Constraint-Relaxation",
        "Implizite Annahmen aufzählen und probeweise streichen — welche "
        "Annahme erzeugt das Problem überhaupt?",
        "Problem: {problem}\n\nBearbeite es per CONSTRAINT-RELAXATION: Liste "
        "alle impliziten Annahmen/Randbedingungen. Streiche probeweise jede "
        "einzelne und prüfe: Verschwindet das Problem? Nenne die Annahme mit "
        "dem größten Hebel und die Lösung, die ihre Lockerung ermöglicht.",
    ),
    Strategy(
        "first_principles",
        "First Principles",
        "Auf physikalische/logische Grundtatsachen zurückgehen und die Lösung "
        "von dort neu aufbauen, statt Bestehendes zu variieren.",
        "Problem: {problem}\n\nBearbeite es per FIRST PRINCIPLES: Reduziere es "
        "auf die unverhandelbaren Grundtatsachen (was ist physikalisch/logisch "
        "wirklich wahr?). Baue von diesen Grundtatsachen aus eine Lösung neu "
        "auf, ohne bestehende Lösungen als Vorlage zu nehmen.",
    ),
    Strategy(
        "perspective_shift",
        "Perspektivwechsel",
        "Das Problem aus 3 stark unterschiedlichen Rollen betrachten; jede "
        "Rolle sieht andere Lösungsräume.",
        "Problem: {problem}\n\nBearbeite es per PERSPEKTIVWECHSEL: Beschreibe "
        "das Problem und je einen Lösungsansatz aus Sicht (a) eines Anfängers "
        "ohne Vorwissen, (b) eines Gegners, der vom Problem profitiert, "
        "(c) eines Archivars in 50 Jahren Rückblick. Synthetisiere daraus den "
        "tragfähigsten Ansatz.",
    ),
    Strategy(
        "recombination",
        "Rekombination",
        "Zwei unvollständige/verworfene Teil-Lösungen kombinieren, deren "
        "Schwächen sich gegenseitig aufheben (SCAMPER: Combine).",
        "Problem: {problem}\n\nBearbeite es per REKOMBINATION: Skizziere zwei "
        "naheliegende, aber je für sich UNZUREICHENDE Lösungsansätze samt "
        "ihrer Hauptschwäche. Kombiniere sie dann so, dass die Stärke des "
        "einen die Schwäche des anderen deckt.",
    ),
)

_STRATEGY_INDEX: Dict[str, Strategy] = {s.key: s for s in STRATEGIES}


def diversify(problem: str, strategy_keys: Optional[Sequence[str]] = None) -> List[Dict[str, str]]:
    """Divergenz-Phase: erzeugt pro Strategie eine Umformulierung des Problems."""
    problem = (problem or "").strip()
    if not problem:
        return []
    keys = list(strategy_keys) if strategy_keys else [s.key for s in STRATEGIES]
    out: List[Dict[str, str]] = []
    for key in keys:
        strat = _STRATEGY_INDEX.get(key)
        if not strat:
            continue
        out.append({"strategy": strat.key, "title": strat.title, "prompt": strat.reframe(problem)})
    return out


# ---------------------------------------------------------------------------
# 2. GENERIERUNG — Backend-Anbindung (injizierbar, mit Offline-Stub)
# ---------------------------------------------------------------------------

def _offline_stub_backend(prompt: str, role: str) -> str:
    """Deterministischer Stub ohne LLM — nur für Tests/CI, inhaltlich wertlos."""
    strategy = "unbekannt"
    m = re.search(r"per ([A-ZÄÖÜ\- ]+):", prompt)
    if m:
        strategy = m.group(1).strip().lower()
    digest = abs(hash(prompt)) % 10_000
    return (
        f"[offline-stub] role={role} strategie={strategy} ref={digest}: "
        f"Kein Backend erreichbar — dieser Text ist ein Platzhalter ohne Lösungswert."
    )


def _router_backend(prompt: str, role: str) -> str:
    """Standard-Backend: rollenbasierter Pfad über agent_backend_router."""
    import agent_backend_router  # lazy: optionale Laufzeit-Abhängigkeit

    out = agent_backend_router.invoke(role, prompt)
    if out.get("ok") and str(out.get("response", "")).strip():
        return str(out["response"])
    raise RuntimeError(out.get("error") or "backend lieferte leere Antwort")


def generate(
    problem: str,
    backend: Optional[BackendFn] = None,
    strategy_keys: Optional[Sequence[str]] = None,
) -> List[Dict[str, Any]]:
    """Fan-out: jede Strategie-Umformulierung an das Backend (Agent-Rolle).

    Fällt der Router-Pfad einmal aus, wird für die restlichen Strategien direkt
    der Offline-Stub genutzt (kein wiederholtes Timeout pro Strategie).
    """
    candidates: List[Dict[str, Any]] = []
    router_dead = _force_offline()
    for frame in diversify(problem, strategy_keys):
        text = ""
        used_backend = "injected" if backend else "agent_backend_router"
        if backend is not None:
            try:
                text = backend(frame["prompt"], "agent")
            except Exception as exc:
                text = f"[backend-error] {exc}"
                used_backend = "injected-error"
        elif router_dead:
            used_backend = "offline-stub"
            text = _offline_stub_backend(frame["prompt"], "agent")
        else:
            try:
                text = _router_backend(frame["prompt"], "agent")
            except Exception:
                router_dead = True
                used_backend = "offline-stub"
                text = _offline_stub_backend(frame["prompt"], "agent")
        candidates.append({
            "strategy": frame["strategy"],
            "title": frame["title"],
            "prompt": frame["prompt"],
            "response": text,
            "backend": used_backend,
        })
    return candidates


# ---------------------------------------------------------------------------
# 3. KONVERGENZ — lexikalische Scores + Simulated-Annealing-Portfolio
# ---------------------------------------------------------------------------

_TOKEN_RE = re.compile(r"[a-zA-Zäöüß0-9]{3,}")


def _tokens(text: str) -> frozenset:
    return frozenset(t.lower() for t in _TOKEN_RE.findall(text or ""))


def lexical_novelty(candidate: str, others: Sequence[str]) -> float:
    """1 − max. Jaccard-Ähnlichkeit zu den anderen Kandidaten (0..1).

    Ehrlich: misst Formulierungs-Verschiedenheit, keine inhaltliche Neuheit.
    """
    a = _tokens(candidate)
    if not a or not others:
        return 1.0
    best_sim = 0.0
    for other in others:
        b = _tokens(other)
        if not b:
            continue
        sim = len(a & b) / max(1, len(a | b))
        best_sim = max(best_sim, sim)
    return round(1.0 - best_sim, 4)


def problem_coverage(candidate: str, problem: str) -> float:
    """Anteil der Problem-Schlüsselwörter, die der Kandidat aufgreift (0..1)."""
    p = _tokens(problem)
    if not p:
        return 0.0
    c = _tokens(candidate)
    return round(len(p & c) / len(p), 4)


def score_candidates(candidates: List[Dict[str, Any]], problem: str) -> List[Dict[str, Any]]:
    """Bewertet Kandidaten: 0.6·Neuheit + 0.4·Abdeckung (lexikalische Heuristik)."""
    texts = [c.get("response", "") for c in candidates]
    for i, cand in enumerate(candidates):
        others = texts[:i] + texts[i + 1:]
        nov = lexical_novelty(texts[i], others)
        cov = problem_coverage(texts[i], problem)
        cand["novelty"] = nov
        cand["coverage"] = cov
        cand["score"] = round(0.6 * nov + 0.4 * cov, 4)
    return candidates


def _portfolio_energy(
    selected: Sequence[int],
    candidates: List[Dict[str, Any]],
) -> float:
    """Zielfunktion (zu maximieren): Summe Scores + Diversitätsbonus im Portfolio."""
    base = sum(candidates[i]["score"] for i in selected)
    div = 0.0
    pairs = 0
    for x in range(len(selected)):
        for y in range(x + 1, len(selected)):
            a = _tokens(candidates[selected[x]].get("response", ""))
            b = _tokens(candidates[selected[y]].get("response", ""))
            if a and b:
                div += 1.0 - len(a & b) / max(1, len(a | b))
                pairs += 1
    if pairs:
        div /= pairs
    return base + _DIVERSITY_WEIGHT * div


def anneal_select(
    candidates: List[Dict[str, Any]],
    k: int = _PORTFOLIO_SIZE,
    steps: int = _SA_STEPS,
    seed: int = _SA_SEED,
) -> List[Dict[str, Any]]:
    """Wählt per Simulated Annealing ein diverses Top-k-Portfolio.

    Deterministisch bei festem Seed (reproduzierbar, testbar).
    """
    n = len(candidates)
    if n == 0:
        return []
    k = max(1, min(k, n))
    rng = random.Random(seed)
    current = list(range(k))  # Start: erste k
    best = list(current)
    e_cur = _portfolio_energy(current, candidates)
    e_best = e_cur
    for step in range(steps):
        if n <= k:
            break
        temp = _SA_T0 * (1.0 - step / max(1, steps))
        proposal = list(current)
        out_idx = rng.randrange(k)
        pool = [i for i in range(n) if i not in current]
        proposal[out_idx] = rng.choice(pool)
        e_new = _portfolio_energy(proposal, candidates)
        accept = e_new >= e_cur or rng.random() < math.exp((e_new - e_cur) / max(temp, 1e-9))
        if accept:
            current, e_cur = proposal, e_new
            if e_cur > e_best:
                best, e_best = list(current), e_cur
    chosen = [candidates[i] for i in best]
    chosen.sort(key=lambda c: c.get("score", 0.0), reverse=True)
    return chosen


# ---------------------------------------------------------------------------
# 4. PRÜFUNG — optionale adversariale Kritik (Anti-Agent-Rolle)
# ---------------------------------------------------------------------------

def critique_top(
    problem: str,
    top_candidate: Dict[str, Any],
    backend: Optional[BackendFn] = None,
) -> Dict[str, Any]:
    """Lässt die Anti-Agent-Rolle den besten Kandidaten adversarial prüfen."""
    prompt = (
        "[anti-agent] Prüfe den folgenden Lösungsansatz adversarial: Wo bricht er, "
        "welche Annahme ist am schwächsten, was wäre der billigste Gegenbeweis?\n\n"
        f"**Problem:** {problem}\n\n"
        f"**Strategie:** {top_candidate.get('title')}\n\n"
        f"**Ansatz:**\n{str(top_candidate.get('response', ''))[:6000]}"
    )
    if backend is not None:
        try:
            return {"ok": True, "backend": "injected", "critique": backend(prompt, "anti_agent")}
        except Exception as exc:
            return {"ok": False, "backend": "injected", "error": str(exc)}
    try:
        return {"ok": True, "backend": "agent_backend_router", "critique": _router_backend(prompt, "anti_agent")}
    except Exception as exc:
        return {"ok": False, "backend": "agent_backend_router", "error": str(exc)}


# ---------------------------------------------------------------------------
# Orchestrierung + Persistenz
# ---------------------------------------------------------------------------

def solve_creative(
    problem: str,
    backend: Optional[BackendFn] = None,
    strategy_keys: Optional[Sequence[str]] = None,
    portfolio_size: int = _PORTFOLIO_SIZE,
    with_critique: bool = True,
    seed: int = _SA_SEED,
    persist: bool = True,
) -> Dict[str, Any]:
    """Voller Durchlauf: Divergenz → Generierung → Konvergenz → Kritik."""
    problem = (problem or "").strip()
    if not problem:
        return {"ok": False, "error": "empty problem"}

    t0 = time.perf_counter()
    candidates = generate(problem, backend=backend, strategy_keys=strategy_keys)
    candidates = score_candidates(candidates, problem)
    portfolio = anneal_select(candidates, k=portfolio_size, seed=seed)

    critique: Optional[Dict[str, Any]] = None
    offline = all(c.get("backend") == "offline-stub" for c in candidates)
    if with_critique and portfolio and not offline:
        critique = critique_top(problem, portfolio[0], backend=backend)

    result = {
        "ok": True,
        "problem": problem,
        "n_strategies": len(candidates),
        "offline": offline,
        "portfolio": portfolio,
        "all_candidates": candidates,
        "critique": critique,
        "elapsed_ms": round((time.perf_counter() - t0) * 1000, 1),
        "honesty": (
            "Scores sind lexikalische Heuristiken (Token-Jaccard), keine semantische "
            "Qualitätsbewertung. Offline-Stub-Antworten haben keinen Lösungswert."
        ),
    }
    if persist:
        _log_run(result)
    return result


def _log_run(result: Dict[str, Any]) -> None:
    """Append-only JSON-Log der Läufe (gekürzt, ohne volle Antworttexte)."""
    try:
        root = _state_root()
        root.mkdir(parents=True, exist_ok=True)
        path = root / "runs.json"
        entry = {
            "ts": time.time(),
            "problem": result["problem"][:200],
            "offline": result["offline"],
            "n_strategies": result["n_strategies"],
            "portfolio": [
                {"strategy": c["strategy"], "score": c.get("score"), "novelty": c.get("novelty")}
                for c in result.get("portfolio", [])
            ],
        }
        runs = []
        if path.exists():
            try:
                runs = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                runs = []
        runs.append(entry)
        path.write_text(json.dumps(runs[-500:], ensure_ascii=False, indent=1), encoding="utf-8")
    except Exception:
        pass  # Logging darf den Lauf nie brechen


def status() -> Dict[str, Any]:
    return {
        "module": "creative_problem_solving",
        "strategies": [{"key": s.key, "title": s.title} for s in STRATEGIES],
        "portfolio_size": _PORTFOLIO_SIZE,
        "sa_steps": _SA_STEPS,
        "diversity_weight": _DIVERSITY_WEIGHT,
        "scoring": "lexikalisch (Token-Jaccard) — ehrlich: keine Semantik",
        "backends": "agent_backend_router (agent/anti_agent) oder injiziert; Offline-Stub als Fallback",
    }


if __name__ == "__main__":
    os.environ.setdefault("FUSION_CREATIVE_OFFLINE", "1")  # Demo hängt nie an Backends
    demo_problem = (
        "Der lokale Llama-Agent liefert bei mehrstufigen Aufgaben inkonsistente "
        "Zwischenergebnisse, weil Kontext zwischen Schritten verloren geht."
    )
    res = solve_creative(demo_problem, with_critique=False, persist=False)
    print(f"Strategien: {res['n_strategies']}  offline={res['offline']}  {res['elapsed_ms']}ms")
    for c in res["portfolio"]:
        print(f"  [{c['strategy']}] score={c['score']} novelty={c['novelty']} coverage={c['coverage']}")
    print(f"Hinweis: {res['honesty']}")
