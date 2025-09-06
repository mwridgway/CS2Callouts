# CS2 Callout Polygon Extraction

## Overview

- Extracts `env_cs_place` callout entities from a CS2 map using ValveResourceFormat (VRF) CLI
- Exports referenced `.vmdl` models to GLB/GLTF format
- Transforms local-space vertices into world-space, projects to 2D, and outputs JSON polygons

## Prerequisites

- **Python 3.10+** with dependencies: `numpy`, `trimesh`, `click`, `matplotlib`, `requests`
- **VRF CLI** - auto-downloaded by the tool (no manual setup required)
- **CS2 Installation** - for VPK file access (auto-detected)

## Quick Start

### Option 1: Complete Pipeline (Recommended)

Run the entire extraction and processing pipeline with a single command:

```bash
# Install the package
pip install -e .

# Run complete pipeline for a map
cs2-callouts pipeline --map de_mirage

# Or without installation
python -m cs2_callouts pipeline --map de_mirage
```

### Option 2: Step-by-Step Process

#### Step 1: Extract Map Data

```bash
# Extract callout entities and models
python -m cs2_callouts extract --map de_mirage

# With specific VPK path
python -m cs2_callouts extract --map de_mirage --vpk-path "C:\Path\To\pak01_dir.vpk"
```

#### Step 2: Generate Polygon Data

```bash
# Process extracted data into 2D polygons
python -m cs2_callouts process --map de_mirage
```

### Option 3: Legacy PowerShell Scripts (Archived)

PowerShell scripts have been moved to the `archive/` folder and are **deprecated**:

```powershell
# DEPRECATED - Use Python versions instead
cd archive
powershell -ExecutionPolicy Bypass -File vrf_extract_callout_models.ps1 -Map de_mirage
cd ..
python -m cs2_callouts process --map de_mirage
```

**⚠️ Recommendation**: Use the Python pipeline command instead for better cross-platform support and enhanced features.

## Utility Commands

The Python CLI includes several utility commands for project management:

```bash
# Setup required tools
cs2-callouts setup

# Clean generated files and caches
cs2-callouts clean --dry-run              # Preview what will be removed
cs2-callouts clean                        # Remove export/, out/, caches
cs2-callouts clean --include-tools        # Also remove tools/

# Check environment variables
cs2-callouts check-env                    # Check default variables
cs2-callouts check-env --names VAR1 VAR2  # Check specific variables

# Run complete pipeline for a map
cs2-callouts run-map --map de_dust2       # Equivalent to old run_map.ps1
```

## Installation (Optional)

For convenient command-line access:

```bash
pip install -e .
```

Then run:
```bash
cs2-callouts --map de_mirage
```

## Key Features

- The pipeline prefers `*_physics.glb` meshes when present, which typically contain solid geometry
- `callouts_found.json` may be encoded with UTF‑8 BOM when produced by some tools; the reader tolerates this
- Automatic rotation order detection for proper geometry transformation

## Visualization

Generate overlay PNG (with optional radar underlay):

```bash
# Basic overlay
python -m cs2_callouts.visualize --json out/de_mirage_callouts.json --out out/de_mirage_overlay.png

# With radar background
python -m cs2_callouts.visualize --json out/de_mirage_callouts.json --radar path/to/radar.png --out out/de_mirage_overlay.png
```

**Visualization Options:**
- `--invert-y/--no-invert-y` - match radar pixel coordinates
- `--labels/--no-labels` - toggle callout names
- `--alpha` and `--linewidth` - styling options
- Console script alias after install: `cs2-callouts-viz ...`

## Implementation Notes & Deviations

### 🔍 Key Discovery: Entity Location

The original assumption was that `env_cs_place` entities would be found in the main `.vmap` file. However, in CS2 these entities are actually located in separate entity lump files (`.vents_c`) within a nested directory structure:

```
export/maps/<map>/vrf/entities/maps/<map>/entities/default_ents.vents
```

### 📋 Major Deviations from Original Plan

1. **Unified Python Implementation** - Converted PowerShell extraction script to Python for cross-platform compatibility
2. **Complete Script Migration** - All PowerShell utility scripts converted to Python CLI commands
3. **Automated Tool Download** - The tool automatically downloads ValveResourceFormat CLI instead of requiring manual installation  
4. **Entity File Discovery** - Had to implement recursive search to find entity files in deeply nested directory structures
5. **Format Changes** - CS2 uses GLB/GLTF for model export instead of parsing raw `.vmdl` DMX text files
6. **Vertex Processing** - Uses trimesh library to load vertices from GLB files rather than manual DMX parsing
7. **Multiple Rotation Orders** - Discovered that different maps may use different Euler angle rotation orders, requiring auto-detection
8. **Cross-Platform Support** - Python implementation works on Windows, Linux, and macOS

> **Migration Note**: All PowerShell scripts (`.ps1`) have been converted to Python CLI commands and moved to the `archive/` folder. See [MIGRATION.md](MIGRATION.md) for detailed conversion guide. Archived scripts are deprecated and will be removed in a future version.

### ✅ Current Status vs Original 4-Phase Plan

| Phase | Status | Implementation | Key Changes |
|-------|--------|----------------|-------------|
| **Phase 1: Asset Decompilation** | ✅ Complete | Automated PowerShell script | Auto-downloads VRF CLI |
| **Phase 2: Entity Parsing** | ✅ Complete | Successfully extracts `env_cs_place` entities from `.vents` files | Found entities in nested structure |
| **Phase 3: Geometric Extraction** | ✅ Complete | Uses modern GLB format instead of raw `.vmdl` parsing | Modern format vs raw DMX |
| **Phase 4: World Transformation** | ✅ Complete | Complete SRT pipeline with automatic rotation order detection | Handles multiple rotation orders |

### 📊 Validation Results

- Successfully extracted **23 callout entities** from de_mirage
- Generated precise 2D polygon coordinates for all callouts
- **Zero missing models** in final output
- Ready for radar overlay validation

## 🎓 Skills & Knowledge Required

To build a similar tool from scratch, a developer would need expertise across multiple domains:

### **Game Development & Reverse Engineering**
- Understanding of Source 2 engine architecture and file formats
- Knowledge of Valve's proprietary formats (VPK, DMX, KeyValues)
- Experience with game asset extraction and decompilation
- Familiarity with 3D model formats (VMDL, GLB, GLTF)

### **3D Mathematics & Computer Graphics**
- Linear algebra: vectors, matrices, transformations
- 3D coordinate systems and space conversions
- Euler angles and rotation order conventions
- Geometric algorithms (convex hull, polygon projection)
- Understanding of Scale-Rotation-Translation (SRT) pipelines

### **Programming Languages & Tools**
- **PowerShell** - Advanced scripting, parameter handling, error management
- **Python** - Object-oriented programming, data structures, file I/O
- **JSON/XML parsing** - Structured data manipulation
- **Regular expressions** - Text pattern matching and extraction

### **Libraries & Frameworks**
- **NumPy** - Numerical computing and array operations
- **Trimesh** - 3D mesh processing and manipulation
- **Click** - Command-line interface development
- **Matplotlib** - Data visualization and plotting

### **System Administration**
- File system navigation and path manipulation
- Process management and external tool integration
- Archive handling and compression formats
- Cross-platform compatibility considerations

### **Debugging & Problem Solving**
- Systematic troubleshooting methodology
- Understanding of nested data structures
- Experience with binary and text file formats
- Ability to reverse-engineer undocumented formats

### **Domain-Specific Knowledge**
- Counter-Strike map structure and conventions
- Game engine entity systems and hierarchies
- 3D rendering pipelines and coordinate transformations
- Understanding of game development workflows

This project represents the intersection of **game reverse engineering**, **3D mathematics**, **data processing**, and **system integration** - requiring both broad technical knowledge and deep domain expertise.

## 📁 Project Structure

```
CS2Callouts/
├── cs2_callouts/           # Main Python package
├── archive/                # Deprecated PowerShell scripts (will be removed)
├── out/                    # Generated polygon JSON files
├── export/                 # Extracted VPK data and models
├── tools/                  # Auto-downloaded VRF CLI
└── README.md              # This file
```

> **Note**: The `archive/` folder contains deprecated PowerShell scripts that will be removed in a future version. All functionality has been migrated to Python CLI commands.

## 🧹 Cleanup

Remove generated outputs, caches, and tools using the Python CLI:

```bash
# Preview what would be removed (includes tools by default)
cs2-callouts clean --dry-run

# Remove all generated files (export/, out/, caches, tools/)
cs2-callouts clean

# Keep tools if you want to avoid re-downloading VRF CLI
cs2-callouts clean --exclude-tools

# Keep caches if you want faster Python imports
cs2-callouts clean --exclude-caches
```

> **Note**: Tools are removed by default since they're automatically downloaded when needed.

# Legacy PowerShell method (archived in archive/ folder)
cd archive && ./clean_outputs.ps1 -WhatIf && cd ..              # Preview
cd archive && ./clean_outputs.ps1 -Confirm:$false && cd ..      # Execute
```
