#!/usr/bin/env python3
"""
Simple cross-platform clean script
"""

import shutil
from pathlib import Path

def main():
    out_dir = Path("out")
    
    if out_dir.exists():
        shutil.rmtree(out_dir)
        print("✅ Cleaned out/ directory")
    else:
        print("ℹ️  out/ directory doesn't exist")
    
    out_dir.mkdir(exist_ok=True)
    print("✅ Created fresh out/ directory")

if __name__ == "__main__":
    main()
