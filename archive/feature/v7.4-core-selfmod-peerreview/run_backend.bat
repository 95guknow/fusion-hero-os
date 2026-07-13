@echo off
cd /d "%~dp003_Code\Dashboard"
if not defined FUSION_AUTO_LOAD set FUSION_AUTO_LOAD=1
set FUSION_HYPERTHREADING=1
set FUSION_PROFILE=two_thirds
set FUSION_PERFORMANCE_RATIO=0.667
set FUSION_BOOT_STEPS=2000
set FUSION_BOOT_N=12
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
set FUSION_TRINITY_FAST=1
set FUSION_TRINITY_MAX_MODELS=2
set FUSION_MODEL_MAX_TOKENS=768
set FUSION_ORCH_EXECUTOR_WORKERS=4
set FUSION_WINDOWS_SKIN=synthwave

REM GPU acceleration for QUBO / Mainframe
set FUSION_USE_GPU=1

REM Virtual Hyper-Threading via GPU VRAM caches (über virtuelle Caches in der GPU)
set FUSION_VIRTUAL_HT_GPU=1
set FUSION_VIRTUAL_THREADS=256
set FUSION_VIRTUAL_STATE_SIZE=256
set FUSION_GPU_STREAMS=8
set FUSION_GPU_SHARE_FACTOR=3.0
set FUSION_VCACHE_AGGRESSIVE=1
set FUSION_SSD_LONGTERM_CACHE=C:\FusionHero\LongTermCache
if not exist "%FUSION_SSD_LONGTERM_CACHE%" mkdir "%FUSION_SSD_LONGTERM_CACHE%"

REM Full performance
set FUSION_PROFILE=admin
set FUSION_PERFORMANCE_RATIO=1.0

REM Port 8000 freimachen — verhindert Errno 10048 bei Doppelstart
powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match 'uvicorn app:app' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"
timeout /t 2 /nobreak >nul

"C:\Users\Admin\venv\Scripts\python.exe" -m uvicorn app:app --host 127.0.0.1 --port 8000 --log-level warning