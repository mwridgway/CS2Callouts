from __future__ import annotations

import sys
from pathlib import Path

import click

from .pipeline import process_callouts, read_callouts_json, write_json


@click.group()
def cli():
    """CS2 Callout Polygon Extraction Tool"""
    pass


@cli.command()
@click.option("--vpk-path", default="", help="Path to CS2 VPK file")
@click.option("--map", "map_name", default="de_mirage", help="Map name")
@click.option("--out-root", default="export", help="Output root directory")
@click.option("--gltf-format", type=click.Choice(["glb", "gltf"]), default="glb", help="GLTF export format")
def extract(vpk_path: str, map_name: str, out_root: str, gltf_format: str):
    """Extract callout entities and models from CS2 VPK files."""
    from .extract import (
        ensure_vrf_cli, resolve_vpk_paths, decompile_map_and_entities_from_multiple_vpks,
        parse_callout_models, export_models, ensure_dir, info, error
    )
    from pathlib import Path
    import json
    
    try:
        # Setup paths
        out_root_path = Path(out_root).resolve()
        cli_dir_path = Path("tools/vrf-cli").resolve()
        
        # Ensure VRF CLI
        cli_path = ensure_vrf_cli(cli_dir_path)
        info(f"VRF CLI: {cli_path}")
        
        # Resolve VPK paths (including map-specific VPKs)
        if vpk_path:
            vpk_paths = [vpk_path]
        else:
            vpk_paths = resolve_vpk_paths(map_name=map_name)
        
        info(f"Using VPKs: {[Path(vpk).name for vpk in vpk_paths]}")
        
        # Decompile and extract from multiple VPKs
        out_map_dir = decompile_map_and_entities_from_multiple_vpks(cli_path, vpk_paths, map_name, out_root_path)
        callouts = parse_callout_models(out_map_dir)
        
        if not callouts:
            error("No env_cs_place entries found")
            return 1
        
        # Save callouts
        report_dir = out_root_path / "maps" / map_name / "report"
        ensure_dir(report_dir)
        callouts_json = report_dir / "callouts_found.json"
        
        with open(callouts_json, 'w', encoding='utf-8') as f:
            json.dump(callouts, f, indent=2, ensure_ascii=False)
        info(f"Saved {len(callouts)} callouts to {callouts_json}")
        
        # Export models
        model_paths = [c['model'] for c in callouts if c.get('model')]
        if model_paths:
            models_out = out_root_path / "models"
            result = export_models(cli_path, vpk_paths, model_paths, models_out, gltf_format, out_map_dir)
            info(f"Exported {len(result['exported'])} models")
        
        info("Extraction complete!")
        
    except Exception as e:
        error(str(e))
        return 1


@cli.command()
@click.option("--map", "map_name", default="all", show_default=True, help="Map name to process, or 'all' to process all available maps.")
@click.option("--callouts-json", "callouts_json", type=click.Path(exists=True), default=None, help="Path to callouts_found.json from the extraction step (only used for single map).")
@click.option("--models-root", type=click.Path(exists=True, file_okay=False), default="export/models", show_default=True, help="Root folder containing exported GLB/GLTF models.")
@click.option("--out", "out_path", type=click.Path(), default=None, help="Output JSON path (only used for single map).")
@click.option("--rotation-order", type=click.Choice(["auto", "rz_rx_ry", "ry_rx_rz", "rz_ry_rx"], case_sensitive=False), default="auto", show_default=True)
@click.option("--projection", "projection_method", type=click.Choice(["top_down", "alpha_shape", "convex_hull"], case_sensitive=False), default="top_down", show_default=True, help="2D projection method for radar visualization.")
@click.option("--global-scale-multiplier", "global_scale_multiplier", type=float, default=1.0, show_default=True, help="Global multiplier applied to all polygon dimensions (e.g., 2.0 for 2x scaling).")
@click.option("--auto-extract", is_flag=True, default=False, help="Automatically extract missing maps before processing (requires CS2 VPK files).")
@click.option("--auto-visualize", is_flag=True, default=False, help="Automatically generate radar visualizations after processing using awpy radar images.")
@click.option("--vpk-path", default="", help="Path to CS2 VPK file for auto-extraction (auto-detected if not provided).")
def process(map_name: str, callouts_json: str | None, models_root: str, out_path: str | None, rotation_order: str, projection_method: str, global_scale_multiplier: float, auto_extract: bool, auto_visualize: bool, vpk_path: str):
    """Process extracted callouts into 2D polygon data with optional extraction and visualization."""
    
    if map_name.lower() == "all":
        # Process all available maps with enhanced functionality
        _process_all_maps_enhanced(models_root, rotation_order, projection_method, global_scale_multiplier, auto_extract, auto_visualize, vpk_path)
    else:
        # Process single map with enhanced functionality  
        _process_single_map_enhanced(map_name, callouts_json, models_root, out_path, rotation_order, projection_method, global_scale_multiplier, auto_extract, auto_visualize, vpk_path)


def _get_radar_path(map_name: str) -> Path | None:
    """Get the awpy radar image path for a map (cross-platform)"""
    home = Path.home()
    radar_path = home / ".awpy" / "maps" / f"{map_name}.png"
    return radar_path if radar_path.exists() else None


def _get_active_duty_maps() -> list[str]:
    """Get the list of CS2 active duty maps"""
    return [
        "de_ancient",
        "de_anubis", 
        "de_dust2",
        "de_inferno",
        "de_mirage",
        "de_nuke",
        "de_overpass",
        "de_vertigo"
    ]


def _discover_available_maps(models_root: str) -> list[str]:
    """Discover all available maps by looking for callouts_found.json files"""
    export_path = Path("export/maps")
    available_maps = []
    
    if export_path.exists():
        for map_dir in export_path.iterdir():
            if map_dir.is_dir():
                callouts_file = map_dir / "report" / "callouts_found.json"
                if callouts_file.exists():
                    available_maps.append(map_dir.name)
    
    return sorted(available_maps)


def _discover_maps_to_process() -> tuple[list[str], list[str]]:
    """
    Discover which maps should be processed and which need extraction.
    Returns: (available_maps, missing_maps)
    """
    active_duty_maps = _get_active_duty_maps()
    available_maps = _discover_available_maps("export/models")
    
    # Find which active duty maps are available vs missing
    available_active_duty = [m for m in active_duty_maps if m in available_maps]
    missing_active_duty = [m for m in active_duty_maps if m not in available_maps]
    
    return available_active_duty, missing_active_duty


def _process_single_map_enhanced(map_name: str, callouts_json: str | None, models_root: str, out_path: str | None, rotation_order: str, projection_method: str, global_scale_multiplier: float, auto_extract: bool, auto_visualize: bool, vpk_path: str):
    """Enhanced single map processing with auto-extraction and auto-visualization"""
    
    # Step 1: Auto-extract if needed and requested
    if auto_extract:
        callouts_file = Path("export") / "maps" / map_name / "report" / "callouts_found.json"
        if not callouts_file.exists():
            click.echo(f"🔄 Auto-extracting {map_name}...")
            ctx = click.get_current_context()
            try:
                result = ctx.invoke(extract, vpk_path=vpk_path, map_name=map_name, out_root="export", gltf_format="glb")
                if result and result != 0:
                    click.echo(f"❌ Auto-extraction failed for {map_name}")
                    return False
            except Exception as e:
                click.echo(f"❌ Auto-extraction failed for {map_name}: {e}")
                return False
    
    # Step 2: Process the map using the legacy function
    if callouts_json is None:
        callouts_json = str(Path("export") / "maps" / map_name / "report" / "callouts_found.json")
    if out_path is None:
        out_path = str(Path("out") / f"{map_name}_callouts.json")

    if not Path(callouts_json).exists():
        click.echo(f"❌ No callouts file found for {map_name}: {callouts_json}", err=True)
        return False

    callouts = read_callouts_json(callouts_json)
    if not callouts:
        click.echo(f"❌ No callouts found in {callouts_json}", err=True)
        return False

    click.echo(f"🔄 Processing {map_name}...")
    data = process_callouts(callouts, models_root=models_root, rotation_order=rotation_order, projection_method=projection_method, global_scale_multiplier=global_scale_multiplier)
    write_json(data, out_path, pretty=True)
    click.echo(f"✅ Wrote {out_path} with {data['count']} callouts. Rotation order: {data['rotation_order']}")
    if data.get("missing_models"):
        click.echo(f"⚠️  Missing models: {len(data['missing_models'])}")
    
    # Step 3: Auto-visualize if requested
    if auto_visualize:
        click.echo(f"🎨 Auto-generating visualization for {map_name}...")
        
        json_path = Path(out_path)
        
        # Try to find radar image
        radar_path = _get_radar_path(map_name)
        
        # Generate visualization
        viz_path = json_path.parent / f"{map_name}_radar.png"
        
        ctx = click.get_current_context()
        try:
            if radar_path and radar_path.exists():
                click.echo(f"📡 Using radar image: {radar_path}")
                ctx.invoke(visualize, json_path=str(json_path), radar=str(radar_path), map_data=None, out_path=str(viz_path), labels=True, invert_y=False, alpha=0.35, linewidth=1.0, min_size=3.0)
                click.echo(f"✅ Generated radar visualization: {viz_path}")
            else:
                click.echo(f"⚠️  No radar image found for {map_name}, generating basic visualization...")
                basic_viz_path = json_path.parent / f"{map_name}_basic.png"
                ctx.invoke(visualize, json_path=str(json_path), radar=None, map_data=None, out_path=str(basic_viz_path), labels=True, invert_y=False, alpha=0.35, linewidth=1.0, min_size=3.0)
                click.echo(f"✅ Generated basic visualization: {basic_viz_path}")
        except Exception as e:
            click.echo(f"⚠️  Visualization failed for {map_name}: {e}")
    
    return True


def _process_all_maps_enhanced(models_root: str, rotation_order: str, projection_method: str, global_scale_multiplier: float, auto_extract: bool, auto_visualize: bool, vpk_path: str):
    """Enhanced processing for all maps with auto-extraction and auto-visualization"""
    
    if auto_extract:
        # Try to extract all missing active duty maps
        click.echo("🔄 Auto-extracting missing maps...")
        active_duty_maps = _get_active_duty_maps()
        extracted_count = 0
        
        for map_name in active_duty_maps:
            callouts_file = Path("export") / "maps" / map_name / "report" / "callouts_found.json"
            if not callouts_file.exists():
                click.echo(f"   Extracting {map_name}...")
                ctx = click.get_current_context()
                try:
                    result = ctx.invoke(extract, vpk_path=vpk_path, map_name=map_name, out_root="export", gltf_format="glb")
                    if not result or result == 0:
                        extracted_count += 1
                        click.echo(f"   ✅ {map_name}")
                    else:
                        click.echo(f"   ❌ {map_name} (failed)")
                except Exception as e:
                    click.echo(f"   ❌ {map_name} (error: {e})")
        
        if extracted_count > 0:
            click.echo(f"✅ Auto-extracted {extracted_count} maps")
        else:
            click.echo("ℹ️  No maps needed extraction")
    
    # Process available maps
    available_maps, missing_maps = _discover_maps_to_process()
    
    if not available_maps:
        click.echo("❌ No maps available for processing after auto-extraction")
        if missing_maps:
            click.echo("⚠️  The following maps still need extraction:")
            for map_name in missing_maps:
                click.echo(f"   • {map_name}")
        return
    
    click.echo(f"🔄 Processing {len(available_maps)} available maps...")
    
    # Ensure output directory exists
    Path("out").mkdir(exist_ok=True)
    
    success_count = 0
    failed_maps = []
    visualization_count = 0
    
    for map_name in available_maps:
        success = _process_single_map_enhanced(
            map_name=map_name,
            callouts_json=None,  # Use default path
            models_root=models_root,
            out_path=None,  # Use default path
            rotation_order=rotation_order,
            projection_method=projection_method,
            global_scale_multiplier=global_scale_multiplier,
            auto_extract=False,  # Already handled above
            auto_visualize=auto_visualize,
            vpk_path=vpk_path
        )
        
        if success:
            success_count += 1
            if auto_visualize:
                visualization_count += 1
        else:
            failed_maps.append(map_name)
    
    # Summary
    click.echo()
    click.echo(f"🎯 Processing complete:")
    click.echo(f"   ✅ Successfully processed: {success_count}/{len(available_maps)} maps")
    if auto_visualize:
        click.echo(f"   🎨 Visualizations generated: {visualization_count} radar overlays")
    if failed_maps:
        click.echo(f"   ❌ Failed maps: {', '.join(failed_maps)}")
    
    if missing_maps and not auto_extract:
        click.echo(f"   ⏳ Still need extraction: {len(missing_maps)} maps")
        click.echo(f"      Use --auto-extract to automatically extract missing maps")
    
    # Show output files
    click.echo(f"\n📁 Generated files:")
    out_dir = Path("out")
    for map_name in available_maps:
        out_file = out_dir / f"{map_name}_callouts.json"
        if out_file.exists():
            size_kb = round(out_file.stat().st_size / 1024, 1)
            click.echo(f"   📄 {out_file.name} ({size_kb} KB)")
            
            if auto_visualize:
                radar_file = out_dir / f"{map_name}_radar.png"
                if radar_file.exists():
                    size_kb = round(radar_file.stat().st_size / 1024, 1)
                    click.echo(f"   🎨 {radar_file.name} ({size_kb} KB)")


@cli.command()
@click.option("--map", "map_name", default="de_mirage", help="Map name for full pipeline")
@click.option("--vpk-path", default="", help="Path to CS2 VPK file (auto-detected if not provided)")
@click.option("--gltf-format", type=click.Choice(["glb", "gltf"]), default="glb", help="GLTF export format")
@click.option("--projection", "projection_method", type=click.Choice(["top_down", "alpha_shape", "convex_hull"], case_sensitive=False), default="top_down", show_default=True, help="2D projection method for radar visualization.")
@click.option("--global-scale-multiplier", "global_scale_multiplier", type=float, default=1.0, show_default=True, help="Global multiplier applied to all polygon dimensions (e.g., 2.0 for 2x scaling).")
def pipeline(map_name: str, vpk_path: str, gltf_format: str, projection_method: str, global_scale_multiplier: float):
    """Run the complete extraction and processing pipeline."""
    click.echo(f"Running complete pipeline for {map_name}...")
    
    # Step 1: Extract
    click.echo("Step 1: Extracting callout data...")
    ctx = click.get_current_context()
    try:
        result = ctx.invoke(extract, vpk_path=vpk_path, map_name=map_name, out_root="export", gltf_format=gltf_format)
        if result and result != 0:
            click.echo("❌ Extraction failed, stopping pipeline.")
            return result
    except Exception as e:
        click.echo(f"❌ Extraction failed: {e}")
        return 1
    
    # Check if extraction produced the required file
    from pathlib import Path
    callouts_file = Path("export/maps") / map_name / "report/callouts_found.json"
    if not callouts_file.exists():
        click.echo("❌ Extraction did not produce callouts_found.json, stopping pipeline.")
        return 1
    
    # Step 2: Process
    click.echo("Step 2: Processing polygons...")
    try:
        result = ctx.invoke(process, map_name=map_name, callouts_json=None, models_root="export/models", out_path=None, rotation_order="auto", projection_method=projection_method, global_scale_multiplier=global_scale_multiplier)
        if result and result != 0:
            click.echo("❌ Processing failed.")
            return result
    except Exception as e:
        click.echo(f"❌ Processing failed: {e}")
        return 1
    
    click.echo(f"✅ Pipeline complete!")


@cli.command()
@click.option("--exclude-tools", is_flag=True, help="Keep downloaded tools (VRF CLI) - by default tools are removed")
@click.option("--exclude-caches", is_flag=True, help="Keep Python cache directories - by default caches are removed")
@click.option("--dry-run", is_flag=True, help="Show what would be removed without actually removing")
def clean(exclude_tools: bool, exclude_caches: bool, dry_run: bool):
    """Clean generated outputs, caches, and tools (tools auto-download when needed)."""
    from pathlib import Path
    import shutil
    
    root = Path.cwd()
    targets = []
    
    # Main output directories (always removed)
    for dirname in ['export', 'out']:
        path = root / dirname
        if path.exists():
            targets.append(path)
    
    # Cache directories (removed by default)
    if not exclude_caches:
        for cache_name in ['.pytest_cache', '.mypy_cache']:
            cache_path = root / cache_name
            if cache_path.exists():
                targets.append(cache_path)
        
        # Find __pycache__ directories
        for pycache in root.rglob('__pycache__'):
            targets.append(pycache)
    
    # Tools directory (removed by default since it's auto-downloaded)
    if not exclude_tools:
        tools_path = root / 'tools'
        if tools_path.exists():
            targets.append(tools_path)
    
    if not targets:
        click.echo(click.style('Nothing to clean.', fg='yellow'))
        return
    
    # Remove duplicates and sort
    targets = sorted(set(targets))
    
    if dry_run:
        click.echo("Would remove:")
        for target in targets:
            click.echo(f"  - {target}")
        return
    
    removed = []
    failed = []
    
    for target in targets:
        try:
            if target.is_file():
                target.unlink()
            else:
                shutil.rmtree(target)
            removed.append(target)
            click.echo(f"Removed: {target}")
        except Exception as e:
            failed.append((target, str(e)))
            click.echo(click.style(f"Failed to remove {target}: {e}", fg='yellow'))
    
    click.echo(click.style(f"Removed: {len(removed)}", fg='cyan'))
    if failed:
        click.echo(click.style(f"Failed: {len(failed)}", fg='yellow'))


@cli.command()
@click.option("--cli-dir", default="tools/vrf-cli", help="VRF CLI directory")
@click.option("--cli-url", default="", help="Explicit VRF CLI download URL")
@click.option("--cli-version", default="", help="VRF CLI version to download")
def setup(cli_dir: str, cli_url: str, cli_version: str):
    """Setup required tools (VRF CLI)."""
    from .extract import ensure_vrf_cli, info
    from pathlib import Path
    
    cli_dir_path = Path(cli_dir).resolve()
    
    try:
        cli_path = ensure_vrf_cli(cli_dir_path, cli_url, cli_version)
        info(f"VRF CLI ready: {cli_path}")
        click.echo(click.style("✅ Setup complete!", fg='green'))
    except Exception as e:
        click.echo(click.style(f"❌ Setup failed: {e}", fg='red'))
        return 1


@cli.command()
@click.option("--names", multiple=True, default=["FIRECRAWL_API_KEY"], help="Environment variable names to check")
@click.option("--strict", is_flag=True, help="Exit with error code if any variables are missing")
def check_env(names: tuple, strict: bool):
    """Check presence of required environment variables."""
    import os
    
    missing = []
    
    for name in names:
        value = os.environ.get(name)
        if value:
            click.echo(f"{name}: SET (len={len(value)})")
        else:
            click.echo(click.style(f"{name}: MISSING", fg='yellow'))
            missing.append(name)
    
    if strict and missing:
        click.echo(click.style(f"❌ Missing required variables: {', '.join(missing)}", fg='red'))
        return 1
    
    if not missing:
        click.echo(click.style("✅ All environment variables are set", fg='green'))


@cli.command()
@click.option("--map", "map_name", default="de_mirage", help="Map name to process")
@click.option("--out-json", default="", help="Output JSON path (default: out/{map}_callouts.json)")
@click.option("--models-root", default="export/models", help="Root folder for models")
@click.option("--vpk-path", default="", help="VPK path for extraction")
def run_map(map_name: str, out_json: str, models_root: str, vpk_path: str):
    """Run complete pipeline for a specific map (equivalent to run_map.ps1)."""
    click.echo(f"🗺️  Processing map: {map_name}")
    
    # Use the pipeline command
    ctx = click.get_current_context()
    ctx.invoke(pipeline, map_name=map_name, vpk_path=vpk_path, gltf_format="glb")
    
    click.echo(click.style(f"✅ Map processing complete for {map_name}!", fg='green'))


@cli.command()
@click.option("--json", "json_path", required=True, type=click.Path(exists=True), help="Path to <map>_callouts.json produced by the pipeline.")
@click.option("--radar", default=None, type=click.Path(exists=True), help="Optional radar image to draw underneath; mapped to world bounds.")
@click.option("--map-data", default=None, type=click.Path(exists=True), help="Optional map-data.json with radar positioning metadata.")
@click.option("--out", "out_path", default=None, type=click.Path(), help="Output image path (PNG). If omitted, shows an interactive window.")
@click.option("--labels/--no-labels", default=True, show_default=True, help="Draw callout names at polygon centroids.")
@click.option("--invert-y/--no-invert-y", default=False, show_default=True, help="Invert Y axis to match image pixel coordinates if needed.")
@click.option("--alpha", default=0.35, show_default=True, help="Polygon fill alpha.")
@click.option("--linewidth", default=1.0, show_default=True, help="Polygon edge line width.")
@click.option("--min-size", default=3.0, show_default=True, help="Minimum polygon size in pixels for visibility.")
def visualize(json_path: str, radar: str, map_data: str, out_path: str, labels: bool, invert_y: bool, alpha: float, linewidth: float, min_size: float):
    """Generate overlay PNG (with optional radar underlay)."""
    from .visualize import _load_output, _centroid, _color_for_name, _ensure_minimum_polygon_size
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as MplPolygon
    from pathlib import Path
    import json
    
    data = _load_output(json_path)
    items = data.get("callouts", [])
    polys = [it.get("polygon_2d") or [] for it in items]

    # Compute world bounds from polygons
    xs = []
    ys = []
    for poly in polys:
        for x, y in poly:
            xs.append(float(x))
            ys.append(float(y))
    if not xs or not ys:
        click.echo("No polygon data to visualize.", err=True)
        raise SystemExit(1)
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    # Load map metadata if provided
    map_metadata = None
    if map_data:
        metadata_file = map_data
    else:
        # Try to auto-detect map-data.json in common locations
        common_locations = [
            "map-data.json",  # Current directory
            "C:/Users/mwrid/.awpy/maps/map-data.json",  # User's awpy directory
            Path.home() / ".awpy/maps/map-data.json"  # Generic user awpy directory
        ]
        metadata_file = None
        for location in common_locations:
            if Path(location).exists():
                metadata_file = str(location)
                break
    
    if metadata_file:
        try:
            with open(metadata_file, 'r') as f:
                all_metadata = json.load(f)
                # Extract map name from JSON path (e.g., "de_mirage_callouts.json" -> "de_mirage")
                # Handle variations like "de_mirage_callouts_2x.json" -> "de_mirage"
                map_name = Path(json_path).stem
                if '_callouts' in map_name:
                    map_name = map_name.split('_callouts')[0]
                map_metadata = all_metadata.get(map_name)
                if map_metadata:
                    click.echo(f"Using map metadata for {map_name}: scale={map_metadata['scale']}, pos_x={map_metadata['pos_x']}, pos_y={map_metadata['pos_y']}")
                else:
                    click.echo(f"No metadata found for {map_name} in {metadata_file}")
        except Exception as e:
            click.echo(f"Warning: Could not load map metadata: {e}")

    fig, ax = plt.subplots(figsize=(12, 12))
    
    if radar and map_metadata:
        from PIL import Image
        
        # Use awpy-style coordinate transformation
        scale = map_metadata['scale']
        pos_x = map_metadata['pos_x']
        pos_y = map_metadata['pos_y']
        
        # Transform callout coordinates to radar pixel coordinates using awpy's method
        def game_to_pixel_x(game_x):
            return (game_x - pos_x) / scale
            
        def game_to_pixel_y(game_y):
            return (pos_y - game_y) / scale  # Y is inverted in awpy
        
        # Transform all callout coordinates to pixel coordinates
        pixel_xs = []
        pixel_ys = []
        for poly in polys:
            for x, y in poly:
                pixel_x = game_to_pixel_x(float(x))
                pixel_y = game_to_pixel_y(float(y))
                pixel_xs.append(pixel_x)
                pixel_ys.append(pixel_y)
        
        if pixel_xs and pixel_ys:
            pixel_min_x, pixel_max_x = min(pixel_xs), max(pixel_xs)
            pixel_min_y, pixel_max_y = min(pixel_ys), max(pixel_ys)
            
            # Load radar image and set it to cover the standard 1024x1024 pixel space
            img = Image.open(radar)
            radar_width, radar_height = img.size
            
            # Radar image maps to pixel coordinates (0,0) to (radar_width, radar_height)
            ax.imshow(img, extent=[0, radar_width, 0, radar_height], alpha=0.7, origin='lower')
            
            # Set plot bounds to show the callouts in pixel coordinates with some padding
            padding = 50
            plot_min_x = max(0, pixel_min_x - padding)
            plot_max_x = min(radar_width, pixel_max_x + padding)
            plot_min_y = max(0, pixel_min_y - padding)
            plot_max_y = min(radar_height, pixel_max_y + padding)
            
            click.echo(f"Transformed to pixel coords: X={pixel_min_x:.1f} to {pixel_max_x:.1f}, Y={pixel_min_y:.1f} to {pixel_max_y:.1f}")
        else:
            # Fallback to full radar
            plot_min_x, plot_max_x = 0, img.size[0]
            plot_min_y, plot_max_y = 0, img.size[1]
            ax.imshow(img, extent=[plot_min_x, plot_max_x, plot_min_y, plot_max_y], alpha=0.7)
    elif radar:
        from PIL import Image
        img = Image.open(radar)
        # Fallback: map radar to callout bounds
        plot_min_x, plot_max_x = min_x, max_x
        plot_min_y, plot_max_y = min_y, max_y
        ax.imshow(img, extent=[plot_min_x, plot_max_x, plot_min_y, plot_max_y], alpha=0.7)
    else:
        # No radar, just use callout bounds
        plot_min_x, plot_max_x = min_x, max_x
        plot_min_y, plot_max_y = min_y, max_y

    for it, poly in zip(items, polys):
        if not poly:
            continue
        name = it.get("name") or it.get("placename") or "?"
        color = _color_for_name(name)
        
        # Transform polygon coordinates if we have map metadata
        if radar and map_metadata:
            # Transform to pixel coordinates
            pixel_poly = []
            for x, y in poly:
                pixel_x = (float(x) - map_metadata['pos_x']) / map_metadata['scale']
                pixel_y = (map_metadata['pos_y'] - float(y)) / map_metadata['scale']  # Y inverted
                pixel_poly.append([pixel_x, pixel_y])
            
            # Ensure minimum polygon size for visibility
            poly_to_plot = _ensure_minimum_polygon_size(pixel_poly, min_size=min_size)
        else:
            poly_to_plot = poly
            
        patch = MplPolygon(poly_to_plot, closed=True, facecolor=color + (alpha,), edgecolor=color, linewidth=linewidth)
        ax.add_patch(patch)
        if labels:
            cx, cy = _centroid(poly_to_plot)
            ax.text(cx, cy, name, fontsize=7, color="black", ha="center", va="center", bbox=dict(boxstyle="round,pad=0.1", fc="white", ec="none", alpha=0.6))

    ax.set_xlim(plot_min_x, plot_max_x)
    ax.set_ylim(plot_min_y, plot_max_y)
    ax.set_aspect("equal", adjustable="box")
    if invert_y:
        ax.invert_yaxis()
    ax.set_title(Path(json_path).stem)
    ax.set_xlabel("X (game units)")
    ax.set_ylabel("Y (game units)")
    ax.grid(True, linestyle=":", linewidth=0.5, alpha=0.5)

    if out_path:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_path, dpi=200, bbox_inches="tight")
        click.echo(f"Saved {out_path}")
    else:
        plt.show()


if __name__ == "__main__":
    cli()

