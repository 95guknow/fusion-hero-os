"""
Private Hacking Suite - BIG STRESS TEST BENCHMARK
Stress the virtual hyperthreading + GPU vcache with large scale QUBO.
Uses max virtual threads, aggressive GPU sharing, full QUBO solves on GPU via vcache.
"""

import os
import sys
import time
import numpy as np

# Ensure imports work - add Dashboard dir for hyperthreading_config, virtual, qb_qubo
DASH = r"C:\Users\Admin\fusion-hero-os\03_Code\Dashboard"
if DASH not in sys.path:
    sys.path.insert(0, DASH)

# Max aggressive settings for max GPU usage via vcache
os.environ['FUSION_USE_GPU'] = '1'
os.environ['FUSION_VIRTUAL_HT_GPU'] = '1'
os.environ['FUSION_VIRTUAL_THREADS'] = '256'
os.environ['FUSION_VIRTUAL_STATE_SIZE'] = '256'
os.environ['FUSION_GPU_SHARE_FACTOR'] = '3.0'
os.environ['FUSION_VCACHE_AGGRESSIVE'] = '1'
os.environ['FUSION_HYPERTHREADING'] = '1'
os.environ['FUSION_PROFILE'] = 'admin'
os.environ['FUSION_PERFORMANCE_RATIO'] = '1.0'

print("=" * 60)
print("PRIVATE HACKING SUITE - BIG STRESS TEST BENCHMARK")
print("=" * 60)
print(f"FUSION_USE_GPU={os.getenv('FUSION_USE_GPU')}")
print(f"FUSION_VIRTUAL_HT_GPU={os.getenv('FUSION_VIRTUAL_HT_GPU')}")
print(f"FUSION_VIRTUAL_THREADS={os.getenv('FUSION_VIRTUAL_THREADS')}")
print(f"FUSION_VCACHE_AGGRESSIVE={os.getenv('FUSION_VCACHE_AGGRESSIVE')}")
print()

from hyperthreading_config import status, parallel_workers
from virtual_gpu_hyperthreading import get_virtual_gpu_ht_cache, gpu_virtual_energy_update
from qb_qubo import simulated_annealing

print("Hyperthreading status:")
s = status()
print(s)
print(f"Effective parallel workers: {parallel_workers()}")
print()

vcache = get_virtual_gpu_ht_cache()
print("VCache initial:", vcache.status())
print()

# Allocate as many virtual threads as possible for stress
print("Allocating max virtual threads for GPU sharing...")
n_vthreads = int(os.getenv('FUSION_VIRTUAL_THREADS', '256'))
tids = []
for i in range(n_vthreads):
    tid = vcache.allocate_virtual_thread()
    if tid > 0:
        tids.append(tid)
print(f"Allocated {len(tids)} virtual GPU threads")

# Pre-populate some QUBO-like data in vcache for sharing
print("Pinning QUBO contexts into vcache for more GPU usage...")
for i, tid in enumerate(tids[:min(32, len(tids))]):
    q = np.random.randn(64, 64).astype(np.float32) * 0.01
    x = np.random.randint(0, 2, 64).astype(np.float32)
    vcache.cache_qubo_context(tid, q, x)

print("VCache after pinning:", vcache.status())
print()

# Big big benchmark: multiple LARGE QUBO solves with virtual HT for stress
n = 512  # bigger - Q matrix ~2MB float32, many virtual states
steps = 20000  # very many steps
n_restarts = 64
num_benchmarks = 5  # sustained stress

print(f"Running {num_benchmarks} BIG QUBO benchmarks (n={n}, steps={steps}, restarts={n_restarts})")
print("This will heavily use GPU via vcache for virtual threads.")

total_time = 0
for b in range(num_benchmarks):
    print(f"\n--- Big Benchmark {b+1}/{num_benchmarks} ---")
    Q = np.random.RandomState(42 + b).randn(n, n)
    Q = (Q.T @ Q) * 0.005

    t0 = time.time()
    # Run with GPU + virtual
    res = simulated_annealing(Q, steps=steps, T0=2.5)
    dt = time.time() - t0
    total_time += dt

    if isinstance(res, (list, tuple)):
        energy = res[1]
    else:
        energy = res
    print(f"Benchmark {b+1} done in {dt:.2f}s, energy={energy:.4f}")

    # Use vcache for extra parallel virtual work - sustained stress
    print("  Running sustained virtual batch updates on GPU for extra stress (100 batches)...")
    dummy_q = np.random.randn(256).astype(np.float32) * 0.001
    for batch_idx in range(100):  # big loop to stress
        batch_start = (batch_idx * 8) % max(1, len(tids)-16)
        batch = tids[batch_start:batch_start+16]
        gpu_virtual_energy_update(batch, dummy_q)
        if batch_idx % 20 == 0:
            print(f"    Batch {batch_idx}/100, VCache: {vcache.status()}")

    print(f"  VCache during stress: {vcache.status()}")

print(f"\n=== STRESS TEST COMPLETE ===")
print(f"Total time: {total_time:.2f}s")
print(f"Average per benchmark: {total_time/num_benchmarks:.2f}s")
print(f"Final VCache: {vcache.status()}")
print("Check nvidia-smi for GPU load. Virtual hyperthreading should have driven heavy GPU usage via vcache.")
print("=" * 60)
