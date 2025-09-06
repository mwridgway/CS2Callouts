#!/usr/bin/env python3
"""
Simple cross-platform demo workflow for available maps
"""

import subprocess
import sys
from pathlib import Path

def run_command(cmd, description=""):
    """Run a command with clear output"""
    if description:
        print(f"\n🔄 {description}")
        print(f"Command: {cmd}")
    
    result = subprocess.run(cmd, shell=True)
    return result.returncode == 0

def main():
    print("🚀 CS2 Callouts - Simple Cross-Platform Demo")
    print("=" * 50)
    
    # Step 1: Check status
    print("\n📊 Step 1: Check available maps")
    run_command("python -m cs2_callouts status", "Checking map status")
    
    # Step 2: Clean and process available maps
    print("\n🧹 Step 2: Clean and process")
    run_command("python clean.py", "Cleaning outputs")
    run_command("python -m cs2_callouts process --map all --global-scale-multiplier 2.0", "Processing available maps")
    
    # Step 3: Generate visualization
    print("\n🎨 Step 3: Generate visualizations")
    
    # Find processed files
    out_dir = Path("out")
    json_files = list(out_dir.glob("*_callouts.json"))
    
    if json_files:
        for json_file in json_files:
            map_name = json_file.stem.replace("_callouts", "")
            
            # Cross-platform radar path
            home = Path.home()
            radar_path = home / ".awpy" / "maps" / f"{map_name}.png"
            
            # Basic visualization
            basic_out = f"out/{map_name}_visualization.png"
            run_command(
                f"python -m cs2_callouts visualize --json {json_file} --out {basic_out}",
                f"Creating basic visualization for {map_name}"
            )
            
            # Radar overlay if available
            if radar_path.exists():
                radar_out = f"out/{map_name}_radar_overlay.png"
                run_command(
                    f"python -m cs2_callouts visualize --json {json_file} --radar {radar_path} --out {radar_out}",
                    f"Creating radar overlay for {map_name}"
                )
                print(f"✅ Generated meaningful radar overlay: {radar_out}")
            else:
                print(f"⚠️  No radar image found for {map_name}")
    else:
        print("❌ No processed map files found")
    
    # Step 4: Show results
    print("\n📁 Step 4: Results")
    if out_dir.exists():
        files = list(out_dir.iterdir())
        if files:
            print("Generated files:")
            for file in sorted(files):
                size_kb = round(file.stat().st_size / 1024, 1)
                file_type = "🖼️ " if file.suffix == ".png" else "📄"
                print(f"   {file_type} {file.name} ({size_kb} KB)")
        else:
            print("No files generated")
    
    print("\n🎉 Demo complete!")
    print("💡 This workflow works the same on Windows, macOS, and Linux")

if __name__ == "__main__":
    main()
