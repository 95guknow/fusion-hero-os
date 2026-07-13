"""
Demo: autonomous self-optimization in action.
Simulates several solves to trigger param tuning.
"""
from optimizer import SelfOptimizer
import random
import time

print("=== DEMO: Miner self-optimization (selbstständig weiter optimieren) ===")
opt = SelfOptimizer()

for i in range(15):
    n = 15
    diff = 80
    # Force some slow solves to trigger adaptation visibly
    if i < 6:
        elapsed = random.uniform(0.45, 0.72)
    else:
        elapsed = random.uniform(0.12, 0.28)
    energy = -random.uniform(8, 32)
    used_gpu = i % 3 == 0

    opt.record_solve(n, elapsed, energy, used_gpu, diff)
    print(f"Sim solve {i+1}: n={n} t={elapsed:.3f}s energy={energy:.2f} gpu={used_gpu} -> mult now {opt.params['num_reads_mult']:.1f}")

print("\nFinal adapted params:", opt.params)
print("Optimizer will continue adapting in real main.py runs and persist to SSD cache.")
print("=== DEMO DONE ===")