param(
  [string]$Map = "de_mirage",
  [string]$OutJson = "",
  [string]$ModelsRoot = "export/models"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not (Test-Path 'scripts/vrf_extract_callout_models.ps1')) {
  Write-Error 'Run from the repo root so scripts/ is available.'
  exit 1
}

Write-Host "[1/2] Decompiling and exporting models for $Map..." -ForegroundColor Cyan
powershell -ExecutionPolicy Bypass -File scripts/vrf_extract_callout_models.ps1 -Map $Map

$calloutsJson = Join-Path "export/maps/$Map/report" 'callouts_found.json'
if (-not (Test-Path $calloutsJson)) {
  Write-Error "callouts_found.json not found at $calloutsJson"
  exit 2
}

if (-not $OutJson -or $OutJson -eq '') { $OutJson = "out/${Map}_callouts.json" }

Write-Host "[2/2] Building polygons JSON -> $OutJson" -ForegroundColor Cyan
python -m cs2_callouts.cli --map $Map --models-root $ModelsRoot --callouts-json $calloutsJson --out $OutJson

