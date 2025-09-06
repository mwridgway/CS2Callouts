param(
    [string]$CliDir = (Join-Path (Get-Location) "tools\vrf-cli"),
    [string]$CliUrl = "",
    [string]$CliVersion = "14.1"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Info($msg) { Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Warn($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Err($msg)  { Write-Host "[ERR ] $msg" -ForegroundColor Red }

function Ensure-Dir([string]$p) {
    if (-not (Test-Path $p)) { New-Item -ItemType Directory -Force -Path $p | Out-Null }
}

function Install-VRFCLI([string]$cliDir, [string]$explicitUrl = "", [string]$version = "") {
    Ensure-Dir $cliDir
    $cliExe = Join-Path $cliDir "Source2Viewer-CLI.exe"
    if (Test-Path $cliExe) {
        Write-Info "VRF CLI already present: $cliExe"
        return $cliExe
    }

    $urls = @()
    if ($explicitUrl) { $urls += $explicitUrl }
    if ($version) {
        $urls += "https://github.com/ValveResourceFormat/ValveResourceFormat/releases/download/$version/cli-windows-x64.zip"
        $urls += "https://github.com/ValveResourceFormat/ValveResourceFormat/releases/download/$version/cli-win-x64.zip"
    }
    $urls += "https://github.com/ValveResourceFormat/ValveResourceFormat/releases/latest/download/cli-windows-x64.zip"
    $urls += "https://github.com/ValveResourceFormat/ValveResourceFormat/releases/latest/download/cli-win-x64.zip"

    foreach ($url in $urls | Select-Object -Unique) {
        try {
            Write-Info "Downloading VRF CLI from $url"
            $tmpZip = Join-Path $env:TEMP ("vrf_cli_" + [System.Guid]::NewGuid().ToString() + ".zip")
            Invoke-WebRequest -UseBasicParsing -OutFile $tmpZip -Uri $url
            Expand-Archive -Path $tmpZip -DestinationPath $cliDir -Force
            Remove-Item $tmpZip -Force -ErrorAction SilentlyContinue
            if (Test-Path $cliExe) { return $cliExe }
            $cand = Get-ChildItem -Path $cliDir -Recurse -Include "Source2Viewer-CLI.exe","*CLI*.exe" -File -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($cand) { return $cand.FullName }
        } catch {
            Write-Warn ("Download failed from {0}: {1}" -f $url, $_.Exception.Message)
        }
    }
    throw "VRF CLI download failed. Specify -CliUrl or -CliVersion explicitly."
}

try {
    $exe = Install-VRFCLI -cliDir $CliDir -explicitUrl $CliUrl -version $CliVersion
    Write-Info "VRF CLI ready: $exe"
    Write-Host ""
    Write-Host "Next: run extraction, for example:" -ForegroundColor Green
    Write-Host "  powershell -File scripts\vrf_extract_callouts.ps1 -CliExe `"$exe`" -Map de_mirage -OutRoot .\export -VpkPaths @(`"C:\\...\\csgo\\maps\\de_mirage.vpk`",`"C:\\...\\csgo_core\\pak01_dir.vpk`")" -ForegroundColor Gray
} catch {
    Write-Err $_
    exit 1
}

