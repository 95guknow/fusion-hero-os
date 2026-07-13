import os
os.environ['FUSION_USE_GPU'] = '1'

import time
import numpy as np
from qb_qubo import simulated_annealing

print("FUSION_USE_GPU =", os.getenv('FUSION_USE_GPU'))
print("Starting GPU QUBO test (n=64, steps=1000, restarts=8)...")

Q = np.random.RandomState(42).randn(64, 64)
Q = (Q.T @ Q) * 0.05

start = time.time()
res = simulated_annealing(Q, steps=2000, T0=2.0)
elapsed = time.time() - start

print("Solve completed in %.2fs" % elapsed)
print("Result:", res)
print("GPU test done. Check nvidia-smi for activity during run.")
