from __future__ import annotations

import math
from typing import Iterable, List, Optional, Sequence, Tuple

import numpy as np


def _rx(a: float) -> np.ndarray:
    c = math.cos(a)
    s = math.sin(a)
    return np.array([[1.0, 0.0, 0.0], [0.0, c, -s], [0.0, s, c]], dtype=np.float64)


def _ry(a: float) -> np.ndarray:
    c = math.cos(a)
    s = math.sin(a)
    return np.array([[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]], dtype=np.float64)


def _rz(a: float) -> np.ndarray:
    c = math.cos(a)
    s = math.sin(a)
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]], dtype=np.float64)


def euler_matrix(pitch_deg: float, yaw_deg: float, roll_deg: float, order: str) -> np.ndarray:
    rpx = math.radians(pitch_deg)
    ryw = math.radians(yaw_deg)
    rrl = math.radians(roll_deg)

    rx = _rx(rpx)
    ry = _ry(ryw)
    rz = _rz(rrl)

    # Orders: compose as R = A @ B @ C meaning first C, then B, then A
    if order.lower() in ("zxy", "rzrxry"):
        return _rz(ryw) @ _rx(pitch_deg * math.pi / 180.0) @ _ry(rrl)
    
    if order.lower() in ("yxz", "ryrxrz"):
        return _ry(ryw) @ _rx(pitch_deg * math.pi / 180.0) @ _rz(rrl)

    if order.lower() in ("zyx", "rzryrx"):
        return _rz(ryw) @ _ry(rrl) @ _rx(pitch_deg * math.pi / 180.0)

    # Fallback: Source-like QAngle commonly yaw(Z), pitch(X), roll(Y)
    return _rz(ryw) @ _rx(rpx) @ _ry(rrl)


def euler_matrix_named(pitch_deg: float, yaw_deg: float, roll_deg: float, name: str) -> np.ndarray:
    # Provide clear named variants
    name_l = name.lower()
    if name_l in ("rz_rx_ry", "zxy"):
        return _rz(math.radians(yaw_deg)) @ _rx(math.radians(pitch_deg)) @ _ry(math.radians(roll_deg))
    if name_l in ("ry_rx_rz", "yxz"):
        return _ry(math.radians(yaw_deg)) @ _rx(math.radians(pitch_deg)) @ _rz(math.radians(roll_deg))
    if name_l in ("rz_ry_rx", "zyx"):
        return _rz(math.radians(yaw_deg)) @ _ry(math.radians(roll_deg)) @ _rx(math.radians(pitch_deg))
    return _rz(math.radians(yaw_deg)) @ _rx(math.radians(pitch_deg)) @ _ry(math.radians(roll_deg))


def apply_srt(
    vertices: np.ndarray,
    scales: Sequence[float],
    angles_deg: Sequence[float],
    origin: Sequence[float],
    order: str = "rz_rx_ry",
    gameplay_scale: float = 1.0,
) -> np.ndarray:
    v = np.asarray(vertices, dtype=np.float64)
    s = np.asarray(scales, dtype=np.float64)
    a = np.asarray(angles_deg, dtype=np.float64)
    o = np.asarray(origin, dtype=np.float64)

    # Apply entity scales first, then gameplay scale for area representation
    vs = v * s[None, :] * gameplay_scale
    R = euler_matrix_named(float(a[0]), float(a[1]), float(a[2]), order)
    vr = vs @ R.T
    vt = vr + o[None, :]
    return vt


def to_xy(vertices_world: np.ndarray) -> np.ndarray:
    v = np.asarray(vertices_world, dtype=np.float64)
    return v[:, :2]


def dedupe_points(points: np.ndarray, eps: float = 1e-5) -> np.ndarray:
    if len(points) == 0:
        return points
    p = np.asarray(points, dtype=np.float64)
    # Round to grid to dedupe robustly
    q = np.round(p / eps).astype(np.int64)
    _, idx = np.unique(q, axis=0, return_index=True)
    return p[np.sort(idx)]


def _cross(o: np.ndarray, a: np.ndarray, b: np.ndarray) -> float:
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def convex_hull(points: np.ndarray) -> np.ndarray:
    pts = dedupe_points(points)
    if len(pts) <= 1:
        return pts
    pts = np.array(sorted(pts.tolist()))
    lower: List[List[float]] = []
    for pt in pts:
        while len(lower) >= 2 and _cross(np.array(lower[-2]), np.array(lower[-1]), np.array(pt)) <= 0:
            lower.pop()
        lower.append([pt[0], pt[1]])
    upper: List[List[float]] = []
    for pt in reversed(pts):
        while len(upper) >= 2 and _cross(np.array(upper[-2]), np.array(upper[-1]), np.array(pt)) <= 0:
            upper.pop()
        upper.append([pt[0], pt[1]])
    ch = np.array(lower[:-1] + upper[:-1], dtype=np.float64)
    return ch


def scale_polygon_to_global_scale(polygon: np.ndarray, global_scale: Sequence[float]) -> np.ndarray:
    """
    Scale a polygon to match the Global Scale dimensions from physics properties.
    
    Args:
        polygon: Original polygon vertices
        global_scale: Target dimensions [width, height, depth] from GLB physics
        
    Returns:
        Scaled polygon matching Global Scale dimensions
    """
    if len(polygon) == 0 or len(global_scale) < 2:
        return polygon
    
    # Calculate current polygon dimensions
    min_coords = polygon.min(axis=0)
    max_coords = polygon.max(axis=0)
    current_dims = max_coords - min_coords
    
    # Target dimensions from Global Scale (use X and Y)
    target_width = global_scale[0]
    target_height = global_scale[1]
    
    # Calculate scale factors
    scale_x = target_width / current_dims[0] if current_dims[0] > 0 else 1.0
    scale_y = target_height / current_dims[1] if current_dims[1] > 0 else 1.0
    
    # Calculate centroid for scaling origin
    centroid = polygon.mean(axis=0)
    
    # Scale polygon around its centroid
    scaled_polygon = centroid + (polygon - centroid) * np.array([scale_x, scale_y])
    
    return scaled_polygon


def apply_global_scale_multiplier(polygon: np.ndarray, multiplier: float, origin: Optional[Sequence[float]] = None) -> np.ndarray:
    """
    Apply a uniform scale multiplier to a polygon around a specified origin or its centroid.
    
    Args:
        polygon: Input polygon vertices
        multiplier: Scale factor to apply (e.g., 2.0 for 2x scaling)
        origin: Optional scaling origin point [x, y]. If None, uses polygon centroid.
        
    Returns:
        Uniformly scaled polygon
    """
    if len(polygon) == 0 or multiplier <= 0:
        return polygon
    
    # Use provided origin or calculate centroid for scaling origin
    if origin is not None and len(origin) >= 2:
        scale_origin = np.array([origin[0], origin[1]])
    else:
        scale_origin = polygon.mean(axis=0)
    
    # Scale polygon around the scaling origin
    scaled_polygon = scale_origin + (polygon - scale_origin) * multiplier
    
    return scaled_polygon


def expand_callout_polygon(polygon: np.ndarray, min_radius: float = 100.0) -> np.ndarray:
    """
    Expand a callout polygon to represent a meaningful gameplay area.
    
    Args:
        polygon: Original polygon vertices
        min_radius: Minimum radius for the expanded area in game units
        
    Returns:
        Expanded polygon representing gameplay area
    """
    if len(polygon) == 0:
        return polygon
    
    # Calculate centroid
    centroid = polygon.mean(axis=0)
    
    # Calculate current radius (distance from centroid to furthest vertex)
    distances = np.linalg.norm(polygon - centroid, axis=1)
    current_radius = distances.max()
    
    # If already large enough, return as-is
    if current_radius >= min_radius:
        return polygon
    
    # Calculate expansion factor
    expansion_factor = min_radius / current_radius
    
    # Expand polygon around centroid
    expanded = centroid + (polygon - centroid) * expansion_factor
    
    return expanded


def polygon_area(poly: np.ndarray) -> float:
    if len(poly) < 3:
        return 0.0
    x = poly[:, 0]
    y = poly[:, 1]
    return 0.5 * float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))


def detailed_2d_projection(vertices_world: np.ndarray, method: str = "top_down") -> np.ndarray:
    """
    Create a detailed 2D projection from full 3D model geometry.
    
    Args:
        vertices_world: Full 3D vertices in world coordinates
        method: Projection method - "top_down", "alpha_shape", or "convex_hull"
        
    Returns:
        np.ndarray: 2D polygon vertices representing the projection
    """
    if len(vertices_world) == 0:
        return np.array([])
    
    if method == "top_down":
        # Project all vertices to XY plane and find alpha shape or boundary
        xy_points = to_xy(vertices_world)
        return alpha_shape_2d(xy_points)
    elif method == "alpha_shape":
        # Use alpha shape for more detailed boundary
        xy_points = to_xy(vertices_world)
        return alpha_shape_2d(xy_points, alpha=0.1)
    else:
        # Fallback to convex hull
        xy_points = to_xy(vertices_world)
        return convex_hull(xy_points)


def alpha_shape_2d(points: np.ndarray, alpha: float = 0.1) -> np.ndarray:
    """
    Compute alpha shape (concave hull) for more detailed 2D boundary.
    Falls back to convex hull if alpha shape computation fails.
    
    Args:
        points: 2D points array
        alpha: Alpha parameter (smaller = more detailed, larger = more convex)
        
    Returns:
        np.ndarray: 2D polygon boundary points
    """
    pts = dedupe_points(points)
    if len(pts) <= 3:
        return pts
    
    try:
        # Try to use alphashape library if available
        import alphashape
        alpha_shape = alphashape.alphashape(pts, alpha)
        
        if hasattr(alpha_shape, 'exterior'):
            # Polygon case
            boundary = np.array(alpha_shape.exterior.coords[:-1])
            return boundary
        elif hasattr(alpha_shape, 'geoms'):
            # MultiPolygon case - take largest polygon
            largest_poly = max(alpha_shape.geoms, key=lambda p: p.area)
            boundary = np.array(largest_poly.exterior.coords[:-1])
            return boundary
        else:
            # Fallback to convex hull
            return convex_hull(pts)
            
    except ImportError:
        # Alphashape not available, use concave hull approximation
        return concave_hull_approximation(pts)
    except Exception:
        # Any other error, fallback to convex hull
        return convex_hull(pts)


def concave_hull_approximation(points: np.ndarray, k: int = 3) -> np.ndarray:
    """
    Approximate concave hull using k-nearest neighbors approach.
    More detailed than convex hull but doesn't require external libraries.
    """
    pts = dedupe_points(points)
    if len(pts) <= 3:
        return pts
    
    try:
        from scipy.spatial import cKDTree
        
        # Build KD-tree for efficient nearest neighbor queries
        tree = cKDTree(pts)
        
        # Start with leftmost point
        current_idx = np.argmin(pts[:, 0])
        hull_indices = [current_idx]
        current_point = pts[current_idx]
        
        while True:
            # Find k nearest neighbors
            k_actual = min(k, len(pts) - 1)
            distances, neighbor_indices = tree.query(current_point, k=k_actual + 1)
            
            # Remove current point from neighbors
            neighbor_indices = neighbor_indices[neighbor_indices != current_idx]
            
            if len(neighbor_indices) == 0:
                break
                
            # Choose next point based on angle (rightmost turn)
            best_angle = -np.pi
            next_idx = neighbor_indices[0]
            
            for idx in neighbor_indices:
                if idx in hull_indices:
                    continue
                    
                neighbor = pts[idx]
                # Calculate angle from current direction
                if len(hull_indices) > 1:
                    prev_point = pts[hull_indices[-2]]
                    v1 = current_point - prev_point
                    v2 = neighbor - current_point
                    angle = np.arctan2(np.cross(v1, v2), np.dot(v1, v2))
                else:
                    # First edge, use rightmost point
                    angle = np.arctan2(neighbor[1] - current_point[1], 
                                     neighbor[0] - current_point[0])
                
                if angle > best_angle:
                    best_angle = angle
                    next_idx = idx
            
            # Check if we've completed the hull
            if next_idx == hull_indices[0]:
                break
                
            if next_idx in hull_indices:
                break
                
            hull_indices.append(next_idx)
            current_idx = next_idx
            current_point = pts[current_idx]
            
            # Prevent infinite loops
            if len(hull_indices) > len(pts):
                break
        
        return pts[hull_indices]
        
    except ImportError:
        # Fallback to convex hull if scipy not available
        return convex_hull(pts)
    except Exception:
        # Any error, fallback to convex hull
        return convex_hull(pts)


def bbox2d(points: np.ndarray) -> Tuple[float, float, float, float]:
    """
    Calculates the axis-aligned bounding box for a set of 2D points.

    Args:
        points (np.ndarray): An array of shape (N, 2) representing N 2D points.

    Returns:
        Tuple[float, float, float, float]: A tuple (min_x, min_y, max_x, max_y) representing
        the coordinates of the bounding box. If points is empty, returns (0.0, 0.0, 0.0, 0.0).
    """
    if len(points) == 0:
        return (0.0, 0.0, 0.0, 0.0)
    mn = points.min(axis=0)
    mx = points.max(axis=0)
    return (float(mn[0]), float(mn[1]), float(mx[0]), float(mx[1]))


def zspan_xyspan_ratio(vertices_world: np.ndarray) -> float:
    if len(vertices_world) == 0:
        return 0.0
    zspan = float(vertices_world[:, 2].max() - vertices_world[:, 2].min())
    xspan = float(vertices_world[:, 0].max() - vertices_world[:, 0].min())
    yspan = float(vertices_world[:, 1].max() - vertices_world[:, 1].min())
    xy = max(xspan, yspan)
    if xy <= 1e-9:
        return float("inf")
    return zspan / xy


def bbox_3d(points: np.ndarray) -> Tuple[float, float, float, float, float, float]:
    """
    Calculates the axis-aligned bounding box for a set of 3D points.

    Args:
        points (np.ndarray): An array of shape (N, 3) representing N 3D points.

    Returns:
        Tuple[float, float, float, float, float, float]: A tuple (min_x, min_y, min_z, max_x, max_y, max_z) 
        representing the coordinates of the bounding box. If points is empty, returns all zeros.
    """
    if len(points) == 0:
        return (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    mn = points.min(axis=0)
    mx = points.max(axis=0)
    return (float(mn[0]), float(mn[1]), float(mn[2]), float(mx[0]), float(mx[1]), float(mx[2]))


def convex_hull_3d(points: np.ndarray) -> np.ndarray:
    """
    Computes the 3D convex hull of a set of points using scipy.spatial.ConvexHull.
    Returns the vertices of the convex hull in 3D space.

    Args:
        points (np.ndarray): An array of shape (N, 3) representing N 3D points.

    Returns:
        np.ndarray: An array of shape (M, 3) representing the M vertices of the convex hull.
    """
    pts = dedupe_points_3d(points)
    if len(pts) <= 3:
        return pts
        
    try:
        from scipy.spatial import ConvexHull
        hull = ConvexHull(pts)
        return pts[hull.vertices]
    except ImportError:
        # Fallback: return all unique points if scipy not available
        return pts
    except Exception:
        # Fallback for degenerate cases
        return pts


def dedupe_points_3d(points: np.ndarray, eps: float = 1e-5) -> np.ndarray:
    """Remove duplicate points in 3D space."""
    if len(points) == 0:
        return points
    p = np.asarray(points, dtype=np.float64)
    # Round to grid to dedupe robustly
    scale = 1.0 / eps
    rounded = np.round(p * scale)
    _, unique_indices = np.unique(rounded, axis=0, return_index=True)
    return p[unique_indices]


ROTATION_CANDIDATES = (
    "rz_rx_ry",  # yaw(Z), pitch(X), roll(Y)
    "ry_rx_rz",  # yaw(Y), pitch(X), roll(Z)
    "rz_ry_rx",  # yaw(Z), roll(Y), pitch(X)
)


def expand_polygon_to_gameplay_area(polygon: np.ndarray, min_radius: float = 64.0) -> np.ndarray:
    """
    Expand a small polygon to represent a meaningful gameplay area.
    
    CS2 callout models are tiny (8-16 game units) but should represent larger
    gameplay areas (~128 game units = ~25 pixels at standard scale).
    
    Args:
        polygon: Original polygon vertices in game coordinates
        min_radius: Minimum radius for gameplay area in game units
        
    Returns:
        np.ndarray: Expanded polygon representing gameplay area
    """
    if len(polygon) == 0:
        return polygon
        
    # Calculate current polygon center and size
    x_coords = polygon[:, 0]
    y_coords = polygon[:, 1]
    center_x = np.mean(x_coords)
    center_y = np.mean(y_coords)
    
    # Calculate current radius (distance from center to furthest point)
    distances = np.sqrt((x_coords - center_x)**2 + (y_coords - center_y)**2)
    current_radius = np.max(distances)
    
    # If already large enough, return as-is
    if current_radius >= min_radius:
        return polygon
        
    # Calculate expansion factor needed
    expansion_factor = min_radius / max(current_radius, 1e-6)
    
    # Expand polygon around center to gameplay size
    expanded_polygon = np.zeros_like(polygon)
    for i, (x, y) in enumerate(polygon):
        # Vector from center to vertex
        dx = x - center_x
        dy = y - center_y
        
        # Expand along this vector
        expanded_polygon[i, 0] = center_x + dx * expansion_factor
        expanded_polygon[i, 1] = center_y + dy * expansion_factor
        
    return expanded_polygon


def choose_best_order(vertices: np.ndarray, scales: Sequence[float], angles_deg: Sequence[float], origin: Sequence[float]) -> Tuple[str, float]:
    best = (ROTATION_CANDIDATES[0], float("inf"))
    for cand in ROTATION_CANDIDATES:
        w = apply_srt(vertices, scales, angles_deg, origin, order=cand)
        ratio = zspan_xyspan_ratio(w)
        if ratio < best[1]:
            best = (cand, ratio)
    return best


def choose_global_order(
    samples: Iterable[Tuple[np.ndarray, Sequence[float], Sequence[float], Sequence[float]]],
    limit: int = 8,
) -> str:
    ratios = {cand: [] for cand in ROTATION_CANDIDATES}
    count = 0
    for vertices, scales, angles, origin in samples:
        for cand in ROTATION_CANDIDATES:
            w = apply_srt(vertices, scales, angles, origin, order=cand)
            ratios[cand].append(zspan_xyspan_ratio(w))
        count += 1
        if count >= limit:
            break
    best = min(
        (
            (cand, (sum(vals) / len(vals)) if vals else float("inf"))
            for cand, vals in ratios.items()
        ),
        key=lambda x: x[1],
    )[0]
    return best

