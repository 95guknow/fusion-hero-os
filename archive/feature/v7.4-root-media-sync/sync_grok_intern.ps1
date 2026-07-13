# Grok-intern Abgleich fuer Fusion Hero OS v1.2
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$GrokSkill = "C:\Users\Admin\.grok\skills\fusion-hero-os"
$KiloWs = "C:\Users\Admin\.config\kilo\fusion-hero-os.code-workspace"

New-Item -ItemType Directory -Force -Path $GrokSkill | Out-Null

@{
    "folders" = @(
        @{ "path" = $Root },
        @{ "path" = "C:\Users\Admin\heroic-core-foundation" },
        @{ "path" = "C:\Users\Admin\.grok\skills\fusion-hero-os" }
    )
    "settings" = @{ "FUSION_OS_VERSION" = "v1.2"; "HEROIC_CORE_VERSION" = "v7.5" }
} | ConvertTo-Json -Depth 4 | Set-Content -Path $KiloWs -Encoding UTF8

Write-Host "Grok-intern Abgleich:" -ForegroundColor Cyan
Write-Host "  Skill:     $GrokSkill"
Write-Host "  Workspace: $KiloWs"
Write-Host "  Version:   Fusion Hero OS v1.2 / Core v7.5"
