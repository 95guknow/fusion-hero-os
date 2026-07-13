@echo off
echo === FUSION HERO OS BIG BIG STRESS TEST BENCHMARK ===
cd /d "C:\Users\Admin\fusion-hero-os\03_Code\Dashboard"

set FUSION_USE_GPU=1
set FUSION_VIRTUAL_HT_GPU=1
set FUSION_VIRTUAL_THREADS=256
set FUSION_VIRTUAL_STATE_SIZE=256
set FUSION_GPU_SHARE_FACTOR=3.0
set FUSION_VCACHE_AGGRESSIVE=1
set FUSION_HYPERTHREADING=1
set FUSION_PROFILE=admin
set FUSION_PERFORMANCE_RATIO=1.0

echo Flags:
echo   FUSION_USE_GPU=%FUSION_USE_GPU%
echo   FUSION_VIRTUAL_HT_GPU=%FUSION_VIRTUAL_HT_GPU%
echo   FUSION_VIRTUAL_THREADS=%FUSION_VIRTUAL_THREADS%
echo   FUSION_VCACHE_AGGRESSIVE=%FUSION_VCACHE_AGGRESSIVE%

echo.
echo Starting stress test (this may take time and load GPU heavily via vcache)...
"C:\Users\Admin\venv\Scripts\python.exe" "C:\Users\Admin\stress_test_big_benchmark.py"

echo.
echo Stress test finished. GPU status:
nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader

echo.
echo Done.
pause
