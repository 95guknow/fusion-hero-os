import os
import time
import numpy as np

os.environ['FUSION_USE_GPU'] = '1'
os.environ['FUSION_VIRTUAL_HT_GPU'] = '1'
os.environ['FUSION_VIRTUAL_THREADS'] = '64'

print("FUSION_USE_GPU =", os.getenv('FUSION_USE_GPU'))
print("FUSION_VIRTUAL_HT_GPU =", os.getenv('FUSION_VIRTUAL_HT_GPU'))
print("Starting HEAVY job: QUBO n=256, 10000 steps with GPU + virtual hyperthreading...")

from qb_qubo import simulated_annealing

Q = np.random.RandomState(42).randn(256, 256)
Q = (Q.T @ Q) * 0.005

t0 = time.time()
res = simulated_annealing(Q, steps=10000, T0=2.5)
dt = time.time() - t0

print("Heavy job completed in", round(dt, 1), "seconds")
if isinstance(res, (list, tuple)):
    print("Best energy:", res[1])
else:
    print("Result:", res)

print("Check nvidia-smi for GPU load and the virtual cache usage.")
