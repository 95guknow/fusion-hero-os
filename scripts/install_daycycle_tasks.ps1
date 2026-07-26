# Install Windows Scheduled Tasks for Daycycle v12.1
# Minute mem · Hourly flush · 4h PR · Daily top merge/fanout
# Requires: Python on PATH, fusion-hero-os checkout, private daily-plans clone

param(
    [string]$RepoRoot = "C:\Users\Admin\fusion-hero-os",
    [switch]$Unregister
)

$ErrorActionPreference = "Stop"
$py = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $py) { throw "python not found on PATH" }

$envLine = "set PYTHONPATH=$RepoRoot&& set FUSION_PUSH_INTENT=1&&"
$mod = "python -m fusion_hero_os.core.daycycle_mem"

function Register-DayTask($Name, $Args, $Trigger) {
    $action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c $envLine $mod $Args >> `"$env:USERPROFILE\.fusion\daycycle\task_$Name.log`" 2>&1" -WorkingDirectory $RepoRoot
    Register-ScheduledTask -TaskName $Name -Action $action -Trigger $Trigger -Force | Out-Null
    Write-Host "registered $Name" -ForegroundColor Green
}

if ($Unregister) {
    @(
        "FusionHeroOS-Daycycle-Minute",
        "FusionHeroOS-Daycycle-Hourly",
        "FusionHeroOS-Daycycle-PR4h",
        "FusionHeroOS-Daycycle-Daily"
    ) | ForEach-Object {
        Unregister-ScheduledTask -TaskName $_ -Confirm:$false -ErrorAction SilentlyContinue
        Write-Host "unregistered $_"
    }
    exit 0
}

New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.fusion\daycycle" | Out-Null

# Minute: every 1 minute
$tMin = New-ScheduledTaskTrigger -Once -At (Get-Date).Date -RepetitionInterval (New-TimeSpan -Minutes 1) -RepetitionDuration (New-TimeSpan -Days 3650)
Register-DayTask "FusionHeroOS-Daycycle-Minute" "--minute" $tMin

# Hourly: every hour at :00-ish via 60 min repetition from next hour
$nextHour = (Get-Date).Date.AddHours((Get-Date).Hour + 1)
$tHour = New-ScheduledTaskTrigger -Once -At $nextHour -RepetitionInterval (New-TimeSpan -Hours 1) -RepetitionDuration (New-TimeSpan -Days 3650)
Register-DayTask "FusionHeroOS-Daycycle-Hourly" "--hourly" $tHour

# 4h PR
$tPr = New-ScheduledTaskTrigger -Once -At $nextHour -RepetitionInterval (New-TimeSpan -Hours 4) -RepetitionDuration (New-TimeSpan -Days 3650)
Register-DayTask "FusionHeroOS-Daycycle-PR4h" "--pr" $tPr

# Daily 03:00 local — merge + fanout
$tDay = New-ScheduledTaskTrigger -Daily -At "03:00"
Register-DayTask "FusionHeroOS-Daycycle-Daily" "--daily" $tDay

Write-Host "Daycycle tasks installed. Logs under ~/.fusion/daycycle/task_*.log"
Write-Host "Agent protocol: passive unless operator says testtest"
