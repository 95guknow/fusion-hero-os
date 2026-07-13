import os
os.environ['FUSION_USE_GPU'] = '1'
os.environ['FUSION_VIRTUAL_HT_GPU'] = '1'
os.environ['FUSION_VCACHE_AGGRESSIVE'] = '1'

from virtual_gpu_hyperthreading import get_virtual_gpu_ht_cache
import time

print("Testing self-adapting vcache size...")

c = get_virtual_gpu_ht_cache()
print("Initial max:", c.max, "status:", c.status())

# Simulate high demand
for i in range(50):
    c.allocate_virtual_thread()

print("After allocs:", c.status())

# Call adapt manually (simulates pressure)
c.adapt_size(gpu_pressure=0.9, gpu_util=0.7)
print("After adapt high pressure:", c.status())

time.sleep(1)
c.adapt_size(gpu_pressure=0.1, gpu_util=0.2)
print("After adapt low pressure:", c.status())

print("Self-adapting vcache size test done.")
