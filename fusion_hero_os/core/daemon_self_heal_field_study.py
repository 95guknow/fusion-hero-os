"""
Daemon self-heal field study — Fixpunkt-Inversion + QUBO (lab only).

Uses **public clearweb** concepts about enterprise ontology/ops platforms
(as *comparative literature*, not as a live target) to design how *our*
local daemon returns to a healthy fixed point after drift.

Does NOT:
  - send traffic, payloads, or data to Palantir or any third party
  - scan external infrastructure
  - invert or extract foreign proprietary datasets

Does:
  - model local health bits as QUBO variables
  - invert drift toward Banach-style contraction to a healthy fixed point
  - write a field-study summary under docs/security/

Policy: sandbox_only · no_external_targets · Meister Hasch labor
Geltung: Spezifikation (local sim) · clearweb mapping = Modell
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
UTC = timezone.utc  # py3.10+compat (was datetime.UTC)
from pathlib import Path
from typing import Any
from collections.abc import Sequence

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SUMMARY = ROOT / "docs" / "security" / "daemon_self_heal_field_study.summary.json"
ALERT = Path.home() / ".fusion" / "alerts" / "daemon_self_heal_field_study.json"

# Binary health dimensions (lab-local daemon)
DIMS = (
    "api_auth_gate",       # P0 super-door hygiene
    "sandbox_only",        # offense locked
    "vault_local",         # secrets not in git
    "dead_letter_quarantine",
    "cors_localhost",
    "god_layer_state_ok",
    "mesh_secret_present",
    "public_narrative_clean",  # no combat framing
)

# Prefer healthy = 1 for all dims in target fixed point
TARGET = np.ones(len(DIMS), dtype=np.float64)


@dataclass
class ClearwebLens:
    """Public-category notes (not live recon)."""

    source_class: str
    public_idea: str
    daemon_analogy: str
    geltung: str = "Modell"


# What one finds on clearweb product/docs *categories* (no private data)
CLEARWEB_LENSES: list[ClearwebLens] = [
    ClearwebLens(
        source_class="enterprise_ontology_ops (public product narrative)",
        public_idea="Semantic object model (ontology) as single decision surface; closed-loop ops on customer-owned data.",
        daemon_analogy="Our Layer registry + MasterSeed: one integrity object model; heal means restore contraction to M0, not exfiltrate foreign ontology.",
    ),
    ClearwebLens(
        source_class="AIP / LLM-on-ops (public)",
        public_idea="Generative AI wired into operational workflows with governance claims.",
        daemon_analogy="Grok/connectors: heal = dry-run defaults, no silent external write; quarantine bad intents in dead letterboxes.",
    ),
    ClearwebLens(
        source_class="SRE / reliability (general clearweb)",
        public_idea="Detect drift, auto-remediate toward known-good config, circuit-break on blast radius.",
        daemon_analogy="QUBO chooses minimal flip-set of health bits; fixed-point iteration stops when distance to target is contracted.",
    ),
    ClearwebLens(
        source_class="fixed-point control / chaos stabilisation (literature)",
        public_idea="Stabilise fixed points under perturbation; contraction maps.",
        daemon_analogy="Invert drift vector: x <- x + alpha*(x* - x); require d(x_{k+1},x*) < d(x_k,x*).",
    ),
]


@dataclass
class HealStep:
    iteration: int
    state: list[int]
    energy: float
    distance: float
    flipped: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _energy(Q: np.ndarray, x: np.ndarray) -> float:
    return float(x @ Q @ x)


def _build_qubo(n: int, current: np.ndarray) -> np.ndarray:
    """
    QUBO favoring the target fixed point (all healthy=1).

    Diagonal: cost of being 0 when we want 1 (stronger if currently broken).
    Off-diagonal: weak coupling so flips come in coherent pairs (auth+cors, vault+sandbox).
    """
    Q = np.zeros((n, n), dtype=np.float64)
    for i in range(n):
        # Prefer x_i = 1: energy contribution ~ (1 - x_i)^2 via diagonal trick
        # Using standard: minimize x^T Q x with Q_ii negative for prefer-1 is messy;
        # we use: cost for x_i=0 encoded as +c on diagonal when flipped to 0 in {0,1}^n
        # Simple encoding: E = sum_i w_i (1-x_i)^2 + couplings
        # Expand: (1-x)^2 = 1 - 2x + x^2 = 1 - 2x + x (since x binary)
        # → linear term; map to Q by Q_ii += w_i and constant ignore
        broken = 1.0 if current[i] < 0.5 else 0.25
        Q[i, i] += -2.0 * (1.0 + broken)  # prefer x_i=1
    # Couplings: (x_i - x_j)^2 = x_i + x_j - 2 x_i x_j → off-diag positive for disagree
    pairs = [(0, 4), (1, 2), (3, 5), (6, 7)]
    for i, j in pairs:
        if i < n and j < n:
            Q[i, j] += 0.5
            Q[j, i] += 0.5
            Q[i, i] += 0.25
            Q[j, j] += 0.25
    return Q


def _hamming(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.sum(np.abs(a - b)))


def fixed_point_invert(
    state: np.ndarray,
    target: np.ndarray,
    *,
    alpha: float = 0.5,
    max_iter: int = 12,
    tol: float = 0.0,
) -> tuple[np.ndarray, list[HealStep], bool]:
    """
    Invert drift toward target with discrete projection (Banach-style contraction on Hamming).

    Continuous step then threshold to {0,1}. Success if strict contraction until fixed.
    """
    x = state.astype(np.float64).copy()
    steps: list[HealStep] = []
    Q = _build_qubo(len(x), x)
    contracted = True
    prev_d = _hamming(x, target)

    for k in range(max_iter):
        # Inversion: move opposite of residual (target - x is heal direction)
        residual = target - x
        x_cont = x + alpha * residual
        x_next = (x_cont >= 0.5).astype(np.float64)
        d = _hamming(x_next, target)
        flipped = [
            DIMS[i]
            for i in range(len(DIMS))
            if int(x_next[i]) != int(x[i])
        ]
        steps.append(
            HealStep(
                iteration=k,
                state=[int(v) for v in x_next],
                energy=_energy(Q, x_next),
                distance=d,
                flipped=flipped,
            )
        )
        if d > prev_d + 1e-9:
            contracted = False
        if d <= tol:
            return x_next, steps, contracted and True
        x = x_next
        prev_d = d
        Q = _build_qubo(len(x), x)

    return x, steps, contracted and _hamming(x, target) <= tol


def qubo_local_search(state: np.ndarray, Q: np.ndarray, rounds: int = 20) -> np.ndarray:
    """Greedy bit-flip local search minimizing x^T Q x (and distance to target via Q)."""
    x = state.astype(np.float64).copy()
    n = len(x)
    best_e = _energy(Q, x) + 0.1 * _hamming(x, TARGET)
    for _ in range(rounds):
        improved = False
        for i in range(n):
            x[i] = 1.0 - x[i]
            e = _energy(Q, x) + 0.1 * _hamming(x, TARGET)
            if e < best_e - 1e-12:
                best_e = e
                improved = True
            else:
                x[i] = 1.0 - x[i]
        if not improved:
            break
    return x


def run_field_study(
    *,
    initial: Sequence[int] | None = None,
    write: bool = True,
    seed: int = 0,
) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    if initial is None:
        # Simulated drifted daemon (field observation of own stack risks)
        # 0 = unhealthy: e.g. auth gate open problem known from super-door study
        raw = np.array([0, 1, 1, 1, 1, 1, 1, 0], dtype=np.float64)
        # small noise
        for i in range(len(raw)):
            if rng.random() < 0.05:
                raw[i] = 1.0 - raw[i]
        state = raw
    else:
        state = np.array(list(initial), dtype=np.float64)
        if len(state) != len(DIMS):
            raise ValueError(f"initial must have {len(DIMS)} bits")

    Q = _build_qubo(len(DIMS), state)
    after_qubo = qubo_local_search(state, Q)
    final, steps, ok = fixed_point_invert(after_qubo, TARGET, alpha=0.65, max_iter=16)

    report = {
        "kind": "daemon_self_heal_field_study",
        "generated_at": datetime.now(UTC).isoformat(),
        "policy": {
            "sandbox_only": True,
            "no_external_targets": True,
            "no_send_to_third_parties": True,
            "clearweb_lens_only": True,
            "meister_hasch_labor": True,
        },
        "clearweb_lenses": [asdict(c) for c in CLEARWEB_LENSES],
        "dimensions": list(DIMS),
        "target_fixed_point": [1] * len(DIMS),
        "initial_state": [int(v) for v in state],
        "after_qubo_local_search": [int(v) for v in after_qubo],
        "final_state": [int(v) for v in final],
        "healed": bool(_hamming(final, TARGET) == 0),
        "contraction_ok": ok,
        "steps": [s.to_dict() for s in steps],
        "initial_distance": _hamming(state, TARGET),
        "final_distance": _hamming(final, TARGET),
        "method": {
            "qubo": "local bit-flip search on health Q",
            "fixed_point_inversion": "x <- project(x + alpha*(x* - x))",
        },
        "explicit_non_actions": [
            "did_not_http_post_to_palantir",
            "did_not_scan_foreign_hosts",
            "did_not_exfiltrate_or_request_proprietary_data",
        ],
        "sha16": hashlib.sha256(
            json.dumps(
                {"i": [int(v) for v in state], "f": [int(v) for v in final]},
                sort_keys=True,
            ).encode()
        ).hexdigest()[:16],
        "geltung": "Local heal outcomes = Satz · clearweb analogy = Modell",
        "doc": "docs/security/DAEMON_SELF_HEAL_FIELD_STUDY.md",
    }

    if write:
        SUMMARY.parent.mkdir(parents=True, exist_ok=True)
        ALERT.parent.mkdir(parents=True, exist_ok=True)
        public = {
            k: report[k]
            for k in (
                "kind",
                "generated_at",
                "policy",
                "dimensions",
                "target_fixed_point",
                "initial_state",
                "after_qubo_local_search",
                "final_state",
                "healed",
                "contraction_ok",
                "initial_distance",
                "final_distance",
                "method",
                "explicit_non_actions",
                "sha16",
                "geltung",
                "doc",
            )
        }
        public["clearweb_lens_count"] = len(CLEARWEB_LENSES)
        public["step_count"] = len(steps)
        SUMMARY.write_text(
            json.dumps(public, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        ALERT.write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        report["evidence_paths"] = {"summary": str(SUMMARY), "alert": str(ALERT)}

    return report


def main(argv: list[str] | None = None) -> int:
    import argparse

    p = argparse.ArgumentParser(description="Daemon self-heal field study (lab only)")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--json", action="store_true")
    p.add_argument("--no-write", action="store_true")
    args = p.parse_args(argv)
    r = run_field_study(seed=args.seed, write=not args.no_write)
    if args.json:
        print(json.dumps(r, indent=2, ensure_ascii=False))
    else:
        print(
            f"[self-heal] dist {r['initial_distance']}→{r['final_distance']} "
            f"healed={r['healed']} contraction_ok={r['contraction_ok']} "
            f"sha16={r['sha16']}"
        )
        print("  clearweb lenses: comparative only — nothing sent off-box")
        if "evidence_paths" in r:
            print(f"  summary: {r['evidence_paths']['summary']}")
    return 0 if r["healed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
