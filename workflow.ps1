#!/usr/bin/env powershell
<#
.SYNOPSIS
Complete workflow to clean, process, and visualize CS2 callout data

.DESCRIPTION
This script provides a step-by-step workflow to:
1. Clean previous outputs
2. Process callout data with different scale multipliers
3. Generate visualizations
4. Compare results

.EXAMPLE
.\workflow.ps1
#>

Write-Host "🧹 CS2 Callouts - Complete Workflow" -ForegroundColor Cyan
Write-Host "=" * 50

# Step 1: Clean previous outputs
Write-Host "`n📂 Step 1: Cleaning previous outputs..." -ForegroundColor Yellow
if (Test-Path "out") {
    Remove-Item "out\*" -Force -Recurse -ErrorAction SilentlyContinue
    Write-Host "   ✅ Cleaned out/ directory" -ForegroundColor Green
} else {
    New-Item -ItemType Directory -Path "out" -Force | Out-Null
    Write-Host "   ✅ Created out/ directory" -ForegroundColor Green
}

# Step 2: Process callouts with different scale multipliers
Write-Host "`n⚙️  Step 2: Processing all available maps with different scale multipliers..." -ForegroundColor Yellow

Write-Host "   🔄 Processing all maps with 1.0x scale (original)..." -ForegroundColor White
python -m cs2_callouts process --map all --global-scale-multiplier 1.0
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ 1.0x scale complete" -ForegroundColor Green
} else {
    Write-Host "   ❌ 1.0x scale failed" -ForegroundColor Red
}

Write-Host "   🔄 Processing all maps with 2.0x scale..." -ForegroundColor White
python -m cs2_callouts process --map all --global-scale-multiplier 2.0
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ 2.0x scale complete" -ForegroundColor Green
} else {
    Write-Host "   ❌ 2.0x scale failed" -ForegroundColor Red
}

Write-Host "   🔄 Processing all maps with 3.0x scale..." -ForegroundColor White
python -m cs2_callouts process --map all --global-scale-multiplier 3.0
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ 3.0x scale complete" -ForegroundColor Green
} else {
    Write-Host "   ❌ 3.0x scale failed" -ForegroundColor Red
}

# Step 3: Generate visualizations
Write-Host "`n📊 Step 3: Generating visualizations for all processed maps..." -ForegroundColor Yellow

# Find all processed map files
$jsonFiles = Get-ChildItem "out" -Filter "*_callouts.json" | Where-Object { $_.Name -match "^(.+)_callouts\.json$" }

if ($jsonFiles.Count -eq 0) {
    Write-Host "   ⚠️  No processed map files found in out/ directory" -ForegroundColor Yellow
} else {
    Write-Host "   📁 Found $($jsonFiles.Count) processed map files" -ForegroundColor White
    
    foreach ($jsonFile in $jsonFiles) {
        # Extract map name from filename (e.g., "de_mirage_callouts.json" -> "de_mirage")
        if ($jsonFile.Name -match "^(.+)_callouts\.json$") {
            $mapName = $matches[1]
            $radarPath = "$env:USERPROFILE\.awpy\maps\$mapName.png"
            
            Write-Host "   🎨 Processing visualizations for $mapName..." -ForegroundColor White
            
            # Basic visualization without radar
            $basicOutput = "out\$($mapName)_visualization.png"
            python -m cs2_callouts visualize --json $jsonFile.FullName --out $basicOutput
            if ($LASTEXITCODE -eq 0) {
                Write-Host "   ✅ $mapName basic visualization complete" -ForegroundColor Green
            } else {
                Write-Host "   ❌ $mapName basic visualization failed" -ForegroundColor Red
            }
            
            # Radar overlay visualization if radar exists
            if (Test-Path $radarPath) {
                Write-Host "   🗺️  Creating radar overlay for $mapName..." -ForegroundColor White
                $radarOutput = "out\$($mapName)_radar_overlay.png"
                python -m cs2_callouts visualize --json $jsonFile.FullName --radar $radarPath --out $radarOutput
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "   ✅ $mapName radar overlay complete" -ForegroundColor Green
                } else {
                    Write-Host "   ❌ $mapName radar overlay failed" -ForegroundColor Red
                }
            } else {
                Write-Host "   ⚠️  No radar image found for $mapName at $radarPath" -ForegroundColor Yellow
            }
        }
    }
}

# Step 4: Generate comparison data
Write-Host "`n📈 Step 4: Generating comparison data..." -ForegroundColor Yellow
python debug\compare_scaling_results.py
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ Comparison data generated" -ForegroundColor Green
} else {
    Write-Host "   ❌ Comparison data failed" -ForegroundColor Red
}

# Step 5: Summary
Write-Host "`n📋 Step 5: Results Summary" -ForegroundColor Yellow
Write-Host "   Generated files:" -ForegroundColor White

Get-ChildItem "out" -Filter "*.json" | ForEach-Object {
    $size = [math]::Round($_.Length / 1KB, 1)
    Write-Host "   📄 $($_.Name) ($size KB)" -ForegroundColor Cyan
}

Get-ChildItem "out" -Filter "*.png" | ForEach-Object {
    $size = [math]::Round($_.Length / 1KB, 1)
    Write-Host "   🖼️  $($_.Name) ($size KB)" -ForegroundColor Magenta
}

Write-Host "`n🎉 Workflow complete! Check the out/ directory for results." -ForegroundColor Green
Write-Host "   💡 Tip: Open PNG files to compare different scale multipliers" -ForegroundColor White
