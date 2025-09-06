from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np


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

