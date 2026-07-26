@echo off
cd /d "%~dp003_Code\Dashboard"
REM === Always: full frameworks + dashboard on :8000 ===
if not defined FUSION_AUTO_LOAD set FUSION_AUTO_LOAD=1
if not defined FUSION_PRELOAD_ALL set FUSION_PRELOAD_ALL=1
if not defined FUSION_ALL_MODULES set FUSION_ALL_MODULES=1
if not defined FUSION_BOOT_PHASE set FUSION_BOOT_PHASE=full
set FUSION_BACKEND_PORT=8000
set FUSION_DASHBOARD_PORT=8000
set FUSION_PORT_BASE=8000
set PORT=8000
set FUSION_HYPERTHREADING=1
set FUSION_PROFILE=admin
set FUSION_PERFORMANCE_RATIO=1.0
set FUSION_BOOT_STEPS=2000
set FUSION_BOOT_N=12
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
set FUSION_TRINITY_FAST=1
set FUSION_TRINITY_MAX_MODELS=2
set FUSION_MODEL_MAX_TOKENS=768
set FUSION_ORCH_EXECUTOR_WORKERS=4
set FUSION_WINDOWS_SKIN=synthwave
REM BIG ALPHA visual asset (Dissertation + static)
if not defined FUSION_BIG_ALPHA_ASSET set FUSION_BIG_ALPHA_ASSET=C:\Dissertation_95guknow\assets\big_ALPHA.png
if exist "%USERPROFILE%\.fusion\gdrive_spill.env" (
  for /f "usebackq tokens=1,* delims==" %%A in ("%USERPROFILE%\.fusion\gdrive_spill.env") do (
    if not "%%A"=="" if not "%%A:~0,1%"=="#" set "%%A=%%B"
  )
)
if not defined FUSION_SSD_LONGTERM_CACHE set FUSION_SSD_LONGTERM_CACHE=G:\Meine Ablage\FusionHero_Offload\LongTermCache
if not defined FUSION_MEMORY_SPILL set FUSION_MEMORY_SPILL=1
if not exist "%FUSION_SSD_LONGTERM_CACHE%" mkdir "%FUSION_SSD_LONGTERM_CACHE%" 2>nul

REM GPU acceleration for QUBO / Mainframe
set FUSION_USE_GPU=1

REM Adaptives CPU-Tuning: Last+Temperatur (z.B. 40%% Last / 70C -> Boost)
set FUSION_CPU_TUNER_AUTO=1
set FUSION_CPU_TEMP_SOFT_C=75
set FUSION_CPU_TEMP_HARD_C=82
set FUSION_CPU_LOAD_LOW_PCT=50
set FUSION_CPU_LOAD_HIGH_PCT=85

REM Adaptive VRAM-Steuerung: dedizierten Grafikspeicher fast voll, System-RAM minimal
set FUSION_GPU_ALLOCATOR_AUTO=1
set FUSION_VRAM_TARGET_RATIO=0.85
set FUSION_VRAM_FILL_BELOW_PCT=45
set FUSION_VRAM_FILL_RAM_MAX_PCT=72
set FUSION_VRAM_PRIORITIZER_AUTO=1
set FUSION_GPU_ALLOCATOR_MIN_INTERVAL=2
set FUSION_GPU_ALLOCATOR_MAX_INTERVAL=30

REM CPU+GPU+SSD gekoppelt — autonome Lastverteilung
set FUSION_RESOURCE_COUPLER_AUTO=1
set FUSION_RAM_SOFT_PCT=78
set FUSION_RAM_HARD_PCT=85
set FUSION_RAM_CRITICAL_PCT=90
set FUSION_MEMORY_GUARD_AUTO=1
set FUSION_LLAMA_GPU_LAYERS=20
set FUSION_LLAMA_CTX_SIZE=2048
set FUSION_VRAM_LOW_PCT=50
set FUSION_COUPLER_MIN_INTERVAL=2
set FUSION_COUPLER_MAX_INTERVAL=15

REM QUBO-Logik in lokalem Llama (Inference + Multi-Kandidaten-Scoring)
set FUSION_LLAMA_QUBO=1
set FUSION_LLAMA_QUBO_CANDIDATES=2
REM Subagenten testen Llama parallel (Status/CLI/QUBO; Generate nur bei freiem RAM)
set FUSION_LLAMA_SUBAGENT_AUTO=1
set FUSION_QUBO_SA_STEPS=1200
set FUSION_OFFLOAD_TO_GPU=1
set FUSION_HOST_RAM_MINIMAL=1

REM GPU Rechenlast (SM-Auslastung) autonom anheben wenn < 30%%
set FUSION_GPU_COMPUTE_BOOSTER_AUTO=1
set FUSION_GPU_COMPUTE_TARGET_PCT=55
set FUSION_GPU_COMPUTE_LOW_PCT=30
set FUSION_GPU_BOOSTER_MIN_INTERVAL=2
set FUSION_GPU_BOOSTER_MAX_INTERVAL=10
set FUSION_LLAMA_SERVER_AUTO=1
set FUSION_LLAMA_SERVER_PORT=8081
set FUSION_GPU_BOOST_MODEL=C:\Users\Admin\internal_llm\models\Llama-3.2-1B-Instruct-Q4_K_M.gguf

REM Alle Module freigeben
set FUSION_ALL_MODULES=1
set FUSION_PROVIDER_AUTO=1
set FUSION_PROVIDER_ORDER=llama-local,claude-science,grok-intern,fusion-hero
set FUSION_CLAUDE_SCIENCE=1
set FUSION_CLAUDE_SCIENCE_ESCALATE=1
set FUSION_BANACH_LAMBDA=0.74
set FUSION_LLM_BACKEND=llama-local
REM Agent nutzt Llama, Anti-Agent nutzt Grok
set FUSION_AGENT_BACKEND=llama-local
set FUSION_ANTI_AGENT_BACKEND=grok-intern
set FUSION_DUAL_AGENT=1
set FUSION_ORCH_DUAL_AGENT=1
set FUSION_FIRST_INSTALL_AUTO=1

REM Globale Agenten-Kontrolle (Multi-Strategie: geltung, peer_review, meta, audit)
set FUSION_AGENT_CONTROL=1
set FUSION_AGENT_CONTROL_FAIL_CLOSED=1
set FUSION_AGENT_CONTROL_STRATEGIES=geltung,peer_review,meta,audit
set FUSION_AGENT_CONTROL_MIN_VOTES=2

REM Supabase Persistenz (YOUR_SUPABASE_PROJECT_REF)
set FUSION_SUPABASE_SYNC=1
set PUBLIC_SUPABASE_PROJECT_REF=YOUR_SUPABASE_PROJECT_REF

REM Virtual Hyper-Threading via GPU VRAM caches (über virtuelle Caches in der GPU)
set FUSION_VIRTUAL_HT_GPU=1
set FUSION_VIRTUAL_THREADS=256
set FUSION_VIRTUAL_STATE_SIZE=256
set FUSION_GPU_STREAMS=8
set FUSION_GPU_SHARE_FACTOR=3.0
set FUSION_VCACHE_AGGRESSIVE=1
if not exist "%FUSION_SSD_LONGTERM_CACHE%" mkdir "%FUSION_SSD_LONGTERM_CACHE%" 2>nul

REM Stale exclusivity locks (dashboard:8000 / :42069) freigeben
powershell -NoProfile -Command "$ld=Join-Path $env:USERPROFILE '.fusion-hero-os\process_locks'; if(Test-Path $ld){ Get-ChildItem $ld -Filter 'dashboard_*.lock' -EA SilentlyContinue | Remove-Item -Force -EA SilentlyContinue }"

REM Port 8000 freimachen — verhindert Errno 10048 bei Doppelstart
powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match 'uvicorn app:app' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"
timeout /t 2 /nobreak >nul

REM Sync big_ALPHA into dashboard static (always available at /static/big_ALPHA.png)
if exist "%FUSION_BIG_ALPHA_ASSET%" (
  if not exist "static" mkdir static
  copy /Y "%FUSION_BIG_ALPHA_ASSET%" "static\big_ALPHA.png" >nul 2>&1
)

REM Port 8000 = Standard-GUI (templates/index.html) + REST API + WebSocket + frameworks preload
"C:\Users\Admin\venv\Scripts\python.exe" -m uvicorn app:app --host 127.0.0.1 --port 8000 --log-level warning