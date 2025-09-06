#!/usr/bin/env python3
"""
Complete workflow to clean, process, and visualize CS2 callout data
Cross-platform replacement for workflow.ps1
"""

import subprocess
import sys
from pathlib import Path
import shutil
import json

def run_command(cmd, description=""):
    """Run a command and return success status"""
    if description:
        print(f"   🔄 {description}...")
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Command failed: {e}")
        return False, e.stderr

def main():
    print("🧹 CS2 Callouts - Complete Workflow")
    print("=" * 50)

    # Step 1: Clean previous outputs
    print("\n📂 Step 1: Cleaning previous outputs...")
    out_dir = Path("out")
    if out_dir.exists():
        shutil.rmtree(out_dir)
        print("   ✅ Cleaned out/ directory")
    out_dir.mkdir(exist_ok=True)
    print("   ✅ Created fresh out/ directory")

    # Step 2: Process callouts with different scale multipliers
    print("\n⚙️  Step 2: Processing all available maps with different scale multipliers...")
    
    scales = [1.0, 2.0, 3.0]
    for scale in scales:
        success, output = run_command(
            f"python -m cs2_callouts process --map all --global-scale-multiplier {scale}",
            f"Processing all maps with {scale}x scale"
        )
        if success:
            print(f"   ✅ {scale}x scale complete")
        else:
            print(f"   ❌ {scale}x scale failed")

    # Step 3: Generate visualizations
    print("\n📊 Step 3: Generating visualizations for all processed maps...")
    
    # Find all processed map files
    json_files = list(out_dir.glob("*_callouts.json"))
    
    if not json_files:
        print("   ⚠️  No processed map files found in out/ directory")
    else:
        print(f"   📁 Found {len(json_files)} processed map files")
        
        # Get user's home directory for awpy maps
        home = Path.home()
        awpy_maps_dir = home / ".awpy" / "maps"
        
        for json_file in json_files:
            # Extract map name from filename (e.g., "de_mirage_callouts.json" -> "de_mirage")
            map_name = json_file.stem.replace("_callouts", "")
            radar_path = awpy_maps_dir / f"{map_name}.png"
            
            print(f"   🎨 Processing visualizations for {map_name}...")
            
            # Basic visualization without radar
            basic_output = out_dir / f"{map_name}_visualization.png"
            success, _ = run_command(
                f"python -m cs2_callouts visualize --json {json_file} --out {basic_output}",
                f"Creating basic visualization for {map_name}"
            )
            if success:
                print(f"   ✅ {map_name} basic visualization complete")
            else:
                print(f"   ❌ {map_name} basic visualization failed")
            
            # Radar overlay visualization if radar exists
            if radar_path.exists():
                radar_output = out_dir / f"{map_name}_radar_overlay.png"
                success, _ = run_command(
                    f"python -m cs2_callouts visualize --json {json_file} --radar {radar_path} --out {radar_output}",
                    f"Creating radar overlay for {map_name}"
                )
                if success:
                    print(f"   ✅ {map_name} radar overlay complete")
                else:
                    print(f"   ❌ {map_name} radar overlay failed")
            else:
                print(f"   ⚠️  No radar image found for {map_name} at {radar_path}")

    # Step 4: Generate comparison data
    print("\n📈 Step 4: Generating comparison data...")
    compare_script = Path("debug/compare_scaling_results.py")
    if compare_script.exists():
        success, _ = run_command("python debug/compare_scaling_results.py", "Running scaling analysis")
        if success:
            print("   ✅ Comparison data generated")
        else:
            print("   ❌ Comparison data failed")
    else:
        print("   ⚠️  Comparison script not found")

    # Step 5: Summary
    print("\n📋 Step 5: Results Summary")
    print("   Generated files:")

    for file in sorted(out_dir.glob("*.json")):
        size_kb = round(file.stat().st_size / 1024, 1)
        print(f"   📄 {file.name} ({size_kb} KB)")

    for file in sorted(out_dir.glob("*.png")):
        size_kb = round(file.stat().st_size / 1024, 1)
        print(f"   🖼️  {file.name} ({size_kb} KB)")

    print("\n🎉 Workflow complete! Check the out/ directory for results.")
    print("   💡 Tip: Open PNG files to compare different scale multipliers")

if __name__ == "__main__":
    main()
