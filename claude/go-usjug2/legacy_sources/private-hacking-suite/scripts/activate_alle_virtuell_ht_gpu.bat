@echo off
echo === Private Hacking Suite - Activate Virtual HT over GPU Caches ===
cd /d "%~dp0\..\"
REM Adjust paths as needed for your private setup

set PRIVATE_USE_GPU=1
set PRIVATE_VIRTUAL_HT_GPU=1
set PRIVATE_VIRTUAL_THREADS=64
set PRIVATE_VIRTUAL_STATE_SIZE=512
set PRIVATE_HYPERTHREADING=1
set PRIVATE_PROFILE=admin
set FUSION_PERFORMANCE_RATIO=1.0

echo Flags gesetzt:
echo FUSION_USE_GPU=%FUSION_USE_GPU%
echo FUSION_VIRTUAL_HT_GPU=%FUSION_VIRTUAL_HT_GPU%
echo FUSION_VIRTUAL_THREADS=%FUSION_VIRTUAL_THREADS%

echo.
echo Starte virtuelles Hyperthreading Test (schwerer Load)...
"C:\Users\Admin\venv\Scripts\python.exe" "C:\Users\Admin\test_virtual_gpu_ht.py"

echo.
echo Starte schweren QUBO mit GPU + virtuellem HT...
"C:\Users\Admin\venv\Scripts\python.exe" -c "
import os, time, numpy as np
print('FUSION_USE_GPU=', os.getenv('FUSION_USE_GPU'))
print('FUSION_VIRTUAL_HT_GPU=', os.getenv('FUSION_VIRTUAL_HT_GPU'))
from qb_qubo import simulated_annealing
Q = np.random.RandomState(42).randn(80,80)
Q = (Q.T @ Q) * 0.03
print('Running heavy QUBO n=80, 4000 steps with virtual GPU-HT...')
t0 = time.time()
res = simulated_annealing(Q, steps=4000, T0=2.0)
print('Done in', round(time.time()-t0,2), 's')
print('Result shape/energy:', res[0].shape if hasattr(res[0],'shape') else 'scalar', res[1] if isinstance(res,tuple) else res)
"

echo.
echo Hyperthreading Status:
"C:\Users\Admin\venv\Scripts\python.exe" -c "
import os
os.environ['FUSION_USE_GPU']='1'
os.environ['FUSION_VIRTUAL_HT_GPU']='1'
from hyperthreading_config import status, parallel_workers
import json
s = status()
print(json.dumps(s, indent=2))
print('Effective workers:', parallel_workers())
"

echo.
echo GPU Status:
nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader

echo.
echo === Aktivierung abgeschlossen. Virtuelles Hyperthreading ueber GPU-Caches online. ===
pause
