# CYHZ GRP — Developer Notes

Living document for future maintainers of the CYHZ Ground Radar Plugin configuration. Started 2026-05-15.

## Project location

- **Repo:** `D:\GitHub\CZQM-vACC\`
- **Working subfolder:** `D:\GitHub\CZQM-vACC\GroundRadar\`
- **Branch in flight:** `grp/cyhz-rebuild` (off `main`)
- **Spec (authoritative):** `D:\GitHub\CZQM-vACC\GroundRadar\CLAUDE_CODE_TASK_grp_cyhz.md`
- **LPPT reference clone (read-only, outside the repo):** `D:\GitHub\references\topskylppc\` — `pinatacolada/topskylppc` on GitHub, GPL-3.0

A separate Claude.ai project mirrors this work for design continuity. File-level work happens here in Claude Code; planning may happen on the Claude.ai side.

## Current state of `GroundRadar\`

As of 2026-05-15:

```
GroundRadar\
├── CLAUDE_CODE_TASK_grp_cyhz.md        # Spec
├── reference docs\
│   ├── Ground Radar plugin for EuroScope - Developer Guide.pdf
│   ├── Ground Radar plugin for EuroScope - General.pdf
│   ├── Ground Radar plugin for EuroScope - Version History.pdf
│   ├── GRpluginOperatorInfo.txt
│   ├── CZQQ-CZQM-CZQX_20260515002325-260501-0001.sct      # AeroNav/Navigraph navdata, AIRAC 2605/1
│   └── CZQQ-CZQM-CZQX_20260515002325-260501-0001.ese
├── CYHZ\
│   ├── CYHZ-TWR_GRP.asr                 # Existing ASR — wired to load geometry from the sector file
│   └── docs\
│       ├── developer-notes.md           # This file
│       └── lppt-analysis.md             # LPPT reference analysis
└── tools\osm-to-grp\                    # OSM extraction work in progress
    ├── explore_osm.py                   # First-pass Overpass query for CYHZ
    ├── inspect_geometry.py              # Open-vs-closed-ways inspection
    └── data\cyhz_raw.json               # Raw OSM payload (gitignored — regenerable)
```

## What's actually present for CYHZ today

### The existing ASR

`CYHZ\CYHZ-TWR_GRP.asr` (82 lines) is a working GR display configuration. It is not standalone geometry — it **references named items defined in the AIRAC sector file**:

| ASR line | Loads from .sct |
|---|---|
| `Geo:CYHZ Groundlayout Halifax:` | `[GEO]` group at line 34414 (~1,300 line segments, `COLOR_TaxiwayGrey`) |
| `Geo:CYHZ Groundlayout Halifax Parking:` | `[GEO]` group at line 36009 (parking lines, `COLOR_ParkPos`) |
| `Regions:CYHZ Halifax:polygon` | All 74 `REGIONNAME CYHZ Halifax` polygons in `[REGIONS]` from line 45226+ (surface fills, `COLOR_GrasSurface` and others) |
| 50 `Free Text:CYHZ CYHZ PARKING\*:freetext` entries | Parking-stand labels in `[LABELS]` / `[FREETEXT]` |
| 13 `Free Text:CYHZ CYHZ TAXIWAY\*:freetext` entries | Taxiway letter labels in `[LABELS]` / `[FREETEXT]` |

There is also a **low-visibility variant** in the sector file (`[GEO]` group `CYHZ Groundlayout Halifax - low vis` at line 35732, using `COLOR_TaxiwayOrange`) which the existing ASR does not currently reference but which exists ready for use.

### What "bare-bones" means in context

The existing setup is "bare-bones" only in the GRP-plugin sense:
- No `MAP:` blocks (the GRP-native geometry container)
- No `COORDTYPE` tagging for runway/taxiway safety classification
- No safety-net configuration (`Airport_Runway_End`, `System_*` flags)
- No tag-family customization beyond the global `TopSky_QM` family
- No light/dark variants
- No position-aware filtering

The actual surface drawing **is** present and AIRAC-current — it's just in EuroScope's native `[GEO]`/`[REGIONS]` format inside the navdata, not in GRP plugin format.

### Other ASR header facts to preserve

- `DisplayRotation:18.00000` — 18° rotation, the existing visual orientation Joel has been using
- `WINDOWAREA:44.846061:-63.616579:44.905912:-63.458254` — viewport extent
- `AirportElevation:477`, `AirportRadius:1.9`
- `TAGFAMILY:TopSky_QM` — existing tag family (to be replaced in Phase 5 with ground/tower-specific families)
- `PLUGIN:Ground Radar plugin:GroundMode:CYHZ` and `PLUGIN:Ground Radar plugin:TowerMode:CYHZ` — both modes declared (note: LPPT's tower ASR uses only `GroundMode`; CYHZ uses both)

### CZQM sector reference data

The `reference docs\` folder ships the AIRAC 2605/1 sector pair (`.sct` / `.ese`) — AeroNav Association / Navigraph navdata. The `.sct` is the source of truth for:

- Runway thresholds (CYHZ 05/23, 14/32) in `[RUNWAY]` section at line 5151
- Navaid positions
- ARTCC and TMA boundaries used by the approach-mode display
- The 24-bit BGR-packed colour palette (`#define COLOR_*` in `[INFO]`)
- The existing CYHZ surface drawing (above)

**Licensing observation:** the file header explicitly restricts redistribution — *"FILES MUST NOT BE DISTRIBUTED OUTSIDE OF AERONAV SERVICES"* and *"data must not be … translated, reverse engineered, decompiled or reduced to any electronic medium or machine legible form."* This means **derived geometry ported from the sector file inherits the same restriction**, which would constrain public release of a GroundRadar package. The chosen path forward (see next section) avoids this issue by sourcing geometry from OSM (ODbL) and using the `.sct` only as a visual benchmark.

## Chosen approach

**Hybrid: OSM-sourced geometry, with the existing `.sct` rendering as a visual benchmark during Phase 4 polish.**

Why OSM and not port the `.sct`:
1. **License-clean.** OSM data is under ODbL and can be redistributed with attribution. The AeroNav `.sct` cannot.
2. **Re-runnable.** OSM updates are pulled fresh each AIRAC; geometry stays current without manual edits.
3. **Reusable.** The same Overpass tool will work for CYQM and CYYT in the next phase.
4. **The `.sct` remains useful as a "does this look right" reference.** When polishing the OSM output in Phase 4, the existing rendering is the visual target.

Why the OSM tool is a real piece of engineering, not just a one-shot:
- OSM maps runways and taxiways as **centerlines**, not surface polygons (confirmed for CYHZ). LPPT-style filled-surface rendering requires buffering each centerline by an assumed/known width.
- Width handling: runway 14/32 has `width=63` (m); 05/23 lacks the tag. Taxiways lack widths entirely. We supply config-driven defaults per aeroway type.
- The tool deliverable lives at `tools/osm-to-grp/` and is shared across CYHZ → CYQM → CYYT.

## What OSM provides for CYHZ (confirmed)

234 elements returned from the Overpass query over bbox `44.846,-63.617,44.906,-63.458`:

| OSM `aeroway=` | Element kind | Mapped as | Useful directly? |
|---|---|---|---|
| `apron` × 13 | way (closed) | Polygon | ✓ Direct fill |
| `hangar` × 13 | way (closed) | Polygon | ✓ Building outline |
| `runway` × 3 (refs `14/32`, `05/23`, plus a 3-vertex fragment) | way (open) | Centerline, `width=63` on one | ⚠ Buffer needed |
| `taxiway` × 48 (refs A,B,C,D,E,F,G,H,J,K,L,M,N + unnamed) | way (open) | Centerline, no `width` | ⚠ Buffer with default |
| `parking_position` × 36 | way (open) | Centerline through stand | ⚠ Buffer or use as label anchor |
| `taxilane` × 3 | way (open) | Centerline | ⚠ Buffer |
| `holding_position` × 15 | way (open, 2-vertex) | Line segment across taxiway | ✓ Direct as marking |
| `gate` × 32 | node | Point with `ref` (e.g. "36", "2A") | ✓ Direct as TEXT label |
| `navigationaid` × 38 | mix | Navaids (out of GR surface scope) | — |
| `terminal` × 1 + `tower` × 1 + `control_tower` × 1 | way + node | Buildings | ✓ Direct |
| `aerodrome` × 1 multipolygon relation | rel | Airport boundary, `icao=CYHZ` | ✓ Reference |

Data source attribution: OSM contributors via Gagravarr_Airports edits (recent way IDs > 1.4 B). Coverage is good and consistent.

## Planned output structure (per spec §4, updated)

```
GroundRadar\
├── README.md                          # Phase 7
├── ATTRIBUTION.md                     # Phase 7 — OSM ODbL + LPPT GPL-3.0 + GRP plugin author
├── CYHZ\
│   ├── GRpluginMaps.txt              # Phase 3 (OSM-emitted) + Phase 4 (polish)
│   ├── GRpluginSettings.txt          # Phase 2 (settings + safety nets) + Phase 5 (tag families)
│   ├── GRpluginSymbols.txt           # Phase 4 (custom symbols if any)
│   ├── GRpluginAirports.txt          # Phase 2 (if needed)
│   ├── CYHZ-TWR_GRP.asr              # Existing — preserved for now; replaced/superseded in Phase 4
│   ├── asr\
│   │   ├── CYHZ_Ground_Light.asr     # Phase 4 + 5
│   │   ├── CYHZ_Ground_Dark.asr
│   │   ├── CYHZ_Tower_Light.asr
│   │   └── CYHZ_Tower_Dark.asr
│   └── docs\
│       ├── controllers-guide.md      # Phase 7
│       └── developer-notes.md        # this file
└── tools\
    └── osm-to-grp\                    # Phase 3 — proper tool
        ├── README.md
        ├── extract.py                 # Promoted from explore_osm.py
        ├── emit.py                    # Centerline buffering + MAP block emission
        ├── requirements.txt           # shapely, possibly pyproj
        ├── config\
        │   └── cyhz.yaml              # Bbox, default widths, output paths, folder names
        └── data\                      # Cached Overpass payloads (gitignored)
            └── cyhz_raw.json
```

No `current\CYHZ\` folder is needed — the existing geometry lives in the AeroNav sector file under `reference docs\`, and we're not porting it.

## Phase status (updated)

| Phase | Status | Deliverable | Notes |
|------:|--------|-------------|-------|
| 1 | Complete | This file + `lppt-analysis.md` + OSM exploration scripts | Awaiting review pause before Phase 3 starts |
| 2 | Reframed | `[CYHZ]` block in `GRpluginSettings.txt`: `Airport_Runway_End`, `System_*` safety-net flags, runway-area dimensions | Phase 2 is settings-only — no geometry tagging required (LPPT pattern: RMCA works off settings, not map directives). See lppt-analysis.md §13. |
| 3 | Up next | OSM extraction tool + `GRpluginMaps.txt` for CYHZ | Hybrid approach: OSM geometry, `.sct` as visual benchmark |
| 4 | Not started | Visual polish — runway/taxiway buffering tuning, marking layer, light/dark | Side-by-side comparison vs existing `.sct` render |
| 5 | Not started | Ground/tower tag families | |
| 6 | Not started | Position-aware filtering | |
| 7 | Not started | Docs + packaging + attribution | |

## Conventions

- Commit style: conventional (`feat(grp): ...`, `fix(grp): ...`, `docs(grp): ...`)
- Branch: `grp/cyhz-rebuild` — do not merge to `main`; do not push to remote without explicit instruction
- Per-airport ICAO directories under `GroundRadar\` (`CYHZ\`, future `CYQM\`, `CYYT\`)
- License: GPL-3.0 (inherited from the repo and required by `topskylppc` attribution); OSM data is ODbL (attribution required for any redistribution)
- Phase boundaries: pause for review per spec §7

## Cross-references

- LPPT reference analysis: [`lppt-analysis.md`](./lppt-analysis.md). Translation notes in §13 explain how spec language (`AREATYPE`, `LAYER:N`, `ZOOM:N`) maps to the LPPT reality (`COORDTYPE:<family>:<render>`, file ordering, ASR folder visibility).
- OSM exploration: `..\..\tools\osm-to-grp\explore_osm.py` and `inspect_geometry.py` validate the Overpass pipeline. They'll be subsumed by the proper extractor in Phase 3.
- Open questions: spec §8 + lppt-analysis.md §14.
