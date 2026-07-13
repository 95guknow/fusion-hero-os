import os
import subprocess
import sys

print("=== GPU Capacity Check for Fusion Hero OS ===")

# nvidia-smi basic
try:
    result = subprocess.run(['nvidia-smi', '--query-gpu=name,driver_version,compute_cap,memory.total,memory.free,utilization.gpu', '--format=csv,noheader'], 
                            capture_output=True, text=True, timeout=10)
    print("nvidia-smi:", result.stdout.strip())
except Exception as e:
    print("nvidia-smi error:", e)

# CuPy properties
try:
    import cupy as cp
    print("\nCuPy version:", cp.__version__)
    if not cp.cuda.is_available():
        print("CuPy: No CUDA device available")
        sys.exit(1)
    
    dev = cp.cuda.Device(0)
    print("Device 0:", dev)
    
    attrs = dev.attributes
    print("\nKey attributes:")
    print("  Compute Capability:", f"{attrs.get('compute_capability_major', '?')}.{attrs.get('compute_capability_minor', '?')}")
    print("  Total Memory (GB):", round(dev.mem_info[1] / 1024**3, 2))
    print("  Free Memory (GB):", round(dev.mem_info[0] / 1024**3, 2))
    print("  Max threads per block:", attrs.get('max_threads_per_block', 'N/A'))
    print("  Max shared memory per block (KB):", attrs.get('shared_memory_per_block', 'N/A') // 1024 if 'shared_memory_per_block' in attrs else 'N/A')
    print("  Multiprocessor count:", attrs.get('multiprocessor_count', 'N/A'))
    
    # Theoretical for 1050 Ti
    print("\nTheoretical max for GTX 1050 Ti (Pascal CC 6.1):")
    print("  CUDA Cores: 768")
    print("  VRAM: 4 GB GDDR5")
    print("  Memory Bandwidth: ~112 GB/s")
    print("  Max concurrent kernels limited by 4GB and driver")
    
    # Current vcache context
    try:
        sys.path.insert(0, r'C:\Users\Admin\fusion-hero-os\03_Code\Dashboard')
        from virtual_gpu_hyperthreading import get_virtual_gpu_ht_cache
        c = get_virtual_gpu_ht_cache()
        print("\nCurrent VCache in setup:")
        print("  Max virtual threads:", c.max)
        print("  State size (floats):", c.state_size)
        print("  Estimated VRAM per state (KB):", round(c.state_size * 4 / 1024, 1))
        print("  Theoretical max threads in 3GB free:", int(3*1024*1024*1024 / (c.state_size * 4)) if c.state_size > 0 else 'N/A')
        status = c.status()
        print("  Current status:", status)
    except Exception as e:
        print("VCache not loadable:", e)

except ImportError:
    print("CuPy not installed or CUDA not detectable in this env.")
except Exception as e:
    print("CuPy query error:", e)

print("\n=== End of GPU Capacity Check ===")