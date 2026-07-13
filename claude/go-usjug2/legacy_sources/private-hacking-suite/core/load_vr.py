#!/usr/bin/env python3
"""
Quick loader for VR / Highest Layer (Private Hacking Suite).
Run: python load_vr.py
"""

import sys
from pathlib import Path

# Point to the copied highest layer in benchmarks
module_path = Path(__file__).parent.parent / "benchmarks"
sys.path.insert(0, str(module_path))

try:
    from highest_layer import load_vr
except ImportError:
    print("highest_layer not found in benchmarks, adjust as needed.")
    sys.exit(1)

if __name__ == "__main__":
    print("=== Private Hacking Suite - Loading VR / Highest Layer ===")
    hl = load_vr()
    
    print(f"Mode: {hl.meta['mode']}")
    print(f"VR Active: {getattr(hl, 'vr_active', False)}")
    print(f"Generation: {hl.protocol.current_generation}")
    print(f"Fitness: {hl.protocol.last_fitness}")
    
    print("\nVR Assets loaded:")
    for asset in hl.vr_assets.list_assets():
        print(f"  • {asset['id']}")
    
    print("\nVR Track active in protocol.")
    print("\nUsage:")
    print("  hl.run_generation_cycle(100)")
    print("  hl.create_vr_snapshot()")
    print("  print(hl.render_roadmap_visual())")
    print("  print(hl.get_vr_status())")
    
    # Keep hl in globals for interactive use if run with python -i
    globals()['hl'] = hl
    print("\n✓ Highest Layer (mit VR) loaded into variable 'hl'")
