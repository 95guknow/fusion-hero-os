@echo off
echo Stopping old uvicorn...
powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match 'uvicorn app:app' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"
timeout /t 3 /nobreak >nul

cd /d "C:\Users\Admin\fusion-hero-os\03_Code\Dashboard"
set FUSION_USE_GPU=1
set FUSION_PROFILE=admin
set FUSION_PERFORMANCE_RATIO=1.0
set FUSION_HYPERTHREADING=1
set FUSION_VIRTUAL_HT_GPU=1
set FUSION_VIRTUAL_THREADS=128
set FUSION_VIRTUAL_STATE_SIZE=256
set FUSION_GPU_STREAMS=8
set FUSION_GPU_SHARE_FACTOR=2.0

echo Launching backend with GPU support...
start /min "" "C:\Users\Admin\venv\Scripts\python.exe" -m uvicorn app:app --host 127.0.0.1 --port 8000 --log-level warning

echo Waiting for backend...
timeout /t 8 /nobreak >nul

echo Done. Check http://127.0.0.1:8000/api/health
