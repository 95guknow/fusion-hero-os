# Sync Fusion Hero OS v1.2 zum Medienserver (Google Drive G:)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Target = "G:\Meine Ablage\Fusion_Hero_OS_v1.2"
$Exclude = @(".git", "__pycache__", "venv", "node_modules", "logs", ".pytest_cache")

Write-Host "=== Fusion Hero OS v1.2 -> Medienserver (Google Drive) ===" -ForegroundColor Cyan

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

if (-not (Test-Path "G:\Meine Ablage")) {
    Write-Host "Google Drive (G:) nicht verfuegbar." -ForegroundColor Red
    exit 1
}

New-Item -ItemType Directory -Force -Path $Target | Out-Null

# Optimiert für Netzwerk/Drive Bottleneck + Storage: Delta-only (/XO), /FFT for skew, /J unbuf, higher MT for parallel net I/O
$RoboOpts = "/E /XO /XD $Exclude /NFL /NDL /NJH /NJS /nc /ns /np /MT:12 /R:0 /W:0 /FFT /J /DCOPY:DA"
robocopy $Root $Target $RoboOpts | Out-Null
if ($LASTEXITCODE -ge 8) {
    Write-Host "Robocopy Fehler: $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}

$manifest = @{
    version = "v1.2"
    core = "v7.5"
    synced_at = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
    github = "https://github.com/95guknow/fusion-hero-os"
    grok_online = @{
        repo = "95guknow/fusion-hero-os"
        branch = "main"
        health_local = "http://127.0.0.1:8000/api/health"
        workspace_local = "http://127.0.0.1:8080"
    }
    medienserver_path = $Target
} | ConvertTo-Json -Depth 4

Set-Content -Path (Join-Path $Target "GROK_ONLINE_MANIFEST.json") -Value $manifest -Encoding UTF8

Write-Host "OK: $Target" -ForegroundColor Green
Write-Host "Grok online: https://github.com/95guknow/fusion-hero-os" -ForegroundColor Cyan