# qubo_llama_bridge.py — QUBO-Logik in lokales Llama (Inference + Synthese)

from __future__ import annotations

import hashlib
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_TOOLS = Path(__file__).resolve().parent.parent / "tools"
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

_QUBO_TERMS = (
    "qubo",
    "q/b",
    "q∘b",
    "ising",
    "annealing",
    "optimierung",
    "optimierung",
    "energy",
    "energie",
    "matrix q",
    "qb_qubo",
    "max-cut",
    "submodular",
    "spin",
    "bitlevel",
    "qubo_miner",
    "simulated annealing",
    "lokalsuche",
    "local search",
    "quadratisch",
    "binary optimization",
)

_rng_seed = 7


def is_enabled() -> bool:
    return os.getenv("FUSION_LLAMA_QUBO", "1") == "1"


def is_qubo_query(text: str) -> bool:
    q = (text or "").lower()
    if "[qubo]" in q or "#qubo" in q:
        return True
    return any(t in q for t in _QUBO_TERMS)


def _stable_n(text: str, default: int = 8) -> int:
    h = int(hashlib.md5(text.encode("utf-8")).hexdigest()[:6], 16)
    return max(4, min(16, default + (h % 5)))


def build_qubo_from_query(query: str, n: Optional[int] = None) -> Tuple[Any, Dict[str, Any]]:
    """
    Heuristische q/b-QUBO-Matrix aus Anfrage (qb_qubo.make_Q Stil).
    Deterministisch pro Query-Hash.
    """
    import numpy as np

    size = n or _stable_n(query)
    seed = int(hashlib.sha256(query.encode("utf-8")).hexdigest()[:8], 16) % (2**31)
    rng = np.random.default_rng(seed)

    Q = np.zeros((size, size), dtype=np.float64)
    r = rng.normal(0, 1.0, size=(size, size))
    Q += (r + r.T) / 2.0
    np.fill_diagonal(Q, rng.normal(0.2, 0.8, size=size))

    # q/b-Nicht-Kommutativität: leichte Asymmetrie-Strafe
    if "q" in query.lower() and "b" in query.lower():
        off = np.ones_like(Q) - np.eye(size)
        Q = np.where(off, -np.abs(Q) * 0.6, Q)

    meta = {
        "n": size,
        "seed": seed,
        "source": "heuristic_qb_query",
        "formula": "x^T Q x",
    }
    return Q, meta


def solve_qubo_matrix(Q: Any, bias: Optional[Dict] = None) -> Dict[str, Any]:
    """Solver-Kette: qubo_miner → qb_qubo SA → heroic_orchestration → Greedy."""
    result: Dict[str, Any] = {"backend": "none", "energy": None, "solution": {}}

    # 1) External qubo_miner via heroic_orchestration
    try:
        from heroic_orchestration import solve_qubo

        out = solve_qubo(Q, bias or {})
        if out and out.get("solution") is not None:
            result.update({
                "backend": out.get("solver", "qubo_miner+vht") if out.get("vht_used") else "qubo_miner",
                "energy": out.get("energy"),
                "solution": out.get("solution", {}),
                "raw": out,
            })
            if result["energy"] is not None:
                return result
    except Exception:
        pass

    # 2) Internal qb_qubo simulated_annealing
    try:
        import numpy as np
        from qb_qubo import simulated_annealing  # type: ignore

        Qa = np.asarray(Q, dtype=np.float64)
        x, energy = simulated_annealing(Qa, steps=int(os.getenv("FUSION_QUBO_SA_STEPS", "1200")))
        sol = {int(i): int(v) for i, v in enumerate(np.asarray(x).astype(int).tolist())}
        return {
            "backend": "qb_qubo_sa",
            "energy": float(energy),
            "solution": sol,
            "n": Qa.shape[0],
        }
    except Exception:
        pass

    # 3) Greedy fallback
    try:
        import numpy as np

        Qa = np.asarray(Q, dtype=np.float64)
        n = Qa.shape[0]
        x = np.zeros(n, dtype=np.int8)
        for i in range(n):
            e0 = float(Qa[i, i])
            e1 = float(-Qa[i, i])
            for j in range(n):
                if j != i:
                    e0 += float(Qa[i, j] * x[j])
                    e1 += float(Qa[i, j] * x[j])
            x[i] = 1 if e1 < e0 else 0
        energy = float(x.astype(np.float64) @ Qa @ x.astype(np.float64))
        return {
            "backend": "greedy_fallback",
            "energy": energy,
            "solution": {int(i): int(v) for i, v in enumerate(x.tolist())},
            "n": n,
        }
    except Exception as exc:
        return {"backend": "error", "error": str(exc), "solution": {}, "energy": None}


def qubo_score_response(query: str, response: str) -> float:
    """Niedrigere Energie = bessere Antwort (Heuristik)."""
    if not response or not response.strip():
        return 1e6
    q_tokens = set(re.findall(r"\w+", query.lower()))
    r_tokens = re.findall(r"\w+", response.lower())
    if not r_tokens:
        return 1e6
    overlap = len(q_tokens & set(r_tokens)) / max(len(q_tokens), 1)
    length_pen = abs(len(r_tokens) - 80) * 0.002
    qubo_bonus = 0.0
    if any(t in response.lower() for t in ("qubo", "energy", "ising", "annealing", "λ", "fixpunkt")):
        qubo_bonus = -0.15
    return max(0.0, 1.0 - overlap + length_pen + qubo_bonus)


def _qubo_context_block(qubo_result: Dict[str, Any], qubo_meta: Dict[str, Any]) -> str:
    sol = qubo_result.get("solution") or {}
    active: List[int] = []
    for k, v in sol.items():
        try:
            if int(v) != 0:
                active.append(int(k))
        except (TypeError, ValueError):
            pass
    active = sorted(active)[:8]
    energy = qubo_result.get("energy")
    backend = qubo_result.get("backend", "?")
    n = qubo_meta.get("n", len(sol))
    bits = "".join(str(sol.get(i, sol.get(str(i), 0))) for i in range(min(n, 12)))
    return (
        f"\n[QUBO-Solver · {backend}]\n"
        f"Matrix n={n}, Energie E={energy}\n"
        f"Lösung (Bits): {bits}{'…' if n > 12 else ''}\n"
        f"Aktive Spins: {active[:8]}\n"
        "Nutze diese QUBO-Ergebnisse in deiner Antwort (Modell, nicht Satz).\n"
    )


def augment_system_prompt(system: str, query: str, qubo_result: Optional[Dict[str, Any]] = None,
                          qubo_meta: Optional[Dict[str, Any]] = None) -> str:
    base = system or (
        "Du bist ALTE_Frau_95g Heroic Core — Fusion Hero OS v8. "
        "QUBO, q/b-Beziehung, Hyperthreading, Banach-Fixpunkt."
    )
    if not qubo_result:
        return base
    return base + _qubo_context_block(qubo_result, qubo_meta or {})


def generate_with_qubo(
    llama_generate_fn,
    prompt: str,
    system: Optional[str] = None,
    gen_cfg: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    QUBO-augmentierte Llama-Generierung:
      1. QUBO lösen (wenn Query passt oder immer bei FUSION_LLAMA_QUBO_ALWAYS=1)
      2. System-Prompt anreichern
      3. Optional Multi-Kandidaten + QUBO-Scoring (wie heroic_qubo_annealing)
    """
    gen_cfg = dict(gen_cfg or {})
    qubo_applied = False
    qubo_result: Dict[str, Any] = {}
    qubo_meta: Dict[str, Any] = {}

    always = os.getenv("FUSION_LLAMA_QUBO_ALWAYS", "0") == "1"
    if is_enabled() and (is_qubo_query(prompt) or always):
        Q, qubo_meta = build_qubo_from_query(prompt)
        qubo_result = solve_qubo_matrix(Q)
        qubo_applied = True

    sys_aug = augment_system_prompt(system or "", prompt, qubo_result if qubo_applied else None, qubo_meta)

    n_cand = 1
    if is_enabled() and qubo_applied:
        try:
            n_cand = max(1, min(5, int(os.getenv("FUSION_LLAMA_QUBO_CANDIDATES", "2"))))
        except ValueError:
            n_cand = 2

    candidates: List[str] = []
    scores: List[float] = []
    for i in range(n_cand):
        cfg = dict(gen_cfg)
        if n_cand > 1:
            cfg["temperature"] = float(cfg.get("temperature", 0.7)) + 0.08 * i
        try:
            text = llama_generate_fn(prompt, sys_aug, cfg)
            candidates.append(text)
            scores.append(qubo_score_response(prompt, text))
        except Exception as exc:
            if i == 0:
                raise
            candidates.append(f"[candidate error: {exc}]")
            scores.append(1e6)

    best_idx = int(min(range(len(scores)), key=lambda k: scores[k])) if scores else 0
    response = candidates[best_idx] if candidates else ""

    return {
        "response": response,
        "qubo_applied": qubo_applied,
        "qubo_result": qubo_result if qubo_applied else None,
        "qubo_meta": qubo_meta if qubo_applied else None,
        "candidates": len(candidates),
        "candidate_scores": [round(s, 4) for s in scores],
        "selected_index": best_idx,
        "backend": "llama-local+qubo" if qubo_applied else "llama-local",
    }


def status() -> Dict[str, Any]:
    solvers = []
    try:
        from heroic_orchestration import get_best_qubo_solver
        if get_best_qubo_solver():
            solvers.append("qubo_miner")
    except Exception:
        pass
    try:
        from qb_qubo import simulated_annealing  # type: ignore
        _ = simulated_annealing
        solvers.append("qb_qubo_sa")
    except Exception:
        pass
    solvers.append("greedy_fallback")
    return {
        "enabled": is_enabled(),
        "always": os.getenv("FUSION_LLAMA_QUBO_ALWAYS", "0") == "1",
        "candidates": int(os.getenv("FUSION_LLAMA_QUBO_CANDIDATES", "2")),
        "solvers_available": solvers,
        "terms": len(_QUBO_TERMS),
        "integration": "inference+synthesis",
        "training_algorithm": "heroic_qubo_annealing_v1",
    }