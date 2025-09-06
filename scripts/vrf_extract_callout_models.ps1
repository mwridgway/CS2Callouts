param(
    [string]$VpkPath = "",
    [string[]]$VpkPaths = @(),
    [string[]]$InputFiles = @(),
    [string]$Map = "de_mirage",
    [string]$OutRoot = (Join-Path (Get-Location) "export"),
    [string]$CliDir = (Join-Path (Get-Location) "tools\vrf-cli"),
    [string]$CliUrl = "",
    [string]$CliVersion = "",
    [ValidateSet("glb","gltf")]
    [string]$GltfFormat = "glb"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Info($msg) { Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Warn($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Err($msg)  { Write-Host "[ERR ] $msg" -ForegroundColor Red }

function Ensure-Dir([string]$p) {
    if (-not (Test-Path $p)) { New-Item -ItemType Directory -Force -Path $p | Out-Null }
}

function Resolve-VpkPath([string]$userPath) {
    if ($userPath -and (Test-Path $userPath)) { return (Resolve-Path $userPath).Path }
    $candidates = @(
        "$env:ProgramFiles(x86)\Steam\steamapps\common\Counter-Strike Global Offensive\game\csgo_core\pak01_dir.vpk",
        "$env:ProgramFiles(x86)\Steam\steamapps\common\Counter-Strike Global Offensive\game\core\pak01_dir.vpk",
        "$env:ProgramFiles(x86)\Steam\steamapps\common\Counter-Strike Global Offensive\game\csgo\pak01_dir.vpk",
        "$env:ProgramFiles(x86)\Steam\steamapps\common\Counter-Strike 2\game\core\pak01_dir.vpk",
        "$env:ProgramFiles(x86)\Steam\steamapps\common\Counter-Strike 2\game\csgo_core\pak01_dir.vpk",
        "$env:ProgramFiles(x86)\Steam\steamapps\common\Counter-Strike 2\game\csgo\pak01_dir.vpk",
        "$env:ProgramFiles\Steam\steamapps\common\Counter-Strike Global Offensive\game\csgo_core\pak01_dir.vpk",
        "$env:ProgramFiles\Steam\steamapps\common\Counter-Strike Global Offensive\game\core\pak01_dir.vpk",
        "$env:ProgramFiles\Steam\steamapps\common\Counter-Strike Global Offensive\game\csgo\pak01_dir.vpk",
        "$env:ProgramFiles\Steam\steamapps\common\Counter-Strike 2\game\core\pak01_dir.vpk",
        "$env:ProgramFiles\Steam\steamapps\common\Counter-Strike 2\game\csgo_core\pak01_dir.vpk",
        "$env:ProgramFiles\Steam\steamapps\common\Counter-Strike 2\game\csgo\pak01_dir.vpk"
    )
    foreach ($c in $candidates) { if (Test-Path $c) { return (Resolve-Path $c).Path } }
    throw "Could not find pak01_dir.vpk. Pass -VpkPath with the full path to your CS2 VPK."
}

function Ensure-VrfCli([string]$cliDir, [string]$explicitUrl = "", [string]$version = "") {
    Ensure-Dir $cliDir
    $cliExe = Join-Path $cliDir "Source2Viewer-CLI.exe"
    if (Test-Path $cliExe) { return $cliExe }
    $foundExe = $null
    $urls = @()
    if ($explicitUrl) { $urls += $explicitUrl }
    if ($version) {
        $urls += "https://github.com/ValveResourceFormat/ValveResourceFormat/releases/download/$version/cli-windows-x64.zip"
        $urls += "https://github.com/ValveResourceFormat/ValveResourceFormat/releases/download/$version/cli-win-x64.zip"
    }
    # Fallbacks to latest tag
    $urls += "https://github.com/ValveResourceFormat/ValveResourceFormat/releases/latest/download/cli-windows-x64.zip"
    $urls += "https://github.com/ValveResourceFormat/ValveResourceFormat/releases/latest/download/cli-win-x64.zip"

    foreach ($url in $urls | Select-Object -Unique) {
        try {
            Write-Info "Downloading VRF CLI from $url"
            $tmpZip = Join-Path $env:TEMP ("vrf_cli_" + [System.Guid]::NewGuid().ToString() + ".zip")
            Invoke-WebRequest -UseBasicParsing -OutFile $tmpZip -Uri $url
            Expand-Archive -Path $tmpZip -DestinationPath $cliDir -Force
            Remove-Item $tmpZip -Force -ErrorAction SilentlyContinue
            # Look for the executable
            if (Test-Path $cliExe) { $foundExe = $cliExe; break }
            $cand = Get-ChildItem -Path $cliDir -Recurse -Include "Source2Viewer-CLI.exe","*CLI*.exe" -File -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($cand) { $foundExe = $cand.FullName; break }
        } catch {
            Write-Warn ("Download failed from {0}: {1}" -f $url, $_.Exception.Message)
            continue
        }
    }
    if (-not $foundExe) { throw "VRF CLI download failed. Pass -CliUrl or -CliVersion to specify an exact asset (e.g., 14.1)." }
    return $foundExe
}

function Decompile-MapAndEntities([string]$cli, [string]$vpk, [string]$mapName, [string]$outRoot) {
    $outMapDir = Join-Path $outRoot ("maps\" + $mapName + "\vrf")
    Ensure-Dir $outMapDir
    Write-Info "Scanning VPK for map resources..."
    $listAll = (& $cli -i $vpk --vpk_list) 2>$null
    $vmapCandidates = @()
    $entitiesCandidates = @()
    if ($listAll) {
        $base = $mapName
        if ($mapName.StartsWith('de_')) { $base = $mapName.Substring(3) }
        $namePattern = "(" + [Regex]::Escape($mapName) + "|" + [Regex]::Escape($base) + ")"
        $vmapCandidates = $listAll |
            Where-Object { ($_ -match "^maps/.+\.vmap_c$") -and ($_ -match $namePattern) -and ($_ -notmatch "/worldnodes/") } |
            Sort-Object -Unique
        $entitiesCandidates = $listAll |
            Where-Object { ($_ -match "^maps/.+/entities/.+\.vents_c$") -and ($_ -match $namePattern) } |
            Sort-Object -Unique
    }

    if (-not $vmapCandidates -or $vmapCandidates.Count -eq 0) {
        Write-Warn "No .vmap_c files with '$mapName' in path found in this VPK. Attempting common map paths."
        $base = $mapName
        if ($mapName.StartsWith('de_')) { $base = $mapName.Substring(3) }
        $guesses = @(
            ("maps/" + $mapName + "/" + $mapName + ".vmap_c"),
            ("maps/" + $mapName + "/" + $mapName + "_d.vmap_c"),
            ("maps/" + $base + "/de_" + $base + ".vmap_c"),
            ("maps/" + $base + "/de_" + $base + "_d.vmap_c")
        )
        foreach ($guess in $guesses) {
            try {
                Write-Info ("Trying vmap guess: {0}" -f $guess)
                & $cli -i $vpk --vpk_filepath $guess -o $outMapDir -d | Out-Null
                $vmapCandidates += $guess
            } catch {
                # ignore failures
            }
        }
    } else {
        foreach ($vm in $vmapCandidates) {
            Write-Info ("Decompiling vmap: {0}" -f $vm)
            & $cli -i $vpk --vpk_filepath $vm -o $outMapDir -d | Out-Null
        }
    }

    $entitiesOutRoot = Join-Path $outMapDir "entities"
    Ensure-Dir $entitiesOutRoot
    if ($entitiesCandidates -and $entitiesCandidates.Count -gt 0) {
        Write-Info ("Decompiling {0} entity lump(s)" -f $entitiesCandidates.Count)
        foreach ($ec in $entitiesCandidates) {
            & $cli -i $vpk --vpk_filepath $ec -o $entitiesOutRoot -d | Out-Null
        }
    } else {
        Write-Info "No specific entity lumps found by listing; trying folder heuristic."
        & $cli -i $vpk --vpk_filepath ("maps/" + $mapName + "/entities/") -e "vents_c" -o $entitiesOutRoot -d | Out-Null
    }
    return $outMapDir
}

function Decompile-DirectFiles([string]$cli, [string[]]$files, [string]$mapName, [string]$outRoot) {
    if (-not $files -or $files.Count -eq 0) { return $null }
    $outMapDir = Join-Path $outRoot ("maps\" + $mapName + "\vrf")
    Ensure-Dir $outMapDir
    foreach ($f in $files) {
        if (-not (Test-Path $f)) {
            Write-Warn "Input file not found: $f"
            # Fallback A: common locations within OutRoot for this map
            $candidates = @(
                (Join-Path $outRoot ("maps\" + $mapName + "\vrf\default_ents.vents")),
                (Join-Path $outRoot ("maps\" + $mapName + "\vrf\entities\maps\" + $mapName + "\entities\default_ents.vents"))
            )
            foreach ($candPath in $candidates) {
                if (Test-Path $candPath) { Write-Info ("Using fallback input: {0}" -f $candPath); $f = $candPath; break }
            }
            # Fallback B: search by leaf name anywhere under OutRoot
            if (-not (Test-Path $f)) {
                try {
                    $leaf = Split-Path -Leaf $f
                    $cand = Get-ChildItem -Path (Join-Path $outRoot '*') -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -ieq $leaf } | Select-Object -First 1
                    if ($cand) { Write-Info ("Found fallback input under OutRoot: {0}" -f $cand.FullName); $f = $cand.FullName } else { continue }
                } catch { continue }
            }
        }
        $p = (Resolve-Path $f).Path
        $ext = [System.IO.Path]::GetExtension($p).ToLowerInvariant()
        $isCompiled = $p -match "_c$"
        if ($ext -in @('.vents', '.vmap', '.txt') -and -not $isCompiled) {
            # Already decompiled text; copy for scanning
            $dest = Join-Path $outMapDir (Split-Path -Leaf $p)
            Write-Info ("Copying text resource: {0}" -f $p)
            Copy-Item -LiteralPath $p -Destination $dest -Force
        } else {
            Write-Info ("Decompiling resource file: {0}" -f $p)
            try { & $cli -i $p -o $outMapDir -d | Out-Null } catch { Write-Warn ("Decompile failed for {0}: {1}" -f $p, $_.Exception.Message) }
        }
    }
    return $outMapDir
}

function Parse-CalloutModels([string]$searchRoot) {
    # Robust scanner for decompiled VMAP/VENTS text. Aggregates fields per block.
    $files = Get-ChildItem -Path (Join-Path $searchRoot '*') -Recurse -Include *.vmap,*.vents,*.txt -File -ErrorAction SilentlyContinue
    if (-not $files) { Write-Warn "No text files found under $searchRoot"; return @() }
    $results = New-Object System.Collections.Generic.List[object]

    foreach ($f in $files) {
        $lines = Get-Content -LiteralPath $f.FullName -ErrorAction SilentlyContinue
        if (-not $lines) { continue }

        $curr = @{}
        function Flush-Block() {
            if ($curr.ContainsKey('classname') -and ($curr['classname'] -match '^env_cs_place$') -and $curr.ContainsKey('model')) {
                $obj = [ordered]@{
                    file      = $f.FullName
                    placename = if ($curr.ContainsKey('place_name')) { ($curr['place_name'] -as [string]).Trim() } elseif ($curr.ContainsKey('placename')) { ($curr['placename'] -as [string]).Trim() } else { $null }
                    model     = ($curr['model'] -as [string]).Trim()
                    origin    = if ($curr.ContainsKey('origin')) { $curr['origin'] } else { $null }
                    angles    = if ($curr.ContainsKey('angles')) { $curr['angles'] } else { $null }
                    scales    = if ($curr.ContainsKey('scales')) { $curr['scales'] } elseif ($curr.ContainsKey('scale')) { $curr['scale'] } else { $null }
                }
                $results.Add([pscustomobject]$obj) | Out-Null
            }
            $script:curr = @{}
        }

        foreach ($ln in $lines) {
            if ($ln -match '^=+') { Flush-Block; continue }
            if ($ln -match '^(?:place_name|placename)\s+(.+)$') { $curr['place_name'] = $Matches[1]; continue }
            if ($ln -match '^classname\s+(.+)$') { $curr['classname'] = $Matches[1]; continue }
            if ($ln -match '^model\s+([^\s]+)$') { $curr['model'] = $Matches[1]; continue }
            if ($ln -match '^origin\s+([\-0-9\.]+)\s+([\-0-9\.]+)\s+([\-0-9\.]+)') { $curr['origin'] = @($Matches[1],$Matches[2],$Matches[3]); continue }
            if ($ln -match '^angles\s+([\-0-9\.]+)\s+([\-0-9\.]+)\s+([\-0-9\.]+)') { $curr['angles'] = @($Matches[1],$Matches[2],$Matches[3]); continue }
            if ($ln -match '^scales?\s+([\-0-9\.]+)\s+([\-0-9\.]+)\s+([\-0-9\.]+)') { $curr['scales'] = @($Matches[1],$Matches[2],$Matches[3]); continue }
        }
        Flush-Block
    }

    $res = $results | Where-Object { $_.model -and $_.model -ne "" } | Sort-Object -Property placename, model -Unique
    return $res
}

function Export-Models([string]$cli, [string[]]$vpks, [System.Collections.IEnumerable]$modelPaths, [string]$outDir, [string]$fmt, [string]$fallbackDir) {
    Ensure-Dir $outDir
    $exported = @()
    $missing = @()
    foreach ($m in ($modelPaths | Sort-Object -Unique)) {
        $mp = $m
        # Normalize internal VPK path
        $mp = $mp -replace "\\", "/"
        if ($mp -match "\.vmdl(_c)?$") {
            if (-not ($mp -match "_c$")) { $mp = $mp + "_c" }
        } elseif ($mp -notmatch "\.vmdl_c$") {
            # Some callouts might reference maps/...; keep as is
        }
        Write-Info "Decompiling model: $mp"
        $ok = $false
        foreach ($v in $vpks) {
            try {
                & $cli -i $v --vpk_filepath $mp -o $outDir -d --gltf_export_format $fmt | Out-Null
                $exported += $mp
                $ok = $true
                break
            } catch {
                continue
            }
        }
        if (-not $ok -and $fallbackDir) {
            # Try decompiling from a local decompiled text .vmdl, if present
            $local = Join-Path $fallbackDir ($mp -replace '/', '\')
            $local = [System.IO.Path]::ChangeExtension($local, '.vmdl')
            if (Test-Path $local) {
                try {
                    & $cli -i $local -o $outDir -d --gltf_export_format $fmt | Out-Null
                    $exported += $mp
                    $ok = $true
                } catch {}
            }
        }
        if (-not $ok) { $missing += $mp }
    }
    return @{ Exported = $exported; Missing = $missing }
}

try {
    $cli = Ensure-VrfCli -cliDir $CliDir -explicitUrl $CliUrl -version $CliVersion
    Write-Info "VRF CLI: $cli"

    $pathsToTry = @()
    if ($VpkPaths -and $VpkPaths.Count -gt 0) {
        # If user passed a single long string with commas/semicolons, split it
        if ($VpkPaths.Count -eq 1 -and ($VpkPaths[0] -match ",|;")) {
            $pathsToTry = $VpkPaths[0] -split ",[\s]*|;[\s]*"
        } else {
            $pathsToTry = $VpkPaths
        }
    } elseif ($VpkPath -and $VpkPath -ne "") {
        $pathsToTry = @($VpkPath)
    } else {
        $pathsToTry = @((Resolve-VpkPath $null))
    }

    $allCallouts = @()
    $tried = @()
    
    # First try direct compiled resources if provided (e.g., .vmap_c / .vents_c on disk)
    if ($InputFiles -and $InputFiles.Count -gt 0) {
        $outMapDir = Decompile-DirectFiles -cli $cli -files $InputFiles -mapName $Map -outRoot $OutRoot
        if ($outMapDir) {
            Write-Info "Scanning for env_cs_place entries..."
            $found = Parse-CalloutModels $outMapDir
            if ($found -and $found.Count -gt 0) {
                $allCallouts += $found
            }
        }
    }
    foreach ($path in $pathsToTry) {
        if (-not (Test-Path $path)) { Write-Warn "VPK not found: $path"; continue }
        $vpkResolved = (Resolve-Path $path).Path
        $tried += $vpkResolved
        Write-Info ("Trying VPK: {0}" -f $vpkResolved)
        $outMapDir = Decompile-MapAndEntities -cli $cli -vpk $vpkResolved -mapName $Map -outRoot $OutRoot
        Write-Info "Scanning for env_cs_place entries..."
        $found = Parse-CalloutModels $outMapDir
        if ($found -and $found.Count -gt 0) {
            $allCallouts += $found
            break
        }
    }

    $reportDir = Join-Path $OutRoot ("maps\" + $Map + "\report")
    Ensure-Dir $reportDir
    $calloutsJson = Join-Path $reportDir "callouts_found.json"
    if (-not $allCallouts -or $allCallouts.Count -eq 0) {
        Write-Err "No env_cs_place entries found in decompiled outputs."
        Write-Info ("Tried VPKs: {0}" -f ($tried -join "; "))
        Write-Info "Suggestions:"
        Write-Info " - Add the map VPK(s): ...\\csgo\\maps\\de_<map>.vpk and ...\\csgo\\maps\\de_<map>_d.vpk to -VpkPaths"
        Write-Info " - Pass -InputFiles with explicit .vmap_c and any entities/*.vents_c present"
        Write-Info " - In VRF GUI, Decompile & Export the map, then re-run the script"
        exit 2
    }

    # Deduplicate and export models
    $callouts = $allCallouts | Sort-Object -Property placename, model -Unique
    Write-Info ("Found {0} callout entities with models." -f $callouts.Count)
    $callouts | ConvertTo-Json -Depth 6 | Out-File -Encoding UTF8 $calloutsJson
    Write-Info "Saved callouts report: $calloutsJson"

    $models = $callouts | Where-Object { $_.model } | Select-Object -ExpandProperty model -Unique
    if ($models -and $models.Count -gt 0) {
        $modelsOut = Join-Path $OutRoot "models"
        # Use all tried VPKs and also the outMapDir as a local fallback for .vmdl
        $res = Export-Models -cli $cli -vpks $tried -modelPaths $models -outDir $modelsOut -fmt $GltfFormat -fallbackDir $outMapDir
        $summary = [ordered]@{
            map = $Map
            vpkTried = @($tried)
            modelsRequested = @($models)
            modelsExported  = @($res.Exported)
            modelsMissing   = @($res.Missing)
        }
        $summaryPath = Join-Path $reportDir "models_export_summary.json"
        $summary | ConvertTo-Json -Depth 6 | Out-File -Encoding UTF8 $summaryPath
        Write-Info "Saved model export summary: $summaryPath"
    } else {
        Write-Warn "No model paths detected from callouts; skipping model export."
    }

    Write-Info "Done."
} catch {
    Write-Err $_
    exit 1
}
