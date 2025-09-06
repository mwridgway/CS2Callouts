#!/usr/bin/env python3

import json
from pathlib import Path

# Load the callout data
data = json.load(open('out/de_mirage_callouts.json'))
callouts = data['callouts']

print(f"Found {len(callouts)} callouts")
print()

for i, callout in enumerate(callouts[:5]):
    name = callout.get('name', 'Unknown')
    poly = callout.get('polygon_2d', [])
    bbox = callout.get('bbox_2d', {})
    
    print(f"{i+1}. {name}")
    print(f"   Vertices: {len(poly)}")
    if poly:
        print(f"   First vertex: {poly[0]}")
        print(f"   Last vertex: {poly[-1]}")
    if bbox:
        width = bbox.get('max_x', 0) - bbox.get('min_x', 0)
        height = bbox.get('max_y', 0) - bbox.get('min_y', 0)
        print(f"   BBox size: {width:.2f} x {height:.2f} units")
    print()
