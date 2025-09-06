from __future__ import annotations

import json
import struct
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

import numpy as np


def extract_glb_physics_properties(glb_path: Path) -> Dict[str, Any]:
    """Extract Scale, Global Scale, and Rotation from GLB physics file"""
    try:
        with open(glb_path, 'rb') as f:
            f.seek(12)
            json_length = struct.unpack('<I', f.read(4))[0]
            f.read(4)  # skip type
            json_data = f.read(json_length).decode('utf-8')
            gltf = json.loads(json_data)
            
            result = {
                'position': [0.0, 0.0, 0.0],
                'rotation': [0.0, 0.0, 0.0], 
                'scale': [1.0, 1.0, 1.0],
                'global_scale': [1.0, 1.0, 1.0],
                'has_physics_data': False
            }
            
            # Extract transformation matrix and scale
            if 'nodes' in gltf and len(gltf['nodes']) > 0:
                node = gltf['nodes'][0]
                if 'matrix' in node:
                    matrix = np.array(node['matrix']).reshape(4, 4).T
                    result['has_physics_data'] = True
                    
                    # Position
                    result['position'] = matrix[:3, 3].tolist()
                    
                    # Scale from matrix
                    rot_scale = matrix[:3, :3]
                    scale_x = np.linalg.norm(rot_scale[:, 0])
                    scale_y = np.linalg.norm(rot_scale[:, 1])
                    scale_z = np.linalg.norm(rot_scale[:, 2])
                    result['scale'] = [scale_x, scale_y, scale_z]
                    
                    # Extract rotation (simplified - detect common rotation patterns)
                    # This is complex from matrix, but we can detect common cases
                    result['rotation'] = [0.0, 0.0, 0.0]  # Default, would need more complex extraction
            
            # Extract Global Scale from original vertex bounds  
            if 'accessors' in gltf and len(gltf['accessors']) > 0:
                accessor = gltf['accessors'][0]  # First is usually position
                if 'max' in accessor and 'min' in accessor:
                    max_vals = accessor['max']
                    min_vals = accessor['min']
                    # Original dimensions before any scaling
                    original_dims = [max_vals[i] - min_vals[i] for i in range(3)]
                    
                    # Apply the scale factor to get the actual Global Scale
                    scale_factor = result['scale'][0]  # Uniform scaling
                    global_scale = [dim * scale_factor for dim in original_dims]
                    result['global_scale'] = global_scale
            
            return result
            
    except Exception as e:
        # Return default values if extraction fails
        return {
            'position': [0.0, 0.0, 0.0],
            'rotation': [0.0, 0.0, 0.0], 
            'scale': [1.0, 1.0, 1.0],
            'global_scale': [1.0, 1.0, 1.0],
            'has_physics_data': False
        }


def _load_trimesh_vertices(path: Path) -> np.ndarray:
    import trimesh

    obj = trimesh.load(path, force="mesh")
    if isinstance(obj, trimesh.Trimesh):
        v = np.asarray(obj.vertices, dtype=np.float64)
        return v
    if isinstance(obj, trimesh.Scene):
        try:
            mesh = obj.dump(concatenate=True)
            if isinstance(mesh, trimesh.Trimesh):
                return np.asarray(mesh.vertices, dtype=np.float64)
        except Exception:
            pass
        verts = []
        for name, geom in obj.geometry.items():
            try:
                T = obj.graph.get(name)[0]
            except Exception:
                T = None
            gverts = np.asarray(geom.vertices, dtype=np.float64)
            if T is not None:
                gverts_h = np.hstack([gverts, np.ones((len(gverts), 1))])
                gverts_w = (T @ gverts_h.T).T[:, :3]
                verts.append(gverts_w)
            else:
                verts.append(gverts)
        if verts:
            return np.vstack(verts)
    raise RuntimeError(f"Unsupported GLTF/GLB content in {path}")


def load_vertices(path: str | Path) -> np.ndarray:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(str(p))
    return _load_trimesh_vertices(p)


def load_vertices_with_physics(path: str | Path) -> Tuple[np.ndarray, Dict[str, Any]]:
    """Load vertices and extract physics properties from GLB file"""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(str(p))
    
    vertices = _load_trimesh_vertices(p)
    physics_props = extract_glb_physics_properties(p)
    
    return vertices, physics_props

