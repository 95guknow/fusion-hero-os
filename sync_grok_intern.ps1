# Fusion-Hero-OS v12.1.0 - Grok Intern Abgleich (delegiert an workstation/; VERSION-driven)
$WsScript = Join-Path $PSScriptRoot "workstation\sync_grok_intern.ps1"
if (-not (Test-Path $WsScript)) {
    Write-Host "FEHLER: $WsScript nicht gefunden" -ForegroundColor Red
    exit 1
}
& $WsScript @args
exit $LASTEXITCODE
