# Fusion Hero OS — Start Docs Server + Phone Notification v8.1
# Startet den Heroic Docs Server und pusht sofort die Zugriffs-URL ans Handy via Phone Link

param(
    [int]$Port = 8088
)

$ErrorActionPreference = "Stop"

Write-Host "`n[FUSION HERO OS] Starte Heroic Docs Server mit Phone Notification..." -ForegroundColor Cyan

# 1. LAN-IP ermitteln
$lanIp = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.*" } | Select-Object -First 1).IPAddress
if (-not $lanIp) { $lanIp = "127.0.0.1" }

$localUrl = "http://127.0.0.1:$Port"
$phoneUrl = "http://$lanIp:$Port"
$statusUrl = "http://$lanIp:$Port/status"

Write-Host "[INFO] LAN-IP: $lanIp" -ForegroundColor Green
Write-Host "[INFO] Handy-URL: $phoneUrl" -ForegroundColor Green

# 2. Notification an Handy senden (verwendet dein bestehendes phonelink-control Setup)
$notificationScript = "C:\Users\Admin\fusion-hero-os\scripts\Send-CoreNotification.ps1"  # Passe den Pfad an, falls anders

if (Test-Path $notificationScript) {
    & $notificationScript -Title "Fusion Hero OS" -Message "Docs Server aktiv`n`nHandy: $phoneUrl`nStatus: $statusUrl" -Level "Evolution"
    Write-Host "[PHONE] Notification an Handy gesendet." -ForegroundColor Magenta
} else {
    Write-Host "[WARN] Send-CoreNotification.ps1 nicht gefunden. Notification übersprungen." -ForegroundColor Yellow
    Write-Host "       Du kannst die URL manuell vom Handy aus öffnen: $phoneUrl" -ForegroundColor Yellow
}

# 3. Docs Server starten (im Hintergrund)
Write-Host "`n[START] Starte Python Docs Server auf Port $Port ..." -ForegroundColor Cyan

$pythonScript = Join-Path $PSScriptRoot "hero-docs-server.py"

if (Test-Path $pythonScript) {
    Start-Process python -ArgumentList "`"$pythonScript`"" -WindowStyle Hidden
    Write-Host "[OK] Server läuft im Hintergrund." -ForegroundColor Green
    Write-Host "`nÖffne jetzt auf dem Handy:`n$phoneUrl" -ForegroundColor White
} else {
    Write-Host "[ERROR] hero-docs-server.py nicht gefunden!" -ForegroundColor Red
}

Write-Host "`n[MASTERSEED] Docs Server + Phone Bridge aktiviert. Horkrux läuft." -ForegroundColor Green
Read-Host "Drücke Enter zum Beenden (Server läuft weiter im Hintergrund)"