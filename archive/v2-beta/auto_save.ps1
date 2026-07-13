# auto_save.ps1
# Fusion Hero OS - Automatisches Speichern aller Neuerungen
# Speichert (git add + commit) Änderungen.
# Aufruf-Beispiele:
#   powershell -ExecutionPolicy Bypass -File auto_save.ps1 -Once
#   powershell -ExecutionPolicy Bypass -File auto_save.ps1

param(
    [switch]$Once,
    [int]$IntervalSec = 45,
    [switch]$AllWorktrees = $true,
    [string]$MessagePrefix = "auto-save"
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
    }
    if ($didSomething) {
        Write-Host "Auto-Save fertig." -ForegroundColor Cyan
    }
    exit 0
}

# Continuous loop
Write-Host ("Loop-Modus gestartet. Intervall: " + $IntervalSec + "s  (Strg+C = Stop)")
while ($true) {
    foreach ($t in $targets) {
        CommitChanges $t.path $t.branch | Out-Null
    }
    Start-Sleep -Seconds $IntervalSec
}