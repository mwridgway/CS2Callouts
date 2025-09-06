from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

from .gltf_loader import load_vertices
from .geometry import (
    ROTATION_CANDIDATES,
    apply_srt,
    bbox2d,
    choose_global_order,
    convex_hull,
    polygon_area,
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


def load_vertices_cache(callouts: Iterable[Callout], index: Dict[str, Path]) -> Dict[str, np.ndarray]:
    cache: Dict[str, np.ndarray] = {}
    for c in callouts:
        mid = _normalize_model_id(c.model)
        if mid in cache:
            continue
        fp = resolve_model_file(c.model, index)
        if not fp:
            continue
        try:
            cache[mid] = load_vertices(fp)
        except Exception:
            continue
    return cache


def choose_order_auto(callouts: List[Callout], vcache: Dict[str, np.ndarray], limit: int = 6) -> str:
    samples: List[Tuple[np.ndarray, Sequence[float], Sequence[float], Sequence[float]]] = []
    for c in callouts:
        mid = _normalize_model_id(c.model)
        v = vcache.get(mid)
        if v is None:
            continue
        samples.append((v, c.scales, c.angles, c.origin))
        if len(samples) >= limit:
            break
    if not samples:
        return ROTATION_CANDIDATES[0]
    return choose_global_order(samples, limit=limit)


def process_callouts(
    callouts: List[Callout],
    models_root: str | Path,
    rotation_order: str = "auto",
) -> Dict:
    index = build_model_index(models_root)
    vcache = load_vertices_cache(callouts, index)
    order = rotation_order
    if rotation_order == "auto":
        order = choose_order_auto(callouts, vcache)

    results = []
    missing_models = []
    for c in callouts:
        mid = _normalize_model_id(c.model)
        verts = vcache.get(mid)
        if verts is None:
            fp = resolve_model_file(c.model, index)
            missing_models.append({"placename": c.placename, "model": c.model, "resolved": str(fp) if fp else None})
            continue
        world = apply_srt(verts, c.scales, c.angles, c.origin, order=order)
        poly2d = convex_hull(to_xy(world))
        bbox = bbox2d(poly2d)
        record = {
            "name": c.placename,
            "model": c.model,
            "origin": [float(x) for x in c.origin],
            "angles": [float(x) for x in c.angles],
            "scales": [float(x) for x in c.scales],
            "rotation_order": order,
            "vertices_count": int(len(verts)),
            "polygon_2d": [[float(x), float(y)] for x, y in poly2d.tolist()],
            "bbox_2d": {"min_x": bbox[0], "min_y": bbox[1], "max_x": bbox[2], "max_y": bbox[3]},
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
