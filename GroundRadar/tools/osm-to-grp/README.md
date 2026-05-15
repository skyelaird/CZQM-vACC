# osm-to-grp

Generates GRP plugin `GRpluginMaps.txt` + `[<icao>]` settings block from OpenStreetMap data.

Pulls airport surface features via Overpass API, buffers runway/taxiway/parking centerlines into polygons, and emits MAP blocks following the `pinatacolada/topskylppc` (LPPC) convention.

## Setup

```powershell
cd D:\GitHub\CZQM-vACC\GroundRadar\tools\osm-to-grp
pip install -r requirements.txt
```

Dependencies: `shapely>=2.0`, `PyYAML>=6.0`. Python 3.10+ (uses union types).

## Run

```powershell
python extract.py config/cyhz.yaml
```

Output paths and behaviour come from the YAML config. The first run hits Overpass and caches the raw JSON under `data/<icao>_raw.json`. Subsequent runs reuse the cache — pass `--refresh` to force a re-fetch.

For another airport: copy `config/cyhz.yaml` to `config/cyqm.yaml`, edit the `icao`, `bbox`, `projection_lat`, `output:` paths, `airport:`, and `runways:` sections, and run with the new config.

## What it generates

Given a config, the tool writes two files (paths from `config/<icao>.yaml > output:`):

- **`GRpluginMaps.txt`** — full geometry. Sections:
  - `COLORDEF` palette (12 SMGS_* colours, RGB triples)
  - `MAP:BACKGROUND` (FOLDER:DIV) — bbox-wide background
  - `MAP:APRON / RUNWAY / TAXIWAY / TAXILANE / PARKING / BUILDINGS` (FOLDER:<ICAO>) — surface fills, in bottom-to-top draw order
  - `MAP:HOLDING POSITIONS` (FOLDER:<ICAO>) — yellow marking lines
  - `MAP:STAND NUMBER` and `MAP:TAXIWAY NAME` (FOLDER:<ICAO>) — text labels
  - Hidden `MAP:TWY <ref>` blocks (FOLDER:<ICAO> TWY DATA) — one per named taxiway, `COORDTYPE:TWYTYPE:NONE` for CMAC incursion-monitoring tagging

- **`GRpluginSettings.txt`** — `[<ICAO>]` block with:
  - `Airport_Elevation`, `Airport_Radius`
  - `Airport_Runway_End` for each runway threshold (from config, sourced from AIRAC `.sct`)
  - `Airport_SMR_*`, `Airport_ModeA`, `Airport_ModeS`
  - `System_RwyArea*` dimensions (normal + LVP)
  - `System_*` safety-net flags (APM, APW, CBM, ECM, ICM, OSM, RIM, RUM, RVM)

The header on `GRpluginMaps.txt` says **DO NOT EDIT BY HAND** — re-run the tool instead. Hand edits will be overwritten.

## How it handles OSM data

| OSM | Treatment |
|---|---|
| `aeroway=runway` | Buffer centerline to polygon. Width from OSM `width` tag if present, else `default_widths.runway`. Ways below `min_runway_vertices` are dropped (filters duplicate fragments). |
| `aeroway=taxiway` | Group by `ref`; buffer per named taxiway (one polygon per letter). Unnamed connectors buffered together. Each named taxiway also gets a hidden `TWYTYPE:NONE` block in the TWY DATA folder for safety-net tagging. |
| `aeroway=taxilane` | Buffer with thinner width. |
| `aeroway=parking_position` | Way: buffer for fill. Midpoint also used as a label position if its `ref` isn't covered by a gate node. |
| `aeroway=apron` | Used directly as polygon fill (already closed in OSM). |
| `aeroway=hangar` | Polygon fill in the BUILDINGS map. |
| `aeroway=holding_position` (way) | Direct marking line (`COORDTYPE:OTHER:POLYLINE`). |
| `aeroway=gate` (node) | Text label at the node position. |
| `aeroway=navigationaid` | Skipped — these are typically ALS lamps, not real navaids; use `.sct` `[VOR]`/`[NDB]` for that. |

Holes in buffered polygons (rare, from union of overlapping taxiway buffers) are dropped with a warning — GRP does not support polygon holes. Visual impact is minor.

## Source attribution

Per ODbL, derived works of OSM data carry attribution. The output's header comment line credits OpenStreetMap and the LPPC pattern. End-user-facing attribution (in the GroundRadar README and ATTRIBUTION.md) goes in Phase 7.

## Files

- `extract.py` — the tool
- `config/cyhz.yaml` — CYHZ config
- `data/<icao>_raw.json` — cached Overpass payload (gitignored)
- `explore_osm.py`, `inspect_geometry.py`, `refine_inventory.py` — earlier diagnostic scripts kept for ad-hoc OSM inspection; not needed for normal use
