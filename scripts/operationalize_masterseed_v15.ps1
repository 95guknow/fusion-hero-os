# Operationalize MasterSeed against current VERSION (v15.x)
# Usage: powershell -File scripts\operationalize_masterseed_v15.ps1 [-Train] [-NoDashboard]
param(
    [switch]$Train,
    [switch]$NoDashboard,
    [switch]$NoTests,
    [switch]$NoSeal
)
$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Py = if (Test-Path "C:\Users\Admin\venv\Scripts\python.exe") {
    "C:\Users\Admin\venv\Scripts\python.exe"
} else { "python" }
$argsList = @((Join-Path $Root "scripts\operationalize_masterseed_v15.py"))
if ($Train) { $argsList += "--train" }
if ($NoDashboard) { $argsList += "--no-dashboard" }
if ($NoTests) { $argsList += "--no-tests" }
if ($NoSeal) { $argsList += "--no-seal" }
Write-Host "=== MasterSeed operationalize (VERSION-driven) ===" -ForegroundColor Cyan
& $Py @argsList
exit $LASTEXITCODE
