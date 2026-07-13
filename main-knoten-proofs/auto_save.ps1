# auto_save.ps1
# Fusion Hero OS - Automatisches Speichern aller Neuerungen
# Speichert (git add + commit) Änderungen; mit -Push zusätzlich Push zu GitHub.
# Aufruf-Beispiele:
#   powershell -ExecutionPolicy Bypass -File auto_save.ps1 -Once
#   powershell -ExecutionPolicy Bypass -File auto_save.ps1 -Once -Push
#   powershell -ExecutionPolicy Bypass -File auto_save.ps1 -Push        # Loop + Push
#
# -Push pusht jeden (Worktree-)Branch zu seinem Upstream-Remote (bzw. dem ersten
# konfigurierten Remote). Secrets sind über .gitignore (.env, .env.*) geschützt
# und werden von 'git add -A' nicht erfasst.

param(
    [switch]$Once,
    [int]$IntervalSec = 45,
    [switch]$AllWorktrees = $true,
    [string]$MessagePrefix = "auto-save",
    [switch]$Push
)

$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

function GetAllWorktrees {
    $output = git worktree list --porcelain
    $wts = @()
    $cur = $null
    foreach ($l in $output) {
        if ($l -match '^worktree (.+)') {
            if ($cur -ne $null) { $wts += $cur }
            $cur = @{path = $matches[1]; branch = "main"}
        } elseif ($l -match '^branch refs/heads/(.+)') {
            if ($cur -ne $null) { $cur.branch = $matches[1] }
        }
    }
    if ($cur -ne $null) { $wts += $cur }
    return $wts
}

function CommitChanges($Path, $BranchName) {
    Push-Location $Path
    try {
        $status = git status --porcelain --untracked-files=all
        if (-not $status) {
            Write-Host ("[" + (Split-Path $Path -Leaf) + "] clean")
            return $false
        }

        $ts = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
        $files = ($status | Select-Object -First 4 | ForEach-Object { $_.Trim() }) -join " | "
        $commitMsg = "$MessagePrefix [$ts] $BranchName - $files"

        git add -A
        git commit -m "$commitMsg" --no-verify | Out-Null
        Write-Host ("[" + (Split-Path $Path -Leaf) + "] COMMITTED: " + $commitMsg) -ForegroundColor Green
        return $true
    } catch {
        Write-Host ("[" + (Split-Path $Path -Leaf) + "] ERROR: " + $_) -ForegroundColor Red
        return $false
    } finally {
        Pop-Location | Out-Null
    }
}

function PushBranch($Path, $BranchName) {
    Push-Location $Path
    try {
        # Upstream-Remote der Branch, sonst erstes konfiguriertes Remote (hier: fusion-hero-os)
        $remoteName = git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>$null
        if ($remoteName) {
            $remoteName = ($remoteName -split '/')[0]
        } else {
            $remoteName = (git remote 2>$null | Select-Object -First 1)
        }
        if (-not $remoteName) {
            Write-Host ("[" + (Split-Path $Path -Leaf) + "] kein Remote - Push uebersprungen") -ForegroundColor Yellow
            return $false
        }
        git push $remoteName ("HEAD:" + $BranchName) 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host ("[" + (Split-Path $Path -Leaf) + "] PUSHED -> " + $remoteName + "/" + $BranchName) -ForegroundColor Green
            return $true
        }
        Write-Host ("[" + (Split-Path $Path -Leaf) + "] Push fehlgeschlagen (Exit " + $LASTEXITCODE + ")") -ForegroundColor Red
        return $false
    } catch {
        Write-Host ("[" + (Split-Path $Path -Leaf) + "] PUSH-ERROR: " + $_) -ForegroundColor Red
        return $false
    } finally {
        Pop-Location | Out-Null
    }
}

Write-Host "=== Fusion Hero OS - Auto-Save aller Neuerungen ===" -ForegroundColor Cyan

$targets = @()
if ($AllWorktrees) {
    $targets = GetAllWorktrees
} else {
    $currentBranch = git branch --show-current
    $targets = @(@{path = $Root; branch = $currentBranch})
}

$didSomething = $false

if ($Once) {
    foreach ($t in $targets) {
        if (CommitChanges $t.path $t.branch) { $didSomething = $true }
        if ($Push) { PushBranch $t.path $t.branch | Out-Null }
    }
    if ($didSomething) {
        Write-Host "Auto-Save fertig." -ForegroundColor Cyan
    }
    exit 0
}

# Continuous loop
$pushNote = if ($Push) { " + Push" } else { "" }
Write-Host ("Loop-Modus gestartet" + $pushNote + ". Intervall: " + $IntervalSec + "s  (Strg+C = Stop)")
while ($true) {
    foreach ($t in $targets) {
        CommitChanges $t.path $t.branch | Out-Null
        if ($Push) { PushBranch $t.path $t.branch | Out-Null }
    }
    Start-Sleep -Seconds $IntervalSec
}