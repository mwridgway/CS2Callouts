# CS2 Callouts - Command Reference (Cross-Platform)

All commands work on **Windows, macOS, and Linux** using Python scripts instead of PowerShell.

## Quick Commands

### 🔍 Check status of all active duty maps
```bash
python -m cs2_callouts status
```

### 🧹 Clean outputs
```bash
python clean.py
```

### ⚙️ Process callouts
```bash
# Process all available active duty maps (default)
python -m cs2_callouts process --global-scale-multiplier 2.0

# Check which maps are available first
python -m cs2_callouts status

# Process specific map only
python -m cs2_callouts process --map de_mirage --global-scale-multiplier 2.0

# Extract missing maps first (requires CS2 VPK files)
python -m cs2_callouts extract --map de_dust2
python -m cs2_callouts extract --map de_inferno
```

### 📊 Visualize results
```bash
# Basic visualization (polygons only)
python -m cs2_callouts visualize --json out/de_mirage_callouts.json --out out/visualization.png

# With radar overlay (cross-platform path detection)
python -c "from pathlib import Path; print(Path.home() / '.awpy' / 'maps' / 'de_mirage.png')"
python -m cs2_callouts visualize --json out/de_mirage_callouts.json --radar [PATH_FROM_ABOVE] --out out/radar_overlay.png

# With custom settings
python -m cs2_callouts visualize --json out/de_mirage_callouts.json --radar [RADAR_PATH] --out out/viz.png --alpha 0.5 --min-size 5.0 --linewidth 2.0
```

### 🔍 Debug and analyze
```bash
# Compare scaling results
python debug/compare_scaling_results.py

# Verify coordinates
python debug/verify_fixed_coordinates.py

# Check physics properties
python debug/verify_3d_data.py
```

## ✨ Enhanced CLI Features

The `process` command now includes powerful automation:

- **`--auto-extract`**: Automatically extracts missing maps before processing (requires CS2 VPK files)
- **`--auto-visualize`**: Automatically generates radar visualizations after processing using awpy radar images
- **Cross-platform radar detection**: Automatically finds awpy radar images on Windows, macOS, and Linux
- **Intelligent workflow**: Combines extraction, processing, and visualization in a single command

### Quick Examples:
```bash
# Process with auto-visualization (most common)
python -m cs2_callouts process --map all --auto-visualize

# Full automation (extract + process + visualize)
python -m cs2_callouts process --map all --auto-extract --auto-visualize

# Single map with full automation
python -m cs2_callouts process --map de_dust2 --auto-extract --auto-visualize
```

## 🚀 Complete Workflow

### Option 1: One-command workflow (RECOMMENDED) 
```bash
# Complete extract + process + visualize for all maps with auto-detection
python -m cs2_callouts process --map all --global-scale-multiplier 2.0 --auto-extract --auto-visualize
```

### Option 2: Simple demo (recommended for testing available maps)
```bash
# Complete workflow for available maps - works on any platform
python demo.py
```

### Option 3: Process all available maps with visualization
```bash
# Process and visualize all available maps (no extraction)
python -m cs2_callouts process --map all --global-scale-multiplier 2.0 --auto-visualize
```

### Option 4: Step-by-step workflow  
```bash
# Step 1: Check what's available
python -m cs2_callouts status

# Step 2: Extract missing maps (requires CS2 VPK files)
python extract_all_maps.py

# Step 3: Process all maps with visualization
python -m cs2_callouts process --map all --global-scale-multiplier 2.0 --auto-visualize

# Step 4: Check final status
python -m cs2_callouts status
```

### Option 5: Full automated processing script
```bash
# Processes all available maps with multiple scales and generates visualizations
python workflow.py
```

### Option 6: Single map workflow
```bash
# Process specific map with auto-extraction and visualization
python -m cs2_callouts process --map de_dust2 --global-scale-multiplier 2.0 --auto-extract --auto-visualize
```

## 📁 Expected Output Files

After running the workflow, you should have:

```
out/
├── de_mirage_callouts.json         # Original scale data
├── de_mirage_callouts_2x.json      # 2x scale data  
├── de_mirage_callouts_3x.json      # 3x scale data
├── de_mirage_visualization.png     # Basic visualization
├── de_mirage_radar_overlay.png     # Radar overlay (meaningful!)
└── (similar files for other maps)
```

## 🎯 Key Features

- **Cross-Platform**: Works on Windows, macOS, and Linux
- **CS2 Active Duty Maps**: Supports all 8 current active duty maps:
  - de_ancient, de_anubis, de_dust2, de_inferno, de_mirage, de_nuke, de_overpass, de_vertigo
- **Individual Physics Properties**: Each callout has unique global_scale dimensions
- **Global Scale Multiplier**: Uniform scaling while preserving proportions
- **Fixed Coordinate System**: Proper transformation to radar/pixel coordinates
- **Visual Comparison**: PNG outputs for easy comparison of different scales
- **Multi-Map Processing**: Process all maps at once or individually

## 🔧 Troubleshooting

### Common Issues:
1. **"No callout data"** - Run the processing step first
2. **"Coordinate outside bounds"** - Fixed in latest version
3. **"Double transformation"** - Fixed in latest version
4. **Missing radar image** - Visualizations work without radar overlay

### Verify Installation:
```bash
python -m cs2_callouts --help
python -c "import numpy, matplotlib, click; print('✅ Dependencies OK')"
```

### Platform-Specific Notes:
- **Windows**: Use `%USERPROFILE%\.awpy\maps\` for radar paths
- **Linux/macOS**: Use `~/.awpy/maps/` for radar paths
- **All platforms**: Python scripts work the same way
