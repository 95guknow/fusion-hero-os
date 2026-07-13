# Fusion Hero OS — alle Funktionen und Module freigeben
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$GuiUrl = "http://127.0.0.1:8000"

$env:FUSION_ALL_MODULES = "1"
$env:FUSION_LLM_BACKEND = "llama-local"
$env:FUSION_SUPABASE_SYNC = "1"
$env:FUSION_RESOURCE_COUPLER_AUTO = "1"
$env:FUSION_GPU_COMPUTE_BOOSTER_AUTO = "1"
$env:FUSION_GPU_ALLOCATOR_AUTO = "1"
$env:FUSION_CPU_TUNER_AUTO = "1"
$env:FUSION_HYPERTHREADING = "1"
$env:FUSION_PROFILE = "admin"
$env:FUSION_PERFORMANCE_RATIO = "1.0"

function Invoke-Fusion([string]$Method, [string]$Path, $Body = $null) {
    $uri = "$GuiUrl$Path"
    if ($Body) {
        return Invoke-RestMethod -Uri $uri -Method $Method -Body ($Body | ConvertTo-Json) -ContentType "application/json" -TimeoutSec 60
    }
    return Invoke-RestMethod -Uri $uri -Method $Method -TimeoutSec 60
}

Write-Host "=== Fusion Hero OS — Alle Module freigeben ===" -ForegroundColor Cyan

Write-Host "[1] Load-All..." -NoNewline
try {
    $la = Invoke-Fusion POST "/api/load-all?force=true"
    Write-Host " OK ($($la.count)/$($la.total))" -ForegroundColor Green
} catch { Write-Host " FALLBACK" -ForegroundColor Yellow }

Write-Host "[2] Mainframe..." -NoNewline
try {
    Invoke-Fusion POST "/api/mainframe/load" | Out-Null
    Write-Host " OK" -ForegroundColor Green
} catch { Write-Host " FALLBACK" -ForegroundColor Yellow }

Write-Host "[3] Meta-Layer + Cyber..." -NoNewline
try {
    Invoke-Fusion POST "/api/meta-layer/attach" | Out-Null
    Invoke-Fusion POST "/api/windows/substrate/tune" | Out-Null
    Invoke-Fusion POST "/api/windows/cyber-layer/activate" | Out-Null
    Write-Host " OK" -ForegroundColor Green
} catch { Write-Host " FALLBACK" -ForegroundColor Yellow }

Write-Host "[4] Profil admin..." -NoNewline
try {
    Invoke-Fusion POST "/api/profile/set" @{ name = "admin" } | Out-Null
    Write-Host " OK" -ForegroundColor Green
} catch { Write-Host " FALLBACK" -ForegroundColor Yellow }

Write-Host "[5] Module-Liste..." -NoNewline
try {
    $mods = Invoke-Fusion GET "/api/modules"
    $loaded = ($mods.modules | Where-Object { $_.loaded }).Count
    Write-Host " OK ($loaded/$($mods.modules.Count) geladen)" -ForegroundColor Green
} catch { Write-Host " FALLBACK" -ForegroundColor Yellow }

Write-Host ""
Write-Host "Bereit: $GuiUrl/api/modules" -ForegroundColor Cyan
Write-Host "         $GuiUrl/docs" -ForegroundColor DarkGray