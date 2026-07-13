import sys
print("Python:", sys.version)

try:
    import torch
    print("torch:", torch.__version__)
    print("cuda available:", torch.cuda.is_available())
    if torch.cuda.is_available():
        print("device count:", torch.cuda.device_count())
        print("current device:", torch.cuda.current_device())
except Exception as e:
    print("torch not available or error:", e)

try:
    import cupy as cp
    print("cupy available:", cp.cuda.is_available())
except Exception as e:
    print("cupy error:", e)

try:
    import psutil
    print("psutil available")
except:
    print("psutil not available")

print("Done")