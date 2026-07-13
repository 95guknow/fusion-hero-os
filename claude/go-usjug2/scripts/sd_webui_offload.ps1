# Move stable-diffusion-webui off C: (requires external/target drive with enough space)
param(
    [Parameter(Mandatory = $true)]
    [string]$TargetPath,
    [switch]$Execute
)

$Source = "C:\Users\Admin\stable-diffusion-webui"
$ErrorActionPreference = "Stop"

if (-not (Test-Path $Source)) {
    Write-Error "Source not found: $Source"
}

$targetRoot = [System.IO.Path]::GetFullPath($TargetPath)
$dest = Join-Path $targetRoot "stable-diffusion-webui"
$srcDrive = (Split-Path $Source -Qualifier).TrimEnd(':')
$dstDrive = (Split-Path $dest -Qualifier).TrimEnd(':')

if ($srcDrive -eq $dstDrive) {
    Write-Error "Target must be on a different drive than C: (got $dstDrive`:)"
}

$sizeGb = [math]::Round(
    (Get-ChildItem $Source -Recurse -File -Force -ErrorAction SilentlyContinue |
        Measure-Object Length -Sum).Sum / 1GB, 2)
$freeGb = [math]::Round((Get-PSDrive $dstDrive).Free / 1GB, 2)

Write-Host "Source: $Source ($sizeGb GB)"
Write-Host "Target: $dest (drive $dstDrive`: free $freeGb GB)"

if ($freeGb -lt ($sizeGb + 2)) {
    Write-Error "Not enough free space on $dstDrive`: (need ~$($sizeGb + 2) GB)"
}

if (-not $Execute) {
    Write-Host "Dry-run. Add -Execute to move with robocopy and create junction."
    exit 0
}

New-Item -ItemType Directory -Path $targetRoot -Force | Out-Null
robocopy $Source $dest /E /MOVE /R:2 /W:5 /NFL /NDL /NP
if ($LASTEXITCODE -ge 8) {
    Write-Error "robocopy failed with exit $LASTEXITCODE"
}

cmd /c mklink /J "$Source" "$dest"
Write-Host "Done. Junction: $Source -> $dest" -ForegroundColor Green