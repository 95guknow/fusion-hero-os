#Requires -Version 5.1
<#
.SYNOPSIS
  Inject BIG ALPHA + Meister Hasch into Windows user-mode substrate (NOT ring-0).

.DESCRIPTION
  Not a Windows kernel driver / rootkit. Wires Fusion Hero OS Alpha into:
  - User environment variables
  - ~/.fusion alpha + meister pins
  - Startup folder launcher
  - Scheduled Task AtLogOn (Limited)
  - Immediate eudaemon pulse

  Ring-0 requires WDK + signed drivers - out of scope.
#>
param(
    [switch]$NoTask,
    [switch]$NoStartup,
    [switch]$NoEnv
)

$ErrorActionPreference = "Continue"
$Root = "C:\Users\Admin\fusion-hero-os"
if (-not (Test-Path (Join-Path $Root "VERSION"))) {
    $Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
}

$FusionDir = Join-Path $env:USERPROFILE ".fusion"
$LogDir = Join-Path $FusionDir "logs"
$StatePath = Join-Path $FusionDir "windows_alpha_inject.json"
$AlphaLauncher = Join-Path $FusionDir "run_alpha_eudaemon.cmd"
$TaskName = "FusionHeroOS-AlphaEudaemon"
$Python = "python"
if (Test-Path "C:\Users\Admin\venv\Scripts\python.exe") {
    $Python = "C:\Users\Admin\venv\Scripts\python.exe"
}

$PromptSrc = $null
foreach ($c in @("C:\prompt.txt", (Join-Path $Root "prompt.txt"))) {
    if (Test-Path $c) { $PromptSrc = $c; break }
}
$AlphaMd = $null
foreach ($c in @("C:\alpha_meister_hasch.md", (Join-Path $Root "docs\dissertation\ALPHA_MEISTER_HASCH.md"))) {
    if (Test-Path $c) { $AlphaMd = $c; break }
}
$MeisterPng = "C:\Dissertation_95guknow\meister_hasch.png"
$MeisterSha = "a032b31b3f7025852528d3ce5e6f64c163345a7b50632d5447cb751213d5f81e"

New-Item -ItemType Directory -Force -Path $FusionDir, $LogDir | Out-Null

Write-Host "=== WINDOWS SUBSTRATE INJECT (user-mode, BIG ALPHA) ===" -ForegroundColor Cyan
Write-Host "NOT ring-0 kernel. User session + Autoload surface only." -ForegroundColor Yellow
Write-Host "Root: $Root"

Write-Host "[1] Pin Alpha / Meister into .fusion ..." -ForegroundColor Yellow
if ($PromptSrc) {
    Copy-Item -Force $PromptSrc (Join-Path $FusionDir "prompt.txt")
    Write-Host "  prompt pinned" -ForegroundColor Green
}
if ($AlphaMd) {
    Copy-Item -Force $AlphaMd (Join-Path $FusionDir "alpha_meister_hasch.md")
    Write-Host "  alpha_meister_hasch.md pinned" -ForegroundColor Green
}
$sealSrc = Join-Path $Root "docs\dissertation\alpha_meister_hasch.seal.json"
if (Test-Path $sealSrc) {
    Copy-Item -Force $sealSrc (Join-Path $FusionDir "alpha_meister_hasch.seal.json")
}

$pinPath = Join-Path $FusionDir "alpha_pin.json"
$pinObj = [ordered]@{
    kind             = "windows_alpha_inject"
    mode             = "user_mode_substrate"
    ring0            = $false
    BIG_OMEGA        = "REACHED"
    BIG_ALPHA        = "OPEN"
    platform_version = "12.0.0"
    meister_sha256   = $MeisterSha
    meister_png      = $MeisterPng
    repo_root        = $Root
    entry_line       = "BIG OMEGA sealed. BIG ALPHA open. MasterSeed fixed. Labor only. Build."
    bounds           = @{
        offense      = "FORBIDDEN"
        sandbox_only = $true
        ring0_inject = $false
    }
    injected_at      = (Get-Date).ToUniversalTime().ToString("o")
    hostname         = $env:COMPUTERNAME
}
$utf8 = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($pinPath, ($pinObj | ConvertTo-Json -Depth 6), $utf8)
Write-Host "  alpha_pin.json written" -ForegroundColor Green

if (-not $NoEnv) {
    Write-Host "[2] User environment variables..." -ForegroundColor Yellow
    [Environment]::SetEnvironmentVariable("FUSION_REPO_ROOT", $Root, "User")
    [Environment]::SetEnvironmentVariable("FUSION_PLATFORM_VERSION", "12.0.0", "User")
    [Environment]::SetEnvironmentVariable("FUSION_AUTO_LOAD", "1", "User")
    [Environment]::SetEnvironmentVariable("FUSION_CYCLE", "BIG_ALPHA", "User")
    [Environment]::SetEnvironmentVariable("FUSION_MEISTER_SHA256", $MeisterSha, "User")
    [Environment]::SetEnvironmentVariable("FUSION_ALPHA_PIN", $pinPath, "User")
    $env:FUSION_REPO_ROOT = $Root
    $env:FUSION_PLATFORM_VERSION = "12.0.0"
    $env:FUSION_AUTO_LOAD = "1"
    $env:FUSION_CYCLE = "BIG_ALPHA"
    Write-Host "  FUSION_CYCLE=BIG_ALPHA (User)" -ForegroundColor Green
} else {
    Write-Host "[2] Env skipped" -ForegroundColor DarkGray
}

$logPath = Join-Path $LogDir "alpha_eudaemon.log"
$cmdLines = @(
    "@echo off"
    "REM Fusion Hero OS Alpha substrate - user-mode NOT ring-0"
    "set FUSION_REPO_ROOT=$Root"
    "set FUSION_PLATFORM_VERSION=12.0.0"
    "set FUSION_AUTO_LOAD=1"
    "set FUSION_CYCLE=BIG_ALPHA"
    "set FUSION_MEISTER_SHA256=$MeisterSha"
    "set PYTHONPATH=$Root"
    "cd /d `"$Root`""
    "timeout /t 35 /nobreak >nul"
    "`"$Python`" -m fusion_hero_os.core.eudaemon_agent >> `"$logPath`" 2>&1"
    "`"$Python`" -m fusion_hero_os.core.autoload_controller --status >> `"$logPath`" 2>&1"
)
Set-Content -Path $AlphaLauncher -Value ($cmdLines -join "`r`n") -Encoding ASCII
Write-Host "[3] Launcher: $AlphaLauncher" -ForegroundColor Green

if (-not $NoStartup) {
    $startup = [Environment]::GetFolderPath("Startup")
    $startupCmd = Join-Path $startup "FusionHeroOS-AlphaEudaemon.cmd"
    Copy-Item -Force $AlphaLauncher $startupCmd
    Write-Host "[4] Startup: $startupCmd" -ForegroundColor Green
} else {
    Write-Host "[4] Startup skipped" -ForegroundColor DarkGray
}

$taskOk = $false
if (-not $NoTask) {
    Write-Host "[5] Scheduled Task: $TaskName" -ForegroundColor Yellow
    try {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
        $action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$AlphaLauncher`"" -WorkingDirectory $Root
        $trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
        $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 1)
        $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
        Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null
        $taskOk = $true
        Write-Host "  Task registered (AtLogOn, Limited)" -ForegroundColor Green
    } catch {
        Write-Host "  Task failed: $_" -ForegroundColor Yellow
    }
}

Write-Host "[6] Immediate eudaemon pulse..." -ForegroundColor Yellow
Push-Location $Root
$env:PYTHONPATH = $Root
$env:FUSION_REPO_ROOT = $Root
& $Python -m fusion_hero_os.core.eudaemon_agent --no-walk 2>&1 | Out-Host
Pop-Location

$state = [ordered]@{
    ok               = $true
    mode             = "user_mode_substrate"
    ring0            = $false
    BIG_ALPHA        = "INJECTED"
    platform_version = "12.0.0"
    task_name        = $TaskName
    task_ok          = $taskOk
    launcher         = $AlphaLauncher
    alpha_pin        = $pinPath
    meister_sha256   = $MeisterSha
    injected_at      = (Get-Date).ToUniversalTime().ToString("o")
    hostname         = $env:COMPUTERNAME
    note             = "User-mode only. No Windows kernel driver load."
}
[System.IO.File]::WriteAllText($StatePath, ($state | ConvertTo-Json -Depth 6), $utf8)

try {
    & $Python -c "from fusion_hero_os.core.autoload_controller import mark_ready; import json; print(json.dumps(mark_ready(alpha_inject=True, cycle='BIG_ALPHA', ring0=False), indent=2))" 2>&1 | Out-Host
} catch {}

Write-Host ""
Write-Host "=== SUBSTRATE INJECT COMPLETE (user-mode) ===" -ForegroundColor Green
Write-Host "State: $StatePath"
Write-Host "Pin:   $pinPath"
Write-Host "Task:  $TaskName (ok=$taskOk)"
Write-Host "Ring0: false - no kernel driver"
Write-Host "Logon: Alpha eudaemon pulse after ~35s"
exit 0
