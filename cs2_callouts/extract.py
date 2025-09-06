#!/usr/bin/env python3
"""
CS2 Callout Model Extractor - Python version
Replaces the PowerShell vrf_extract_callout_models.ps1 script
"""
from __future__ import annotations

import json
import os
import json
import os
import platform
import re
import shutil
import subprocess
import tempfile
import uuid
import zipfile
from pathlib import Path
from typing import List, Optional, Dict, Any
from urllib.request import urlretrieve

import click


def info(msg: str) -> None:
    click.echo(click.style(f"[INFO] {msg}", fg="cyan"))


def warn(msg: str) -> None:
    click.echo(click.style(f"[WARN] {msg}", fg="yellow"))


def error(msg: str) -> None:
    click.echo(click.style(f"[ERR ] {msg}", fg="red"))


def ensure_dir(path: Path) -> None:
    """Ensure directory exists, create if not."""
    path.mkdir(parents=True, exist_ok=True)


def resolve_vpk_paths(user_path: Optional[str] = None, map_name: Optional[str] = None) -> List[str]:
    """Find all relevant CS2 VPK files including map-specific VPKs."""
    vpk_paths = []
    
    if user_path and Path(user_path).exists():
        vpk_paths.append(str(Path(user_path).resolve()))
        return vpk_paths
    
    # Common Steam installation paths
    program_files_x86 = os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")
    program_files = os.environ.get("ProgramFiles", "C:\\Program Files")
    
    # Main pak01_dir.vpk candidates
    main_candidates = [
        # CS:GO paths - prioritize csgo_core as in original PowerShell
        f"{program_files_x86}\\Steam\\steamapps\\common\\Counter-Strike Global Offensive\\game\\csgo_core\\pak01_dir.vpk",
        f"{program_files_x86}\\Steam\\steamapps\\common\\Counter-Strike Global Offensive\\game\\core\\pak01_dir.vpk",
        f"{program_files_x86}\\Steam\\steamapps\\common\\Counter-Strike Global Offensive\\game\\csgo\\pak01_dir.vpk",
        f"{program_files}\\Steam\\steamapps\\common\\Counter-Strike Global Offensive\\game\\csgo_core\\pak01_dir.vpk",
        f"{program_files}\\Steam\\steamapps\\common\\Counter-Strike Global Offensive\\game\\core\\pak01_dir.vpk",
        f"{program_files}\\Steam\\steamapps\\common\\Counter-Strike Global Offensive\\game\\csgo\\pak01_dir.vpk",
        # CS2 paths
        f"{program_files_x86}\\Steam\\steamapps\\common\\Counter-Strike 2\\game\\core\\pak01_dir.vpk",
        f"{program_files_x86}\\Steam\\steamapps\\common\\Counter-Strike 2\\game\\csgo_core\\pak01_dir.vpk",
        f"{program_files_x86}\\Steam\\steamapps\\common\\Counter-Strike 2\\game\\csgo\\pak01_dir.vpk",
        f"{program_files}\\Steam\\steamapps\\common\\Counter-Strike 2\\game\\core\\pak01_dir.vpk",
        f"{program_files}\\Steam\\steamapps\\common\\Counter-Strike 2\\game\\csgo_core\\pak01_dir.vpk",
        f"{program_files}\\Steam\\steamapps\\common\\Counter-Strike 2\\game\\csgo\\pak01_dir.vpk",
    ]
    
    # Add first found main VPK
    for candidate in main_candidates:
        if Path(candidate).exists():
            vpk_paths.append(str(Path(candidate).resolve()))
            break
    
    # Add map-specific VPKs if map_name is provided
    if map_name:
        map_vpk_candidates = [
            # CS:GO/CS2 map-specific VPKs
            f"{program_files_x86}\\Steam\\steamapps\\common\\Counter-Strike Global Offensive\\game\\csgo\\maps\\{map_name}.vpk",
            f"{program_files_x86}\\Steam\\steamapps\\common\\Counter-Strike Global Offensive\\game\\csgo\\maps\\{map_name}_d.vpk",
            f"{program_files_x86}\\Steam\\steamapps\\common\\Counter-Strike Global Offensive\\game\\csgo\\maps\\{map_name}_vanity.vpk",
            f"{program_files}\\Steam\\steamapps\\common\\Counter-Strike Global Offensive\\game\\csgo\\maps\\{map_name}.vpk",
            f"{program_files}\\Steam\\steamapps\\common\\Counter-Strike Global Offensive\\game\\csgo\\maps\\{map_name}_d.vpk",
            f"{program_files}\\Steam\\steamapps\\common\\Counter-Strike Global Offensive\\game\\csgo\\maps\\{map_name}_vanity.vpk",
            f"{program_files_x86}\\Steam\\steamapps\\common\\Counter-Strike 2\\game\\csgo\\maps\\{map_name}.vpk",
            f"{program_files_x86}\\Steam\\steamapps\\common\\Counter-Strike 2\\game\\csgo\\maps\\{map_name}_d.vpk",
            f"{program_files_x86}\\Steam\\steamapps\\common\\Counter-Strike 2\\game\\csgo\\maps\\{map_name}_vanity.vpk",
            f"{program_files}\\Steam\\steamapps\\common\\Counter-Strike 2\\game\\csgo\\maps\\{map_name}.vpk",
            f"{program_files}\\Steam\\steamapps\\common\\Counter-Strike 2\\game\\csgo\\maps\\{map_name}_d.vpk",
            f"{program_files}\\Steam\\steamapps\\common\\Counter-Strike 2\\game\\csgo\\maps\\{map_name}_vanity.vpk",
        ]
        
        for candidate in map_vpk_candidates:
            if Path(candidate).exists():
                vpk_paths.append(str(Path(candidate).resolve()))
    
    if not vpk_paths:
        raise FileNotFoundError("Could not find pak01_dir.vpk or map-specific VPKs. Pass --vpk-path with the full path to your CS2 VPK.")
    
    return vpk_paths


def resolve_vpk_path(user_path: Optional[str] = None) -> str:
    """Find CS2 VPK file in common Steam installation locations (legacy function)."""
    paths = resolve_vpk_paths(user_path)
    return paths[0] if paths else ""


def ensure_vrf_cli(cli_dir: Path, explicit_url: str = "", version: str = "") -> str:
    """Download and setup VRF CLI if not present."""
    ensure_dir(cli_dir)
    
    # Determine executable name based on platform
    if platform.system() == "Windows":
        cli_exe = cli_dir / "Source2Viewer-CLI.exe"
        platform_suffix = "windows-x64"
    else:
        cli_exe = cli_dir / "Source2Viewer-CLI"
        platform_suffix = "linux-x64" if platform.system() == "Linux" else "osx-x64"
    
    if cli_exe.exists():
        return str(cli_exe)
    
    # Build download URLs with correct asset names
    urls = []
    if explicit_url:
        urls.append(explicit_url)
    if version:
        # Use exact asset names for versioned downloads
        if platform.system() == "Windows":
            urls.append(f"https://github.com/ValveResourceFormat/ValveResourceFormat/releases/download/{version}/cli-windows-x64.zip")
        elif platform.system() == "Linux":
            urls.append(f"https://github.com/ValveResourceFormat/ValveResourceFormat/releases/download/{version}/cli-linux-x64.zip")
        else:  # macOS
            urls.append(f"https://github.com/ValveResourceFormat/ValveResourceFormat/releases/download/{version}/cli-macos-x64.zip")
    
    # Fallback to latest with correct asset names
    if platform.system() == "Windows":
        urls.append("https://github.com/ValveResourceFormat/ValveResourceFormat/releases/latest/download/cli-windows-x64.zip")
    elif platform.system() == "Linux":
        urls.append("https://github.com/ValveResourceFormat/ValveResourceFormat/releases/latest/download/cli-linux-x64.zip")
    else:  # macOS
        urls.append("https://github.com/ValveResourceFormat/ValveResourceFormat/releases/latest/download/cli-macos-x64.zip")
    
    # Remove duplicates while preserving order
    urls = list(dict.fromkeys(urls))
    
    for url in urls:
        try:
            info(f"Downloading VRF CLI from {url}")
            # Use a more robust temp file approach
            import uuid
            temp_filename = f"vrf_cli_{uuid.uuid4().hex[:8]}.zip"
            temp_path = Path(tempfile.gettempdir()) / temp_filename
            
            try:
                urlretrieve(url, str(temp_path))
                
                with zipfile.ZipFile(str(temp_path), 'r') as zip_ref:
                    zip_ref.extractall(cli_dir)
                
            finally:
                # Ensure temp file is removed even if extraction fails
                if temp_path.exists():
                    temp_path.unlink()
            
            # Look for the executable
            if cli_exe.exists():
                if platform.system() != "Windows":
                    cli_exe.chmod(0o755)  # Make executable on Unix systems
                return str(cli_exe)
            
            # Search for any CLI executable
            patterns = ["Source2Viewer-CLI*", "*CLI*.exe", "*CLI*"]
            for pattern in patterns:
                candidates = list(cli_dir.rglob(pattern))
                if candidates:
                    found_exe = candidates[0]
                    if platform.system() != "Windows":
                        found_exe.chmod(0o755)
                    return str(found_exe)
                    
        except Exception as e:
            warn(f"Download failed from {url}: {e}")
            continue
    
    raise RuntimeError("VRF CLI download failed. Pass --cli-url or --cli-version to specify an exact asset.")


def run_vrf_command(cli_path: str, args: List[str]) -> List[str]:
    """Run VRF CLI command and return output lines."""
    try:
        result = subprocess.run(
            [cli_path] + args,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip().split('\n') if result.stdout.strip() else []
    except subprocess.CalledProcessError as e:
        warn(f"VRF command failed: {e}")
        return []


def decompile_map_and_entities_from_multiple_vpks(cli_path: str, vpk_paths: List[str], map_name: str, out_root: Path) -> Path:
    """Decompile map and entity files from multiple VPK files."""
    out_map_dir = out_root / "maps" / map_name / "vrf"
    ensure_dir(out_map_dir)
    
    all_vmap_candidates = []
    all_entities_candidates = []
    
    # Scan all VPK files for relevant resources
    for vpk_path in vpk_paths:
        info(f"Scanning VPK for map resources: {Path(vpk_path).name}")
        list_output = run_vrf_command(cli_path, ["-i", vpk_path, "--vpk_list"])
        
        if list_output:
            base = map_name[3:] if map_name.startswith('de_') else map_name
            name_pattern = f"({re.escape(map_name)}|{re.escape(base)})"
            
            for line in list_output:
                if re.match(r"^maps/.+\.vmap_c$", line) and re.search(name_pattern, line) and "/worldnodes/" not in line:
                    all_vmap_candidates.append((vpk_path, line))
                elif re.match(r"^maps/.+/entities/.+\.vents_c$", line) and re.search(name_pattern, line):
                    all_entities_candidates.append((vpk_path, line))
    
    # Try to decompile vmap files
    if not all_vmap_candidates:
        warn(f"No .vmap_c files with '{map_name}' found in any VPK. Attempting common map paths.")
        base = map_name[3:] if map_name.startswith('de_') else map_name
        guesses = [
            f"maps/{map_name}/{map_name}.vmap_c",
            f"maps/{map_name}/{map_name}_d.vmap_c",
            f"maps/{base}/de_{base}.vmap_c",
            f"maps/{base}/de_{base}_d.vmap_c"
        ]
        
        for vpk_path in vpk_paths:
            for guess in guesses:
                try:
                    info(f"Trying vmap guess: {guess} in {Path(vpk_path).name}")
                    run_vrf_command(cli_path, ["-i", vpk_path, "--vpk_filepath", guess, "-o", str(out_map_dir), "-d"])
                    all_vmap_candidates.append((vpk_path, guess))
                    break  # Found one, move to next VPK
                except:
                    continue
    else:
        for vpk_path, vmap in all_vmap_candidates:
            info(f"Decompiling vmap: {vmap} from {Path(vpk_path).name}")
            run_vrf_command(cli_path, ["-i", vpk_path, "--vpk_filepath", vmap, "-o", str(out_map_dir), "-d"])
    
    # Decompile entity files
    entities_out_root = out_map_dir / "entities"
    ensure_dir(entities_out_root)
    
    if all_entities_candidates:
        info(f"Decompiling {len(all_entities_candidates)} entity lump(s) from multiple VPKs")
        for vpk_path, entity_file in all_entities_candidates:
            info(f"Decompiling entity file: {entity_file} from {Path(vpk_path).name}")
            run_vrf_command(cli_path, ["-i", vpk_path, "--vpk_filepath", entity_file, "-o", str(entities_out_root), "-d"])
    else:
        info("No specific entity lumps found by listing; trying folder heuristic on all VPKs.")
        for vpk_path in vpk_paths:
            try:
                run_vrf_command(cli_path, ["-i", vpk_path, "--vpk_filepath", f"maps/{map_name}/entities/", "-e", "vents_c", "-o", str(entities_out_root), "-d"])
            except:
                continue
    
    return out_map_dir


def decompile_map_and_entities(cli_path: str, vpk_path: str, map_name: str, out_root: Path) -> Path:
    """Decompile map and entity files from VPK (legacy single VPK function)."""
    return decompile_map_and_entities_from_multiple_vpks(cli_path, [vpk_path], map_name, out_root)
    
    return out_map_dir


def parse_callout_models(search_root: Path) -> List[Dict[str, Any]]:
    """Parse callout models from decompiled text files."""
    text_files = list(search_root.rglob("*.vmap")) + list(search_root.rglob("*.vents")) + list(search_root.rglob("*.txt"))
    
    if not text_files:
        warn(f"No text files found under {search_root}")
        return []
    
    results = []
    
    for file_path in text_files:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
        except:
            continue
        
        current_entity = {}
        
        def flush_block():
            if (current_entity.get('classname') == 'env_cs_place' and 
                current_entity.get('model')):
                
                result = {
                    'file': str(file_path),
                    'placename': current_entity.get('place_name') or current_entity.get('placename'),
                    'model': current_entity.get('model', '').strip(),
                    'origin': current_entity.get('origin'),
                    'angles': current_entity.get('angles'),
                    'scales': current_entity.get('scales') or current_entity.get('scale')
                }
                results.append(result)
            current_entity.clear()
        
        for line in lines:
            line = line.strip()
            if line.startswith('='):
                flush_block()
                continue
            
            # Parse key-value pairs
            if ' ' in line:
                parts = line.split(None, 1)
                if len(parts) == 2:
                    key, value = parts
                    
                    if key in ('place_name', 'placename'):
                        current_entity['place_name'] = value
                    elif key == 'classname':
                        current_entity['classname'] = value
                    elif key == 'model':
                        current_entity['model'] = value
                    elif key == 'origin':
                        coords = value.split()
                        if len(coords) == 3:
                            current_entity['origin'] = [float(x) for x in coords]
                    elif key == 'angles':
                        coords = value.split()
                        if len(coords) == 3:
                            current_entity['angles'] = [float(x) for x in coords]
                    elif key in ('scales', 'scale'):
                        coords = value.split()
                        if len(coords) == 3:
                            current_entity['scales'] = [float(x) for x in coords]
        
        flush_block()  # Handle last entity
    
    # Filter and deduplicate
    filtered = [r for r in results if r['model'] and r['model'].strip()]
    return filtered


def export_models(cli_path: str, vpk_paths: List[str], model_paths: List[str], 
                 out_dir: Path, fmt: str, fallback_dir: Optional[Path] = None) -> Dict[str, List[str]]:
    """Export models to GLB/GLTF format."""
    ensure_dir(out_dir)
    exported = []
    missing = []
    
    for model_path in sorted(set(model_paths)):
        # Normalize path
        mp = model_path.replace("\\", "/")
        if mp.endswith(".vmdl") and not mp.endswith("_c"):
            mp += "_c"
        elif not mp.endswith(".vmdl_c") and not mp.endswith(".vmdl"):
            # Keep as is for special cases
            pass
        
        info(f"Decompiling model: {mp}")
        success = False
        
        for vpk_path in vpk_paths:
            # Try to extract the model
            run_vrf_command(cli_path, ["-i", vpk_path, "--vpk_filepath", mp, "-o", str(out_dir), "-d", "--gltf_export_format", fmt])
            
            # Check if files were actually created
            model_name = Path(mp).stem
            expected_files = [
                out_dir / f"{model_name}.{fmt}",
                out_dir / f"{model_name}_physics.{fmt}"
            ]
            
            # Also check nested path structure (VRF preserves directory structure)
            nested_path = out_dir / mp.replace('.vmdl_c', '.glb').replace('.vmdl', '.glb')
            nested_physics_path = out_dir / mp.replace('.vmdl_c', '_physics.glb').replace('.vmdl', '_physics.glb')
            expected_files.extend([nested_path, nested_physics_path])
            
            if any(f.exists() for f in expected_files):
                exported.append(mp)
                success = True
                break
        
        if not success and fallback_dir:
            # Try local decompiled file
            local_path = fallback_dir / mp.replace('/', '\\')
            local_path = local_path.with_suffix('.vmdl')
            if local_path.exists():
                try:
                    run_vrf_command(cli_path, ["-i", str(local_path), "-o", str(out_dir), "-d", "--gltf_export_format", fmt])
                    exported.append(mp)
                    success = True
                except:
                    pass
        
        if not success:
            missing.append(mp)
    
    return {"exported": exported, "missing": missing}


@click.command()
@click.option("--vpk-path", default="", help="Path to CS2 VPK file")
@click.option("--vpk-paths", multiple=True, help="Multiple VPK paths (can be used multiple times)")
@click.option("--input-files", multiple=True, help="Direct input files (.vmap_c, .vents_c)")
@click.option("--map", "map_name", default="de_mirage", help="Map name")
@click.option("--out-root", default="export", help="Output root directory")
@click.option("--cli-dir", default="tools/vrf-cli", help="VRF CLI directory")
@click.option("--cli-url", default="", help="Explicit VRF CLI download URL")
@click.option("--cli-version", default="", help="VRF CLI version to download")
@click.option("--gltf-format", type=click.Choice(["glb", "gltf"]), default="glb", help="GLTF export format")
def main(vpk_path: str, vpk_paths: tuple, input_files: tuple, map_name: str,
         out_root: str, cli_dir: str, cli_url: str, cli_version: str, gltf_format: str):
    """Extract CS2 callout models using VRF CLI (Python version)."""
    try:
        # Setup paths
        out_root_path = Path(out_root).resolve()
        cli_dir_path = Path(cli_dir).resolve()
        
        # Ensure VRF CLI
        cli_path = ensure_vrf_cli(cli_dir_path, cli_url, cli_version)
        info(f"VRF CLI: {cli_path}")
        
        # Determine VPK paths to try
        paths_to_try = []
        if vpk_paths:
            for path in vpk_paths:
                if ',' in path or ';' in path:
                    paths_to_try.extend(re.split(r'[,;]\s*', path))
                else:
                    paths_to_try.append(path)
        elif vpk_path:
            paths_to_try.append(vpk_path)
        else:
            # Use new multi-VPK resolution that includes map-specific VPKs
            paths_to_try = resolve_vpk_paths(map_name=map_name)
        
        all_callouts = []
        tried_vpks = []
        
        # Process input files if provided
        if input_files:
            # TODO: Implement direct file processing
            pass
        
        # Filter existing VPK files
        existing_vpks = []
        for path in paths_to_try:
            if not Path(path).exists():
                warn(f"VPK not found: {path}")
                continue
            existing_vpks.append(str(Path(path).resolve()))
        
        if not existing_vpks:
            error("No valid VPK files found!")
            return 1
        
        tried_vpks = existing_vpks
        info(f"Using VPKs: {[Path(vpk).name for vpk in existing_vpks]}")
        
        # Process all VPKs together using multi-VPK decompilation
        out_map_dir = decompile_map_and_entities_from_multiple_vpks(cli_path, existing_vpks, map_name, out_root_path)
        info("Scanning for env_cs_place entries...")
        
        found_callouts = parse_callout_models(out_map_dir)
        if found_callouts:
            all_callouts.extend(found_callouts)
        
        # Save callouts report
        report_dir = out_root_path / "maps" / map_name / "report"
        ensure_dir(report_dir)
        callouts_json = report_dir / "callouts_found.json"
        
        if not all_callouts:
            error("No env_cs_place entries found in decompiled outputs.")
            info(f"Tried VPKs: {'; '.join(tried_vpks)}")
            return 2
        
        # Deduplicate callouts
        seen = set()
        unique_callouts = []
        for callout in all_callouts:
            key = (callout.get('placename'), callout.get('model'))
            if key not in seen:
                seen.add(key)
                unique_callouts.append(callout)
        
        info(f"Found {len(unique_callouts)} callout entities with models.")
        
        with open(callouts_json, 'w', encoding='utf-8') as f:
            json.dump(unique_callouts, f, indent=2, ensure_ascii=False)
        info(f"Saved callouts report: {callouts_json}")
        
        # Export models
        model_paths = [c['model'] for c in unique_callouts if c.get('model')]
        if model_paths:
            models_out = out_root_path / "models"
            result = export_models(cli_path, tried_vpks, model_paths, models_out, gltf_format, out_map_dir)
            
            summary = {
                "map": map_name,
                "vpkTried": tried_vpks,
                "modelsRequested": model_paths,
                "modelsExported": result["exported"],
                "modelsMissing": result["missing"]
            }
            
            summary_path = report_dir / "models_export_summary.json"
            with open(summary_path, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            info(f"Saved model export summary: {summary_path}")
        else:
            warn("No model paths detected from callouts; skipping model export.")
        
        info("Done.")
        
    except Exception as e:
        error(str(e))
        return 1


if __name__ == "__main__":
    exit(main())
