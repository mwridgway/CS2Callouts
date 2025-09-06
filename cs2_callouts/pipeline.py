from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

from .gltf_loader import load_vertices, load_vertices_with_physics
from .geometry import (
    ROTATION_CANDIDATES,
    apply_srt,
    bbox2d,
    bbox_3d,
    choose_global_order,
    convex_hull,
    convex_hull_3d,
    detailed_2d_projection,
    expand_callout_polygon,
    polygon_area,
    scale_polygon_to_global_scale,
    apply_global_scale_multiplier,
    to_xy,
    zspan_xyspan_ratio,
)


@dataclass
class Callout:
    placename: Optional[str]
    model: str
    origin: Sequence[float]
    angles: Sequence[float]
    scales: Sequence[float]
    source_file: Optional[str] = None


def _to_floats(seq) -> List[float]:
    return [float(x) for x in seq] if seq is not None else [0.0, 0.0, 0.0]


def read_callouts_json(path: str | Path) -> List[Callout]:
    p = Path(path)
    # Some exporters write UTF-8 with BOM; be tolerant by using utf-8-sig
    data = json.loads(p.read_text(encoding="utf-8-sig"))
    out: List[Callout] = []
    if isinstance(data, dict):
        items = data.get("callouts") or data.get("items") or data.get("data") or []
    else:
        items = data
    for it in items:
        out.append(
            Callout(
                placename=it.get("placename") or it.get("name"),
                model=str(it.get("model")),
                origin=_to_floats(it.get("origin")),
                angles=_to_floats(it.get("angles")),
                scales=_to_floats(it.get("scales")) if it.get("scales") else [1.0, 1.0, 1.0],
                source_file=it.get("file"),
            )
        )
    return out


def _normalize_model_id(model_path: str) -> str:
    s = model_path.replace("\\", "/").lower()
    s = s.replace(".vmdl_c", "").replace(".vmdl", "")
    if s.endswith("_c") and not s.endswith(".vmdl_c"):
        s = s[:-2]
    return s


def build_model_index(models_root: str | Path) -> Dict[str, Path]:
    root = Path(models_root)
    files = list(root.rglob("*.glb")) + list(root.rglob("*.gltf"))
    idx: Dict[str, Path] = {}
    for f in files:
        rel = str(f.relative_to(root)).replace("\\", "/").lower()
        base = f.stem.lower()
        idx[rel.replace(".glb", "").replace(".gltf", "")] = f
        idx[base] = f
    return idx


def resolve_model_file(model_path: str, index: Dict[str, Path]) -> Optional[Path]:
    mid = _normalize_model_id(model_path)
    # Prefer physics mesh if available
    mid_phys = f"{mid}_physics"
    if mid_phys in index:
        return index[mid_phys]
    if mid in index:
        return index[mid]
    # Try matching by suffix; prefer *_physics
    suffix = Path(mid).name
    phys_candidates = [(k, v) for k, v in index.items() if k.endswith(f"{suffix}_physics")]
    if phys_candidates:
        return phys_candidates[0][1]
    for key, fp in index.items():
        if key.endswith(suffix):
            return fp
    return None


def load_vertices_cache(callouts: Iterable[Callout], index: Dict[str, Path]) -> Dict[str, Tuple[np.ndarray, Dict]]:
    """Load vertices and physics properties for each unique model"""
    cache: Dict[str, Tuple[np.ndarray, Dict]] = {}
    for c in callouts:
        mid = _normalize_model_id(c.model)
        if mid in cache:
            continue
        fp = resolve_model_file(c.model, index)
        if not fp:
            continue
        try:
            vertices, physics_props = load_vertices_with_physics(fp)
            cache[mid] = (vertices, physics_props)
        except Exception:
            # Fallback to regular loading
            try:
                vertices = load_vertices(fp)
                default_props = {
                    'position': [0.0, 0.0, 0.0],
                    'rotation': [0.0, 0.0, 0.0], 
                    'scale': [1.0, 1.0, 1.0],
                    'global_scale': [1.0, 1.0, 1.0],
                    'has_physics_data': False
                }
                cache[mid] = (vertices, default_props)
            except Exception:
                continue
    return cache


def choose_order_auto(callouts: List[Callout], vcache: Dict[str, Tuple[np.ndarray, Dict]], limit: int = 6) -> str:
    samples: List[Tuple[np.ndarray, Sequence[float], Sequence[float], Sequence[float]]] = []
    for c in callouts:
        if len(samples) >= limit:
            break
        mid = _normalize_model_id(c.model)
        cache_entry = vcache.get(mid)
        if cache_entry is None:
            continue
        verts, physics_props = cache_entry
        if len(verts) == 0:
            continue
        samples.append((verts, c.scales, c.angles, c.origin))
    if not samples:
        return ROTATION_CANDIDATES[0]
    return choose_global_order(samples)

def process_callouts(
    callouts: List[Callout],
    models_root: str | Path,
    rotation_order: str = "auto",
    projection_method: str = "top_down",
    gameplay_scale: float = 10.0,
    global_scale_multiplier: float = 1.0,
) -> Dict:
    """
    Processes a list of callouts by applying model transformations and extracting geometric information.

    Args:
        callouts (List[Callout]): A list of Callout objects containing model and transformation data.
        models_root (str | Path): Path to the root directory containing model files.
        rotation_order (str, optional): The rotation order to use for transformations. Defaults to "auto".
        projection_method (str, optional): Method for 2D projection. Options: "top_down", "alpha_shape", "convex_hull". Defaults to "top_down".
        gameplay_scale (float, optional): Scale factor to expand callouts to represent gameplay areas. Defaults to 10.0.
        global_scale_multiplier (float, optional): Global multiplier applied to all polygon dimensions after physics-based scaling. Defaults to 1.0.

    Returns:
        Dict: A dictionary containing:
            - "rotation_order": The rotation order used.
            - "count": Number of successfully processed callouts.
            - "missing_models": List of callouts with missing models and their resolved file paths.
            - "callouts": List of processed callout records with geometric and source information.
    """
    index = build_model_index(models_root)
    vcache = load_vertices_cache(callouts, index)
    order = rotation_order
    if rotation_order == "auto":
        order = choose_order_auto(callouts, vcache)

    results = []
    missing_models = []
    for c in callouts:
        mid = _normalize_model_id(c.model)
        cache_entry = vcache.get(mid)
        if cache_entry is None:
            fp = resolve_model_file(c.model, index)
            missing_models.append({"placename": c.placename, "model": c.model, "resolved": str(fp) if fp else None})
            continue
            
        verts, physics_props = cache_entry
        world = apply_srt(verts, c.scales, c.angles, c.origin, order=order)
        
        # Create detailed 2D projection from full 3D model
        poly2d = detailed_2d_projection(world, method=projection_method)
        
        # Use physics properties to scale polygon to correct Global Scale
        if physics_props.get('has_physics_data', False):
            global_scale = physics_props.get('global_scale', [1.0, 1.0, 1.0])
            poly2d_scaled = scale_polygon_to_global_scale(poly2d, global_scale)
        else:
            # Fallback: expand polygon for models without physics data
            poly2d_scaled = expand_callout_polygon(poly2d, min_radius=100.0)
        
        # Apply global scale multiplier if specified
        if global_scale_multiplier != 1.0:
            poly2d_final = apply_global_scale_multiplier(poly2d_scaled, global_scale_multiplier)
        else:
            poly2d_final = poly2d_scaled
            
        bbox = bbox2d(poly2d_final)
        
        # Compute 3D convex hull for full spatial data
        poly3d = convex_hull_3d(world)
        bbox3d = bbox_3d(world)
        
        record = {
            "name": c.placename,
            "model": c.model,
            "origin": [float(x) for x in c.origin],
            "angles": [float(x) for x in c.angles],
            "scales": [float(x) for x in c.scales],
            "rotation_order": order,
            "projection_method": projection_method,
            "vertices_count": int(len(verts)),
            "physics_properties": physics_props,
            "polygon_2d": [[float(x), float(y)] for x, y in poly2d_final.tolist()],
            "bbox_2d": {"min_x": bbox[0], "min_y": bbox[1], "max_x": bbox[2], "max_y": bbox[3]},
            "polygon_3d": [[float(x), float(y), float(z)] for x, y, z in poly3d.tolist()],
            "bbox_3d": {
                "min_x": float(bbox3d[0]), "min_y": float(bbox3d[1]), "min_z": float(bbox3d[2]),
                "max_x": float(bbox3d[3]), "max_y": float(bbox3d[4]), "max_z": float(bbox3d[5])
            },
            "zspan_xyspan_ratio": zspan_xyspan_ratio(world),
            "source": c.source_file,
        }
        results.append(record)

    out = {
        "rotation_order": order,
        "count": len(results),
        "missing_models": missing_models,
        "callouts": results,
    }
    return out


def write_json(data: Dict, out_path: str | Path, pretty: bool = True) -> None:
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if pretty:
        p.write_text(json.dumps(data, indent=2), encoding="utf-8")
    else:
        p.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
