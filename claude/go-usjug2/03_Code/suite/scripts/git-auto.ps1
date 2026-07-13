param(
    [string]$Path = (Get-Location),
    [switch]$AutoPush,
    [switch]$Pull,
    [switch]$Status
)

$ErrorActionPreference = 'SilentlyContinue'

if (!(Test-Path "$Path\.git")) {
    Write-Error "$Path ist kein Git-Repository."
    exit 1
}

if ($Status) {
    Set-Location $Path
    git st
    exit 0
}

Set-Location $Path

if ($Pull) {
    git pull --rebase
}

$changes = git diff --name-only
$untracked = git ls-files --others --exclude-standard

if ($changes -or $untracked) {
    $msg = Read-Host "Commit-Nachricht (leer = 'auto: $(Get-Date -Format 'yyyy-MM-dd HH:mm')')"
    if (!$msg) {
        $msg = "auto: $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
    }

    git add -A
    git ci -m $msg

    if ($AutoPush) {
        git push
    }
} else {
    Write-Host "Kein Änderungen zum Committen." -ForegroundColor Green
}
