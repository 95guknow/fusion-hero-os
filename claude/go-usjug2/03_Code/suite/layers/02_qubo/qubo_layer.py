#!/usr/bin/env python3
"""
Layer 1: QUBO / Math / Skills Core (Private Hacking Suite)
Processed layer-by-layer from public + best version.

Integrates springloop_energy for optimization loops.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.qb_qubo import (
    energy, 
    springloop_energy, 
    brute_force_min, 
    simulated_annealing,
    make_Q,
    local_search
)

def layer1_qubo_optimize(Q, use_springloop=True, **kwargs):
    """
    Layer 1 entry: QUBO optimization using springloop when enabled.
    Middle layer for energy based solving.
    """
    if use_springloop:
        x0 = kwargs.get('x0', None)
        if x0 is None:
            import numpy as np
            x0 = np.random.randint(0, 2, Q.shape[0]).astype(float)
        return springloop_energy(Q, x0, **kwargs)
    else:
        return simulated_annealing(Q, **kwargs)

# Example usage for layer processing
if __name__ == "__main__":
    print("[02_qubo / L1] QUBO Layer with Springloop")
    Q = make_Q(8)
    x, e = layer1_qubo_optimize(Q, use_springloop=True, steps=100)
    print(f"Springloop result energy: {e}")
    x2, e2 = layer1_qubo_optimize(Q, use_springloop=False, steps=1000)
    print(f"SA result energy: {e2}")

    # Hook ghosthunting into this layer's logic, use returned coevo to adjust
    try:
        from ghosthunting.hook import ghosthunt_hook
        snap, coevo = ghosthunt_hook("02_qubo", context={"events": 15}, use_springloop=True)
        if coevo and coevo.get('emerged', 0) > 0:
            print(f"  Adjusted QUBO steps based on ghost emergence: +{coevo['emerged']}")
            # e.g. more steps if more ghosts emerged
            x, e = layer1_qubo_optimize(Q, use_springloop=True, steps=100 + coevo['emerged']*10)
            print(f"  Adjusted Springloop energy: {e}")
    except Exception as e:
        print(f"  Ghosthunt hook failed: {e}")
