# Wrapper: fehlende Assets auditieren und generieren
$FusionRoot = if ($env:FUSION_HERO_ROOT) { $env:FUSION_HERO_ROOT } else { "C:\Users\Admin\fusion-hero-os" }
$Python = if ($env:PYTHON_EXE) { $env:PYTHON_EXE } else { "C:\Users\Admin\venv\Scripts\python.exe" }
$Script = Join-Path $FusionRoot "03_Code\tools\generate_missing_assets.py"

$env:FUSION_HERO_ROOT = $FusionRoot
$env:FUSION_VR_ASSETS_ROOT = Join-Path $FusionRoot "03_VR_Assets"

if ($args -contains "-AuditOnly") {
    & $Python $Script --audit @($args | Where-Object { $_ -ne "-AuditOnly" })
} else {
    & $Python $Script --generate @args
}
exit $LASTEXITCODE