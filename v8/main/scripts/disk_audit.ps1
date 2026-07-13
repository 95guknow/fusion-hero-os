param(
    [switch]$PreviewCleanup,
    [string]$ReportPath = ""
)

$ErrorActionPreference = "SilentlyContinue"

function Get-FolderSizeGB {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return $null }
    $sum = (Get-ChildItem $Path -Recurse -File -Force -ErrorAction SilentlyContinue |
        Measure-Object -Property Length -Sum).Sum
    return [math]::Round($sum / 1GB, 2)
}

$targets = [ordered]@{
    Downloads              = Join-Path $env:USERPROFILE "Downloads"
    pip_Cache              = Join-Path $env:LOCALAPPDATA "pip\Cache"
    Temp                   = Join-Path $env:LOCALAPPDATA "Temp"
    Packages               = Join-Path $env:LOCALAPPDATA "Packages"
    npm_cache              = Join-Path $env:LOCALAPPDATA "npm-cache"
    FusionHero             = "C:\FusionHero"
    fusion_hero_os         = "C:\Users\Admin\fusion-hero-os"
    internal_llm           = "C:\Users\Admin\internal_llm"
    venv                   = "C:\Users\Admin\venv"
    stable_diffusion_webui = "C:\Users\Admin\stable-diffusion-webui"
    Gothic2_Download       = Join-Path $env:USERPROFILE "Downloads\8b9180cb668ea42266ed87e32c109122"
    dot_cache              = Join-Path $env:USERPROFILE ".cache"
    dot_rustup             = Join-Path $env:USERPROFILE ".rustup"
    dot_vscode             = Join-Path $env:USERPROFILE ".vscode"
    dot_grok               = Join-Path $env:USERPROFILE ".grok"
}

$lines = @()
$lines += "Fusion Hero OS Disk Audit - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
$freeGb = [math]::Round((Get-PSDrive C).Free / 1GB, 2)
$lines += "C: Free: $freeGb GB"
$lines += ""

foreach ($name in $targets.Keys) {
    $path = $targets[$name]
    if (Test-Path $path) {
        $gb = Get-FolderSizeGB -Path $path
        $lines += ("{0,-24} {1,8:N2} GB  {2}" -f $name, $gb, $path)
    } else {
        $lines += ("{0,-24} {1,8}     {2}" -f $name, "MISSING", $path)
    }
}

$lines += ""
$lines += "--- Git Worktrees ---"
$wt = git -C "C:\Users\Admin\fusion-hero-os" worktree list 2>$null
if ($wt) { $lines += $wt } else { $lines += "(none)" }

if ($PreviewCleanup) {
    $lines += ""
    $lines += "--- Preview Cleanup (no changes) ---"
    $cutoff = (Get-Date).AddDays(-7)
    $oldTemp = Get-ChildItem (Join-Path $env:LOCALAPPDATA "Temp") -File -Force |
        Where-Object { $_.LastWriteTime -lt $cutoff }
    $tempMb = [math]::Round(($oldTemp | Measure-Object Length -Sum).Sum / 1MB, 1)
    $lines += "Temp files older than 7 days: $($oldTemp.Count) ($tempMb MB)"

    $oldExe = Get-ChildItem (Join-Path $env:USERPROFILE "Downloads") -File -Filter "*.exe" |
        Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-90) }
    $exeGb = [math]::Round(($oldExe | Measure-Object Length -Sum).Sum / 1GB, 2)
    $lines += "Downloads .exe older than 90 days: $($oldExe.Count) ($exeGb GB)"

    $parts = Get-ChildItem (Join-Path $env:USERPROFILE "Downloads") -File -Filter "*.part"
    $lines += "Incomplete .part downloads: $($parts.Count)"
}

$text = $lines -join [Environment]::NewLine
Write-Output $text

if (-not $ReportPath) {
    $ReportPath = Join-Path "C:\Users\Admin\fusion-hero-os" "disk_audit_report.txt"
}
$text | Set-Content -Path $ReportPath -Encoding UTF8
Write-Host "Report saved: $ReportPath"