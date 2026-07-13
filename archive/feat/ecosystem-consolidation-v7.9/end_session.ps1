# end_session.ps1
# Fusion Hero OS - Am Ende der Sitzung: alle Neuerungen committen + sicher an GitHub pushen
# powershell -File end_session.ps1
# Macht: 1. Final Auto-Save auf allen Worktrees
#        2. Für jeden Worktree: fetch + rebase + push (force-with-lease)
#        3. Session-Log + Summary

param(
    [switch]$SkipPush,
    [switch]$ForceWithLease = $true
)

$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root
$SessionDir = Join-Path $Root ".fusion-hero-os"
New-Item -ItemType Directory -Force -Path $SessionDir | Out-Null
$SessionLog = Join-Path $SessionDir "session_log.json"

function Get-Worktrees {
    $lines = git worktree list --porcelain
    $wts = @()
    $current = $null
    foreach ($line in $lines) {
        if ($line -match '^worktree (.+)$') {
            if ($current) { $wts += $current }
            $current = @{ path = $matches[1]; branch = 'main' }
        } elseif ($line -match '^branch refs/heads/(.+)$' -and $current) {
            $current.branch = $matches[1]
        }
    }
    if ($current) { $wts += $current }
    return $wts
}

function Commit-All([string]$Path, [string]$Branch) {
    Push-Location $Path
    try {
        $porcelain = git status --porcelain --untracked-files=all
        if ($porcelain) {
            $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            $msg = "session-end [$ts] $Branch - Alle Neuerungen der Sitzung"
            git add -A
            git commit -m $msg --no-verify | Out-Null
            Write-Host "  [$Branch] Final commit: $msg" -ForegroundColor Green
        }
    } finally { Pop-Location }
}

function Sync-And-Push([string]$Path, [string]$Branch) {
    Push-Location $Path
    $result = @{ branch = $Branch; pushed = $false; error = $null }

    try {
        Write-Host "[$Branch] Fetch + Rebase..." -NoNewline
        git fetch origin | Out-Null

        # Rebase on the tracking branch if exists
        $remoteRef = "origin/$Branch"
        $hasRemote = (git ls-remote --heads origin $Branch | Measure-Object).Count -gt 0

        if ($hasRemote) {
            git rebase $remoteRef 2>&1 | Out-Null
            if ($LASTEXITCODE -ne 0) {
                Write-Host " REBASE KONFLIKT (manuell beheben)" -ForegroundColor Red
                $result.error = "rebase conflict"
                return $result
            }
        }

        if (-not $SkipPush) {
            Write-Host " Push..." -NoNewline
            if ($ForceWithLease) {
                git push origin "HEAD:refs/heads/$Branch" --force-with-lease 2>&1 | Out-Null
            } else {
                git push origin "HEAD:refs/heads/$Branch" 2>&1 | Out-Null
            }

            if ($LASTEXITCODE -eq 0) {
                Write-Host " OK" -ForegroundColor Green
                $result.pushed = $true
            } else {
                Write-Host " PUSH FEHLGESCHLAGEN" -ForegroundColor Red
                $result.error = "push failed"
            }
        } else {
            Write-Host " (Push übersprungen)" -ForegroundColor Yellow
        }
    } catch {
        $result.error = $_.Exception.Message
        Write-Host " FEHLER: $_" -ForegroundColor Red
    } finally {
        Pop-Location
    }
    return $result
}

Write-Host "=== ENDE DER SITZUNG: Alle Neuerungen automatisch speichern + pushen ===" -ForegroundColor Magenta

$worktrees = Get-Worktrees
$results = @()

# 1. Alle final speichern
Write-Host "`n[1/3] Finaler Auto-Save auf allen Worktrees..." -ForegroundColor Cyan
foreach ($wt in $worktrees) {
    Commit-All $wt.path $wt.branch
}

# 2. Sync + Push
if (-not $SkipPush) {
    Write-Host "`n[2/3] Mit GitHub abgleichen + pushen..." -ForegroundColor Cyan
    foreach ($wt in $worktrees) {
        $r = Sync-And-Push $wt.path $wt.branch
        $results += $r
    }
} else {
    Write-Host "`n[2/3] Push übersprungen (--SkipPush)" -ForegroundColor Yellow
}

# 3. Session Log
$endTime = Get-Date
$logEntry = @{
    session_end = $endTime.ToString("o")
    worktrees   = $worktrees | ForEach-Object { $_.branch }
    results     = $results
    note        = "Automatisch via end_session.ps1 - alle Neuerungen gespeichert und gepusht."
}

if (Test-Path $SessionLog) {
    try {
        $existing = Get-Content $SessionLog -Raw | ConvertFrom-Json
        if ($existing -is [array]) {
            $existing += $logEntry
        } else {
            $existing = @($existing, $logEntry)
        }
        $existing | ConvertTo-Json -Depth 6 | Set-Content $SessionLog -Encoding UTF8
    } catch {
        $logEntry | ConvertTo-Json -Depth 6 | Set-Content $SessionLog -Encoding UTF8
    }
} else {
    @($logEntry) | ConvertTo-Json -Depth 6 | Set-Content $SessionLog -Encoding UTF8
}

Write-Host "`n[3/3] Sitzungsprotokoll gespeichert: $SessionLog" -ForegroundColor Cyan

$success = ($results | Where-Object { $_.pushed }).Count
Write-Host "`n=== FERTIG. $success Branches erfolgreich gepusht. ===" -ForegroundColor Green
Write-Host "Nächster Schritt: git log --oneline -5   oder  git worktree list" -ForegroundColor DarkCyan

# Optional: kurze Zusammenfassung auf Main committen (falls auf Main)
Push-Location $Root
try {
    $summary = "session-summary $(Get-Date -Format 'yyyy-MM-dd') : $success / $($worktrees.Count) Branches updated"
    git add .fusion-hero-os/session_log.json 2>$null
    git commit -m $summary --no-verify 2>$null | Out-Null
} finally { Pop-Location }

Write-Host "Session beendet." -ForegroundColor Magenta