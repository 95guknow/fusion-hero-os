# Fusion Hero OS — Phase 3 Storage Cleanup (safe, regenerable caches)
param(
    [switch]$Execute
)

$ErrorActionPreference = "Continue"
$mode = if ($Execute) { "--execute" } else { "--dry-run" }

Write-Host "=== Phase 3 Cleanup ($mode) ===" -ForegroundColor Cyan
$before = [math]::Round((Get-PSDrive C).Free / 1GB, 2)
Write-Host "C: Free before: $before GB"

$py = "C:\Users\Admin\AppData\Local\Programs\Python\Python310\python.exe"
$cleanup = "C:\Users\Admin\fusion-hero-os\03_Code\tools\core_disk_cleanup.py"
& $py $cleanup $mode

if ($Execute) {
    Write-Host "Purging pip cache..."
    & $py -m pip cache purge 2>$null
    if (Get-Command npm -ErrorAction SilentlyContinue) {
        npm cache clean --force 2>$null
    }
}

$after = [math]::Round((Get-PSDrive C).Free / 1GB, 2)
Write-Host "C: Free after:  $after GB (delta: $([math]::Round($after - $before, 2)) GB)" -ForegroundColor Green

if (-not $Execute) {
    Write-Host "Dry-run only. Re-run with -Execute to apply." -ForegroundColor Yellow
}