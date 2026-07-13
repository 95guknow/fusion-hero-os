#!/usr/bin/env python3
"""
Ghosthunting (Geisterjagd) Runner for Private Hacking Suite.

After bringing more stuff, go ghosthunting.

Uses the GeisterjagdBanachViz with optional springloop_energy for contraction.
Phoenix Mode / Ghost Hunt: latent heuristics emerge as manifest via Banach/Springloop contraction to fixed point.

Run:
  python ghosthunting/run_ghosthunt.py
  python ghosthunting/run_ghosthunt.py --springloop

How / When to go ghosthunting:
- When you have latent activations (unresolved ideas, partial states, heuristic signals).
- Use to visualize emergence + convergence.
- Combine with springloop for energy-based "hunting" of stable fixed points.
- Part of middle-out: core viz from middle layers, feeds L0 contraction and L6 vision.
"""

import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ghosthunting.geisterjagd_banach_viz import GeisterjagdBanachViz

def go_ghosthunting(use_springloop: bool = False, steps: int = 30):
    print("=== GO GHOSTHUNTING ===")
    print(f"Mode: {'Springloop + Banach' if use_springloop else 'Banach'}")
    print("Latent ghosts (heuristics) → manifest via contraction to s*")
    print()

    viz = GeisterjagdBanachViz(lambda_contract=0.78)
    hints = {
        "heuristic_score": 0.65,
        "event_rate": 0.4,
        "queue_pressure": 0.25,
        "lambda": 0.78,
        "use_springloop": use_springloop,
    }

    for t in range(steps):
        state = viz.tick(hints)
        if t % 5 == 0 or state["emerged"] > 0:
            print(f"tick={t:3d} | dist={state['distance']:.5f} | lambda={state['lambda']:.2f} | emerged={state['emerged']} | manifest={state['ghosts_manifest']}")
        time.sleep(0.05)

    snap = viz.snapshot()
    print("\nFinal snapshot:")
    print(f"  distance to s*: {snap['distance']}")
    print(f"  emergence_total: {snap['emergence_total']}")
    print(f"  ghosts: {len([g for g in snap.get('ghosts', []) if g.get('manifest')])} manifest")
    print("\nGhosthunting complete. Phoenix mode engaged.")

if __name__ == "__main__":
    use_spring = "--springloop" in sys.argv or "-s" in sys.argv
    go_ghosthunting(use_springloop=use_spring, steps=40)
