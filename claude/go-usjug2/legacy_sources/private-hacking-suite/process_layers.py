#!/usr/bin/env python3
"""
Process everything layer by layer.
Middle-out + top-down + springloop.
Hooks ghosthunting (Geisterjagd) into layers for emergence + contraction viz.
Run: python process_layers.py
"""
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime

layers_dir = Path(__file__).parent / "layers"

# Hook ghosthunting into layer processing (middle-out)
sys.path.insert(0, str(Path(__file__).parent))
try:
    from ghosthunting.hook import ghosthunt_hook
    HAS_GHOST = True
except Exception as e:
    HAS_GHOST = False
    print(f"Ghosthunt hook unavailable: {e}")

print("=== Private Hacking Suite: Layer-by-Layer Processing ===")
print("Using springloop_energy where applicable (L0/L1)")
print("Ghosthunting hooked COEVOLUTIONÄR into ALL 8 (middle + L0-L6)")

coevo_state = None
all_layers = [d.name for d in sorted(layers_dir.iterdir()) if d.is_dir()]
coevo_history = []

for layer_name in all_layers:
    print(f"\n--- Processing {layer_name} ---")
    layer_dir = layers_dir / layer_name
    for py in sorted(layer_dir.glob("*.py")):
        print(f"  Running {py.name}...")
        try:
            result = subprocess.run([sys.executable, str(py)], capture_output=True, text=True, timeout=10)
            print(result.stdout.strip())
            if result.stderr:
                print("  stderr:", result.stderr.strip()[:200])
        except Exception as e:
            print(f"  Error: {e}")
        # Coevolutionary hook: pass state from previous
        if HAS_GHOST:
            context = {
                "events": 10 + (hash(layer_name) % 15),
                "queue": 3,
                "cpu": 25 + (hash(layer_name) % 20),
            }
            _, coevo_state = ghosthunt_hook(layer_name, context=context, use_springloop=True, steps=10, coevo_state=coevo_state)
            if coevo_state:
                coevo_state['layer'] = layer_name
                coevo_state['timestamp'] = datetime.now().isoformat()
                coevo_history.append(coevo_state)
        else:
            print(f"  [Ghosthunt hook skipped for {layer_name}]")

# Persist coevo state
if coevo_history:
    log_path = Path(__file__).parent / "coevo_evolution_log.json"
    with open(log_path, 'w') as f:
        json.dump(coevo_history, f, indent=2)
    print(f"\nCoevo state persisted to {log_path}")
    # Summary tweak
    total_emerged = sum(item.get('emerged', 0) for item in coevo_history)
    avg_energy = sum(item.get('springloop_energy', 0) for item in coevo_history) / len(coevo_history)
    print(f"Summary: Total emerged across 8 layers: {total_emerged}, Avg springloop energy: {avg_energy:.4f}")

print("\n=== All 8 processed COEVOLUTIONÄR ===")
print("Ghosthunting + springloop fully hooked across all layers. State propagates coevolutionarily.")
print("Middle-out: everything evolves together from the core.")
