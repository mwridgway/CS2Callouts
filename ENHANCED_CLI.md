# 🚀 Enhanced CLI Process Command

## Overview

The `process` command has been significantly enhanced to provide a complete one-command workflow for CS2 callout processing, extraction, and visualization.

## New Features

### 🔧 Auto-Extract (`--auto-extract`)
- Automatically extracts missing maps before processing
- Requires CS2 VPK files (auto-detected or specify with `--vpk-path`)
- Processes all active duty maps that need extraction
- Shows progress and status for each map

### 🎨 Auto-Visualize (`--auto-visualize`) 
- Automatically generates radar visualizations after processing
- Uses awpy radar images (cross-platform detection)
- Creates both JSON data and PNG radar overlays
- Handles maps without radar images gracefully

### 🌍 Cross-Platform Compatibility
- Automatically detects awpy radar images on Windows, macOS, Linux
- Uses `Path.home() / ".awpy" / "maps" / f"{map_name}.png"`
- Works identically across all operating systems

## Usage Examples

### Complete Workflow (Recommended)
```bash
# Extract, process, and visualize all maps in one command
python -m cs2_callouts process --map all --global-scale-multiplier 2.0 --auto-extract --auto-visualize
```

### Available Maps Only
```bash
# Process and visualize all available maps (no extraction)
python -m cs2_callouts process --map all --global-scale-multiplier 2.0 --auto-visualize
```

### Single Map
```bash
# Process specific map with full automation
python -m cs2_callouts process --map de_dust2 --global-scale-multiplier 2.0 --auto-extract --auto-visualize
```

## Output

### Processing Results
- JSON files: `out/{map_name}_callouts.json`
- Radar images: `out/{map_name}_radar.png`
- Detailed progress and status reporting
- File size information for generated outputs

### Example Output
```
🔄 Processing 8 available maps...
🔄 Processing de_dust2...
✅ Wrote out\de_dust2_callouts.json with 43 callouts. Rotation order: rz_rx_ry
🎨 Auto-generating visualization for de_dust2...
📡 Using radar image: C:\Users\user\.awpy\maps\de_dust2.png
Using map metadata for de_dust2: scale=4.4, pos_x=-2476, pos_y=3239
Transformed to pixel coords: X=97.2 to 949.4, Y=67.1 to 952.6
Saved out\de_dust2_radar.png
✅ Generated radar visualization: out\de_dust2_radar.png

🎯 Processing complete:
   ✅ Successfully processed: 8/8 maps
   🎨 Visualizations generated: 8 radar overlays

📁 Generated files:
   📄 de_dust2_callouts.json (119.6 KB)
   🎨 de_dust2_radar.png (574.8 KB)
```

## Technical Implementation

### Enhanced Functions
- `_process_single_map_enhanced()`: Handles single map with auto-extract and auto-visualize
- `_process_all_maps_enhanced()`: Handles all maps with enhanced workflow
- `_get_radar_path()`: Cross-platform awpy radar image detection

### Integration
- Seamlessly integrates with existing CLI structure
- Backward compatible with original process command
- Uses existing visualization and extraction commands via `ctx.invoke()`

## Benefits

1. **One Command Workflow**: Extract, process, and visualize in a single command
2. **Cross-Platform**: Works identically on Windows, macOS, and Linux
3. **Intelligent Detection**: Auto-finds awpy radar images and CS2 VPK files
4. **Progress Reporting**: Clear status and progress information
5. **Error Handling**: Graceful handling of missing files or failed operations
6. **Flexible**: Can be used for single maps or all maps
7. **Efficient**: Avoids duplicate work and provides comprehensive output

## Migration from Old Workflow

### Before (Multi-step)
```bash
python -m cs2_callouts extract --map de_dust2
python -m cs2_callouts process --map de_dust2 --global-scale-multiplier 2.0
python -m cs2_callouts visualize --json out/de_dust2_callouts.json --radar ~/.awpy/maps/de_dust2.png --out out/de_dust2_radar.png
```

### After (One command)
```bash
python -m cs2_callouts process --map de_dust2 --global-scale-multiplier 2.0 --auto-extract --auto-visualize
```

This represents a significant improvement in user experience and workflow efficiency while maintaining all existing functionality.
