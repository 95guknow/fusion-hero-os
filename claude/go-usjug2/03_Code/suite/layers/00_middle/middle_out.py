#!/usr/bin/env python3
"""
Private Hacking Suite - Middle-Out Expression (Middle-Out Design)

sprich wir exprimieren middleout

Wir starten im Middle (die praktischen Hacking-Cores: QUBO, GPU, LLM, Fusion-Experiments + Springloop-Energie).
Von dort exprimieren wir nach außen:
- Innen: Layer 0 (Foundation / MasterSeed mit Springloop als Kontraktion)
- Außen: Layer 6 (Vision / Highest) und Struktur (Launchers, Docs, Scripts)

Middle-Out = Core zuerst, dann Layer 0 + Layer 6 + Peripherie.
Springloop-Energie treibt die "Exprimierung" (iterative Kontraktion/Expansion).

Usage:
  python layers/00_middle/middle_out.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.qb_qubo import springloop_energy, energy, make_Q
import numpy as np

# Middle Cores (the expressive heart)
MIDDLE_CORES = {
    "qubo": "qubo/ - QUBO Miner + Optimizer (Springloop ready)",
    "gpu": "gpu/ - Acceleration, HT, Capacity checks",
    "llm": "llm/ - Local models, training, optimizer",
    "fusion": "fusion/ - Experiments, bottleneck tools",
}

def express_from_middle():
    """Express the architecture middle-out using Springloop energy."""
    print("=" * 60)
    print("MIDDLE-OUT EXPRESSION")
    print("sprich wir exprimieren middleout")
    print("=" * 60)

    print("\n[1] THE MIDDLE (Core Hacking Tools)")
    for name, desc in MIDDLE_CORES.items():
        print(f"  - {name}: {desc}")

    print("\n[2] Springloop-Energie als Middle Driver")
    Q = make_Q(6)
    x = np.random.randint(0, 2, 6).astype(float)
    init_e = energy(Q, x)
    x_s, e_s = springloop_energy(Q, x, steps=80, k=0.6, damping=0.88)
    print(f"  Initial Energy: {init_e:.4f}")
    print(f"  After Springloop: {e_s:.4f} (Kontraktion/Expansion)")
    print("  -> Springloop drückt die Middle-Optimierung aus.")

    print("\n[3] Outwards to Layers (from Middle)")
    print("  -> 01_foundation (L0): MasterSeed + Springloop Contraction")
    print("  -> 02_qubo, 03_gpu, 04_llm (Middle Layers)")
    print("  -> 05_fusion (Integration)")
    print("  -> 06_execution (Launchers/Scripts)")
    print("  -> 07_highest (L6 Vision): Top-Down Anchor")

    print("\n[4] Expressed Structure")
    print("  00_middle --Springloop--> 01_foundation ... 07_highest")

    print("\n[5] How to use")
    print("  - python process_layers.py   # all 8 coevo (ghosthunt + springloop)")
    print("  - python ghosthunting/hook.py   # direct hook test")
    print("  - python launcher.py")

    # Demonstrate hook from middle
    print("\n[6] Middle calling layer hooks")
    try:
        from ghosthunting.hook import ghosthunt_hook
        ghosthunt_hook("00_middle-demo", {"events": 20}, use_springloop=True)
    except Exception as e:
        print(f"  Hook from middle failed: {e}")

    print("\n" + "=" * 60)
    print("MIDDLE-OUT EXPRESSED. Core first. Everything radiates from here.")
    print("=" * 60)

if __name__ == "__main__":
    express_from_middle()
