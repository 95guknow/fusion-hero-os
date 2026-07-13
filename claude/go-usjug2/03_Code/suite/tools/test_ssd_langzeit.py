import os
os.environ.setdefault('FUSION_USE_GPU', '1')
os.environ.setdefault('FUSION_VIRTUAL_HT_GPU', '1')
os.environ.setdefault('FUSION_VCACHE_AGGRESSIVE', '1')

from virtual_gpu_hyperthreading import get_virtual_gpu_ht_cache, SSD_CACHE_DIR
import time

print("Testing SSD as Langzeit-Cache in VCache...")
print("SSD Cache Dir:", SSD_CACHE_DIR)

c = get_virtual_gpu_ht_cache()
print("Initial:", c.status())

# Allocate some, force spill
for i in range(10):
    tid = c.allocate_virtual_thread()
    if tid > 0:
        c.update_state(tid, 42.0 + i)
        c.spill_to_ssd(tid)  # manual spill for demo

print("After spill test:", c.status())

# Simulate load from SSD
print("Loading from SSD for a tid...")
c.load_from_ssd(1000)  # may or not exist

print("SSD files:", list(SSD_CACHE_DIR.glob("*.pkl"))[:5])

print("Langzeit SSD cache active for Fusion Hero OS.")
