# Sync Fusion Hero OS v8 zum Medienserver (Google Drive)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Exclude = @(".git", "__pycache__", "venv", "node_modules", "logs", ".pytest_cache")

function Resolve-MedienserverTarget {
    if ($env:FUSION_MEDIENSERVER) { return $env:FUSION_MEDIENSERVER }
    $candidates = @(
        "G:\Meine Ablage\Fusion_Hero_OS_v1.2",
        (Join-Path $env:USERPROFILE "Google Drive-Streaming\Meine Ablage\Fusion_Hero_OS_v1.2"),
        (Join-Path $env:USERPROFILE "Google Drive\Meine Ablage\Fusion_Hero_OS_v1.2")
    )
    foreach ($c in $candidates) {
        $parent = Split-Path $c -Parent
        if (Test-Path $parent) { return $c }
    }
    return $null
}

$Target = Resolve-MedienserverTarget
if (-not $Target) {
    Write-Host "Google Drive nicht gefunden (G: oder Google Drive-Streaming)." -ForegroundColor Red
    exit 1
}

Write-Host "=== Fusion Hero OS v8 -> Medienserver (Google Drive) ===" -ForegroundColor Cyan
Write-Host "Ziel: $Target" -ForegroundColor DarkGray

$ManifestPath = Join-Path $Target "GROK_ONLINE_MANIFEST.json"
$MaxAgeMin = if ($env:FUSION_SYNC_MAX_AGE_MIN) { [int]$env:FUSION_SYNC_MAX_AGE_MIN } else { 60 }
if ($env:FUSION_FORCE_SYNC -ne "1" -and (Test-Path $ManifestPath)) {
    try {
        $manifest = Get-Content $ManifestPath -Raw | ConvertFrom-Json
        if ($manifest.synced_at) {
            $synced = [datetime]::ParseExact($manifest.synced_at, "yyyy-MM-dd HH:mm:ss", $null)
            $ageMin = ((Get-Date) - $synced).TotalMinutes
            if ($ageMin -lt $MaxAgeMin) {
                Write-Host "SKIP: Sync aktuell ($($manifest.synced_at), ${ageMin}min)" -ForegroundColor Yellow
                exit 0
            }
        }
    } catch {}
}

New-Item -ItemType Directory -Force -Path $Target | Out-Null

# Delta-only (/XO), /FFT for Drive skew, parallel I/O
& robocopy $Root $Target /E /XO /XD $Exclude /NFL /NDL /NJH /NJS /nc /ns /np /MT:8 /R:1 /W:1 /FFT /J /DCOPY:DA | Out-Null
$rc = $LASTEXITCODE
if ($rc -ge 8) {
    Write-Host "Robocopy Fehler: $rc" -ForegroundColor Red
    exit $rc
}

$gitHead = "unknown"
try {
    Push-Location $Root
    $gitHead = (git rev-parse --short HEAD 2>$null)
    Pop-Location
} catch { Pop-Location -ErrorAction SilentlyContinue }

$manifest = @{
    version = "v8"
    core = "v8"
    github_head = $gitHead
    synced_at = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
    file_sync_status = "OK"
    github = "https://github.com/95guknow/fusion-hero-os"
    grok_online = @{
        repo = "95guknow/fusion-hero-os"
        branch = "main"
        health_local = "http://127.0.0.1:8000/api/health"
        gui_local = "http://127.0.0.1:8000"
        nicegui_legacy = "http://127.0.0.1:8080"
    }
    medienserver_path = $Target
} | ConvertTo-Json -Depth 4

$manifestPath = Join-Path $Target "GROK_ONLINE_MANIFEST.json"
[System.IO.File]::WriteAllText($manifestPath, $manifest, [System.Text.UTF8Encoding]::new($false))

Write-Host "OK: $Target" -ForegroundColor Green
Write-Host "Grok online: https://github.com/95guknow/fusion-hero-os" -ForegroundColor Cyan