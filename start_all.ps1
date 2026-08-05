# Fusion-Hero-OS v8 - Auto-Load aller Komponenten
# Standard-GUI: FastAPI Dashboard auf Port 8000 (templates/index.html + /ws)
# NiceGUI workspace.py (:8080) nur optional via -NiceGUI

param(
    [switch]$Force,
    [switch]$NiceGUI,
    [switch]$NoGui
)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Dash = Join-Path $Root "03_Code\Dashboard"
$Python = "C:\Users\Admin\venv\Scripts\python.exe"
$GuiUrl = "http://127.0.0.1:8000"
$LegacyNiceGuiUrl = "http://127.0.0.1:8080"

function Stop-FusionProcesses {
    Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -match 'uvicorn app:app|workspace\.py|rest_api_server' } |
        ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
}

function Wait-HttpReady([string]$Url, [int]$MaxSec = 180) {
    $deadline = (Get-Date).AddSeconds($MaxSec)
    while ((Get-Date) -lt $deadline) {
        try {
            $r = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 3
            if ($r.StatusCode -eq 200) { return $true }
        } catch {}
        Start-Sleep -Milliseconds 500
    }
    return $false
}

function Clear-DashboardLocks {
    $ld = Join-Path $env:USERPROFILE ".fusion-hero-os\process_locks"
    if (Test-Path $ld) {
        Get-ChildItem $ld -Filter "dashboard_*.lock" -ErrorAction SilentlyContinue |
            Remove-Item -Force -ErrorAction SilentlyContinue
    }
}

function Sync-BigAlphaAsset {
    $src = $env:FUSION_BIG_ALPHA_ASSET
    if (-not $src -or -not (Test-Path $src)) {
        $candidates = @(
            "C:\Dissertation_95guknow\assets\big_ALPHA.png",
            (Join-Path $Root "ascension_os\assets\big_ALPHA.png")
        )
        foreach ($c in $candidates) {
            if (Test-Path $c) { $src = $c; break }
        }
    }
    if (-not $src -or -not (Test-Path $src)) {
        Write-Host "BIG ALPHA asset missing" -ForegroundColor Yellow
        return $null
    }
    $staticDir = Join-Path $Dash "static"
    New-Item -ItemType Directory -Force -Path $staticDir | Out-Null
    $dst = Join-Path $staticDir "big_ALPHA.png"
    Copy-Item -LiteralPath $src -Destination $dst -Force
    $env:FUSION_BIG_ALPHA_ASSET = $src
    Write-Host "BIG ALPHA -> $dst" -ForegroundColor Green
    return $dst
}

function Wait-MainframeLoaded([int]$MaxSec = 120) {
    $deadline = (Get-Date).AddSeconds($MaxSec)
    while ((Get-Date) -lt $deadline) {
        try {
            $s = Invoke-RestMethod -Uri "$GuiUrl/api/health" -TimeoutSec 3
            $s = $s.mainframe
            if ($s.loaded) { return $s }
        } catch {}
        Start-Sleep -Seconds 1
    }
    return $null
}

Write-Host "=== Fusion Hero OS v13 - Auto-Load ALL (Frameworks+Module+Mesh+Dashboard) ===" -ForegroundColor Cyan
# Default: alles beim Start laden (User-Direktive) — Frameworks immer, Dashboard :8000
$env:FUSION_AUTO_LOAD = "1"
$env:FUSION_PRELOAD_ALL = "1"
$env:FUSION_ALL_MODULES = "1"
$env:FUSION_BOOT_PHASE = "full"
$env:FUSION_DUAL_AGENT = if ($env:FUSION_DUAL_AGENT) { $env:FUSION_DUAL_AGENT } else { "1" }
$env:FUSION_QUANTIZER_AGENT = if ($env:FUSION_QUANTIZER_AGENT) { $env:FUSION_QUANTIZER_AGENT } else { "1" }
$env:FUSION_BACKEND_PORT = "8000"
$env:FUSION_DASHBOARD_PORT = "8000"
$env:FUSION_PORT_BASE = "8000"
$env:PORT = "8000"
$env:FUSION_MEMORY_SPILL = if ($env:FUSION_MEMORY_SPILL) { $env:FUSION_MEMORY_SPILL } else { "1" }
# GDrive spill env (optional)
$spillEnv = Join-Path $env:USERPROFILE ".fusion\gdrive_spill.env"
if (Test-Path $spillEnv) {
    Get-Content $spillEnv | ForEach-Object {
        if ($_ -match '^\s*#' -or $_ -notmatch '=') { return }
        $k, $v = $_.Split('=', 2)
        if ($k) { Set-Item -Path "Env:$($k.Trim())" -Value $v.Trim() }
    }
}
if (-not $env:FUSION_SSD_LONGTERM_CACHE) {
    $env:FUSION_SSD_LONGTERM_CACHE = "G:\Meine Ablage\FusionHero_Offload\LongTermCache"
}
# BIG ALPHA asset
$env:FUSION_BIG_ALPHA_ASSET = if ($env:FUSION_BIG_ALPHA_ASSET) {
    $env:FUSION_BIG_ALPHA_ASSET
} else {
    "C:\Dissertation_95guknow\assets\big_ALPHA.png"
}
if ($Force) {
    $env:FUSION_FORCE_SYNC = "1"
    $env:FUSION_AUTO_LOAD = "1"
    $env:FUSION_BOOT_PHASE = "full"
    Write-Host "Modus: FORCE (Full-Boot · Preload ALL · Medienserver-Sync)" -ForegroundColor Magenta
}
Write-Host "Substrat: Windows | Meta-Layer: Fusion Hero OS v13" -ForegroundColor DarkCyan
Write-Host "Standard-GUI: $GuiUrl  (FastAPI Dashboard · frameworks always on)" -ForegroundColor DarkGray
Write-Host "BIG ALPHA:    $($env:FUSION_BIG_ALPHA_ASSET)" -ForegroundColor DarkGray
Write-Host "GitHub:       https://github.com/95guknow/fusion-hero-os (main @ v13)" -ForegroundColor DarkGray

Write-Host "[0] Automatische Faktor-Erkennung..." -NoNewline
try {
    $factorPy = @'
import sys, json
from pathlib import Path
sys.path.insert(0, r"""__DASH__""")
from app import detect_input_factors, detect_output_factors
print(json.dumps({"input": detect_input_factors(), "output": detect_output_factors()}))
'@
    $factorPy = $factorPy.Replace("__DASH__", $Dash.Replace("\", "/"))
    $factors = & $Python -c $factorPy 2>$null
    if ($factors) {
        Write-Host " OK (Input/Output Faktoren erkannt)" -ForegroundColor Green
    } else {
        Write-Host " (Fallback)" -ForegroundColor Yellow
    }
} catch {
    Write-Host " (nicht verfuegbar)" -ForegroundColor Yellow
}

& (Join-Path $Root "sync_grok_intern.ps1")

# Medienserver: non-fatal (Drive ENOSPC must not block dashboard)
if ((Test-Path "G:\Meine Ablage") -and ($env:FUSION_SKIP_SYNC -ne "1")) {
    try {
        & (Join-Path $Root "sync_medienserver.ps1")
    } catch {
        Write-Host "Medienserver-Sync note (non-fatal): $_" -ForegroundColor Yellow
    }
} else {
    Write-Host "SYNC SKIP (FUSION_SKIP_SYNC=1 oder kein Drive)"
}

Write-Host "[0b] BIG ALPHA + locks..." -NoNewline
Sync-BigAlphaAsset | Out-Null
Clear-DashboardLocks
Write-Host " OK" -ForegroundColor Green

Stop-FusionProcesses
Start-Sleep -Seconds 1

Start-Process -FilePath (Join-Path $Root "run_backend.bat") -WorkingDirectory $Root -WindowStyle Minimized

Write-Host "[1/3] Dashboard + API starten (:8000)..." -NoNewline
# Full boot with frameworks can take >2 min; light health is enough to open GUI
if (-not (Wait-HttpReady -Url "$GuiUrl/api/health?light=true" -MaxSec 180)) {
    Write-Host " FEHLER - retry once after lock clear" -ForegroundColor Red
    Clear-DashboardLocks
    Stop-FusionProcesses
    Start-Sleep -Seconds 2
    Start-Process -FilePath (Join-Path $Root "run_backend.bat") -WorkingDirectory $Root -WindowStyle Minimized
    if (-not (Wait-HttpReady -Url "$GuiUrl/api/health?light=true" -MaxSec 120)) {
        Write-Host " FEHLER (Dashboard nicht erreichbar)" -ForegroundColor Red
        exit 1
    }
}
if (-not $NoGui) {
    if (-not (Wait-HttpReady $GuiUrl)) {
        Write-Host " FEHLER (GUI /)" -ForegroundColor Red
        exit 1
    }
}
Write-Host " OK" -ForegroundColor Green

Write-Host "[2/3] Universal Preload + AutoLoader (ALL frameworks)..." -NoNewline
try {
    # Explizit: alle Connectoren/Module/Frameworks vor API-Call
    # (single-quoted here-string: avoid PowerShell \U unicode in C:\Users)
    $preloadPy = @'
import sys
from pathlib import Path
root = Path(r"""__ROOT__""")
sys.path[:0] = [str(root), str(root / "03_Code"), str(root / "03_Code" / "core")]
from universal_startup_preload import preload_all
r = preload_all(force=True)
print(r.get("steps_ok"), r.get("steps_total"), r.get("ok"))
'@
    $preloadPy = $preloadPy.Replace("__ROOT__", $Root.Replace("\", "/"))
    & $Python -c $preloadPy 2>$null
    $alBody = '{"phase":"full","force":true,"sync":true,"attach_meta":true}'
    $alTimeout = 300
    $al = Invoke-RestMethod -Uri "$GuiUrl/api/autoload/run" -Method POST `
        -Body $alBody -ContentType "application/json" -TimeoutSec $alTimeout
    $sum = $al.summary
    $ready = if ($sum.drivers_ready) { $sum.drivers_ready } else { $sum.drivers_loaded }
    Write-Host " OK (Treiber $ready/$($sum.drivers_total), geladen $($sum.drivers_loaded), phase=full)" -ForegroundColor Green
} catch {
    Write-Host " FALLBACK (preload local only)" -ForegroundColor Yellow
    try {
        $preloadPy2 = @'
import sys
from pathlib import Path
root = Path(r"""__ROOT__""")
sys.path[:0] = [str(root / "03_Code" / "core"), str(root / "03_Code")]
from universal_startup_preload import preload_all
print(preload_all(force=True).get("ok"))
'@
        $preloadPy2 = $preloadPy2.Replace("__ROOT__", $Root.Replace("\", "/"))
        & $Python -c $preloadPy2
    } catch {}
}

Write-Host "[3/3] Mainframe-Status..." -NoNewline
$mf = Wait-MainframeLoaded
if ($mf) {
    Write-Host " OK ($($mf.version))" -ForegroundColor Green
} else {
    Write-Host " TIMEOUT" -ForegroundColor Yellow
}

Write-Host "[CPU] Adaptives Tuning (Last+Temp)..." -NoNewline
try {
    $ct = Invoke-RestMethod -Uri "$GuiUrl/api/cpu/tuner/run" -Method POST -TimeoutSec 10
    $cpu = $ct.cpu
    Write-Host " OK ($($ct.action) | Last=$($cpu.load_pct)% Temp=$($cpu.temp_c)C)" -ForegroundColor Green
} catch {
    Write-Host " FALLBACK" -ForegroundColor Yellow
}

Write-Host "[Supabase] Projekt YOUR_SUPABASE_PROJECT_REF..." -NoNewline
try {
    $sb = Invoke-RestMethod -Uri "$GuiUrl/api/supabase/health?probe=true" -TimeoutSec 10
    if ($sb.probe.key_accepted) {
        Write-Host " OK (verbunden, $($sb.probe.latency_ms)ms)" -ForegroundColor Green
    } elseif ($sb.configured) {
        Write-Host " OK (konfiguriert)" -ForegroundColor Green
    } else {
        Write-Host " NICHT KONFIGURIERT" -ForegroundColor Yellow
    }
} catch {
    Write-Host " FALLBACK" -ForegroundColor Yellow
}

Write-Host "[GPU] Compute-Booster (SM-Auslastung)..." -NoNewline
try {
    $gb = Invoke-RestMethod -Uri "$GuiUrl/api/gpu/compute/boost" -Method POST -TimeoutSec 30
    Write-Host " OK ($($gb.action) | SM=$($gb.compute_util_pct)% -> Ziel $($gb.target_compute_pct)%)" -ForegroundColor Green
} catch {
    Write-Host " FALLBACK" -ForegroundColor Yellow
}

Write-Host "[Module] Alle Funktionen freigeben..." -NoNewline
try {
    $la = Invoke-RestMethod -Uri "$GuiUrl/api/load-all?force=true" -Method POST -TimeoutSec 90
    Write-Host " OK ($($la.count)/$($la.total) Module)" -ForegroundColor Green
} catch {
    Write-Host " FALLBACK" -ForegroundColor Yellow
}

Write-Host "[Coupler] CPU+GPU+SSD gekoppelt..." -NoNewline
try {
    $rc = Invoke-RestMethod -Uri "$GuiUrl/api/resource/coupler/run" -Method POST -TimeoutSec 15
    $ram = $rc.memory.system_ram.util_pct
    $vram = $rc.memory.dedicated_vram.util_pct
    Write-Host " OK ($($rc.action) | RAM=$ram% VRAM=$vram%)" -ForegroundColor Green
} catch {
    Write-Host " FALLBACK" -ForegroundColor Yellow
}

Write-Host "[Meta] Windows-Substrat + Meta-Layer attach..." -NoNewline
try {
    $ml = Invoke-RestMethod -Uri "$GuiUrl/api/meta-layer/attach" -Method POST -TimeoutSec 10
    $hostName = $ml.substrate.hostname
    Write-Host " OK ($hostName)" -ForegroundColor Green
} catch {
    Write-Host " WARTE" -ForegroundColor Yellow
}

Write-Host "[Substrat] Windows-Substrat-Tuning..." -NoNewline
try {
    $st = Invoke-RestMethod -Uri "$GuiUrl/api/windows/substrate/tune" -Method POST -TimeoutSec 20
    $pwr = $st.scan.power_plan.name
    Write-Host " OK ($pwr · $($st.applied_count) Aktionen)" -ForegroundColor Green
} catch {
    Write-Host " FALLBACK" -ForegroundColor Yellow
}

Write-Host "[Cyber] Cyber Layer aktivieren..." -NoNewline
try {
    $cy = Invoke-RestMethod -Uri "$GuiUrl/api/windows/cyber-layer/activate" -Method POST -TimeoutSec 12
    $badge = $cy.visual.badge
    Write-Host " OK ($badge · Score $($cy.optimization_score))" -ForegroundColor Green
} catch {
    Write-Host " FALLBACK" -ForegroundColor Yellow
}

if ($NiceGUI) {
    Write-Host "[Optional] NiceGUI Legacy-Workspace (:8080)..." -NoNewline
    Start-Process -FilePath (Join-Path $Root "run_workspace.bat") -WorkingDirectory $Root -WindowStyle Minimized
    if (Wait-HttpReady $LegacyNiceGuiUrl) {
        Write-Host " OK" -ForegroundColor Green
    } else {
        Write-Host " FEHLER" -ForegroundColor Yellow
    }
}

if (-not $NoGui) {
    Start-Process $GuiUrl
}
Write-Host ""
Write-Host "Bereit:" -ForegroundColor Cyan
if ($NoGui) {
    Write-Host "  Modus:     Core only (kein Browser, kein GUI-Wait)" -ForegroundColor DarkGray
    Write-Host "  API:       $GuiUrl/api/health"
} else {
    Write-Host "  GUI:       $GuiUrl  (Dashboard templates/index.html + WebSocket /ws)"
    Write-Host "  API:       $GuiUrl/api/health"
}
Write-Host "  AutoLoad:  $GuiUrl/api/autoload/status"
Write-Host "  API Docs:  $GuiUrl/docs"
if ($NiceGUI) {
    Write-Host "  Legacy:    $LegacyNiceGuiUrl  (NiceGUI workspace.py, optional)"
}

Write-Host "[Auto-Save] Starte automatisches Speichern aller Neuerungen..." -NoNewline
try {
    $autoSave = Join-Path $Root "auto_save.ps1"
    if (Test-Path $autoSave) {
        Start-Process -FilePath "powershell" -ArgumentList "-ExecutionPolicy Bypass -File `"$autoSave`"" `
            -WorkingDirectory $Root -WindowStyle Minimized -ErrorAction SilentlyContinue
        Write-Host " OK (Loop)" -ForegroundColor Green
    } else {
        Write-Host " (Script fehlt)" -ForegroundColor Yellow
    }
} catch {
    Write-Host " (Fehler)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Zum finalen Push:  powershell -File end_session.ps1" -ForegroundColor DarkCyan
Write-Host "NiceGUI nur bei Bedarf:  start_all.ps1 -NiceGUI" -ForegroundColor DarkGray
Write-Host "Nur Backend/Core:        workstation\start_core.ps1  oder  start_all.ps1 -NoGui" -ForegroundColor DarkGray