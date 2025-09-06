# Verifies presence of required env vars without printing their values.
param(
  [string[]]$Names = @('FIRECRAWL_API_KEY'),
  [switch]$Strict
)

function Get-EnvStatus {
  param([string]$Name)
  $scopes = @('Process','User','Machine')
  foreach ($s in $scopes) {
    $val = [Environment]::GetEnvironmentVariable($Name, $s)
    if ($val) {
      return @{ Name = $Name; Present = $true; Scope = $s; Length = $val.Length }
    }
  }
  return @{ Name = $Name; Present = $false }
}

$results = @()
foreach ($n in $Names) { $results += Get-EnvStatus -Name $n }

foreach ($r in $results) {
  if ($r.Present) {
    Write-Output ("{0}: SET in {1} (len={2})" -f $r.Name, $r.Scope, $r.Length)
  } else {
    Write-Output ("{0}: MISSING" -f $r.Name)
  }
}

if ($Strict -and ($results | Where-Object { -not $_.Present }).Count -gt 0) { exit 1 }

