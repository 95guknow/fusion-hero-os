# Fusion-Hero-OS v8 - Grok Intern Abgleich mit GitHub
# Synchronisiert lokalen Grok-Skill + Kilo-Workspace mit Repo-Stand

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$GrokSkill = "C:\Users\Admin\.grok\skills\fusion-hero-os"
$KiloWs = "C:\Users\Admin\.config\kilo\fusion-hero-os.code-workspace"
$GitRemote = "https://github.com/95guknow/fusion-hero-os"

New-Item -ItemType Directory -Force -Path $GrokSkill | Out-Null

# GitHub-Stand ermitteln
$gitHead = "unknown"
$gitDate = "unknown"
try {
    Push-Location $Root
    $gitHead = (git rev-parse --short HEAD 2>$null)
    $gitDate = (git log -1 --format="%ci" 2>$null)
    Pop-Location
} catch {
    Pop-Location -ErrorAction SilentlyContinue
}

@{
    "folders" = @(
        @{ "path" = $Root },
        @{ "path" = "C:\Users\Admin\heroic-core-foundation" },
        @{ "path" = $GrokSkill }
    )
    "settings" = @{
        "FUSION_OS_VERSION" = "v8"
        "HEROIC_CORE_VERSION" = "v8"
        "GITHUB_REPO" = "95guknow/fusion-hero-os"
        "GITHUB_HEAD" = $gitHead
        "GITHUB_SYNCED" = $gitDate
    }
} | ConvertTo-Json -Depth 4 | Set-Content -Path $KiloWs -Encoding UTF8

Write-Host "[v8] Grok-intern Abgleich mit GitHub:" -ForegroundColor Cyan
Write-Host "  Repo:      $GitRemote"
Write-Host "  HEAD:      $gitHead ($gitDate)"
Write-Host "  Skill:     $GrokSkill"
Write-Host "  Workspace: $KiloWs"
Write-Host "  Version:   Fusion Hero OS v8 / Heroic Core v8"

# Skill-Manifest aktualisieren (falls vorhanden)
$manifest = Join-Path $GrokSkill "GITHUB_SYNC.json"
@{
    repo = "95guknow/fusion-hero-os"
    branch = "main"
    head = $gitHead
    synced_at = (Get-Date -Format "yyyy-MM-ddTHH:mm:ss")
    version = "v8"
    deployment_guide = "DEPLOYMENT_GUIDE.md"
    gui = "http://127.0.0.1:8000"
    gui_module = "03_Code/Dashboard/app.py"
    nicegui_legacy = "http://127.0.0.1:8080"
} | ConvertTo-Json -Depth 3 | Set-Content -Path $manifest -Encoding UTF8

Write-Host "  Manifest:  $manifest" -ForegroundColor DarkGray