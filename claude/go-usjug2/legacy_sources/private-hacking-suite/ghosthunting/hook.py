#!/usr/bin/env python3
"""
Ghosthunting hook for layers.
Middle-out: call this from any layer to "hunt" latent states using Geisterjagd + springloop.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ghosthunting.geisterjagd_banach_viz import GeisterjagdBanachViz, build_hints_from_system
from core.qb_qubo import springloop_energy
import numpy as np

def ghosthunt_hook(layer_name: str, context: dict = None, use_springloop: bool = True, steps: int = 12, coevo_state: dict = None):
    """
    Hook Geisterjagd into a layer (coevolutionary).
    - context: hints
    - use_springloop: use springloop_energy
    - coevo_state: incoming energy/emergence from previous layer for coevolution
    Returns snapshot + updated coevo_state for next layer.
    """
    context = context or {}
    if coevo_state:
        # Coevolve: previous layer's energy influences this layer's heuristic
        prev_energy = coevo_state.get("springloop_energy", 0.0)
        context["heuristic_score"] = context.get("heuristic_score", 0.5) + (prev_energy * 0.1)
        context["events"] = context.get("events", 10) + int(abs(prev_energy) * 5)

    viz = GeisterjagdBanachViz(lambda_contract=0.78)
    
    hints = build_hints_from_system(
        event_count=context.get("events", 12),
        queue_len=context.get("queue", 5),
        cpu_pct=context.get("cpu", 30),
    )
    hints["use_springloop"] = use_springloop
    hints.update(context)

    # Boost for demo
    hints["event_rate"] = max(hints.get("event_rate", 0.3), 0.65)
    hints["heuristic_score"] = max(hints.get("heuristic_score", 0.4), 0.8)

    emerged_total = 0
    last_es = 0.0
    init_e = 0.0
    for _ in range(steps):
        state = viz.tick(hints)
        emerged_total += state.get("emerged", 0)
        
        if use_springloop:
            # Better Q for demo: use state to simulate energy landscape
            d = max(0.01, state.get("distance", 0.1))
            h = max(0.1, hints.get("heuristic_score", 0.5))
            Q = np.array([[1.0 + d, 0.2], [0.2, 0.9 + h]])
            x = np.array([d, h])
            init_e = sum(x * x)  # simple
            init_e_for_step = sum(x * x)
            xs, es = springloop_energy(Q, x, steps=5, k=0.6, damping=0.85)
            last_es = es
            delta = init_e_for_step - es
            hints["heuristic_score"] = max(0.1, min(0.95, abs(float(delta)) / 2 + 0.5))

    snap = viz.snapshot()
    print(f"[Ghosthunt hook -> {layer_name}] emerged={emerged_total} final_dist={snap['distance']:.5f} lambda={snap['lambda']}")
    if use_springloop:
        print(f"  Springloop delta energy: {init_e - last_es:.4f}")
    
    new_coevo = {
        "springloop_energy": last_es,
        "emerged": emerged_total,
        "dist": snap['distance']
    }
    return snap, new_coevo
