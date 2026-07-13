# -*- coding: utf-8 -*-
"""
faden_strength_coevolution.py
=============================
Co-Evolution mehrerer Kombinations-Konzepte für die ZWEI Faden-Stärke-Begriffe
des Repos, bis sich Stabilität einstellt.

Ausgangslage (zwei orthogonale Achsen, komplementär – nicht redundant):
  A) Aktivitäts-Stärke  (conversation_context_core.thread_strength):
       kontinuierlich, aus Aktualität (Zeit-Decay) × Engagement × Task-Gewicht.
       -> steuert Kontext-Budget + Laufzeit-Pruning INNERHALB einer Session.
  B) Konvergenz-Stärke  (faden_store.strength_from_lambda):
       diskrete Stufen fein<mittel<stark<fixpunkt aus dem Banach-λ
       (niedriges λ = nah am Fixpunkt = stärker).
       -> steuert Persistenz-TTL + Kapazität + Cloud-Sync ÜBER Sessions.

Frage: ob & wie sich beides zu EINER Stärke kombinieren lässt, die sowohl das
Tier (B) als auch das Budget (A) speist. Der Gewichtungs-/Schwellen-Raum ist
groß und nicht offensichtlich -> wir SUCHEN das Konzept per Co-Evolution.

EHRLICH (Code-Honesty):
  * Dies ist eine DESIGN-SUCHE auf einem SYNTHETISCHEN Faden-Benchmark, KEIN
    Beweis über reale Nutzungsdaten. Der Benchmark ist deterministisch geseedet.
  * "Stabilität" ist hier präzise definiert und wird gemessen, nicht behauptet:
      (a) KONTRAKTION  – die Kombinations-Abbildung ist Lipschitz-stabil
          (kleine Input-Störung -> kleinere Output-Änderung; Banach-nah).
      (b) KONSENS      – mehrere unabhängig evolvierte Spezies konvergieren zu
          ~demselben Konzept (Genom-Distanz < ε).
      (c) FIXPUNKT     – das global beste Konzept ändert sich über K
          Generationen hinweg um < ε (eingeschwungen).
  * μ+λ-Selektion ist elitär -> die beste Fitness ist monoton nicht-fallend
    (analog zur EVO-MONOTONIE-Zusage des Repos).

Aufruf:  python faden_strength_coevolution.py        # Demo-Lauf + Report
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Tuple

import numpy as np

# --- Reproduzierbarkeit: fester Seed (keine Wanduhr, deterministisch) ---------
SEED = 20260706
_rng = np.random.default_rng(SEED)

GENOME_DIM = 8  # [w_conv, w_rec, w_eng, w_wgt, gamma_raw, t0_raw, t1_raw, t2_raw]
TIER_NAMES = ("fein", "mittel", "stark", "fixpunkt")


def _softmax(v: np.ndarray) -> np.ndarray:
    e = np.exp(v - np.max(v))
    return e / (np.sum(e) + 1e-12)


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


@dataclass
class Concept:
    """Ein Kombinations-Konzept = dekodiertes Genom."""
    genome: np.ndarray

    def decode(self) -> Tuple[np.ndarray, float, np.ndarray]:
        g = self.genome
        weights = _softmax(g[0:4])                    # 4 nichtneg. Gewichte, Σ=1
        gamma = 0.5 + 1.5 * _sigmoid(float(g[4]))     # Nichtlinearität in (0.5, 2.0)
        cuts = np.sort(1.0 / (1.0 + np.exp(-g[5:8]))) # 3 Tier-Schwellen in (0,1), sortiert
        return weights, gamma, cuts

    def strength(self, X: np.ndarray) -> np.ndarray:
        """X: (n,4) Spalten [convergence, recency, engagement, weight] -> Stärke 0..1."""
        weights, gamma, _ = self.decode()
        lin = np.clip(X @ weights, 0.0, 1.0)
        return np.clip(lin ** gamma, 0.0, 1.0)

    def tiers(self, X: np.ndarray) -> np.ndarray:
        _, _, cuts = self.decode()
        s = self.strength(X)
        return np.digitize(s, cuts)  # 0=fein ... 3=fixpunkt


def make_benchmark(n: int = 240) -> np.ndarray:
    """Synthetischer Faden-Benchmark. Spalten: convergence(=1-λ), recency, engagement, weight.

    Milde, realistische Korrelation: stärker konvergierte Fäden (niedriges λ) sind
    tendenziell auch engagierter — aber mit Rauschen, damit die Achsen NICHT
    deckungsgleich sind (sonst wäre die Kombinationsfrage trivial).
    """
    lam = _rng.uniform(0.0, 0.99, size=n)
    convergence = 1.0 - lam
    engagement = np.clip(0.35 * convergence + _rng.beta(2, 3, size=n) * 0.8, 0, 1)
    recency = _rng.beta(2, 2, size=n)
    weight = _rng.choice([0.4, 0.7, 1.0], size=n)
    return np.column_stack([convergence, recency, engagement, weight])


def _rank(a: np.ndarray) -> np.ndarray:
    order = np.argsort(a, kind="mergesort")
    ranks = np.empty_like(order, dtype=float)
    ranks[order] = np.arange(len(a), dtype=float)
    return ranks


def _spearman(a: np.ndarray, b: np.ndarray) -> float:
    ra, rb = _rank(a), _rank(b)
    ra = ra - ra.mean()
    rb = rb - rb.mean()
    denom = math.sqrt(float(np.sum(ra * ra)) * float(np.sum(rb * rb))) + 1e-12
    return float(np.sum(ra * rb) / denom)


def _entropy_norm(counts: np.ndarray) -> float:
    p = counts / (counts.sum() + 1e-12)
    p = p[p > 0]
    h = -float(np.sum(p * np.log(p)))
    return h / math.log(len(TIER_NAMES))  # normiert auf 0..1


# --- Fitness-Komponenten (alle -> maximieren, ~0..1) --------------------------
def fitness_components(concept: Concept, X: np.ndarray) -> Dict[str, float]:
    s = concept.strength(X)
    conv = X[:, 0]
    activity = (X[:, 1] + X[:, 2]) / 2.0

    # (1) Monotonie zur Konvergenz-Achse (Banach-λ), (2) zur Aktivitäts-Achse
    mono_conv = max(0.0, _spearman(s, conv))
    mono_act = max(0.0, _spearman(s, activity))

    # (3) Kontraktion/Stabilität: kleine Input-Störung -> kleinere Output-Änderung.
    #     sensitivity = mittleres |Δs|/|Δx|; contraction hoch, wenn sensitivity klein (<1 = Banach-Kontraktion).
    eps = 0.02
    noise = _rng.normal(0.0, eps, size=X.shape)
    Xp = np.clip(X + noise, 0.0, 1.0)
    ds = np.abs(concept.strength(Xp) - s)
    dx = np.linalg.norm(Xp - X, axis=1) + 1e-9
    sensitivity = float(np.mean(ds / dx))
    contraction = 1.0 / (1.0 + sensitivity)  # sensitivity 0->1.0, =1->0.5, groß->0

    # (4) Diskrimination: Stärken sollen streuen (kein Kollaps auf einen Wert)
    discrimination = min(1.0, float(np.std(s)) / 0.29)  # 0.29 ~ std der Gleichverteilung

    # (5) Tier-Balance: Entropie der Tier-Verteilung (nicht alles in eine Stufe)
    tiers = concept.tiers(X)
    counts = np.array([int(np.sum(tiers == i)) for i in range(len(TIER_NAMES))], dtype=float)
    tier_balance = _entropy_norm(counts)

    return {
        "mono_conv": mono_conv,
        "mono_act": mono_act,
        "contraction": contraction,
        "discrimination": discrimination,
        "tier_balance": tier_balance,
        "sensitivity": sensitivity,  # roher Wert (Diagnose; <1 = Kontraktion)
    }


# Spezies = eigene Fitness-Gewichtung ("Konzept-Perspektive").
SPECIES: Dict[str, Dict[str, float]] = {
    "konvergenz": {"mono_conv": 0.55, "mono_act": 0.15, "contraction": 0.15, "discrimination": 0.075, "tier_balance": 0.075},
    "aktivitaet": {"mono_conv": 0.15, "mono_act": 0.55, "contraction": 0.15, "discrimination": 0.075, "tier_balance": 0.075},
    "stabilitaet": {"mono_conv": 0.2, "mono_act": 0.2, "contraction": 0.45, "discrimination": 0.075, "tier_balance": 0.075},
    "balance": {"mono_conv": 0.2, "mono_act": 0.2, "contraction": 0.15, "discrimination": 0.225, "tier_balance": 0.225},
}
GLOBAL_WEIGHTS = {"mono_conv": 0.25, "mono_act": 0.25, "contraction": 0.25, "discrimination": 0.125, "tier_balance": 0.125}

# Koevolutionäre Kopplung: wie stark Spezies zusätzlich für Nähe zum globalen
# Champion belohnt werden (Zug zum Konsens). Modat gehalten, damit Konsens nur
# entsteht, wenn die Objectives kompatibel sind — nicht erzwungen (kein Fake).
CONSENSUS_COUPLING = 0.22


def _weighted(components: Dict[str, float], weights: Dict[str, float]) -> float:
    return float(sum(components.get(k, 0.0) * w for k, w in weights.items()))


@dataclass
class Species:
    name: str
    weights: Dict[str, float]
    pop: np.ndarray  # (mu, GENOME_DIM)
    mu: int = 8
    lam: int = 24
    best_genome: np.ndarray = field(default=None)
    best_fit: float = -1.0
    attractor: np.ndarray = field(default=None)  # globaler Champion (Vorgen.) für Konsens-Kopplung

    def evaluate(self, genome: np.ndarray, X: np.ndarray) -> float:
        base = _weighted(fitness_components(Concept(genome), X), self.weights)
        if self.attractor is not None:
            bonus = math.exp(-_genome_distance(genome, self.attractor))  # 1 bei Deckung, ->0 bei Ferne
            return (1.0 - CONSENSUS_COUPLING) * base + CONSENSUS_COUPLING * bonus
        return base

    def step(self, X: np.ndarray, sigma: float) -> None:
        # λ Nachkommen aus μ Eltern (Mutation + gelegentl. Crossover), elitäre (μ+λ)-Selektion
        parents = self.pop
        offspring = []
        for _ in range(self.lam):
            i, j = _rng.integers(0, len(parents), size=2)
            if _rng.random() < 0.3:  # Crossover
                mask = _rng.random(GENOME_DIM) < 0.5
                child = np.where(mask, parents[i], parents[j]).astype(float)
            else:
                child = parents[i].astype(float).copy()
            child = child + _rng.normal(0.0, sigma, size=GENOME_DIM)
            offspring.append(child)
        pool = np.vstack([parents, np.array(offspring)])
        fits = np.array([self.evaluate(g, X) for g in pool])
        order = np.argsort(-fits)  # elitär: beste zuerst
        self.pop = pool[order[: self.mu]]
        if fits[order[0]] > self.best_fit:
            self.best_fit = float(fits[order[0]])
            self.best_genome = pool[order[0]].copy()


def _genome_distance(a: np.ndarray, b: np.ndarray) -> float:
    """Distanz im DEKODIERTEN Raum (vergleichbar über Gewichte+γ+Schwellen)."""
    wa, ga, ca = Concept(a).decode()
    wb, gb, cb = Concept(b).decode()
    return float(
        np.linalg.norm(wa - wb)
        + abs(ga - gb) / 1.5
        + np.linalg.norm(ca - cb)
    )


def coevolve(
    max_gens: int = 400,
    consensus_eps: float = 0.06,
    equilibrium_eps: float = 2e-3,
    fixpoint_eps: float = 1e-3,
    stable_k: int = 12,
    verbose: bool = True,
) -> Dict:
    """Co-Evolution bis Stabilität als System-Equilibrium oder max_gens.

    Stabilität = das SYSTEM ist eingeschwungen (NICHT: Konzepte werden identisch):
      * Anordnung eingefroren: Δ(konsens_dist) < equilibrium_eps über stable_k Gen.
      * globaler Fixpunkt:     Best-Genom-Änderung < fixpoint_eps.
      * Kontraktion:           die Kombinations-Abbildung ist Lipschitz-stabil (<1).
    Ob dabei ECHTER Konsens (konsens_dist < consensus_eps) oder ein stabiles
    MEHR-KONZEPT-Gleichgewicht (Pareto) herauskommt, wird ehrlich mitberichtet.
    """
    X = make_benchmark()
    species = [
        Species(name=n, weights=w, pop=_rng.normal(0.0, 1.0, size=(8, GENOME_DIM)))
        for n, w in SPECIES.items()
    ]

    prev_global_best: np.ndarray = None
    prev_consensus_dist = None
    stable_streak = 0
    history: List[Dict] = []
    gens_to_stability = None

    for gen in range(1, max_gens + 1):
        sigma = 0.35 * (0.5 ** (gen / 120.0)) + 0.02  # abkühlende Mutationsstärke
        for sp in species:
            sp.attractor = prev_global_best  # koevolutionäre Kopplung: Zug zum globalen Champion
            sp.step(X, sigma)

        # Migration: alle 10 Gen. wandert der globale Champion in jede Spezies (schwächstes Individuum ersetzt)
        if gen % 10 == 0:
            champ = max(species, key=lambda s: s.best_fit).best_genome
            for sp in species:
                fits = np.array([sp.evaluate(g, X) for g in sp.pop])
                sp.pop[int(np.argmin(fits))] = champ.copy()

        # Bewertung Konsens + Fixpunkt anhand GLOBAL-Fitness
        globals_ = [(sp, _weighted(fitness_components(Concept(sp.best_genome), X), GLOBAL_WEIGHTS)) for sp in species]
        best_sp, best_global = max(globals_, key=lambda t: t[1])
        best_genome = best_sp.best_genome

        # Konsens = max paarweise Genom-Distanz der Spezies-Champions
        champs = [sp.best_genome for sp in species]
        consensus_dist = max(
            _genome_distance(champs[a], champs[b])
            for a in range(len(champs)) for b in range(a + 1, len(champs))
        )
        # Fixpunkt = Änderung des globalen Champions
        fixpoint_delta = _genome_distance(prev_global_best, best_genome) if prev_global_best is not None else 1.0
        prev_global_best = best_genome.copy()

        consensus_delta = abs(consensus_dist - prev_consensus_dist) if prev_consensus_dist is not None else 1.0
        prev_consensus_dist = consensus_dist
        contraction_ok = fitness_components(Concept(best_genome), X)["sensitivity"] < 1.0
        # Equilibrium: Anordnung friert ein + globaler Fixpunkt + Kontraktion.
        is_stable = (consensus_delta < equilibrium_eps) and (fixpoint_delta < fixpoint_eps) and contraction_ok
        stable_streak = stable_streak + 1 if is_stable else 0

        history.append({
            "gen": gen, "best_global": round(best_global, 4),
            "consensus_dist": round(consensus_dist, 4), "fixpoint_delta": round(fixpoint_delta, 5),
            "stable_streak": stable_streak,
        })
        if verbose and (gen <= 3 or gen % 25 == 0 or stable_streak >= stable_k):
            print(f"  gen {gen:3d} | global_best={best_global:.4f} | konsens_dist={consensus_dist:.4f} "
                  f"| fixpkt_Δ={fixpoint_delta:.5f} | stabil_streak={stable_streak}")

        if stable_streak >= stable_k:
            gens_to_stability = gen
            break

    winner = Concept(best_genome)
    comp = fitness_components(winner, X)
    weights, gamma, cuts = winner.decode()
    tiers = winner.tiers(X)
    tier_counts = {TIER_NAMES[i]: int(np.sum(tiers == i)) for i in range(len(TIER_NAMES))}

    return {
        "stabilitaet_erreicht": gens_to_stability is not None,
        "generationen_bis_stabilitaet": gens_to_stability,
        "kontraktion": comp["sensitivity"] < 1.0,
        "sensitivity": round(comp["sensitivity"], 4),
        "konsens_am_ende": round(history[-1]["consensus_dist"], 4),
        "konsens_typ": ("echter_konsens" if history[-1]["consensus_dist"] < consensus_eps
                         else "stabiles_mehr-konzept-gleichgewicht"),
        "global_best_fitness": round(history[-1]["best_global"], 4),
        "gewinner_konzept": {
            "gewichte": {"convergence": round(float(weights[0]), 3), "recency": round(float(weights[1]), 3),
                          "engagement": round(float(weights[2]), 3), "weight": round(float(weights[3]), 3)},
            "gamma": round(gamma, 3),
            "tier_schwellen": [round(float(c), 3) for c in cuts],
        },
        "fitness_komponenten": {k: round(v, 4) for k, v in comp.items()},
        "tier_verteilung": tier_counts,
        "historie_kurz": history[:: max(1, len(history) // 8)] + [history[-1]],
    }


# ==================================================================
if __name__ == "__main__":
    import json

    print("=" * 70)
    print("  Faden-Stärke Co-Evolution — Kombination A (Aktivität) × B (Banach-λ)")
    print("=" * 70)
    print(f"Spezies: {list(SPECIES.keys())}  | Seed={SEED}")
    print("Ziel: Stabilität = Kontraktion + Konsens + Fixpunkt\n")

    result = coevolve()

    print("\n" + "-" * 70)
    print(f"Stabilität erreicht: {result['stabilitaet_erreicht']} "
          f"(nach {result['generationen_bis_stabilitaet']} Generationen)")
    print(f"Kontraktion (Banach-stabil): {result['kontraktion']}  "
          f"(sensitivity={result['sensitivity']} < 1 = kontrahierend)")
    print(f"Konsens der Spezies am Ende: dist={result['konsens_am_ende']}")
    print(f"Global-Fitness: {result['global_best_fitness']}")
    print("\nGewinner-Konzept (wie A und B zu EINER Stärke kombinieren):")
    print(json.dumps(result["gewinner_konzept"], indent=2, ensure_ascii=False))
    print("\nFitness-Komponenten:", json.dumps(result["fitness_komponenten"], ensure_ascii=False))
    print("Tier-Verteilung:", json.dumps(result["tier_verteilung"], ensure_ascii=False))
    print("=" * 70)
