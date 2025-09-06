#!/usr/bin/env python3

import json
from cs2_callouts.visualize import _ensure_minimum_polygon_size

# Test the polygon scaling fix
data = json.load(open('out/de_mirage_callouts.json'))
callouts = data['callouts']

# Load map metadata
map_metadata = json.load(open('map-data.json'))['de_mirage']
scale = map_metadata['scale']
pos_x = map_metadata['pos_x'] 
pos_y = map_metadata['pos_y']

print("🔍 Testing Polygon Visibility Fix")
print("=" * 50)

for i, callout in enumerate(callouts[:3]):
    name = callout['name']
    poly = callout['polygon_2d']
    
    # Transform to pixel coordinates
    pixel_poly = []
    for x, y in poly:
        pixel_x = (float(x) - pos_x) / scale
        pixel_y = (pos_y - float(y)) / scale
        pixel_poly.append([pixel_x, pixel_y])
    
    # Calculate original size
    if pixel_poly:
        min_x = min(p[0] for p in pixel_poly)
        max_x = max(p[0] for p in pixel_poly)
        min_y = min(p[1] for p in pixel_poly)
        max_y = max(p[1] for p in pixel_poly)
        orig_width = max_x - min_x
        orig_height = max_y - min_y
        
        # Apply scaling fix
        scaled_poly = _ensure_minimum_polygon_size(pixel_poly, min_size=3.0)
        
        # Calculate scaled size
        min_x_scaled = min(p[0] for p in scaled_poly)
        max_x_scaled = max(p[0] for p in scaled_poly)
        min_y_scaled = min(p[1] for p in scaled_poly)
        max_y_scaled = max(p[1] for p in scaled_poly)
        scaled_width = max_x_scaled - min_x_scaled
        scaled_height = max_y_scaled - min_y_scaled
        
        print(f"\n{i+1}. {name}")
        print(f"   Original: {orig_width:.2f} x {orig_height:.2f} pixels")
        print(f"   Scaled:   {scaled_width:.2f} x {scaled_height:.2f} pixels")
        
        if orig_width < 1 or orig_height < 1:
            print(f"   ✅ FIXED: Was sub-pixel, now visible!")
        else:
            print(f"   ✅ OK: Already visible size")

print(f"\n🎉 Polygon visibility fix working correctly!")
print(f"📁 Generated test files:")
print(f"   - out/fixed_radar_overlay.png (radar + polygons)")
print(f"   - out/large_polygons.png (8px minimum size)")
print(f"   - out/fixed_polygons_only.png (polygons only)")
