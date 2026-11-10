#!/usr/bin/env python3
"""Inline the GeoJSON datasets into the single-file web map."""

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
TEMPLATE = ROOT / "scripts" / "map_template.html"
OUT = ROOT / "myanmar_seismic_map.html"


def load(name):
    return json.loads((DATA / name).read_text())


def main():
    html = TEMPLATE.read_text()
    for token, path in (
        ("__EQ_DATA__", "myanmar_earthquakes.geojson"),
        ("__FLT_DATA__", "myanmar_active_faults.geojson"),
        ("__BND_DATA__", "myanmar_boundary.geojson"),
    ):
        payload = json.dumps(load(path), ensure_ascii=False, separators=(",", ":"))
        html = html.replace(token, payload)
    OUT.write_text(html)
    print(f"wrote {OUT} ({OUT.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
