"""
Power Mesh Fusion — long-term evolution bottom-up of the dissertation.

Bottom-up strata S0→S6: leaf fragments → core → mesh → fusion organs →
power/governance (Ω) → dissertation text → public merge expression.

Each generation mutates a genome of stratum emphasis weights; fitness is
measured against real repo evidence (file presence + size honesty). Dual
timeline: t = wall clock, τ = structural height of strongest stratum.

Geltung:
  - Pipeline / scan / score = Spezifikation (what this module does)
  - Trajectory interpretation = Modell
  - Fitness as "progress of dissertation" = Bedingt (repo evidence only)

Policy: pseudo_inhouse_only · freemium=false · Dissertation ≡ OS
"""
from __future__ import annotations

import hashlib
import json
import os
import random
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
UTC = timezone.utc  # py3.10+compat (was datetime.UTC)
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

__all__ = [
    "StratumState",
    "Genome",
    "GenerationRecord",
    "EvolutionReport",
    "load_config",
    "scan_strata",
    "run_evolution",
    "status",
]


@dataclass
class StratumState:
    id: str
    name: str
    tau: float
    desc: str
    evidence_total: int
    evidence_hit: int
    coverage: float
    bytes_total: int
    missing: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Genome:
    """Emphasis weights per stratum (normalized)."""

    weights: dict[str, float]
    seed_tag: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"weights": dict(self.weights), "seed_tag": self.seed_tag}


@dataclass
class GenerationRecord:
    generation: int
    best_fitness: float
    mean_fitness: float
    best_genome: dict[str, float]
    tau_peak: float
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class EvolutionReport:
    ok: bool
    generations: int
    best_fitness: float
    initial_fitness: float
    fitness_delta: float
    trajectory: list[GenerationRecord]
    strata: list[StratumState]
    fusion_score: float
    mesh_score: float
    power_score: float
    dissertation_score: float
    tau_final: float
    t_started: str
    t_finished: str
    latency_ms: float
    principle: str
    platform: str = "10.0.0"
    direction: str = "bottom_up"
    geltung: str = "Spezifikation+Modell"

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["trajectory"] = [
            r.to_dict() if hasattr(r, "to_dict") else r for r in self.trajectory
        ]
        d["strata"] = [s.to_dict() if hasattr(s, "to_dict") else s for s in self.strata]
        return d


def load_config() -> dict[str, Any]:
    path = ROOT / "power_mesh_fusion_evolution.yaml"
    if not path.exists():
        return {}
    try:
        import yaml

        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}


def _output_dir(cfg: dict[str, Any] | None = None) -> Path:
    cfg = cfg or load_config()
    raw = (cfg.get("evolution") or {}).get("output_dir") or "~/.fusion/power_mesh_evolution"
    p = Path(os.path.expanduser(str(raw)))
    p.mkdir(parents=True, exist_ok=True)
    return p


def _file_bytes(rel: str) -> int | None:
    path = ROOT / rel
    if not path.is_file():
        return None
    try:
        return path.stat().st_size
    except OSError:
        return None


def scan_strata(cfg: dict[str, Any] | None = None) -> list[StratumState]:
    cfg = cfg or load_config()
    out: list[StratumState] = []
    for s in cfg.get("strata") or []:
        evidence = list(s.get("evidence") or [])
        hit = 0
        total_b = 0
        missing: list[str] = []
        for rel in evidence:
            b = _file_bytes(str(rel))
            if b is None:
                missing.append(str(rel))
            else:
                hit += 1
                total_b += int(b)
        n = max(1, len(evidence))
        cov = hit / n if evidence else 0.0
        out.append(
            StratumState(
                id=str(s.get("id") or ""),
                name=str(s.get("name") or ""),
                tau=float(s.get("tau") or 0.0),
                desc=str(s.get("desc") or ""),
                evidence_total=len(evidence),
                evidence_hit=hit,
                coverage=round(cov, 4),
                bytes_total=total_b,
                missing=missing,
            )
        )
    return out


def _stratum_map(strata: list[StratumState]) -> dict[str, StratumState]:
    return {s.id: s for s in strata}


def _normalize(weights: dict[str, float]) -> dict[str, float]:
    s = sum(max(0.0, float(v)) for v in weights.values()) or 1.0
    return {k: max(0.0, float(v)) / s for k, v in weights.items()}


def _default_genome(strata: list[StratumState]) -> Genome:
    # Bottom-up bias: lower strata slightly higher initial weight
    n = len(strata) or 1
    w = {}
    for i, s in enumerate(strata):
        # reverse index → more mass on bottom
        w[s.id] = float(n - i)
    return Genome(weights=_normalize(w), seed_tag="bottom_up_init")


def _component_scores(strata: list[StratumState]) -> dict[str, float]:
    sm = _stratum_map(strata)

    def cov(*ids: str) -> float:
        vals = [sm[i].coverage for i in ids if i in sm]
        return sum(vals) / len(vals) if vals else 0.0

    return {
        "stratum_coverage": sum(s.coverage for s in strata) / max(1, len(strata)),
        "fusion_coherence": cov("S1", "S3"),
        "mesh_presence": cov("S2"),
        "power_governance": cov("S4"),
        "dissertation_expression": cov("S5", "S6"),
    }


def fitness(
    genome: Genome,
    strata: list[StratumState],
    weights_cfg: dict[str, float],
) -> tuple[float, dict[str, float], float]:
    """Return (fitness, component_scores, tau_peak)."""
    comps = _component_scores(strata)
    # Genome modulates: reward emphasis that matches actual coverage (honest bottom-up)
    sm = _stratum_map(strata)
    alignment = 0.0
    tau_num = 0.0
    tau_den = 0.0
    for sid, w in genome.weights.items():
        c = sm[sid].coverage if sid in sm else 0.0
        alignment += w * c
        if sid in sm:
            tau_num += w * sm[sid].tau * c
            tau_den += w * c + 1e-9
    # Bottom-up bonus: if lower strata stronger than upper when upper is incomplete
    bottom_ids = [s.id for s in strata[:3]]
    top_ids = [s.id for s in strata[-2:]]
    bottom = sum(sm[i].coverage for i in bottom_ids if i in sm) / max(1, len(bottom_ids))
    top = sum(sm[i].coverage for i in top_ids if i in sm) / max(1, len(top_ids))
    bottom_up_bonus = 0.05 if bottom >= top - 0.05 else 0.0

    w = weights_cfg or {}
    score = (
        float(w.get("stratum_coverage", 0.35)) * comps["stratum_coverage"]
        + float(w.get("fusion_coherence", 0.20)) * comps["fusion_coherence"]
        + float(w.get("mesh_presence", 0.15)) * comps["mesh_presence"]
        + float(w.get("power_governance", 0.15)) * comps["power_governance"]
        + float(w.get("dissertation_expression", 0.15)) * comps["dissertation_expression"]
        + 0.15 * alignment
        + bottom_up_bonus
    )
    score = max(0.0, min(1.0, score))
    tau_peak = tau_num / tau_den if tau_den else 0.0
    return round(score, 6), comps, round(tau_peak, 4)


def _mutate(genome: Genome, rate: float, rng: random.Random) -> Genome:
    w = dict(genome.weights)
    keys = list(w.keys())
    if not keys:
        return genome
    for k in keys:
        if rng.random() < rate:
            w[k] = max(0.01, w[k] + rng.uniform(-0.15, 0.15))
    # occasional bottom-up reassert
    if rng.random() < rate * 0.5 and keys:
        w[keys[0]] *= 1.1
    return Genome(weights=_normalize(w), seed_tag=genome.seed_tag)


def _crossover(a: Genome, b: Genome, rng: random.Random) -> Genome:
    keys = sorted(set(a.weights) | set(b.weights))
    w = {}
    for k in keys:
        w[k] = a.weights.get(k, 0.0) if rng.random() < 0.5 else b.weights.get(k, 0.0)
    return Genome(weights=_normalize(w), seed_tag="xover")


def run_evolution(
    *,
    generations: int | None = None,
    seed: int | None = None,
) -> EvolutionReport:
    cfg = load_config()
    evo = cfg.get("evolution") or {}
    n_gen = int(generations if generations is not None else evo.get("generations", 64))
    mu = int(evo.get("mu", 4))
    lam = int(evo.get("lambda", 12))
    elite = int(evo.get("elite_keep", 2))
    mut_rate = float(evo.get("mutation_rate", 0.18))
    rng = random.Random(int(seed if seed is not None else evo.get("seed", 95)))
    weights_cfg = dict(evo.get("weights") or {})

    t0 = time.time()
    t_started = datetime.now(UTC).isoformat()
    strata = scan_strata(cfg)

    # Population of genomes; fitness landscape fixed by repo evidence (honest)
    base = _default_genome(strata)
    pop: list[Genome] = [base]
    for i in range(mu + lam - 1):
        pop.append(_mutate(base, mut_rate + 0.05, rng))

    trajectory: list[GenerationRecord] = []
    best_fit = -1.0
    best_g = base
    initial_fit = 0.0

    for g in range(n_gen):
        scored: list[tuple[float, Genome, float]] = []
        fits = []
        for genome in pop:
            fit, _, tau_p = fitness(genome, strata, weights_cfg)
            scored.append((fit, genome, tau_p))
            fits.append(fit)
        scored.sort(key=lambda x: x[0], reverse=True)
        best_fit, best_g, tau_peak = scored[0]
        if g == 0:
            initial_fit = best_fit
        mean_f = sum(fits) / max(1, len(fits))
        trajectory.append(
            GenerationRecord(
                generation=g,
                best_fitness=best_fit,
                mean_fitness=round(mean_f, 6),
                best_genome=dict(best_g.weights),
                tau_peak=tau_peak,
                notes="elite bottom-up" if g == 0 else "",
            )
        )
        # next generation: elites + offspring
        elites = [s[1] for s in scored[: max(1, elite)]]
        next_pop: list[Genome] = list(elites)
        while len(next_pop) < mu + lam:
            p1 = elites[rng.randrange(len(elites))]
            p2 = scored[rng.randrange(min(mu, len(scored)))][1]
            child = _crossover(p1, p2, rng)
            child = _mutate(child, mut_rate, rng)
            next_pop.append(child)
        pop = next_pop

    comps = _component_scores(strata)
    _, _, tau_final = fitness(best_g, strata, weights_cfg)
    t_finished = datetime.now(UTC).isoformat()
    report = EvolutionReport(
        ok=True,
        generations=n_gen,
        best_fitness=best_fit,
        initial_fitness=initial_fit,
        fitness_delta=round(best_fit - initial_fit, 6),
        trajectory=trajectory,
        strata=strata,
        fusion_score=round(comps["fusion_coherence"], 4),
        mesh_score=round(comps["mesh_presence"], 4),
        power_score=round(comps["power_governance"], 4),
        dissertation_score=round(comps["dissertation_expression"], 4),
        tau_final=tau_final,
        t_started=t_started,
        t_finished=t_finished,
        latency_ms=round((time.time() - t0) * 1000, 2),
        principle=str(cfg.get("principle") or "").strip(),
        platform=str(cfg.get("platform_version") or "10.0.0"),
        direction=str(cfg.get("direction") or "bottom_up"),
    )

    out = _output_dir(cfg)
    full_path = out / "last_evolution_report.json"
    full_path.write_text(
        json.dumps(report.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # public-safe summary (no huge missing lists beyond counts)
    pub = {
        "generated_at": t_finished,
        "ok": report.ok,
        "version": cfg.get("version"),
        "direction": report.direction,
        "generations": report.generations,
        "best_fitness": report.best_fitness,
        "initial_fitness": report.initial_fitness,
        "fitness_delta": report.fitness_delta,
        "fusion_score": report.fusion_score,
        "mesh_score": report.mesh_score,
        "power_score": report.power_score,
        "dissertation_score": report.dissertation_score,
        "tau_final": report.tau_final,
        "strata": [
            {
                "id": s.id,
                "name": s.name,
                "tau": s.tau,
                "coverage": s.coverage,
                "evidence_hit": s.evidence_hit,
                "evidence_total": s.evidence_total,
                "missing_count": len(s.missing),
            }
            for s in strata
        ],
        "trajectory_tail": [r.to_dict() for r in trajectory[-5:]],
        "geltung": report.geltung,
        "ontology": "dissertation_as_os",
        "sha16": hashlib.sha256(
            json.dumps(
                {"bf": report.best_fitness, "g": report.generations}, sort_keys=True
            ).encode()
        ).hexdigest()[:16],
    }
    (out / "last_evolution.summary.json").write_text(
        json.dumps(pub, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    pub_docs = ROOT / (cfg.get("public_summary") or "docs/dissertation/power_mesh_evolution.summary.json")
    pub_docs.parent.mkdir(parents=True, exist_ok=True)
    pub_docs.write_text(json.dumps(pub, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


def status() -> dict[str, Any]:
    cfg = load_config()
    strata = scan_strata(cfg)
    comps = _component_scores(strata)
    g = _default_genome(strata)
    fit, _, tau = fitness(g, strata, dict((cfg.get("evolution") or {}).get("weights") or {}))
    out = _output_dir(cfg)
    last = out / "last_evolution.summary.json"
    last_pub = None
    if last.is_file():
        try:
            last_pub = json.loads(last.read_text(encoding="utf-8"))
        except Exception:
            last_pub = None
    return {
        "ok": True,
        "version": cfg.get("version"),
        "direction": cfg.get("direction"),
        "ontology": cfg.get("ontology"),
        "strata": [s.to_dict() for s in strata],
        "component_scores": comps,
        "baseline_fitness": fit,
        "tau_baseline": tau,
        "merge_ladder": cfg.get("merge_ladder"),
        "power_operators": cfg.get("power_operators"),
        "last_summary": last_pub,
        "output_dir": str(out),
        "policy": cfg.get("policy"),
        "freemium": False,
    }


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(
        description="Power Mesh Fusion — long-term evolution bottom-up (dissertation)"
    )
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--generations", type=int, default=None)
    ap.add_argument("--seed", type=int, default=None)
    args = ap.parse_args()
    if args.status:
        print(json.dumps(status(), indent=2, ensure_ascii=False))
        return 0
    report = run_evolution(generations=args.generations, seed=args.seed)
    print(
        json.dumps(
            {
                "ok": report.ok,
                "generations": report.generations,
                "best_fitness": report.best_fitness,
                "initial_fitness": report.initial_fitness,
                "fitness_delta": report.fitness_delta,
                "fusion_score": report.fusion_score,
                "mesh_score": report.mesh_score,
                "power_score": report.power_score,
                "dissertation_score": report.dissertation_score,
                "tau_final": report.tau_final,
                "latency_ms": report.latency_ms,
                "strata": [
                    {
                        "id": s.id,
                        "coverage": s.coverage,
                        "hit": f"{s.evidence_hit}/{s.evidence_total}",
                    }
                    for s in report.strata
                ],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
