import subprocess
import re

def get_gpu_temp():
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=temperature.gpu', '--format=csv,noheader,nounits'],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            temp = float(result.stdout.strip().split('\n')[0])
            return temp
    except Exception as e:
        pass
    return None

def get_cpu_temp():
    # Fallback - on Windows with Ryzen often not easy without tools.
    # Try a simple method or return estimate.
    try:
        # Using wmic if available for rough
        result = subprocess.run(
            ['wmic', 'path', 'Win32_PerfFormattedData_Counters_ThermalZoneInformation', 'get', 'Temperature'],
            capture_output=True, text=True, timeout=5, shell=True
        )
        # This often doesn't give direct C, skip detailed.
    except:
        pass
    # For now, return None or known from previous ~ high if load
    return None  # Placeholder, real reading tricky without admin/tools

if __name__ == "__main__":
    gpu = get_gpu_temp()
    cpu = get_cpu_temp()
    print(f"GPU Temp: {gpu} C" if gpu else "GPU Temp: N/A")
    print(f"CPU Temp: {cpu} C" if cpu else "CPU Temp: N/A (use HWInfo or Ryzen Master for accurate)")
