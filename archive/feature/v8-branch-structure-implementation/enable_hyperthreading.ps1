# Hyperthreading aktivieren (Fusion Hero OS v8)
$Api = "http://127.0.0.1:8000"

function Invoke-FusionApi($Method, $Path, $Body = $null) {
    $params = @{
        Uri = "$Api$Path"
        Method = $Method
        TimeoutSec = 15
    }
    if ($Body) {
        $params.Body = ($Body | ConvertTo-Json -Compress)
        $params.ContentType = "application/json"
    }
    return Invoke-RestMethod @params
}

Write-Host "[HT] Aktiviere Hyperthreading..." -ForegroundColor Cyan
try {
    $before = Invoke-FusionApi GET "/api/hyperthreading"
    Write-Host "  Vorher: enabled=$($before.enabled), workers=$($before.workers)"
} catch {
    Write-Host "  Backend nicht erreichbar auf $Api" -ForegroundColor Red
    Write-Host "  Starte: powershell -File start_all.ps1" -ForegroundColor Yellow
    exit 1
}

$after = Invoke-FusionApi POST "/api/hyperthreading" @{ enabled = $true }
Write-Host "  Nachher: enabled=$($after.enabled), workers=$($after.workers), profile=$($after.profile)" -ForegroundColor Green

if ($after.virtual_ht_gpu) {
    Write-Host "  Virtual HT GPU: $($after.virtual_ht_gpu), virtual_threads=$($after.virtual_threads)"
}

$health = Invoke-FusionApi GET "/api/health"
Write-Host "[HT] Health: mainframe=$($health.mainframe.loaded), HT enabled=$($health.hyperthreading.enabled)" -ForegroundColor Green
Write-Host "[HT] Hyperthreading aktiv." -ForegroundColor Cyan