# Fusion Hero OS - Auto-Load aller Komponenten
param([switch]$Force)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Dash = Join-Path $Root "03_Code\Dashboard"
$Python = "C:\Users\Admin\venv\Scripts\python.exe"
$BackendUrl = "http://127.0.0.1:8000"
$WorkspaceUrl = "http://127.0.0.1:8080"

function Stop-FusionProcesses {
    Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -match 'uvicorn app:app|workspace\.py' } |
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
            $s = Invoke-RestMethod -Uri "$BackendUrl/api/health" -TimeoutSec 3
            $s = $s.mainframe
            if ($s.loaded) { return $s }
        } catch {}
        Start-Sleep -Seconds 1
    }
    return $null
}

Write-Host "=== Fusion Hero OS v1.2 - Auto-Load ===" -ForegroundColor Cyan
if ($Force) {
    $env:FUSION_FORCE_SYNC = "1"
    $env:FUSION_AUTO_LOAD = "0"
    Write-Host "Modus: FORCE (Full-Boot · Medienserver-Sync)" -ForegroundColor Magenta
}
Write-Host "Substrat: Windows | Meta-Layer: Fusion Hero OS v1.2" -ForegroundColor DarkCyan
& (Join-Path $Root "sync_grok_intern.ps1")
if ((Test-Path "G:\Meine Ablage") -and ($env:FUSION_SKIP_SYNC -ne "1")) {
    # Skip teure Syncs bei GPU-heavy Runs um Netzwerk/Drive Bottleneck zu vermeiden
    & (Join-Path $Root "sync_medienserver.ps1")
} else {
    Write-Host "SYNC SKIP (FUSION_SKIP_SYNC=1 oder kein Drive)"
}
Stop-FusionProcesses
Start-Sleep -Seconds 1

Start-Process -FilePath (Join-Path $Root "run_backend.bat") -WorkingDirectory $Root -WindowStyle Minimized

Write-Host "[1/4] Backend starten..." -NoNewline
if (-not (Wait-HttpReady "$BackendUrl/api/health?light=true")) {
    Write-Host " FEHLER" -ForegroundColor Red
    exit 1
}
Write-Host " OK" -ForegroundColor Green

Write-Host "[2/4] AutoLoader Treiber+Prozesse..." -NoNewline
try {
    if ($Force) {
        $alBody = '{"phase":"full","force":true,"sync":true,"attach_meta":true}'
        $alTimeout = 300
    } else {
        $alBody = '{"phase":"staged","attach_meta":true}'
        $alTimeout = 90
    }
    $al = Invoke-RestMethod -Uri "$BackendUrl/api/autoload/run" -Method POST `
        -Body $alBody -ContentType "application/json" -TimeoutSec $alTimeout
    $sum = $al.summary
    $ready = if ($sum.drivers_ready) { $sum.drivers_ready } else { $sum.drivers_loaded }
    Write-Host " OK (Treiber $ready/$($sum.drivers_total), geladen $($sum.drivers_loaded))" -ForegroundColor Green
} catch {
    Write-Host " FALLBACK" -ForegroundColor Yellow
}

Write-Host "[3/4] Mainframe-Status..." -NoNewline
$mf = Wait-MainframeLoaded
if ($mf) {
    Write-Host " OK ($($mf.version))" -ForegroundColor Green
} else {
    Write-Host " TIMEOUT" -ForegroundColor Yellow
}

Write-Host "[Profil] Fusion-Leistung 2/3 (ohne Windows)..." -NoNewline
try {
    $pr = Invoke-RestMethod -Uri "$BackendUrl/api/performance/set" -Method POST -Body '{"ratio":0.667}' -ContentType "application/json" -TimeoutSec 8
    Write-Host " OK ($($pr.fusion.active))" -ForegroundColor Green
} catch {
    Write-Host " WARTE" -ForegroundColor Yellow
}

Write-Host "[Meta] Windows-Substrat + Meta-Layer attach..." -NoNewline
try {
    $ml = Invoke-RestMethod -Uri "$BackendUrl/api/meta-layer/attach" -Method POST -TimeoutSec 10
    $hostName = $ml.substrate.hostname
    Write-Host " OK ($hostName)" -ForegroundColor Green
} catch {
    Write-Host " WARTE" -ForegroundColor Yellow
}

Write-Host "[Substrat] Windows-Substrat-Tuning..." -NoNewline
try {
    $st = Invoke-RestMethod -Uri "$BackendUrl/api/windows/substrate/tune" -Method POST -TimeoutSec 20
    $pwr = $st.scan.power_plan.name
    Write-Host " OK ($pwr · $($st.applied_count) Aktionen)" -ForegroundColor Green
} catch {
    Write-Host " FALLBACK" -ForegroundColor Yellow
}

Write-Host "[Cyber] Cyber Layer aktivieren..." -NoNewline
try {
    $cy = Invoke-RestMethod -Uri "$BackendUrl/api/windows/cyber-layer/activate" -Method POST -TimeoutSec 12
    $badge = $cy.visual.badge
    Write-Host " OK ($badge · Score $($cy.optimization_score))" -ForegroundColor Green
} catch {
    Write-Host " FALLBACK" -ForegroundColor Yellow
}

Start-Process -FilePath (Join-Path $Root "run_workspace.bat") -WorkingDirectory $Root -WindowStyle Minimized
Write-Host "[4/4] Workspace starten..." -NoNewline
if (Wait-HttpReady $WorkspaceUrl) {
    Write-Host " OK" -ForegroundColor Green
} else {
    Write-Host " FEHLER" -ForegroundColor Red
    exit 1
}

Start-Process $WorkspaceUrl
Write-Host ""
Write-Host "Bereit:" -ForegroundColor Cyan
Write-Host "  Workspace: $WorkspaceUrl  (gui/ + workspace.py)"
Write-Host "  GUI API:   $BackendUrl/api/gui/status"
Write-Host "  AutoLoad:  $BackendUrl/api/autoload/status"
Write-Host "  Backend:   $BackendUrl"
Write-Host ('  Mainframe: ' + $BackendUrl + '/api/mainframe/status')
