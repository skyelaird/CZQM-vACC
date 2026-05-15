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
│   ├── CZQQ-CZQM-CZQX_20260515002325-260501-0001.ese
│   └── portugal\                                          # LPPC (Portugal vACC) reference, in-repo
│       ├── GroundRadar\GRpluginMaps.txt                   # Primary LPPT geometry reference
│       ├── GroundRadar\GRpluginSettings.txt
│       ├── GroundRadar\GRpluginSymbols.txt
│       ├── GroundRadar\GRpluginStands.txt
│       ├── GroundRadar\GRpluginEventStands.txt            # Event-mode stand variant
│       ├── GroundRadar\Documentation\*.pdf
│       └── ASR\*.asr                                      # 8 tower/CTR ASR files
├── CYHZ\
│   ├── CYHZ-TWR_GRP.asr                 # Existing ASR — wired to load geometry from the sector file
│   └── docs\
│       ├── developer-notes.md           # This file
│       └── lppt-analysis.md             # LPPT reference analysis
└── tools\osm-to-grp\                    # OSM extraction work in progress
    ├── explore_osm.py                   # First-pass Overpass query for CYHZ
    ├── inspect_geometry.py              # Open-vs-closed-ways inspection
    ├── refine_inventory.py              # Grouping + ASR-cross-reference pass
    └── data\cyhz_raw.json               # Raw OSM payload (gitignored — regenerable)
```

The Portugal reference is now in-repo at `reference docs\portugal\` (previously cited from the external clone at `D:\GitHub\references\topskylppc\`). The external clone is no longer the source of truth; future analysis should read from the in-repo copy. Content is the same plus one extra file (`GRpluginEventStands.txt`).

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

**Licensing note (informational, not a blocker):** the file header asserts redistribution restrictions — *"FILES MUST NOT BE DISTRIBUTED OUTSIDE OF AERONAV SERVICES"*. In practice this is over-reach: the underlying AIRAC data (runway thresholds, taxiway centerlines, surface geometry) is public-domain factual data from Transport Canada / NAV CANADA, and facts are not copyrightable. The notice does not actually block our work, and the vACC operates under the assumption that this assertion is unenforceable for the geometry itself. The OSM-primary path is chosen for technical reasons (see below), not legal ones.

## Chosen approach

**OSM is the primary geometry source. The existing `.sct` rendering is the Phase 4 visual benchmark, and selected `.sct` elements may be imported where they materially improve on the OSM output.**

Why OSM as primary:
1. **Re-runnable.** OSM updates are pulled fresh each AIRAC; geometry stays current without manual edits.
2. **Reusable.** The same Overpass tool will work for CYQM and CYYT in the next phase without re-tracing geometry.
3. **Mechanically processable.** Tagged, structured, machine-friendly. The `.sct` is a flat list of line segments and polygons with no per-feature semantics beyond colour.
4. **Distribution-clean.** OSM (ODbL with attribution) carries no ambiguity about redistribution.

Where the `.sct` may still contribute, evaluated case-by-case during Phase 4:
- The 74 hand-drawn `[REGIONS] CYHZ Halifax` surface polygons — possibly more polished than OSM-buffered output for irregular grass/island areas
- The `CYHZ Groundlayout Halifax - low vis` linework — a ready-made low-vis variant that OSM doesn't model
- The `CYHZ Groundlayout Halifax Parking` lines — stand outlines that complement OSM's centerlines
- The `.sct` colour palette (`#define COLOR_*` BGR values) — directly usable as `COLORDEF` entries with conversion

Why the OSM tool is a real piece of engineering, not just a one-shot:
- OSM maps runways and taxiways as **centerlines**, not surface polygons. LPPT-style filled-surface rendering requires buffering each centerline by an assumed/known width.
- Width handling: runway 14/32 has `width=63` (m); 05/23 lacks the tag. Taxiways lack widths entirely. We supply config-driven defaults per aeroway type.
- The tool deliverable lives at `tools/osm-to-grp/` and is shared across CYHZ → CYQM → CYYT.

## What OSM provides for CYHZ — grouped/deduped

234 raw elements from Overpass over bbox `44.846,-63.617,44.906,-63.458`. The raw counts include OSM-typical fragmentation (taxiways split at intersections, ALS lamps as separate nodes, duplicate runway fragments). After grouping by `ref` and cross-checking against the existing ASR's authoritative FREETEXT labels:

| Feature | Raw OSM count | After grouping | Vs reality | Tool action |
|---|---|---|---|---|
| Runways | 3 ways | **2 distinct refs** (`05/23`, `14/32`) | 2 runways at CYHZ ✓ | Drop the 3-vertex duplicate fragment of `05/23` (way `1271831703`); buffer the remaining two centerlines (one has `width=63`, the other needs a default) |
| Taxiways | 48 ways | **13 named refs** (A–N, no `I`) + 31 unnamed connectors | All 13 taxiway labels from the ASR are present ✓ | Group by `ref`; buffer each named taxiway with a config default width; unnamed connectors get buffered too but with a thinner "lane" width |
| Aprons | 13 polygons (unnamed) | 13 polygons | Sub-divided rather than logical; needs visual review | Emit as-is for now; merge or relabel selectively in Phase 4 |
| Parking positions | 41 elements (36 ways + 5 nodes) + 32 separate `gate` nodes | **40 distinct refs** (union of `parking_position` and `gate`) | ASR has 39 distinct labels. Overlap **37/39 = 95 %**. Missing from OSM: `57`, `6A`, `46A`. In OSM but not ASR: `2B`, `34`, `40`, `44` | Trust OSM as primary; cross-check labels against the ASR; surface gaps for Phase 4 manual fill-in |
| Holding positions | 15 ways + 19 nodes = 34 elements | **15 line segments**, typed: 14 `runway`, 2 `intermediate`, 18 untyped | Reasonable count for CYHZ's major intersections | Emit ways directly as marking lines; nodes are likely duplicate point markers — verify by spatial coincidence |
| Navaids | 38 nodes | **All tagged `navigationaid=als`** | These are individual approach-lighting-system lamps, not separate navaids | Out of surface-GR scope. Real navaid positions (VOR/NDB/ILS) come from the `.sct` `[VOR]` and `[NDB]` sections, not OSM |
| Buildings | 13 hangar polygons + 1 terminal + 1 tower polygon | Direct | ✓ | Direct fill |
| `aerodrome` relation | 1 (`icao=CYHZ`) | Airport boundary | ✓ | Reference / clipping mask |

**Coverage summary:** all 13 named taxiways present, both runways present, ~95 % of parking labels match, holding lines typed for safety-net use. Coverage is **sufficient and consistent** with the existing ASR's labels — usable as the primary geometry source, with the few gaps (3 missing gates, no low-vis variant, sub-divided aprons) handled in Phase 4.

Data source: OSM contributors, primarily via Gagravarr_Airports edits (recent way IDs > 1.4 B). License: ODbL.

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
