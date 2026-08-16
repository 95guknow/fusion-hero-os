# Install a hourly Windows task that evaluates the Totmannschalter.
# Requires: Python on PATH, fusion-hero-os checkout.

param(
    [string]$RepoRoot = "C:\Users\Admin\fusion-hero-os",
    [switch]$Unregister
)

$ErrorActionPreference = "Stop"
$py = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $py) { throw "python not found on PATH" }

$taskName = "FusionHeroOS-Totmannschalter"
$logDir = Join-Path $env:USERPROFILE ".fusion\totmann"
$envLine = "set PYTHONPATH=$RepoRoot&&"
$mod = "python -m fusion_hero_os.core.totmann_schalter --evaluate"

if ($Unregister) {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "unregistered $taskName"
    exit 0
}

New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$action = New-ScheduledTaskAction `
    -Execute "cmd.exe" `
    -Argument "/c $envLine $mod >> `"$logDir\task_evaluate.log`" 2>&1" `
    -WorkingDirectory $RepoRoot

$nextHour = (Get-Date).Date.AddHours((Get-Date).Hour + 1)
$trigger = New-ScheduledTaskTrigger `
    -Once -At $nextHour `
    -RepetitionInterval (New-TimeSpan -Hours 1) `
    -RepetitionDuration (New-TimeSpan -Days 3650)

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Force | Out-Null
Write-Host "registered $taskName (hourly --evaluate). Logs: $logDir\task_evaluate.log"
