"""
Test: Virtuelles Hyperthreading über GPU Virtual Caches
Führt "hyper-parallele" Arbeit aus, indem viele virtuelle Threads ihre States im VRAM cachen.
"""
import os
import sys
os.environ.setdefault("FUSION_USE_GPU", "1")
os.environ.setdefault("FUSION_VIRTUAL_HT_GPU", "1")
os.environ.setdefault("FUSION_VIRTUAL_THREADS", "32")
os.environ.setdefault("FUSION_VIRTUAL_STATE_SIZE", "256")

# Make imports work when run from anywhere
DASHBOARD = r"C:\Users\Admin\fusion-hero-os\03_Code\Dashboard"
if DASHBOARD not in sys.path:
    sys.path.insert(0, DASHBOARD)

import time
import numpy as np
from hyperthreading_config import status, parallel_workers
from virtual_gpu_hyperthreading import get_virtual_gpu_ht_cache, gpu_virtual_energy_update

print("=== Virtual Hyper-Threading via GPU Caches Test ===")
print("HT status:", status())
print("Effective parallel workers:", parallel_workers())

cache = get_virtual_gpu_ht_cache()
print("Initial cache:", cache.status())

# Alloc viele virtuelle Threads (jeder hat State im VRAM)
n_vt = 24
tids = [cache.allocate_virtual_thread() for _ in range(n_vt)]
print(f"Allocated {len(tids)} virtual GPU threads")

# Simuliere hyper-parallele "Theorie-Modul" Arbeit (z.B. QUBO-like Updates)
start = time.time()
dummy_q = np.random.randn(256).astype(np.float32) * 0.001
for batch_start in range(0, len(tids), 8):
    batch = tids[batch_start:batch_start+8]
    gpu_virtual_energy_update(batch, dummy_q)

elapsed = time.time() - start
print(f"Batch virtual updates done in {elapsed:.3f}s")
print("Final cache:", cache.status())

# Cleanup
for t in tids:
    cache.free(t)
print("After free:", cache.status())
print("=== Test complete. GPU should show activity in nvidia-smi ===")
