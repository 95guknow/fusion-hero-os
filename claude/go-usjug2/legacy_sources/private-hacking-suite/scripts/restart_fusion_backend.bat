@echo off
setlocal enabledelayedexpansion

echo === Fusion Hero OS - Backend Neustart mit vollem Virtual Hyperthreading + GPU ===

cd /d "C:\Users\Admin\fusion-hero-os\03_Code\Dashboard"

echo Stopping old uvicorn processes...
powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like '*uvicorn*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"

timeout /t 3 /nobreak >nul

echo Setting all activation flags...
set FUSION_USE_GPU=1
set FUSION_VIRTUAL_HT_GPU=1
set FUSION_VIRTUAL_THREADS=256
set FUSION_VIRTUAL_STATE_SIZE=256
set FUSION_GPU_SHARE_FACTOR=3.0
set FUSION_VCACHE_AGGRESSIVE=1
set FUSION_USE_GPU=1
set FUSION_HYPERTHREADING=1
set FUSION_PROFILE=admin
set FUSION_PERFORMANCE_RATIO=1.0
set FUSION_HYPERTHREADING=1
set FUSION_PROFILE=admin
set FUSION_PERFORMANCE_RATIO=1.0
set FUSION_TRINITY_FAST=1
set FUSION_TRINITY_MAX_MODELS=2
set FUSION_MODEL_MAX_TOKENS=768
set FUSION_ORCH_EXECUTOR_WORKERS=4
set FUSION_WINDOWS_SKIN=synthwave
set FUSION_SSD_LONGTERM_CACHE=C:\FusionHero\LongTermCache
if not exist "%FUSION_SSD_LONGTERM_CACHE%" mkdir "%FUSION_SSD_LONGTERM_CACHE%"

echo Flags set:
echo   FUSION_USE_GPU=%FUSION_USE_GPU%
echo   FUSION_VIRTUAL_HT_GPU=%FUSION_VIRTUAL_HT_GPU%
echo   FUSION_PROFILE=%FUSION_PROFILE%
echo   FUSION_PERFORMANCE_RATIO=%FUSION_PERFORMANCE_RATIO%

echo Starting backend minimized...
start "FusionBackend" /min cmd /c ""C:\Users\Admin\venv\Scripts\python.exe" -m uvicorn app:app --host 127.0.0.1 --port 8000 --log-level warning"

echo Waiting for startup (8s)...
timeout /t 8 /nobreak >nul

echo Done.
echo Check: http://127.0.0.1:8000/api/health
echo Workspace: http://127.0.0.1:8080

echo.
echo Current GPU status:
nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader

echo.
echo Hyperthreading status (if backend responsive):
powershell -Command "try { $h=Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/health' -TimeoutSec 3; Write-Host ('Profile: ' + $h.profile.active + ' | HT enabled: ' + $h.hyperthreading.enabled + ' | Workers: ' + $h.hyperthreading.workers) } catch { Write-Host 'Backend not yet responding on health endpoint.' }"

endlocal
pause
