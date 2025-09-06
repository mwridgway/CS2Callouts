#!/usr/bin/env python3

import json
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon
from PIL import Image

# Load data
data = json.load(open('out/de_mirage_callouts.json'))
callouts = data['callouts']

# Load map metadata
map_metadata = json.load(open('map-data.json'))['de_mirage']
scale = map_metadata['scale']
pos_x = map_metadata['pos_x'] 
pos_y = map_metadata['pos_y']

print(f"Map metadata: scale={scale}, pos_x={pos_x}, pos_y={pos_y}")

# Transform one callout for debugging
first_callout = callouts[0]
name = first_callout['name']
poly = first_callout['polygon_2d']

print(f"\nDebugging callout: {name}")
print(f"Original polygon (game coords): {poly}")

# Transform to pixel coordinates
pixel_poly = []
for x, y in poly:
    pixel_x = (float(x) - pos_x) / scale
    pixel_y = (pos_y - float(y)) / scale  # Y inverted
    pixel_poly.append([pixel_x, pixel_y])

print(f"Transformed polygon (pixel coords): {pixel_poly}")

# Calculate polygon size in pixels
if len(pixel_poly) >= 2:
    min_x = min(p[0] for p in pixel_poly)
    max_x = max(p[0] for p in pixel_poly)
    min_y = min(p[1] for p in pixel_poly)
    max_y = max(p[1] for p in pixel_poly)
    width_pixels = max_x - min_x
    height_pixels = max_y - min_y
    print(f"Polygon size in pixels: {width_pixels:.2f} x {height_pixels:.2f}")
    
    if width_pixels < 1 or height_pixels < 1:
        print("⚠️  PROBLEM: Polygon is less than 1 pixel in size!")
    else:
        print("✅ Polygon size looks reasonable")
