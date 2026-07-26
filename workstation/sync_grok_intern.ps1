# Fusion-Hero-OS Grok Intern Abgleich mit GitHub
# Platform version = root VERSION (source of truth). Sync upgrade v12.x.
# Synchronisiert lokalen Grok-Skill + Kilo-Workspace mit Repo-Stand (operativer Kanon)

$ErrorActionPreference = "Continue"
$Root = if ($env:FUSION_HERO_ROOT) { $env:FUSION_HERO_ROOT } else { (Resolve-Path (Join-Path $PSScriptRoot "..")).Path }
$GrokSkill = Join-Path $env:USERPROFILE ".grok\skills\fusion-hero-os"
$KiloWs = Join-Path $env:USERPROFILE ".config\kilo\fusion-hero-os.code-workspace"
$GitRemote = "https://github.com/95guknow/fusion-hero-os"
$CheckScript = Join-Path $PSScriptRoot "check-grok-cli.ps1"
# Prefer root VERSION; fallback 12.1.0
$versionFileEarly = Join-Path $Root "VERSION"
$PlatformVersion = if (Test-Path $versionFileEarly) { (Get-Content $versionFileEarly -Raw).Trim() } else { "12.1.0" }
$OperativeKanon = "v$PlatformVersion"
$Aspirational = "v9.10 AscensionOS track (loadable)"
$Inherits = "v8.3 functional stack + Stage-A/B + v12 daycycle"

New-Item -ItemType Directory -Force -Path $GrokSkill | Out-Null

# Grok CLI Version (check-grok-cli.ps1 oder inline)
$grokVersion = $null
$previousGrokVersion = $null
$grokCheckedAt = (Get-Date).ToString("o")
if (Test-Path $CheckScript) {
    & $CheckScript -Quiet 2>$null | Out-Null
    $statusFile = Join-Path $env:USERPROFILE ".fusion\grok-cli.status.json"
    if (Test-Path $statusFile) {
        try {
            $st = Get-Content $statusFile -Raw | ConvertFrom-Json
            $grokVersion = $st.version
            $previousGrokVersion = $st.previous_version
        } catch {}
    }
}
if (-not $grokVersion) {
    try {
        $grokBin = Join-Path $env:USERPROFILE ".grok\bin\grok.exe"
        $raw = if (Test-Path $grokBin) {
            & $grokBin --version 2>&1 | Out-String
        } else {
            & grok --version 2>&1 | Out-String
        }
        if ($raw -match 'v?(\d+\.\d+\.\d+)') { $grokVersion = $Matches[1] }
    } catch {}
}

# GitHub-Stand ermitteln
$gitHead = "unknown"
$gitDate = "unknown"
$gitHeadFull = "unknown"
try {
    Push-Location $Root
    $gitHead = (git rev-parse --short HEAD 2>$null)
    $gitHeadFull = (git rev-parse HEAD 2>$null)
    $gitDate = (git log -1 --format="%ci" 2>$null)
    Pop-Location
} catch {
    Pop-Location -ErrorAction SilentlyContinue
}

# Platform VERSION file (source of truth)
$versionFile = Join-Path $Root "VERSION"
$fileVersion = $null
if (Test-Path $versionFile) {
    $fileVersion = (Get-Content $versionFile -Raw).Trim()
}
if ($fileVersion) {
    $PlatformVersion = $fileVersion
    $OperativeKanon = "v$PlatformVersion"
}

@{
    "folders" = @(
        @{ "path" = $Root },
        @{ "path" = "C:\Users\Admin\heroic-core-foundation" },
        @{ "path" = $GrokSkill }
    )
    "settings" = @{
        "FUSION_OS_VERSION" = $OperativeKanon
        "FUSION_PLATFORM_VERSION" = $PlatformVersion
        "HEROIC_CORE_VERSION" = "v8.3+v9.10"
        "OPERATIVE_KANON" = $OperativeKanon
        "ASPIRATIONAL_TRACK" = $Aspirational
        "INHERITS" = $Inherits
        "GITHUB_REPO" = "95guknow/fusion-hero-os"
        "GITHUB_HEAD" = $gitHead
        "GITHUB_SYNCED" = $gitDate
        "FUSION_GROK_CLI_VERSION" = $grokVersion
        "BEST_VERSION" = "BEST_VERSION.md"
        "GUI" = "http://127.0.0.1:8000"
    }
} | ConvertTo-Json -Depth 4 | Set-Content -Path $KiloWs -Encoding UTF8

Write-Host "[$OperativeKanon] Grok-intern Abgleich mit GitHub:" -ForegroundColor Cyan
Write-Host "  Repo:      $GitRemote"
Write-Host "  HEAD:      $gitHead ($gitDate)"
Write-Host "  Skill:     $GrokSkill"
Write-Host "  Workspace: $KiloWs"
Write-Host "  Version:   Fusion Hero OS $OperativeKanon (platform $PlatformVersion)"
Write-Host "  Inherits:  $Inherits"
Write-Host "  Aspirat.:  $Aspirational"
if ($grokVersion) {
    Write-Host "  Grok CLI:  v$grokVersion" -ForegroundColor Green
    if ($previousGrokVersion -and ($previousGrokVersion -ne $grokVersion)) {
        Write-Host "  Grok Update: v$previousGrokVersion -> v$grokVersion" -ForegroundColor Magenta
    }
} else {
    Write-Host "  Grok CLI:  (nicht ermittelt)" -ForegroundColor Yellow
}

# Skill-Manifest aktualisieren (v10.0.0 Kanon — nicht mehr v8)
$manifest = Join-Path $GrokSkill "GITHUB_SYNC.json"
$manifestObj = [ordered]@{
    repo = "95guknow/fusion-hero-os"
    branch = "main"
    head = $gitHeadFull
    synced_at = (Get-Date -Format "yyyy-MM-ddTHH:mm:ss")
    version = $OperativeKanon
    platform_version = $PlatformVersion
    operative_kanon = $OperativeKanon
    inherits = $Inherits
    aspirational = $Aspirational
    best_version = "BEST_VERSION.md"
    deployment_guide = "DEPLOYMENT_GUIDE.md"
    release_url = "https://github.com/95guknow/fusion-hero-os/releases/tag/v10.0.0"
    grok_cli_version = $grokVersion
    grok_cli_checked_at = $grokCheckedAt
    previous_grok_cli_version = $previousGrokVersion
    gui = "http://127.0.0.1:8000"
    gui_module = "03_Code/Dashboard/app.py"
    nicegui_legacy = "http://127.0.0.1:8080"
}
$manifestObj | ConvertTo-Json -Depth 3 | Set-Content -Path $manifest -Encoding UTF8

Write-Host "  Manifest:  $manifest" -ForegroundColor DarkGray
Write-Host "  OK:        $OperativeKanon propagated to Grok skill + Kilo workspace" -ForegroundColor Green
