import os
import subprocess
import urllib.request
import json

print("=== Enabling GPU (Private Hacking Suite) ===")

# Check if we can reach backend
try:
    h = json.loads(urllib.request.urlopen("http://127.0.0.1:8000/api/health", timeout=4).read().decode())
    print("Backend online, profile:", h.get("profile", {}).get("active"))
except:
    print("Backend not reachable yet.")

print("\nCurrent FUSION_USE_GPU:", os.getenv("FUSION_USE_GPU", "NOT SET (will be 0)"))

print("\nTo force GPU path for next QUBO solves (after CuPy is installed):")
print("  - The env is set in the launch script.")
print("  - When FUSION_USE_GPU=1 and CuPy works, qb_qubo switches to GPU arrays automatically.")

print("\nTest command (once CuPy ready):")
print('  $env:FUSION_USE_GPU="1"; python -c "from qb_qubo import simulated_annealing; import numpy as np; Q=np.random.randn(32,32); Q=Q.T@Q; print(simulated_annealing(Q, steps=100))"')
