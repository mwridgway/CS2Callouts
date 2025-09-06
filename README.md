# CS2 Callout Polygon Extraction

## Overview

- Extracts `env_cs_place` callout entities from a CS2 map using ValveResourceFormat (VRF) CLI
- Exports referenced `.vmdl` models to GLB/GLTF format
- Transforms local-space vertices into world-space, projects to 2D, and outputs JSON polygons

## Prerequisites

- **Windows PowerShell** (script tested on Windows)
- **VRF CLI** - auto-downloaded by the script (or place it under `tools/vrf-cli`)
- **Python 3.10+** with dependencies: `numpy`, `trimesh`, `click`, `matplotlib`

## Quick Start

### 1. Extract Map Data

Decompile map + entities and export models (writes under `export/`):

```powershell
powershell -ExecutionPolicy Bypass -File vrf_extract_callout_models.ps1 -Map de_mirage
```

**Useful flags:**
- `-VpkPath` or `-VpkPaths` - point at CS2 VPKs
- `-InputFiles` - pass specific `.vmap_c` / `entities/*.vents_c`
- `-GltfFormat glb|gltf` - choose output format

### 2. Generate Polygon Data

Build callout polygons JSON:

```bash
python -m cs2_callouts.cli --map de_mirage
```

**Options:**
- `--callouts-json` - Path to `callouts_found.json` (defaults under `export/maps/<map>/report/`)
- `--models-root` - Root for exported models (default `export/models`)
- `--out` - Output JSON path (default `out/<map>_callouts.json`)
- `--rotation-order` - `auto|rz_rx_ry|ry_rx_rz|rz_ry_rx` (default `auto`)

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

1. **Automated Tool Download** - The script automatically downloads ValveResourceFormat CLI instead of requiring manual installation
2. **Entity File Discovery** - Had to implement recursive search to find entity files in deeply nested directory structures  
3. **Format Changes** - CS2 uses GLB/GLTF for model export instead of parsing raw `.vmdl` DMX text files
4. **Vertex Processing** - Uses trimesh library to load vertices from GLB files rather than manual DMX parsing
5. **Multiple Rotation Orders** - Discovered that different maps may use different Euler angle rotation orders, requiring auto-detection

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

## 🧹 Cleanup

Remove generated outputs (`export/`, `out/`, caches):

```powershell
# Preview changes
./clean_outputs.ps1 -WhatIf

# Execute cleanup
./clean_outputs.ps1 -Confirm:$false

# Also remove downloaded tools (VRF CLI) for pristine tree
./clean_outputs.ps1 -IncludeTools -Confirm:$false
```
