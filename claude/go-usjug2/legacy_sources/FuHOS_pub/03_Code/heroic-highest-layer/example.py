#!/usr/bin/env python3
"""Example: Loading and using the Highest Layer (ohne VR)."""

from highest_layer import load

print("Loading highest layer (ohne VR)...")
hl = load()

print("\nStatus:")
print(hl.status())

print("\nCurrent Roadmap (clean):")
print(hl.get_roadmap())

print("\nRunning 250 generations...")
results = hl.run_generation_cycle(250)
print(f"Final generation: {results[-1]['generation']}")
print(f"Final fitness: {results[-1]['fitness']:.4f}")

print("\nSample proposal:")
prop = hl.propose()
for p in prop["proposals"]:
    print("  -", p)

print("\nCreating snapshot...")
snap = hl.create_snapshot()
print("Snapshot:", snap["version"])

print("\n✓ Highest layer loaded and exercised without any VR or visuals.")
