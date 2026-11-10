#!/usr/bin/env python3
"""Build Myanmar earthquake + GEM active fault GeoJSON datasets.

Inputs
------
data/_raw/eq_raw.json          raw USGS FDSN event query (bbox around Myanmar)
data/_raw/myanmar_boundary.geojson  Natural Earth 10m Myanmar boundary

Outputs
-------
data/myanmar_earthquakes.geojson   earthquakes with epicentres inside Myanmar
data/gem_active_faults.geojson     complete GEM Global Active Faults Database
data/myanmar_active_faults.geojson GEM faults clipped to the Myanmar region
"""

import json
import pathlib
import shutil
import subprocess
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = DATA / "_raw"
RAW.mkdir(parents=True, exist_ok=True)

EARTHQUAKE_START = "2025-03-28"
EARTHQUAKE_END = "2026-11-10"  # present date

# Bounding box used for the USGS query (generous superset of the country).
BB = {
    "minlatitude": 8.0,
    "maxlatitude": 29.5,
    "minlongitude": 89.5,
    "maxlongitude": 102.5,
}

USGS_URL = (
    "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson"
    f"&starttime={EARTHQUAKE_START}&endtime={EARTHQUAKE_END}"
    f"&minlatitude={BB['minlatitude']}&maxlatitude={BB['maxlatitude']}"
    f"&minlongitude={BB['minlongitude']}&maxlongitude={BB['maxlongitude']}"
    "&orderby=time-asc&limit=20000"
)

GEM_REPO = "https://github.com/GEMScienceTools/gem-global-active-faults.git"
GEM_GEOJSON = "geojson/gem_active_faults.geojson"

NE_BOUNDARY_URL = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/"
    "geojson/ne_10m_admin_0_countries.geojson"
)


def log(msg):
    print(f"[build] {msg}", flush=True)


def download(url, dest):
    if dest.exists() and dest.stat().st_size > 0:
        log(f"cached {dest.name}")
        return
    log(f"downloading {url}")
    with urllib.request.urlopen(url) as r, open(dest, "wb") as f:
        shutil.copyfileobj(r, f)


def clone_gem(dest):
    if dest.exists():
        log("cached gem clone")
        return
    log("cloning GEM Global Active Faults")
    subprocess.run(["git", "clone", "--depth", "1", GEM_REPO, str(dest)], check=True)


def load_boundary():
    path = RAW / "myanmar_boundary.geojson"
    download(NE_BOUNDARY_URL, path)
    fc = json.loads(path.read_text())
    for feat in fc["features"]:
        props = feat.get("properties", {})
        if props.get("ADMIN") == "Myanmar" or props.get("ISO_A3") == "MMR":
            out = {
                "type": "FeatureCollection",
                "features": [feat],
            }
            (DATA / "myanmar_boundary.geojson").write_text(
                json.dumps(out, ensure_ascii=False)
            )
            return feat["geometry"]
    raise SystemExit("Myanmar boundary not found in Natural Earth data")


def build_earthquakes(boundary):
    from shapely.geometry import Point, shape

    poly = shape(boundary)
    raw_path = RAW / "eq_raw.json"
    download(USGS_URL, raw_path)
    raw = json.loads(raw_path.read_text())

    features = []
    offshore = 0
    for feat in raw["features"]:
        lon, lat, depth = feat["geometry"]["coordinates"]
        p = feat["properties"]
        place = p.get("place") or ""
        # Inclusion rule: the epicentre lies inside the Natural Earth land boundary,
        # OR USGS itself attributes the event to Burma/Myanmar (this catches the
        # offshore Andaman Sea / Bay of Bengal events that fall outside the
        # land polygon but are still catalogued against Myanmar).
        inside_land = poly.covers(Point(lon, lat))
        usgs_myanmar = ("Myanmar" in place) or ("Burma" in place)
        if not (inside_land or usgs_myanmar):
            continue
        if not inside_land:
            offshore += 1
        features.append(
            {
                "type": "Feature",
                "id": feat.get("id"),
                "geometry": {"type": "Point", "coordinates": [lon, lat, depth]},
                "properties": {
                    "id": feat.get("id"),
                    "mag": p["mag"],
                    "magType": p.get("magType"),
                    "place": p.get("place"),
                    "time": p.get("time"),
                    "updated": p.get("updated"),
                    "tz": p.get("tz"),
                    "status": p.get("status"),
                    "type": p.get("type"),
                    "depth_km": depth,
                    "significance": p.get("sig"),
                    "felt": p.get("felt"),
                    "cdi": p.get("cdi"),
                    "mmi": p.get("mmi"),
                    "alert": p.get("alert"),
                    "tsunami": p.get("tsunami"),
                    "nst": p.get("nst"),
                    "gap": p.get("gap"),
                    "rms": p.get("rms"),
                    "dmin": p.get("dmin"),
                    "net": p.get("net"),
                    "code": p.get("code"),
                    "ids": p.get("ids"),
                    "sources": p.get("sources"),
                    "title": p.get("title"),
                    "url": p.get("url"),
                    "detail": p.get("detail"),
                    "inside_land_boundary": inside_land,
                },
            }
        )

    fc = {
        "type": "FeatureCollection",
        "name": "myanmar_earthquakes",
        "metadata": {
            "source": "USGS FDSN Event Web Service (earthquake.usgs.gov/fdsnws/event/1)",
            "query": USGS_URL,
            "region": "Myanmar",
            "selection_rule": (
                "Epicentre inside the Natural Earth 10m Myanmar land boundary, "
                "or a USGS place name attributing the event to Burma/Myanmar "
                "(captures offshore Andaman Sea / Bay of Bengal events)."
            ),
            "start_time_utc": EARTHQUAKE_START,
            "end_time_utc": EARTHQUAKE_END,
            "feature_count": len(features),
            "onland_count": len(features) - offshore,
            "offshore_count": offshore,
            "license": "U.S. Government public domain (USGS)",
        },
        "features": features,
    }
    out = DATA / "myanmar_earthquakes.geojson"
    out.write_text(json.dumps(fc, ensure_ascii=False))
    log(
        f"earthquakes: {len(features)} features "
        f"({len(features) - offshore} on land, {offshore} offshore) -> {out.name}"
    )
    return fc


def build_faults():
    clone_gem(RAW / "gem-global-active-faults")
    src = RAW / "gem-global-active-faults" / GEM_GEOJSON

    complete = DATA / "gem_active_faults.geojson"
    if not complete.exists():
        shutil.copyfile(src, complete)
        log(f"copied complete GEM dataset -> {complete.name}")
    else:
        log(f"cached {complete.name}")

    gem = json.loads(src.read_text())
    log(f"GEM global features: {len(gem['features'])}")
    return gem


def build_myanmar_faults(gem, boundary):
    from shapely.geometry import shape
    from shapely.ops import unary_union

    poly = shape(boundary)
    region = poly.buffer(1.5)  # keep regional context (Bangladesh, China, Thailand, India)

    features = []
    for feat in gem["features"]:
        geom = shape(feat["geometry"])
        if not region.intersects(geom):
            continue
        clipped = geom.intersection(region)
        if clipped.is_empty:
            continue
        parts = []
        if clipped.geom_type == "LineString":
            parts = [list(clipped.coords)]
        elif clipped.geom_type in ("MultiLineString", "GeometryCollection"):
            parts = [list(g.coords) for g in clipped.geoms if g.geom_type == "LineString"]
        if not parts:
            continue
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "MultiLineString", "coordinates": parts},
                "properties": dict(feat["properties"]),
            }
        )

    fc = {
        "type": "FeatureCollection",
        "name": "myanmar_active_faults",
        "metadata": {
            "source": "GEM Global Active Faults Database (GEMScienceTools/gem-global-active-faults)",
            "url": GEM_REPO,
            "region": "Myanmar (Natural Earth 10m country boundary buffered by 1.5 degrees)",
            "feature_count": len(features),
            "license": "CC BY-SA 4.0 (GEM Foundation)",
            "citation": "Styron, R., and M. Pagani (2020). The GEM Global Active Faults Database. Earthquake Spectra, 36(1_suppl), 160-180.",
        },
        "features": features,
    }
    out = DATA / "myanmar_active_faults.geojson"
    out.write_text(json.dumps(fc, ensure_ascii=False))
    log(f"myanmar faults: {len(features)} features -> {out.name}")


def main():
    boundary = load_boundary()
    build_earthquakes(boundary)
    gem = build_faults()
    build_myanmar_faults(gem, boundary)


if __name__ == "__main__":
    main()
