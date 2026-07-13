#!/usr/bin/env python3
"""Example: Load Highest Layer mit VR."""

from highest_layer import load_vr

print("Loading highest layer MIT VR...")

hl = load_vr()

print("\n=== Status (mit VR) ===")
print(hl.get_vr_status())

print("\n=== VR Assets ===")
for asset in hl.vr_assets.list_assets():
    print(f"  - {asset['id']}: {asset['description']}")

print("\n=== VR Roadmap Visual ===")
print(hl.render_roadmap_visual())

print("\n=== Run generations with VR track ===")
results = hl.run_generation_cycle(80)
print(f"Final fitness: {results[-1]['fitness']:.4f}")

print("\n=== VR Snapshot ===")
snap = hl.create_vr_snapshot()
print("VR Snapshot version:", snap.get("vr", {}).get("assets_referenced"))

print("\n✓ Highest layer loaded WITH VR (visual protocol + assets active).")
