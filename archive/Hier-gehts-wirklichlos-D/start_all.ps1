# Fusion-Hero-OS v8 - Auto-Load aller Komponenten
# Standard-GUI: FastAPI Dashboard auf Port 8000 (templates/index.html + /ws)
# NiceGUI workspace.py (:8080) nur optional via -NiceGUI

param(
    [switch]$Force,
    [switch]$NiceGUI
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

function Wait-HttpReady([string]$Url, [int]$MaxSec = 120) {
    $deadline = (Get-Date).AddSeconds($MaxSec)
    while ((Get-Date) -lt $deadline) {
        try {
            $r = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 2
            if ($r.StatusCode -eq 200) { return $true }
        } catch {}
        Start-Sleep -Milliseconds 500
    }
    return $false
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

Write-Host "=== Fusion Hero OS v8 - Auto-Load ===" -ForegroundColor Cyan
if ($Force) {
    $env:FUSION_FORCE_SYNC = "1"
    $env:FUSION_AUTO_LOAD = "0"
    Write-Host "Modus: FORCE (Full-Boot · Medienserver-Sync)" -ForegroundColor Magenta
}
Write-Host "Substrat: Windows | Meta-Layer: Fusion Hero OS v8" -ForegroundColor DarkCyan
Write-Host "Standard-GUI: $GuiUrl  (FastAPI Dashboard, kein NiceGUI)" -ForegroundColor DarkGray
Write-Host "GitHub:       https://github.com/95guknow/fusion-hero-os (main @ v8)" -ForegroundColor DarkGray

Write-Host "[0] Automatische Faktor-Erkennung..." -NoNewline
try {
    $factors = & $Python -c "
import sys, os, json
sys.path.insert(0, '$Dash')
from app import detect_input_factors, detect_output_factors
i = detect_input_factors()
o = detect_output_factors()
print(json.dumps({'input': i, 'output': o}))
" 2>$null
    if ($factors) {
        Write-Host " OK (Input/Output Faktoren erkannt)" -ForegroundColor Green
    } else {
        Write-Host " (Fallback)" -ForegroundColor Yellow
    }
} catch {
    Write-Host " (nicht verfügbar)" -ForegroundColor Yellow
}

& (Join-Path $Root "sync_grok_intern.ps1")

if ((Test-Path "G:\Meine Ablage") -and ($env:FUSION_SKIP_SYNC -ne "1")) {
    & (Join-Path $Root "sync_medienserver.ps1")
} else {
    Write-Host "SYNC SKIP (FUSION_SKIP_SYNC=1 oder kein Drive)"
}

Stop-FusionProcesses
Start-Sleep -Seconds 1

Start-Process -FilePath (Join-Path $Root "run_backend.bat") -WorkingDirectory $Root -WindowStyle Minimized

Write-Host "[1/3] Dashboard + API starten (:8000)..." -NoNewline
if (-not (Wait-HttpReady "$GuiUrl/api/health?light=true")) {
    Write-Host " FEHLER" -ForegroundColor Red
    exit 1
}
if (-not (Wait-HttpReady $GuiUrl)) {
    Write-Host " FEHLER (GUI /)" -ForegroundColor Red
    exit 1
}
Write-Host " OK" -ForegroundColor Green

Write-Host "[2/3] AutoLoader Treiber+Prozesse..." -NoNewline
try {
    if ($Force) {
        $alBody = '{"phase":"full","force":true,"sync":true,"attach_meta":true}'
        $alTimeout = 300
    } else {
        $alBody = '{"phase":"staged","attach_meta":true}'
        $alTimeout = 90
    }
    $al = Invoke-RestMethod -Uri "$GuiUrl/api/autoload/run" -Method POST `
        -Body $alBody -ContentType "application/json" -TimeoutSec $alTimeout
    $sum = $al.summary
    $ready = if ($sum.drivers_ready) { $sum.drivers_ready } else { $sum.drivers_loaded }
    Write-Host " OK (Treiber $ready/$($sum.drivers_total), geladen $($sum.drivers_loaded))" -ForegroundColor Green
} catch {
    Write-Host " FALLBACK" -ForegroundColor Yellow
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

Write-Host "[Supabase] Projekt swmmoxhdzarmoupyssqe..." -NoNewline
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

Start-Process $GuiUrl
Write-Host ""
Write-Host "Bereit:" -ForegroundColor Cyan
Write-Host "  GUI:       $GuiUrl  (Dashboard templates/index.html + WebSocket /ws)"
Write-Host "  API:       $GuiUrl/api/health"
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