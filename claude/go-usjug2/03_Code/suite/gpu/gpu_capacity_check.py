import os
import sys
sys.path.insert(0, r'C:\Users\Admin\fusion-hero-os\03_Code\Dashboard')

os.environ['FUSION_USE_GPU'] = '1'
os.environ['FUSION_VIRTUAL_HT_GPU'] = '1'

print("=== GPU Capacity Analysis for Fusion Hero OS ===")

try:
    import cupy as cp
    print("CuPy OK, version:", cp.__version__)
    if cp.cuda.is_available():
        dev = cp.cuda.Device(0)
        free, total = dev.mem_info
        print(f"Total VRAM: {total / 1024**2:.0f} MiB")
        print(f"Free VRAM: {free / 1024**2:.0f} MiB")
        print(f"Used VRAM: {(total-free)/1024**2:.0f} MiB")
        
        from virtual_gpu_hyperthreading import get_virtual_gpu_ht_cache
        c = get_virtual_gpu_ht_cache()
        print(f"\nVCache config: max={c.max}, state_size={c.state_size} floats ({c.state_size*4} bytes)")
        
        bytes_per = c.state_size * 4
        theo = free // bytes_per if bytes_per > 0 else 0
        realistic = int(theo * 0.5)  # headroom for QUBO matrices, kernels, overhead
        print(f"Theoretical max v-threads in free VRAM: {theo}")
        print(f"Realistic (50% headroom): {realistic}")
        
        print("\nHardware limits (GTX 1050 Ti):")
        print("  4GB VRAM total")
        print("  ~1.8 TFLOPS FP32")
        print("  768 CUDA cores (6 SMs x 128)")
        print("  CC 6.1 - limited modern CUDA features")
        print("  Current bottleneck: VRAM shared with desktop apps (~2GB used typically)")
        
        print("\nIn Fusion Hero OS context:")
        print("  - vcache can use ~1.5-2GB effectively for states")
        print("  - For QUBO: limit n to ~256-512 per batch to fit with v-threads")
        print("  - Use SSD spill for anything larger (long-term cache)")
        print("  - CPU (12 threads) for orchestration/agents when GPU saturated")
    else:
        print("No CUDA")
except Exception as e:
    print("Error:", e)

print("\nRecommendations:")
print("1. Close browsers/Edge/Discord to free 1-2GB VRAM")
print("2. Set smaller state_size (128) for more virtual threads")
print("3. Rely on SSD long-term cache for big datasets")
print("4. Full HT + admin profile for CPU side")
print("5. Monitor with nvidia-smi during heavy jobs")
