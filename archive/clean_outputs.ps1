<#
Clean generated outputs for CS2Callouts.

Usage examples:
  # Dry run (preview):
  .\clean_outputs.ps1 -WhatIf

  # Remove export/, out/, caches (default):
  .\clean_outputs.ps1 -Confirm:$false

  # Also remove downloaded tools/ (VRF CLI):
  .\clean_outputs.ps1 -IncludeTools -Confirm:$false

Notes:
  - Supports PowerShell -WhatIf / -Confirm via ShouldProcess.
  - Run from any directory; paths resolve relative to this script.
#>
[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = 'Medium')]
param(
  [switch]$IncludeTools,
  [switch]$IncludeCaches = $true
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSCommandPath
Push-Location $root
try {
  $targets = @()

  foreach ($d in @('export', 'out')) {
    if (Test-Path $d) { $targets += (Resolve-Path $d).Path }
  }

  if ($IncludeCaches) {
    foreach ($c in @('.pytest_cache', '.mypy_cache')) {
      if (Test-Path $c) { $targets += (Resolve-Path $c).Path }
    }
  }

  $pycacheDirs = @()
  if ($IncludeCaches) {
    $pycacheDirs = Get-ChildItem -Recurse -Directory -Filter '__pycache__' -ErrorAction SilentlyContinue |
                   Select-Object -ExpandProperty FullName
  }

  if ($IncludeTools) {
    if (Test-Path 'tools') { $targets += (Resolve-Path 'tools').Path }
  }

  if (-not $targets -and -not $pycacheDirs) {
    Write-Host 'Nothing to clean.' -ForegroundColor Yellow
    return
  }

  $removed = New-Object System.Collections.Generic.List[string]
  $failed  = New-Object System.Collections.Generic.List[string]

  foreach ($p in ($targets + $pycacheDirs | Select-Object -Unique)) {
    if (-not $p) { continue }
    if (-not ($p -like "$root*")) {
      Write-Warning "Skipping path outside repo root: $p"
      continue
    }
    if ($PSCmdlet.ShouldProcess($p, 'Remove')) {
      try {
        Remove-Item -LiteralPath $p -Recurse -Force -ErrorAction Stop
        $removed.Add($p) | Out-Null
      } catch {
        Write-Warning ("Failed to remove {0}: {1}" -f $p, $_.Exception.Message)
        $failed.Add($p) | Out-Null
      }
    }
  }

  Write-Host ("Removed: {0}" -f $removed.Count) -ForegroundColor Cyan
  foreach ($r in $removed) { Write-Host " - $r" }
  if ($failed.Count -gt 0) {
    Write-Host ("Failed: {0}" -f $failed.Count) -ForegroundColor Yellow
    foreach ($f in $failed) { Write-Host " - $f" }
  }
} finally {
  Pop-Location
}

