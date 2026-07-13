# Fusion Hero OS — E2E smoke tests (API + Watch + Connectivity)
$Base = "http://127.0.0.1:8000"
$failed = 0

function Test-Endpoint($name, $url, $method = "GET", $body = $null) {
    try {
        $params = @{ Uri = $url; Method = $method; TimeoutSec = 15; UseBasicParsing = $true }
        if ($body) {
            $params.Body = ($body | ConvertTo-Json)
            $params.ContentType = "application/json"
        }
        $r = Invoke-WebRequest @params
        if ($r.StatusCode -ge 200 -and $r.StatusCode -lt 300) {
            Write-Host "[OK] $name" -ForegroundColor Green
            return $true
        }
        Write-Host "[FAIL] $name status $($r.StatusCode)" -ForegroundColor Red
        return $false
    } catch {
        Write-Host "[FAIL] $name $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

$checks = @(
    @{ Name = "gui/status"; Url = "$Base/api/gui/status" },
    @{ Name = "discovery"; Url = "$Base/api/discovery" },
    @{ Name = "connectivity"; Url = "$Base/api/connectivity" },
    @{ Name = "jobs"; Url = "$Base/api/jobs?limit=3" },
    @{ Name = "supabase/sync"; Url = "$Base/api/supabase/sync/status" },
    @{ Name = "watch/realtime"; Url = "$Base/api/watch/realtime/config" }
)

foreach ($c in $checks) {
    if (-not (Test-Endpoint $c.Name $c.Url)) { $failed++ }
}

$room = Invoke-RestMethod -Uri "$Base/api/watch/room" -Method POST -Body (@{ url = "https://youtu.be/dQw4w9WgXcQ" } | ConvertTo-Json) -ContentType "application/json"
if ($room.ok -and $room.video_id) {
    Write-Host "[OK] watch/create room $($room.room_id)" -ForegroundColor Green
    $state = Invoke-RestMethod -Uri "$Base/api/watch/room/$($room.room_id)/state"
    if ($state.ok -and $state.state.video_id) {
        Write-Host "[OK] watch/state video=$($state.state.video_id)" -ForegroundColor Green
    } else { $failed++; Write-Host "[FAIL] watch/state" -ForegroundColor Red }
} else { $failed++; Write-Host "[FAIL] watch/create" -ForegroundColor Red }

if ($failed -eq 0) {
    Write-Host "All smoke tests passed." -ForegroundColor Green
    exit 0
}
Write-Host "$failed smoke test(s) failed." -ForegroundColor Red
exit 1