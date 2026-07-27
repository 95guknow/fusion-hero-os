"""CLI vertical slice for the meta-neural network (local-only).

Uses the stdlib ``argparse`` (no new dependency). Runs the full flow on the
bundled neutral fixture and prints an auditable JSON summary::

    python -m fusion_hero_os.meta.cli demo
    python -m fusion_hero_os.meta.cli demo --backend numpy --seed 7
"""

from __future__ import annotations

import argparse
import json
import sys

from .consent import Purpose
from .fixtures import load_neutral_fixture
from .pipeline import MetaNeuralService


def run_demo(backend: str = "numpy", seed: int = 7, steps: int = 2000,
             cardinality: int | None = 2) -> dict:
    fixture = load_neutral_fixture()
    subject = fixture["subject_id"]
    svc = MetaNeuralService()

    # A grant per purpose used in the flow.
    grants = {
        p: svc.grant_consent(subject, p).grant_id
        for p in (Purpose.INGEST, Purpose.WORKING_MEMORY, Purpose.ASSOCIATION,
                  Purpose.OPTIMIZATION, Purpose.AUDIT_READ)
    }

    snapshot = svc.ingest(subject, grants[Purpose.INGEST],
                          fixture["nodes"], fixture["edges"])
    report = svc.activate(subject, grants[Purpose.WORKING_MEMORY],
                          fixture["activations"], steps=1)
    svc.associate(subject, grants[Purpose.ASSOCIATION])
    convergence = svc.analyze_convergence(subject, grants[Purpose.ASSOCIATION])
    result = svc.optimize(subject, grants[Purpose.OPTIMIZATION],
                          selection_dimension="salience", cardinality=cardinality,
                          backend=backend, seed=seed, steps=steps)
    valid, events = svc.audit_trail(subject, grants[Purpose.AUDIT_READ])

    return {
        "subject_id": subject,
        "snapshot": {"content_hash": snapshot.content_hash,
                     "nodes": len(snapshot.nodes), "edges": len(snapshot.edges)},
        "working_memory": report.to_dict(),
        "convergence": convergence.to_dict(),
        "optimization": result.to_dict(),
        "audit": {"chain_valid": valid, "event_count": len(events)},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Meta-neural vertical slice (local-only).")
    sub = parser.add_subparsers(dest="command", required=True)
    demo = sub.add_parser("demo", help="Run the full consent->optimize->audit flow.")
    demo.add_argument("--backend", default="numpy",
                      choices=["auto", "numpy", "qb_qubo", "rust", "brute"])
    demo.add_argument("--seed", type=int, default=7)
    demo.add_argument("--steps", type=int, default=2000)
    demo.add_argument("--cardinality", type=int, default=2)

    args = parser.parse_args(argv)
    if args.command == "demo":
        summary = run_demo(backend=args.backend, seed=args.seed, steps=args.steps,
                           cardinality=args.cardinality)
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0
    return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
