from __future__ import annotations

import sys
from pathlib import Path

import click

from .pipeline import process_callouts, read_callouts_json, write_json


@click.command()
@click.option("--map", "map_name", default="de_mirage", show_default=True, help="Map name used for path defaults.")
@click.option("--callouts-json", "callouts_json", type=click.Path(exists=True), default=None, help="Path to callouts_found.json from the VRF script.")
@click.option("--models-root", type=click.Path(exists=True, file_okay=False), default="export/models", show_default=True, help="Root folder containing exported GLB/GLTF models.")
@click.option("--out", "out_path", type=click.Path(), default=None, help="Output JSON path.")
@click.option("--rotation-order", type=click.Choice(["auto", "rz_rx_ry", "ry_rx_rz", "rz_ry_rx"], case_sensitive=False), default="auto", show_default=True)
def main(map_name: str, callouts_json: str | None, models_root: str, out_path: str | None, rotation_order: str):
    if callouts_json is None:
        callouts_json = str(Path("export") / "maps" / map_name / "report" / "callouts_found.json")
    if out_path is None:
        out_path = str(Path("out") / f"{map_name}_callouts.json")

    callouts = read_callouts_json(callouts_json)
    if not callouts:
        click.echo(f"No callouts found in {callouts_json}", err=True)
        sys.exit(1)

    data = process_callouts(callouts, models_root=models_root, rotation_order=rotation_order)
    write_json(data, out_path, pretty=True)
    click.echo(f"Wrote {out_path} with {data['count']} callouts. Rotation order: {data['rotation_order']}")
    if data.get("missing_models"):
        click.echo(f"Missing models: {len(data['missing_models'])}")


if __name__ == "__main__":
    main()

