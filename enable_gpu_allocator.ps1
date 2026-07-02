# Adaptiven GPU-VRAM-Allocator aktivieren (dediziert priorisieren)
$Api = "http://127.0.0.1:8000"

Write-Host "[GPU] Adaptiver VRAM-Allocator..." -ForegroundColor Cyan
try {
    $status = Invoke-RestMethod -Uri "$Api/api/gpu/allocator/status" -TimeoutSec 10
    $vram = $status.memory.dedicated_vram
    Write-Host ("  VRAM: {0}/{1} MB ({2}%)" -f $vram.used_mb, $vram.total_mb, $vram.util_pct)
    Write-Host ("  RAM:  {0}% genutzt" -f $status.memory.system_ram.util_pct)
    Write-Host ("  Auto: {0}, Ziel: {1}%" -f $status.allocator.auto_enabled, ($status.allocator.target_vram_ratio * 100))
} catch {
    Write-Host "  Backend nicht erreichbar. Starte: start_all.ps1" -ForegroundColor Red
    exit 1
}

$result = Invoke-RestMethod -Uri "$Api/api/gpu/allocator/rebalance" -Method POST -TimeoutSec 30
$after = $result.after.dedicated_vram
Write-Host ("  Rebalance: {0}" -f $result.action) -ForegroundColor Green
Write-Host ("  VRAM nachher: {0}/{1} MB ({2}%)" -f $after.used_mb, $after.total_mb, $after.util_pct)
Write-Host ("  Nächstes Intervall: {0}s (adaptiv)" -f $result.next_interval_s)
Write-Host "[GPU] Allocator läuft autonom im Backend-Hintergrund." -ForegroundColor Cyan