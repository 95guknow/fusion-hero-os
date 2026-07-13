# Fusion Hero OS — inbound firewall rule for Dashboard (port 8000)
# Requires: Run as Administrator

$ruleName = "Fusion Hero Dashboard 8000"
$existing = netsh advfirewall firewall show rule name="$ruleName" 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "Rule '$ruleName' already exists."
    exit 0
}

netsh advfirewall firewall add rule name="$ruleName" dir=in action=allow protocol=TCP localport=8000 profile=private,domain
if ($LASTEXITCODE -eq 0) {
    Write-Host "Firewall rule added: TCP 8000 (private, domain)."
} else {
    Write-Error "Failed - run this script as Administrator."
    exit 1
}