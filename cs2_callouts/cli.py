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
            result = export_models(cli_path, [vpk_path], model_paths, models_out, gltf_format, out_map_dir)
            info(f"Exported {len(result['exported'])} models")
        
        info("Extraction complete!")
        
    except Exception as e:
        error(str(e))
        return 1


@cli.command()
@click.option("--map", "map_name", default="de_mirage", show_default=True, help="Map name used for path defaults.")
@click.option("--callouts-json", "callouts_json", type=click.Path(exists=True), default=None, help="Path to callouts_found.json from the extraction step.")
@click.option("--models-root", type=click.Path(exists=True, file_okay=False), default="export/models", show_default=True, help="Root folder containing exported GLB/GLTF models.")
@click.option("--out", "out_path", type=click.Path(), default=None, help="Output JSON path.")
@click.option("--rotation-order", type=click.Choice(["auto", "rz_rx_ry", "ry_rx_rz", "rz_ry_rx"], case_sensitive=False), default="auto", show_default=True)
def process(map_name: str, callouts_json: str | None, models_root: str, out_path: str | None, rotation_order: str):
    """Process extracted callouts into 2D polygon data."""
    if callouts_json is None:
        callouts_json = str(Path("export") / "maps" / map_name / "report" / "callouts_found.json")
    if out_path is None:
        out_path = str(Path("out") / f"{map_name}_callouts.json")

    callouts = read_callouts_json(callouts_json)
    if not callouts:
        click.echo(f"No callouts found in {callouts_json}", err=True)
        sys.exit(1)

    data = process_callouts(callouts, models_root=models_root, rotation_order=rotation_order)
    write_json(data, out_path, pretty=True)
    click.echo(f"Wrote {out_path} with {data['count']} callouts. Rotation order: {data['rotation_order']}")
    if data.get("missing_models"):
        click.echo(f"Missing models: {len(data['missing_models'])}")


@cli.command()
@click.option("--map", "map_name", default="de_mirage", help="Map name for full pipeline")
@click.option("--vpk-path", default="", help="Path to CS2 VPK file (auto-detected if not provided)")
@click.option("--gltf-format", type=click.Choice(["glb", "gltf"]), default="glb", help="GLTF export format")
def pipeline(map_name: str, vpk_path: str, gltf_format: str):
    """Run the complete extraction and processing pipeline."""
    click.echo(f"Running complete pipeline for {map_name}...")
    
    # Step 1: Extract
    click.echo("Step 1: Extracting callout data...")
    ctx = click.get_current_context()
    ctx.invoke(extract, vpk_path=vpk_path, map_name=map_name, out_root="export", gltf_format=gltf_format)
    
    # Step 2: Process
    click.echo("Step 2: Processing polygons...")
    ctx.invoke(process, map_name=map_name, callouts_json=None, models_root="export/models", out_path=None, rotation_order="auto")
    
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


if __name__ == "__main__":
    cli()

