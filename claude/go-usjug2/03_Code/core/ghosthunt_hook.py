"""Canonical Geisterjagd hook — coevolutionary layer bridge (merged from suite)."""
from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

import numpy as np

from geisterjagd_banach_viz import GeisterjagdBanachViz, build_hints_from_system
from qb_qubo import springloop_energy


def ghosthunt_hook(
    layer_name: str,
    context: Optional[Dict[str, Any]] = None,
    *,
    use_springloop: bool = True,
    steps: int = 12,
    coevo_state: Optional[Dict[str, Any]] = None,
    verbose: bool = False,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Hook Geisterjagd into a layer with optional coevolutionary state propagation."""
    context = dict(context or {})
    if coevo_state:
        prev_energy = float(coevo_state.get("springloop_energy", 0.0))
        context["heuristic_score"] = context.get("heuristic_score", 0.5) + (prev_energy * 0.1)
        context["events"] = context.get("events", 10) + int(abs(prev_energy) * 5)

    viz = GeisterjagdBanachViz(lambda_contract=0.78)
    hints = build_hints_from_system(
        event_count=int(context.get("events", 12)),
        queue_len=int(context.get("queue", 5)),
        cpu_pct=float(context.get("cpu", 30)),
    )
    hints["use_springloop"] = use_springloop
    hints.update(context)
    hints["event_rate"] = max(hints.get("event_rate", 0.3), 0.65)
    hints["heuristic_score"] = max(hints.get("heuristic_score", 0.4), 0.8)

    emerged_total = 0
    last_es = 0.0
    init_e = 0.0
    for _ in range(steps):
        state = viz.tick(hints)
        emerged_total += int(state.get("emerged", 0))
        if use_springloop:
            d = max(0.01, float(state.get("distance", 0.1)))
            h = max(0.1, float(hints.get("heuristic_score", 0.5)))
            Q = np.array([[1.0 + d, 0.2], [0.2, 0.9 + h]])
            x = np.array([d, h])
            init_e = float(sum(x * x))
            _, es = springloop_energy(Q, x, steps=5, k=0.6, damping=0.85)
            last_es = float(es)
            delta = init_e - last_es
            hints["heuristic_score"] = max(0.1, min(0.95, abs(delta) / 2 + 0.5))

    snap = viz.snapshot()
    new_coevo = {
        "layer": layer_name,
        "springloop_energy": last_es,
        "emerged": emerged_total,
        "dist": float(snap.get("distance", 0.0)),
    }
    if verbose:
        print(
            f"[Ghosthunt hook -> {layer_name}] emerged={emerged_total} "
            f"final_dist={snap['distance']:.5f} lambda={snap.get('lambda', 0):.3f}"
        )
        if use_springloop:
            print(f"  Springloop delta energy: {init_e - last_es:.4f}")
    return snap, new_coevo