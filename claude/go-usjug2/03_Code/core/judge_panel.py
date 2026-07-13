# -*- coding: utf-8 -*-
"""
judge_panel.py — Semantisches Judge-Panel (best-of-N, Mehrheitsvotum)
=====================================================================
Ersetzt die lexikalische Bewertung (Token-Jaccard) aus creative_problem_solving
durch N unabhängige Judge-Urteile mit strukturierter (schema-validierter)
Ausgabe — das Frontier-Muster. Liefert einen aggregierten Qualitäts-Score, der
u.a. die Fitness des coevolution_router speist.

Ablauf:
  * N Judges bewerten denselben Kandidaten unabhängig entlang mehrerer Kriterien
    (Korrektheit, Vollständigkeit, Umsetzbarkeit, Klarheit) auf 0..1.
  * Jeder Judge liefert schema-validiertes JSON (structured_output) -> robust
    gegen Freitext-Geschwätz.
  * Aggregation: Mittelwert + Übereinstimmung (1 - Streuung). Mehrheitsvotum
    für ein binäres accept/reject relativ zu einem Schwellwert.

Ehrlich (Code-Honesty):
  * Der Score ist nur so gut wie das Judge-Backend. Mit dem Offline-Stub ist er
    ein deterministischer LEXIKALISCHER Proxy (keine Semantik) — als solcher
    markiert (offline=True). Erst mit einem echten Claude-/LLM-Backend wird das
    Urteil semantisch.
  * N identische Judges gegen dasselbe Modell sind korreliert; echte
    Perspektiven-Diversität entsteht über verschiedene `criteria`-Lenses.

Aufruf:  python judge_panel.py     # Offline-Demo
"""
from __future__ import annotations

import json
import os
import re
from typing import Any, Callable, Dict, List, Optional, Sequence

BackendFn = Callable[[str, str], str]  # (prompt, role) -> antwort

DEFAULT_CRITERIA = ("korrektheit", "vollstaendigkeit", "umsetzbarkeit", "klarheit")
_DEFAULT_N = int(os.getenv("FUSION_JUDGE_N", "3"))
_ACCEPT_THRESHOLD = float(os.getenv("FUSION_JUDGE_ACCEPT", "0.6"))

_TOKEN_RE = re.compile(r"[a-zA-Zäöüß0-9]{3,}")


def _judge_schema(criteria: Sequence[str]) -> Dict[str, Any]:
    props: Dict[str, Any] = {
        c: {"type": "number", "minimum": 0, "maximum": 1} for c in criteria
    }
    props["begruendung"] = {"type": "string"}
    return {"type": "object", "required": list(criteria), "properties": props}


def _judge_prompt(problem: str, candidate: str, criteria: Sequence[str], idx: int) -> str:
    crit_list = ", ".join(criteria)
    return (
        f"[judge #{idx}] Bewerte die folgende Lösung streng und unabhängig. "
        f"Vergib für JEDES Kriterium ({crit_list}) einen Wert 0.0–1.0 "
        f"(0=unbrauchbar, 1=exzellent). Sei kalibriert, nicht großzügig.\n\n"
        f"**Problem:** {problem}\n\n**Lösung:**\n{str(candidate)[:6000]}"
    )


def _offline_judge(problem: str, candidate: str, criteria: Sequence[str]) -> Dict[str, float]:
    """Deterministischer lexikalischer Proxy (kein LLM). Ehrlich: keine Semantik."""
    p = frozenset(t.lower() for t in _TOKEN_RE.findall(problem or ""))
    c = frozenset(t.lower() for t in _TOKEN_RE.findall(candidate or ""))
    coverage = len(p & c) / max(1, len(p))
    length = min(1.0, len(c) / 60.0)  # sehr kurze Antworten schwächer
    base = round(0.5 * coverage + 0.5 * length, 4)
    # leichte deterministische Variation je Kriterium (kein Zufall)
    out: Dict[str, float] = {}
    for i, crit in enumerate(criteria):
        jitter = ((abs(hash(crit)) % 17) - 8) / 100.0
        out[crit] = float(max(0.0, min(1.0, base + jitter)))
    return out


def judge_once(
    problem: str,
    candidate: str,
    criteria: Sequence[str],
    idx: int,
    backend: Optional[BackendFn],
) -> Dict[str, Any]:
    """Ein Judge-Urteil (schema-validiert, wenn Backend vorhanden)."""
    if backend is None:
        scores = _offline_judge(problem, candidate, criteria)
        return {"ok": True, "offline": True, "scores": scores,
                "overall": round(sum(scores.values()) / len(scores), 4)}
    try:
        import structured_output as so
    except Exception:
        scores = _offline_judge(problem, candidate, criteria)
        return {"ok": True, "offline": True, "scores": scores,
                "overall": round(sum(scores.values()) / len(scores), 4)}

    schema = _judge_schema(criteria)
    prompt = _judge_prompt(problem, candidate, criteria, idx)
    res = so.request_structured(backend, prompt, schema, role="anti_agent")
    if not res.get("ok"):
        return {"ok": False, "offline": False, "error": res.get("issues"), "scores": {}, "overall": 0.0}
    data = res["data"]
    scores = {c: float(data.get(c, 0.0)) for c in criteria}
    return {"ok": True, "offline": False, "scores": scores,
            "overall": round(sum(scores.values()) / len(scores), 4),
            "begruendung": data.get("begruendung", "")}


def _mean(xs: Sequence[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def _std(xs: Sequence[float]) -> float:
    if len(xs) < 2:
        return 0.0
    m = _mean(xs)
    return (sum((x - m) ** 2 for x in xs) / len(xs)) ** 0.5


def evaluate(
    problem: str,
    candidate: str,
    backend: Optional[BackendFn] = None,
    n_judges: int = _DEFAULT_N,
    criteria: Sequence[str] = DEFAULT_CRITERIA,
    accept_threshold: float = _ACCEPT_THRESHOLD,
) -> Dict[str, Any]:
    """N unabhängige Judges bewerten den Kandidaten; aggregiert Score + Konsens."""
    n_judges = max(1, n_judges)
    verdicts = [judge_once(problem, candidate, criteria, i + 1, backend) for i in range(n_judges)]
    ok = [v for v in verdicts if v.get("ok")]
    overalls = [v["overall"] for v in ok]
    offline = all(v.get("offline") for v in ok) if ok else True

    score = round(_mean(overalls), 4)
    agreement = round(1.0 - min(1.0, _std(overalls) / 0.5), 4)  # 1=einig, ->0 uneins
    # Mehrheitsvotum accept/reject je Judge relativ zum Schwellwert
    accepts = sum(1 for o in overalls if o >= accept_threshold)
    majority_accept = accepts * 2 > len(overalls) if overalls else False

    per_criterion: Dict[str, float] = {}
    for c in criteria:
        vals = [v["scores"].get(c, 0.0) for v in ok if v.get("scores")]
        per_criterion[c] = round(_mean(vals), 4)

    return {
        "ok": bool(ok),
        "offline": offline,
        "score": score,
        "agreement": agreement,
        "majority_accept": majority_accept,
        "accepts": accepts,
        "n_judges": len(overalls),
        "per_criterion": per_criterion,
        "verdicts": verdicts,
        "honesty": ("Offline-Stub: lexikalischer Proxy, keine Semantik."
                    if offline else "Semantisches Urteil via injiziertes Backend."),
    }


def rank(
    problem: str,
    candidates: Sequence[str],
    backend: Optional[BackendFn] = None,
    n_judges: int = _DEFAULT_N,
    criteria: Sequence[str] = DEFAULT_CRITERIA,
) -> List[Dict[str, Any]]:
    """Best-of-N: bewertet mehrere Kandidaten und sortiert nach Score absteigend."""
    scored = []
    for i, cand in enumerate(candidates):
        ev = evaluate(problem, cand, backend=backend, n_judges=n_judges, criteria=criteria)
        scored.append({"index": i, "candidate": cand, **ev})
    scored.sort(key=lambda s: s["score"], reverse=True)
    return scored


def status() -> Dict[str, Any]:
    return {
        "module": "judge_panel",
        "default_judges": _DEFAULT_N,
        "criteria": list(DEFAULT_CRITERIA),
        "accept_threshold": _ACCEPT_THRESHOLD,
        "scoring": "semantisch (N-Judge, schema-validiert) — offline: lexikalischer Proxy",
    }


if __name__ == "__main__":
    problem = "Kontext geht zwischen Agenten-Schritten verloren."
    cands = [
        "Speichere pro Schritt einen Kontext-Anker im conversation_context_core und "
        "reiche ihn als Root-Kontext an den nächsten Schritt weiter.",
        "Mach halt irgendwas.",
    ]
    ranked = rank(problem, cands)
    for r in ranked:
        print(f"  #{r['index']} score={r['score']} agree={r['agreement']} "
              f"accept={r['majority_accept']} offline={r['offline']}")
    print("Hinweis:", ranked[0]["honesty"])
