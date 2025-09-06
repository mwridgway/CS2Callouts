from __future__ import annotations

import math
from typing import Iterable, List, Sequence, Tuple

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
) -> np.ndarray:
    v = np.asarray(vertices, dtype=np.float64)
    s = np.asarray(scales, dtype=np.float64)
    a = np.asarray(angles_deg, dtype=np.float64)
    o = np.asarray(origin, dtype=np.float64)

    vs = v * s[None, :]
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


def polygon_area(poly: np.ndarray) -> float:
    if len(poly) < 3:
        return 0.0
    x = poly[:, 0]
    y = poly[:, 1]
    return 0.5 * float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))


def bbox2d(points: np.ndarray) -> Tuple[float, float, float, float]:
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


ROTATION_CANDIDATES = (
    "rz_rx_ry",  # yaw(Z), pitch(X), roll(Y)
    "ry_rx_rz",  # yaw(Y), pitch(X), roll(Z)
    "rz_ry_rx",  # yaw(Z), roll(Y), pitch(X)
)


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

