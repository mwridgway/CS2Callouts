from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

import json
import math

import click
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon


def _load_output(path: str | Path) -> Dict:
    p = Path(path)
    return json.loads(p.read_text(encoding="utf-8-sig"))


def _centroid(poly: List[List[float]]) -> Tuple[float, float]:
    if not poly:
        return (0.0, 0.0)
    x = [pt[0] for pt in poly]
    y = [pt[1] for pt in poly]
    return (sum(x) / len(x), sum(y) / len(y))


def _ensure_minimum_polygon_size(poly: List[List[float]], min_size: float = 3.0) -> List[List[float]]:
    """Ensure polygon is at least min_size pixels in each dimension for visibility."""
    if not poly:
        return poly
    
    # Calculate current bounding box
    x_coords = [pt[0] for pt in poly]
    y_coords = [pt[1] for pt in poly]
    min_x, max_x = min(x_coords), max(x_coords)
    min_y, max_y = min(y_coords), max(y_coords)
    
    current_width = max_x - min_x
    current_height = max_y - min_y
    
    # If already large enough, return as-is
    if current_width >= min_size and current_height >= min_size:
        return poly
    
    # Calculate scaling factors needed
    scale_x = max(1.0, min_size / current_width) if current_width > 0 else 1.0
    scale_y = max(1.0, min_size / current_height) if current_height > 0 else 1.0
    
    # Use uniform scaling (larger of the two) to maintain aspect ratio
    scale = max(scale_x, scale_y)
    
    # Calculate centroid for scaling origin
    cx, cy = _centroid(poly)
    
    # Scale polygon around its centroid
    scaled_poly = []
    for x, y in poly:
        new_x = cx + (x - cx) * scale
        new_y = cy + (y - cy) * scale
        scaled_poly.append([new_x, new_y])
    
    return scaled_poly


def _color_for_name(name: str) -> Tuple[float, float, float]:
    # Deterministic pastel
    h = abs(hash(name)) % 360
    s = 0.5
    v = 0.95
    c = v * s
    x = c * (1 - abs(((h / 60) % 2) - 1))
    m = v - c
    if   0 <= h < 60:  r,g,b = c,x,0
    elif 60 <= h <120: r,g,b = x,c,0
    elif 120<= h<180: r,g,b = 0,c,x
    elif 180<= h<240: r,g,b = 0,x,c
    elif 240<= h<300: r,g,b = x,0, c
    else:             r,g,b = c,0, x
    return (r+m, g+m, b+m)


@click.command()
@click.option("--json", "json_path", required=True, type=click.Path(exists=True), help="Path to <map>_callouts.json produced by the pipeline.")
@click.option("--radar", default=None, type=click.Path(exists=True), help="Optional radar image to draw underneath; mapped to world bounds.")
@click.option("--out", "out_path", default=None, type=click.Path(), help="Output image path (PNG). If omitted, shows an interactive window.")
@click.option("--labels/--no-labels", default=True, show_default=True, help="Draw callout names at polygon centroids.")
@click.option("--invert-y/--no-invert-y", default=False, show_default=True, help="Invert Y axis to match image pixel coordinates if needed.")
@click.option("--alpha", default=0.35, show_default=True, help="Polygon fill alpha.")
@click.option("--linewidth", default=1.0, show_default=True, help="Polygon edge line width.")
@click.option("--min-size", default=3.0, show_default=True, help="Minimum polygon size in pixels for visibility.")
def main(json_path: str, radar: str | None, out_path: str | None, labels: bool, invert_y: bool, alpha: float, linewidth: float, min_size: float):
    data = _load_output(json_path)
    items = data.get("callouts", [])
    polys = [it.get("polygon_2d") or [] for it in items]

    # Compute world bounds from polygons or bbox entries
    xs: List[float] = []
    ys: List[float] = []
    for poly in polys:
        for x, y in poly:
            xs.append(float(x))
            ys.append(float(y))
    if not xs or not ys:
        click.echo("No polygon data to visualize.", err=True)
        raise SystemExit(1)
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    fig, ax = plt.subplots(figsize=(8, 8))

    if radar:
        img = plt.imread(radar)
        ax.imshow(img, extent=[min_x, max_x, min_y, max_y], interpolation="bilinear")

    for it in items:
        poly = it.get("polygon_2d") or []
        if len(poly) < 3:
            continue
        name = it.get("name") or it.get("placename") or "?"
        color = _color_for_name(name)
        patch = MplPolygon(poly, closed=True, facecolor=color + (alpha,), edgecolor=color, linewidth=linewidth)
        ax.add_patch(patch)
        if labels:
            cx, cy = _centroid(poly)
            ax.text(cx, cy, name, fontsize=7, color="black", ha="center", va="center", bbox=dict(boxstyle="round,pad=0.1", fc="white", ec="none", alpha=0.6))

    ax.set_xlim(min_x, max_x)
    ax.set_ylim(min_y, max_y)
    ax.set_aspect("equal", adjustable="box")
    if invert_y:
        ax.invert_yaxis()
    ax.set_title(Path(json_path).stem)
    ax.set_xlabel("X (game units)")
    ax.set_ylabel("Y (game units)")
    ax.grid(True, linestyle=":", linewidth=0.5, alpha=0.5)

    if out_path:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_path, dpi=200, bbox_inches="tight")
        click.echo(f"Saved {out_path}")
    else:
        plt.show()


if __name__ == "__main__":
    main()

