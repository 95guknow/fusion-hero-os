import subprocess
import os
import sys

print("=== GPU Hardware ===")
try:
    import cupy as cp
    print("CuPy version:", cp.__version__)
    print("CUDA available in CuPy:", cp.cuda.is_available())
    if cp.cuda.is_available():
        print("CUDA runtime version:", cp.cuda.runtime.runtimeGetVersion())
        print("Device count:", cp.cuda.runtime.getDeviceCount())
        dev = cp.cuda.Device(0)
        print("Device 0 name:", dev.attributes)
except Exception as e:
    print("CuPy not usable:", e)

print("\n=== Current FUSION envs ===")
for k in sorted(os.environ):
    if k.startswith("FUSION"):
        print(k, "=", os.environ[k])

print("\n=== Python / Venv ===")
print("Python:", sys.executable)
print("Trying import torch for GPU check...")
try:
    import torch
    print("PyTorch CUDA available:", torch.cuda.is_available())
    if torch.cuda.is_available():
        print("Torch device:", torch.cuda.get_device_name(0))
except Exception as e:
    print("No PyTorch or CUDA:", e)

print("\n=== Recommendations ===")
print("To enable GPU for QUBO in Fusion:")
print("1. pip install cupy-cuda12x  (in venv)")
print("2. Set FUSION_USE_GPU=1")
print("3. Restart backend")
