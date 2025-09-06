#!/usr/bin/env powershell
<#
.SYNOPSIS
Extract all CS2 active duty maps

.DESCRIPTION
This script will extract callout data for all CS2 active duty maps that are missing.
Requires CS2 VPK files to be available.

.EXAMPLE
.\extract_all_maps.ps1
#>

Write-Host "🗺️ CS2 Active Duty Maps - Extraction Script" -ForegroundColor Cyan
Write-Host "=" * 50

# Check current status
Write-Host "`n📊 Checking current status..." -ForegroundColor Yellow
python -m cs2_callouts status

# Define all active duty maps
$activeDutyMaps = @(
    "de_ancient",
    "de_anubis", 
    "de_dust2",
    "de_inferno",
    "de_mirage",
    "de_nuke",
    "de_overpass",
    "de_vertigo"
)

Write-Host "`n🔄 Starting extraction for all active duty maps..." -ForegroundColor Yellow
Write-Host "⚠️  This requires CS2 VPK files and may take a while!" -ForegroundColor Yellow

$extractedCount = 0
$failedMaps = @()

foreach ($mapName in $activeDutyMaps) {
    $exportPath = "export\maps\$mapName\report\callouts_found.json"
    
    if (Test-Path $exportPath) {
        Write-Host "   ✅ $mapName already extracted" -ForegroundColor Green
        $extractedCount++
    } else {
        Write-Host "   🔄 Extracting $mapName..." -ForegroundColor White
        python -m cs2_callouts extract --map $mapName
        
        if ($LASTEXITCODE -eq 0 -and (Test-Path $exportPath)) {
            Write-Host "   ✅ $mapName extraction complete" -ForegroundColor Green
            $extractedCount++
        } else {
            Write-Host "   ❌ $mapName extraction failed" -ForegroundColor Red
            $failedMaps += $mapName
        }
    }
}

Write-Host "`n📊 Extraction Summary:" -ForegroundColor Yellow
Write-Host "   ✅ Successfully extracted: $extractedCount/$($activeDutyMaps.Count) maps" -ForegroundColor Green

if ($failedMaps.Count -gt 0) {
    Write-Host "   ❌ Failed extractions: $($failedMaps -join ', ')" -ForegroundColor Red
    Write-Host "`n💡 Common issues:" -ForegroundColor Yellow
    Write-Host "   • CS2 VPK files not found or accessible" -ForegroundColor White
    Write-Host "   • VRF CLI not properly setup" -ForegroundColor White
    Write-Host "   • Insufficient disk space" -ForegroundColor White
    Write-Host "`n🔧 Try:" -ForegroundColor Yellow
    Write-Host "   python -m cs2_callouts setup" -ForegroundColor White
    Write-Host "   python -m cs2_callouts check-env" -ForegroundColor White
}

Write-Host "`n📈 Next steps:" -ForegroundColor Yellow
if ($extractedCount -gt 0) {
    Write-Host "   🚀 Process all extracted maps:" -ForegroundColor White
    Write-Host "   python -m cs2_callouts process --map all --global-scale-multiplier 2.0" -ForegroundColor Cyan
    Write-Host "   📊 Check status:" -ForegroundColor White
    Write-Host "   python -m cs2_callouts status" -ForegroundColor Cyan
} else {
    Write-Host "   🔧 Fix extraction issues first" -ForegroundColor White
}

Write-Host "`n🎉 Extraction script complete!" -ForegroundColor Green
