# -*- coding: utf-8 -*-
"""
coevolution_router.py — Koevolvierende Kosten-/Fähigkeits-Routing-Policy
========================================================================
Verschmilzt drei Mythos-Aufhol-Bausteine zu EINEM sich gemeinsam entwickelnden
System (statt drei isolierter Module):

  * #1 Kosten-/Fähigkeits-Routing  — WELCHES Backend für welche Aufgabe.
  * #5 Eval-/Benchmark-Schleife     — die Policy wird an einem Aufgaben-Set
        GEMESSEN, nicht behauptet.
  * #7 Judge-Panel als Fitness       — Qualität liefert judge_panel (semantisch),
        Kosten liefert cost_estimator_node (EWMA). Fitness = Qualität − Kosten.

Mechanik (bewusst identisch zu faden_strength_coevolution.py, damit es an den
vorhandenen Coevolutions-Begriff des Repos andockt statt danebenzustehen):
μ+λ-Evolutionsstrategie, mehrere SPEZIES mit unterschiedlicher Fitness-
Perspektive (qualität / kosten / eskalation / balance), Konsens-Kopplung an den
globalen Champion + Migration, elitäre Selektion (Fitness monoton nicht-fallend).

Was koevolviert: eine Policy, die aus der Aufgaben-SCHWIERIGKEIT d∈[0,1] ein
Backend wählt (score_b = a_b + c_b·d, argmax). Die Population sucht die Policy,
die leichte Aufgaben ans billige lokale Modell und harte ans teure Frontier-
Modell routet — genau die „Mythos-Qualität haben, ohne sie nachzubauen"-Idee.

EHRLICH (Code-Honesty):
  * Die Evolution läuft per Default auf einem SYNTHETISCHEN, deterministisch
    geseedeten Backend-Benchmark (Qualität/Kosten je Backend als Funktion der
    Schwierigkeit) — eine DESIGN-SUCHE, KEIN Beweis über reale Nutzung. Genau
    wie der Faden-Benchmark. Für echte Fitness: fitness_live() mit judge_panel +
    realem generate_fn + cost_estimator einsetzen.
  * Die evolvierte Policy ist ein linearer Schwellen-Router — bewusst einfach
    und inspizierbar, kein Blackbox-Modell.

Aufruf:  python coevolution_router.py     # Coevolution-Lauf + gelernte Policy
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np

SEED = 20260707
_rng = np.random.default_rng(SEED)

# Backends: (name, kosten relativ). Qualität kommt aus dem Benchmark unten.
BACKENDS: Tuple[str, ...] = ("llama-local", "grok-intern", "claude-science")
_COST = {"llama-local": 1.0, "grok-intern": 4.0, "claude-science": 8.0}
_MAX_COST = max(_COST.values())

# Wie stark Kosten gegen Qualität zählen (globales Ziel — NICHT im Genom, sonst
# würde die Policy sich das Ziel selbst schönrechnen).
COST_WEIGHT = float(0.10)

GENOME_DIM = 2 * len(BACKENDS)  # [a_b, c_b] je Backend


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


# ---------------------------------------------------------------------------
# Synthetischer Backend-Benchmark (Qualität/Kosten je Schwierigkeit)
# ---------------------------------------------------------------------------

def _quality(backend: str, d: np.ndarray) -> np.ndarray:
    """Hidden ground truth: Qualität je Backend als Funktion der Schwierigkeit d∈[0,1].

    Realistischer Trade-off: das lokale Modell ist bei leichten Aufgaben top,
    bricht aber bei schweren ein; das Frontier-Modell hält Qualität überall;
    grok liegt dazwischen. (deterministisch, geseedet)
    """
    if backend == "llama-local":
        return np.clip(0.88 - 0.62 * d, 0.0, 1.0)
    if backend == "grok-intern":
        return np.clip(0.82 - 0.22 * d, 0.0, 1.0)
    if backend == "claude-science":
        return np.clip(0.95 - 0.05 * d, 0.0, 1.0)
    return np.zeros_like(d)


def make_task_difficulties(n: int = 200) -> np.ndarray:
    """Aufgaben-Set: Schwierigkeiten d∈[0,1] (Beta -> mehr leichte als schwere)."""
    return _rng.beta(2.0, 2.2, size=n)


# ---------------------------------------------------------------------------
# Policy: lineares Schwellen-Routing
# ---------------------------------------------------------------------------

@dataclass
class Policy:
    genome: np.ndarray  # [a_0, c_0, a_1, c_1, ...] je Backend

    def _scores(self, d: np.ndarray) -> np.ndarray:
        """(n, n_backends) Routing-Scores; argmax je Zeile = gewähltes Backend."""
        g = self.genome
        cols = []
        for i in range(len(BACKENDS)):
            a, c = g[2 * i], g[2 * i + 1]
            cols.append(a + c * d)
        return np.column_stack(cols)

    def route_indices(self, d: np.ndarray) -> np.ndarray:
        return np.argmax(self._scores(d), axis=1)

    def route_one(self, difficulty: float) -> str:
        idx = int(np.argmax(self._scores(np.array([float(difficulty)]))[0]))
        return BACKENDS[idx]

    def decode(self) -> Dict[str, Dict[str, float]]:
        g = self.genome
        return {
            BACKENDS[i]: {"bias": round(float(g[2 * i]), 3), "difficulty_slope": round(float(g[2 * i + 1]), 3)}
            for i in range(len(BACKENDS))
        }


def _rank(a: np.ndarray) -> np.ndarray:
    order = np.argsort(a, kind="mergesort")
    ranks = np.empty_like(order, dtype=float)
    ranks[order] = np.arange(len(a), dtype=float)
    return ranks


def _spearman(a: np.ndarray, b: np.ndarray) -> float:
    ra, rb = _rank(a), _rank(b)
    ra, rb = ra - ra.mean(), rb - rb.mean()
    denom = math.sqrt(float(np.sum(ra * ra)) * float(np.sum(rb * rb))) + 1e-12
    return float(np.sum(ra * rb) / denom)


# ---------------------------------------------------------------------------
# Fitness (synthetischer Benchmark)
# ---------------------------------------------------------------------------

def fitness_components(policy: Policy, d: np.ndarray) -> Dict[str, float]:
    idx = policy.route_indices(d)
    names = [BACKENDS[i] for i in idx]
    qual = np.array([_quality(BACKENDS[i], np.array([d[k]]))[0] for k, i in enumerate(idx)])
    cost = np.array([_COST[n] for n in names])
    norm_cost = cost / _MAX_COST

    mean_quality = float(np.mean(qual))
    cost_efficiency = float(1.0 - np.mean(norm_cost))
    # Eskalation: schwerere Aufgaben sollen an teurere (=fähigere) Backends gehen
    escalation = max(0.0, _spearman(d, cost))
    # Diversität: nicht alles auf ein Backend kollabieren
    used = len(set(names))
    diversity = (used - 1) / (len(BACKENDS) - 1) if len(BACKENDS) > 1 else 1.0
    # Wahres Netto-Ziel (Qualität minus gewichtete Kosten)
    net = float(np.mean(qual - COST_WEIGHT * norm_cost))

    return {
        "mean_quality": round(mean_quality, 4),
        "cost_efficiency": round(cost_efficiency, 4),
        "escalation": round(escalation, 4),
        "diversity": round(diversity, 4),
        "net_objective": round(net, 4),
    }


SPECIES: Dict[str, Dict[str, float]] = {
    "qualitaet":  {"mean_quality": 0.6, "cost_efficiency": 0.1, "escalation": 0.2, "diversity": 0.1},
    "kosten":     {"mean_quality": 0.2, "cost_efficiency": 0.6, "escalation": 0.1, "diversity": 0.1},
    "eskalation": {"mean_quality": 0.25, "cost_efficiency": 0.2, "escalation": 0.45, "diversity": 0.1},
    "balance":    {"mean_quality": 0.3, "cost_efficiency": 0.3, "escalation": 0.25, "diversity": 0.15},
}
GLOBAL_WEIGHTS = {"mean_quality": 0.4, "cost_efficiency": 0.25, "escalation": 0.25, "diversity": 0.1}
CONSENSUS_COUPLING = 0.2


def _weighted(comp: Dict[str, float], w: Dict[str, float]) -> float:
    return float(sum(comp.get(k, 0.0) * wv for k, wv in w.items()))


def _genome_distance(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.linalg.norm(a - b))


@dataclass
class Species:
    name: str
    weights: Dict[str, float]
    pop: np.ndarray
    mu: int = 8
    lam: int = 24
    best_genome: np.ndarray = field(default=None)
    best_fit: float = -1.0
    attractor: np.ndarray = field(default=None)

    def evaluate(self, genome: np.ndarray, d: np.ndarray) -> float:
        base = _weighted(fitness_components(Policy(genome), d), self.weights)
        if self.attractor is not None:
            bonus = math.exp(-_genome_distance(genome, self.attractor))
            return (1.0 - CONSENSUS_COUPLING) * base + CONSENSUS_COUPLING * bonus
        return base

    def step(self, d: np.ndarray, sigma: float) -> None:
        parents = self.pop
        offspring = []
        for _ in range(self.lam):
            i, j = _rng.integers(0, len(parents), size=2)
            if _rng.random() < 0.3:
                mask = _rng.random(GENOME_DIM) < 0.5
                child = np.where(mask, parents[i], parents[j]).astype(float)
            else:
                child = parents[i].astype(float).copy()
            child = child + _rng.normal(0.0, sigma, size=GENOME_DIM)
            offspring.append(child)
        pool = np.vstack([parents, np.array(offspring)])
        fits = np.array([self.evaluate(g, d) for g in pool])
        order = np.argsort(-fits)
        self.pop = pool[order[: self.mu]]
        if fits[order[0]] > self.best_fit:
            self.best_fit = float(fits[order[0]])
            self.best_genome = pool[order[0]].copy()


def coevolve(max_gens: int = 300, stable_k: int = 12, fixpoint_eps: float = 1e-3,
             verbose: bool = False) -> Dict[str, Any]:
    """Koevolviert die Routing-Policy bis Fixpunkt-Stabilität oder max_gens."""
    global _rng
    _rng = np.random.default_rng(SEED)  # reproduzierbar: jeder Lauf startet identisch
    d = make_task_difficulties()
    species = [Species(name=n, weights=w, pop=_rng.normal(0.0, 1.0, size=(8, GENOME_DIM)))
               for n, w in SPECIES.items()]

    prev_global_best: Optional[np.ndarray] = None
    stable_streak = 0
    history: List[Dict[str, Any]] = []
    gens_to_stability = None
    best_genome = species[0].pop[0]

    for gen in range(1, max_gens + 1):
        sigma = 0.35 * (0.5 ** (gen / 100.0)) + 0.02
        for sp in species:
            sp.attractor = prev_global_best
            sp.step(d, sigma)
        if gen % 10 == 0:
            champ = max(species, key=lambda s: s.best_fit).best_genome
            for sp in species:
                fits = np.array([sp.evaluate(g, d) for g in sp.pop])
                sp.pop[int(np.argmin(fits))] = champ.copy()

        globals_ = [(sp, _weighted(fitness_components(Policy(sp.best_genome), d), GLOBAL_WEIGHTS))
                    for sp in species]
        best_sp, best_global = max(globals_, key=lambda t: t[1])
        best_genome = best_sp.best_genome
        fixpoint_delta = _genome_distance(prev_global_best, best_genome) if prev_global_best is not None else 1.0
        prev_global_best = best_genome.copy()

        is_stable = fixpoint_delta < fixpoint_eps
        stable_streak = stable_streak + 1 if is_stable else 0
        history.append({"gen": gen, "best_global": round(best_global, 4),
                        "fixpoint_delta": round(fixpoint_delta, 5), "stable_streak": stable_streak})
        if verbose and (gen <= 3 or gen % 25 == 0):
            print(f"  gen {gen:3d} | global_best={best_global:.4f} | fixpkt_Δ={fixpoint_delta:.5f} "
                  f"| stabil={stable_streak}")
        if stable_streak >= stable_k:
            gens_to_stability = gen
            break

    winner = Policy(best_genome)
    comp = fitness_components(winner, d)
    # Sanity: wie routet die Gewinner-Policy über das Schwierigkeitsspektrum?
    grid = np.linspace(0.0, 1.0, 11)
    routing_map = {round(float(x), 1): winner.route_one(float(x)) for x in grid}

    return {
        "stabilitaet_erreicht": gens_to_stability is not None,
        "generationen_bis_stabilitaet": gens_to_stability,
        "global_best_fitness": round(history[-1]["best_global"], 4),
        "fitness_komponenten": comp,
        "policy": winner.decode(),
        "policy_genome": [round(float(x), 4) for x in best_genome],
        "routing_map": routing_map,
        "honesty": ("DESIGN-SUCHE auf synthetischem Backend-Benchmark (geseedet), "
                    "kein Beweis über reale Nutzung — für echte Fitness fitness_live() nutzen."),
    }


# ---------------------------------------------------------------------------
# Live-Nutzung: gelernte Policy anwenden + echte Fitness messen
# ---------------------------------------------------------------------------

_DIFFICULTY_HINTS = ("beweis", "proof", "architektur", "refactor", "optimier", "sicherheit",
                     "concurren", "race", "distributed", "verify", "mehrstufig", "komplex")


def estimate_difficulty(task_text: str) -> float:
    """Billige Heuristik: Schwierigkeit aus Länge + Signalwörtern (0..1).

    Ehrlich: nur eine Heuristik; für Ernstfälle mit gemessenen Schwierigkeiten
    (z.B. aus vergangenen judge-Scores) ersetzen.
    """
    t = (task_text or "").lower()
    length_sig = min(1.0, len(t) / 400.0)
    hint_sig = min(1.0, sum(1 for h in _DIFFICULTY_HINTS if h in t) / 4.0)
    return round(0.5 * length_sig + 0.5 * hint_sig, 4)


def route(task_text: str, policy_genome: Sequence[float]) -> Dict[str, Any]:
    """Wendet eine (evolvierte) Policy auf eine konkrete Aufgabe an."""
    d = estimate_difficulty(task_text)
    backend = Policy(np.asarray(policy_genome, dtype=float)).route_one(d)
    return {"backend": backend, "difficulty": d, "relative_cost": _COST.get(backend)}


def fitness_live(
    policy_genome: Sequence[float],
    tasks: Sequence[str],
    generate_fn: Callable[[str, str], str],
    judge_backend: Optional[Callable[[str, str], str]] = None,
    cost_of: Optional[Callable[[str], float]] = None,
) -> Dict[str, Any]:
    """ECHTE Fitness: Policy routet jede Aufgabe, generate_fn erzeugt die Antwort
    über das gewählte Backend, judge_panel bewertet die Qualität, cost_of liefert
    die Kosten. Fitness = mean(Qualität − COST_WEIGHT × norm_Kosten).

    generate_fn(prompt, backend_name) -> antwort. judge_backend wird an
    judge_panel durchgereicht (None -> Offline-Proxy). cost_of(backend) ->
    relative Kosten (Default: _COST-Tabelle; real: cost_estimator_node).
    """
    import judge_panel

    cost_of = cost_of or (lambda b: _COST.get(b, _MAX_COST))
    rows = []
    for task in tasks:
        r = route(task, policy_genome)
        backend = r["backend"]
        try:
            answer = generate_fn(task, backend)
        except Exception as exc:
            answer = f"[generate-error] {exc}"
        ev = judge_panel.evaluate(task, answer, backend=judge_backend)
        norm_cost = cost_of(backend) / _MAX_COST
        rows.append({
            "task": task[:80], "backend": backend, "difficulty": r["difficulty"],
            "quality": ev["score"], "norm_cost": round(norm_cost, 4),
            "net": round(ev["score"] - COST_WEIGHT * norm_cost, 4),
            "offline_judge": ev["offline"],
        })
    net = round(sum(x["net"] for x in rows) / len(rows), 4) if rows else 0.0
    return {"fitness": net, "n_tasks": len(rows), "rows": rows,
            "offline": all(x["offline_judge"] for x in rows) if rows else True}


def status() -> Dict[str, Any]:
    return {
        "module": "coevolution_router",
        "role": "koevolvierende Kosten-/Fähigkeits-Routing-Policy (fusioniert #1/#5/#7)",
        "backends": list(BACKENDS),
        "relative_costs": _COST,
        "cost_weight": COST_WEIGHT,
        "species": list(SPECIES.keys()),
        "mechanism": "μ+λ + Konsens-Kopplung + Migration (wie faden_strength_coevolution)",
        "honesty": "synthetischer Benchmark = Design-Suche; fitness_live() für echte Messung",
    }


if __name__ == "__main__":
    import json

    print("=" * 70)
    print("  Coevolution-Router — Kosten-/Faehigkeits-Routing per mu+lambda-Coevolution")
    print("=" * 70)
    res = coevolve(verbose=True)
    print("\nStabilität erreicht:", res["stabilitaet_erreicht"],
          f"(Gen {res['generationen_bis_stabilitaet']})")
    print("Global-Fitness:", res["global_best_fitness"])
    print("Fitness-Komponenten:", json.dumps(res["fitness_komponenten"], ensure_ascii=False))
    print("\nGelernte Policy (Routing über Schwierigkeit 0.0 -> 1.0):")
    print(json.dumps(res["routing_map"], indent=2, ensure_ascii=False))
    print("\nHinweis:", res["honesty"])
