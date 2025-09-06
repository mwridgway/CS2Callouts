#!/usr/bin/env python3
"""
Extract all CS2 active duty maps
Cross-platform replacement for extract_all_maps.ps1
"""

import subprocess
import sys
from pathlib import Path

def run_command(cmd, description=""):
    """Run a command and return success status"""
    if description:
        print(f"   🔄 {description}...")
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def main():
    print("🗺️ CS2 Active Duty Maps - Extraction Script")
    print("=" * 50)

    # Check current status
    print("\n📊 Checking current status...")
    subprocess.run("python -m cs2_callouts status", shell=True)

    # Define all active duty maps
    active_duty_maps = [
        "de_ancient",
        "de_anubis", 
        "de_dust2",
        "de_inferno",
        "de_mirage",
        "de_nuke",
        "de_overpass",
        "de_vertigo"
    ]

    print("\n🔄 Starting extraction for all active duty maps...")
    print("⚠️  This requires CS2 VPK files and may take a while!")

    extracted_count = 0
    failed_maps = []

    for map_name in active_duty_maps:
        export_path = Path(f"export/maps/{map_name}/report/callouts_found.json")
        
        if export_path.exists():
            print(f"   ✅ {map_name} already extracted")
            extracted_count += 1
        else:
            print(f"   🔄 Extracting {map_name}...")
            success, output = run_command(f"python -m cs2_callouts extract --map {map_name}")
            
            if success and export_path.exists():
                print(f"   ✅ {map_name} extraction complete")
                extracted_count += 1
            else:
                print(f"   ❌ {map_name} extraction failed")
                failed_maps.append(map_name)

    print(f"\n📊 Extraction Summary:")
    print(f"   ✅ Successfully extracted: {extracted_count}/{len(active_duty_maps)} maps")

    if failed_maps:
        print(f"   ❌ Failed extractions: {', '.join(failed_maps)}")
        print(f"\n💡 Common issues:")
        print(f"   • CS2 VPK files not found or accessible")
        print(f"   • VRF CLI not properly setup")
        print(f"   • Insufficient disk space")
        print(f"\n🔧 Try:")
        print(f"   python -m cs2_callouts setup")
        print(f"   python -m cs2_callouts check-env")

    print(f"\n📈 Next steps:")
    if extracted_count > 0:
        print(f"   🚀 Process all extracted maps:")
        print(f"   python -m cs2_callouts process --map all --global-scale-multiplier 2.0")
        print(f"   📊 Check status:")
        print(f"   python -m cs2_callouts status")
    else:
        print(f"   🔧 Fix extraction issues first")

    print(f"\n🎉 Extraction script complete!")

if __name__ == "__main__":
    main()
