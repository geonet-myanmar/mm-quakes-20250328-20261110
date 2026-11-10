# Myanmar Seismicity & Active Faults

Earthquake events in Myanmar from **2025-03-28** to the present date, plus the
**GEM Global Active Faults Database**, exported as GeoJSON and visualised in a
single self-contained web map.

## Outputs

| File | Description |
| --- | --- |
| `myanmar_seismic_map.html` | Single-file web map (all data embedded, works offline) |
| `data/myanmar_earthquakes.geojson` | 213 USGS earthquakes in Myanmar |
| `data/myanmar_active_faults.geojson` | 356 GEM active faults in the Myanmar region |
| `data/gem_active_faults.geojson` | Complete GEM Global Active Faults Database (16,195 faults) |
| `data/myanmar_boundary.geojson` | Natural Earth 10m Myanmar boundary (used for selection) |

## Data sources

**Earthquakes** — [USGS FDSN Event Web Service](https://earthquake.usgs.gov/fdsnws/event/1/).
A bounding-box query over the Myanmar region is filtered to events whose epicentre
falls inside the Natural Earth 10m country boundary, plus the offshore Andaman Sea /
Bay of Bengal events that USGS itself catalogues against Burma/Myanmar.

Query used (see `scripts/build_datasets.py`):

```
https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson
  &starttime=2025-03-28&endtime=<present date>
  &minlatitude=8.0&maxlatitude=29.5
  &minlongitude=89.5&maxlongitude=102.5
  &orderby=time-asc&limit=20000
```

**Active faults** — [GEMScienceTools/gem-global-active-faults](https://github.com/GEMScienceTools/gem-global-active-faults)
(GEM Foundation; Styron & Pagani, 2020, *Earthquake Spectra* 36(1_suppl), 160–180;
CC BY-SA 4.0). The complete database is copied verbatim to
`data/gem_active_faults.geojson`; `data/myanmar_active_faults.geojson` holds the
subset intersecting a 1.5° buffer around Myanmar, with geometries clipped to that
region so the traces terminate cleanly at the edge of the map.

## Rebuild

```bash
pip install shapely geopandas
python scripts/build_datasets.py   # downloads + writes the GeoJSON datasets
python scripts/build_map.py        # inlines the datasets into the HTML map
```

Raw downloads are cached in `data/_raw/` (git-ignored).

## Web map

Open `myanmar_seismic_map.html` in a browser. It is one file with the data embedded;
no server required.

- Earthquakes are circle markers coloured and sized by magnitude, with tooltips and a
  detail panel (depth, magnitude type, PAGER alert, shakemap intensity, USGS link).
- Active faults are polylines coloured by slip type (reverse, normal, dextral,
  sinistral, subduction thrust), with slip-rate and geometry attributes in the detail panel.
- Controls: magnitude range, date range, layer toggles, basemap switcher, legend,
  click-to-inspect on both layers.

If Leaflet or the map tiles cannot be reached (offline), the page falls back to a
built-in canvas renderer so the data is still browsable.

## Sources & attribution

- Earthquake data: U.S. Geological Survey, U.S. Government public domain.
- Fault data: GEM Foundation, Global Active Faults Database, CC BY-SA 4.0.
- Country boundary: Natural Earth (public domain).
- Basemap tiles: OpenStreetMap contributors / Esri.
