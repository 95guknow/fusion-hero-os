import sys
sys.path.insert(0, '.')

from virtual_gpu_hyperthreading import get_virtual_gpu_ht_cache
import cupy as cp

print("=== VCache Capacity in Current Setup ===")
c = get_virtual_gpu_ht_cache()
print(f"Configured max virtual threads: {c.max}")
print(f"State size per thread (float32): {c.state_size} floats = {c.state_size * 4} bytes")

free, total = cp.cuda.Device(0).mem_info
free_mb = free // (1024*1024)
total_mb = total // (1024*1024)
print(f"\nActual GPU memory:")
print(f"  Total: {total_mb} MiB")
print(f"  Free:  {free_mb} MiB")
print(f"  Used:  {(total - free) // (1024*1024)} MiB")

bytes_per_state = c.state_size * 4
max_theoretical = (free_mb * 1024 * 1024) // bytes_per_state if bytes_per_state > 0 else 0
print(f"\nTheoretical max states in free VRAM (with current state size): {max_theoretical}")

print(f"\nCurrent vcache status: {c.status()}")

# Realistic limits considering overhead (streams, QUBO matrices, other allocations)
realistic_max = int(max_theoretical * 0.6)  # conservative for overhead
print(f"Realistic max for safe concurrent use: ~{realistic_max} virtual threads")

print("\n=== GTX 1050 Ti Hardware Limits (for reference) ===")
print("VRAM: 4 GiB GDDR5")
print("CUDA Cores: 768")
print("Compute Capability: 6.1")
print("Max threads per block: 1024")
print("Shared memory per block: 48 KiB")
print("Note: Old Pascal architecture - limited concurrency, no modern features like MIG or advanced scheduling.")