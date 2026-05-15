# LPPT GRP Analysis (Phase 1 reference deliverable)

Analysis of how `pinatacolada/topskylppc` builds the LPPT (Lisbon) Ground Radar Plugin configuration, distilled for use as the primary pattern for the CYHZ rebuild.

**Source repo:** [`pinatacolada/topskylppc`](https://github.com/pinatacolada/topskylppc) — GPL-3.0
**Versions targeted by the source:** Ground Radar plugin 1.6b5 (per repo README), TopSky 2.6b3
**Local clone:** `D:\GitHub\references\topskylppc\` (read-only)
**Analyzed on:** 2026-05-15

> **Scope note.** This is a working analysis from grepping the live files, not a substitute for the GRP Developer Guide PDF. Where I infer behaviour from naming, I say so. Always confirm against the PDF before relying on a claim for safety-net or filtering work.

---

## 1. File layout inside the clone

```
LPPC\
├── LPPC ACS.prf, LPPC APS.prf, LPPC_CTR.prf      # Profile files
├── ASR\
│   ├── ADC.asr, CCLIS.asr, CDF.asr               # Misc tower/CTR setups
│   └── TWRLIS.asr, TWRFAR.asr, TWRFUN.asr, ...   # Per-airport tower setups
├── Plugins\
│   ├── ACDM\                                      # Collaborative Decision Making (out of CYHZ scope)
│   ├── topsky\                                    # TopSky plugin files
│   └── GroundRadar\
│       ├── GRplugin.dll                           # The plugin binary
│       ├── GRpluginMaps.txt          (15 344 lines)  # Geometry — everything visible on surface
│       ├── GRpluginSettings.txt         (312 lines)  # Per-airport settings, tag layouts, safety net flags
│       ├── GRpluginSettingsLocal.txt     (35 lines)  # Resolution-specific window positions (mostly commented)
│       ├── GRpluginSymbols.txt            (7 lines)  # GND_PRIMARY / GND_SSR / GND_HISTORY only
│       ├── GRpluginStands.txt          (1862 lines)  # Stand assignment data (LPPT/LPPR/LPFR/LPMA)
│       ├── GRpluginOperatorInfo.txt
│       ├── ICAO_Aircraft.json
│       └── ICAO_Airlines.txt
└── Settings\, Sounds\                              # Other EuroScope setup
```

Note: the README states the ground radar view loads via a user-side `_GND_TSGR.asr` that is **not** in the repo. The ASR files that *are* present (`TWRLIS.asr` etc.) are tower-radar setups whose headers reference `PLUGIN:Ground Radar plugin:GroundMode:LPPT` — i.e., the GR plugin is loaded into the tower view, not into a dedicated ground display. This is a useful pattern for our top-down/tower mode work in Phase 5/6.

---

## 2. Color palette

All 22 `COLORDEF` lines live at the top of `GRpluginMaps.txt`. RGB values in order, with my inferred meaning:

### Generic / utility

| Name | RGB | Purpose |
|---|---|---|
| `DEV` | 255,253,228 | Cream — likely "deviation" or default visible-on-dark |
| `CLSD` | 130,170,100 | Olive green — closed-taxiway overlay fill |
| `TWY` | 96,96,96 | Mid-grey — generic taxiway fill |
| `TWYSAFE` | 125,0,0 | Dark red — used for the `TWYTYPE:NONE` hidden tagging polygons (debug-visible if `HIDDEN` is removed) |
| `BLACK` | 0,0,0 | |
| `WHITE` | 125,125,125 | Note: defined as mid-grey, not 255,255,255 |

### Surface (SMGS = Surface Movement Guidance System)

| Name | RGB | Purpose |
|---|---|---|
| `SMGS_BACKGROUND` | 150,150,150 | Outer background (LPPC-area panel) |
| `SMGS_APRON` | 115,125,125 | Apron fill |
| `SMGS_RWY` | 65,70,65 | Runway fill — dark, almost charcoal |
| `SMGS_RWYMARK` | 115,125,125 | Runway markings (thresholds, edges) |
| `SMGS_STOPBAR_UNK` | 220,180,130 | Stopbar — state unknown (amber) |
| `SMGS_STOPBAR_ON` | 110,215,110 | Stopbar — lit (green) |
| `SMGS_STOPBAR_OFF` | 160,80,65 | Stopbar — off (terracotta) |
| `SMGS_PARKING` | 110,115,115 | Stand / parking fill |
| `SMGS_GRASS` | 135,150,135 | Movement-area grass |
| `SMGS_BUILDING` | 60,60,55 | Terminal / hangar fill |
| `SMGS_TWY_LINE` | 140,160,160 | Taxiway centreline / edge markings |
| `SMGS_ROAD` | 170,170,165 | Vehicle road |

### Airspace

| Name | RGB | Purpose |
|---|---|---|
| `ASP_GREEN` | 0,70,0 | Approach-scale features (CTR fill) |
| `ASP_MIDGREEN` | 0,15,0 | VOR/NDB symbol fill |
| `ASP_GREYPURP` | 100,100,120 | Approach-scale runway representation |

> **Note:** `ASP_DARKGREEN` is referenced (e.g. `MAP:CTR:A`) but **not defined** in the file head. Either it's elsewhere later in the file or it's a GRP built-in fallback. Worth verifying in the Developer Guide before depending on it.

**Aesthetic takeaway for CYHZ:** the LPPT palette is desaturated and dark-on-mid-grey. Runway is the darkest non-text element; apron is one notch lighter; grass blends toward the background. This gives the runway visual primacy without any explicit outline work. For a Canadian variant Joel may want to shift slightly cooler/blueish, but the structure (runway darkest, grass blends, apron mid-grey) should be preserved.

**Light/dark variants:** the repo ships only one palette. The light/dark requirement for CYHZ means we need to define a second `COLORDEF` set with different RGBs but identical names — or use distinct names per palette and reference them from per-ASR maps. Mechanism TBD in Phase 4.

---

## 3. Maps file grammar

A typical LPPT map block looks like:

```
MAP:<map-name>
FOLDER:<folder-name>          # Where it appears in the controller's menu
[AIRPORT:<icao>]              # Scopes the block to one airport
[ACTIVE:1] | [ACTIVE:LVP:<icao>:0]   # Activation condition
COLOR:<colordef-name>
[HIDDEN]                      # Hide from the menu (still used by engine)
COORDTYPE:<type-family>:<render>[:p1:p2]   # Tagging + rendering category
[BLOCKS:<icao>:<stand-list>]  # Cascade stand-availability when active
<coord lines>
```

### Distinct `COORDTYPE` values seen in LPPT

| Value | Count | Use |
|---|---:|---|
| `OTHER:REGION` | ~290 | Generic filled polygon (most surface fills). Outlines drawn. |
| `OTHER:REGION_FILLONLY` | (many; same family) | Filled polygon, no outline (called out explicitly in closures) |
| `OTHER:POLYLINE` | ~55 | Open polylines — centrelines, edges, markings |
| `TWYTYPE:NONE` | 58 | Hidden per-taxiway polygons tagged for the engine to know "this is taxiway X". Used by Conformance Monitoring (CMAC) and incursion detection. |
| `TWYCLOSED:REGION_FILLONLY:0:60` | 10 | Closed-taxiway overlay (rendered in `CLSD` colour). The `0:60` extra parameters appear to be a stroke/alpha pair — confirm against the Developer Guide. |

**Key insight — this is where the spec needs translation:**
The spec mentions `AREATYPE:OTHER:REGION_FILLONLY` and "tag the runway polygons with `AREATYPE`". In LPPT these are not separate `AREATYPE` directives — the tag is the first token of the `COORDTYPE` value. The family-token vocabulary in LPPT is just `OTHER`, `TWYTYPE`, `TWYCLOSED`. There is **no runway-region tag** in LPPT's maps file at all — the runway is just `COLOR:SMGS_RWY` + `COORDTYPE:OTHER:REGION`. RMCA must therefore be driven entirely off `Airport_Runway_End` declarations in `GRpluginSettings.txt`, not off any geometry tagging.

This means Phase 2's "tag the runway polygons with AREATYPE for RMCA" is misframed — there's nothing to tag for RMCA. RMCA gets configured purely in `GRpluginSettings.txt`. Worth confirming with the Developer Guide PDF before committing to this read.

### Coordinate formats (mixed within the same file)

1. Sexagesimal DMS, colon-separated: `N038.45.59.151:W009.08.38.040`
2. Decimal degrees, colon-separated, signed: `38.78010527:-9.132040521`
3. Sexagesimal DMS, space-separated, no leading `COORD:` prefix: `N038.46.05.150 W009.07.54.430` (used inside `MAP:TWY *` blocks)

The OSM-to-GRP tool should pick one format and stick to it (decimal degrees with colon separator is the cleanest machine-friendly choice).

### Symbol drawing primitives in `SYMBOLDEF`

`GRpluginMaps.txt` defines just four symbols:

- `VOR` — 12-segment box with diamond and centre dot
- `NDB` — 12-segment dotted-pattern square
- `RWYMARKER` — solid 2×2 plus corner dots (used for runway threshold ends)
- `UNCORTGT` — X-with-dot (uncorrelated target)

Drawing language: `MOVETO:x:y`, `LINETO:x:y`, `POLYGON:x1:y1:x2:y2:...`, `SETPIXEL:x:y`, `FILLRECT:x1:y1:x2:y2`. Coordinates are in pixels relative to the symbol anchor. `GRpluginSymbols.txt` adds another three (`GND_PRIMARY`, `GND_SSR`, `GND_HISTORY`) — primitive engine symbols, not visual decorations.

**The spec mentions "decorative parked aircraft icons at typical stand positions — pulled from LPPT and adapted."** I see no such symbol definitions in LPPT's maps or symbols files. Stand markers in LPPT's `MAP:STAND NUMBER` blocks are just `TEXT:` labels — no parked-aircraft pictograms. Either:
- The decorative aircraft live elsewhere (TopSky? sector file?) and the spec assumption is wrong, or
- LPPT simply doesn't have them, and the showcase aesthetic comes from polygon work alone.

Worth surfacing to Joel as an open question — see §8 of this document.

---

## 4. Folder organization (LPPT)

The `MAP:`-`FOLDER:` pairing defines what appears in the controller's map menu. LPPT's folder layout:

| Folder | What's in it |
|---|---|
| `DIV` | One block: the panel background fill |
| `APP` | Approach-scale features: CTR boundary, VOR/NDB symbols (long list), simplified RWY representation, shoreline, rivers |
| `LPPT` | The airport's main display group: `MAP:SURFACE` (grass + apron polygons), `MAP:STAND NUMBER` (text labels), `MAP:TAXIWAY NAME` (text labels) |
| `LPPT TWY DATA` | 58 hidden `MAP:TWY <id>` blocks — one per taxiway, each a `COORDTYPE:TWYTYPE:NONE` polygon. These never appear in the menu (`HIDDEN`) and exist solely to tag each taxiway letter for the engine. |
| `LPPT TWY CLOSURES` | 10 `MAP:TWY <id> CLOSED` blocks — visible overlays activated when a specific taxiway is closed. Several use `ACTIVE:LVP:LPPT:0` to auto-engage in Low Visibility Procedures. One (`TWY F CLOSED`) also uses `BLOCKS:LPPT:600,601,...,609` to cascade stand-unavailability. |

The file then repeats this layout for `LPPR`, with similar `LPPR TWY DATA` / `LPPR TWY CLOSURES` folders. The pattern is: **one folder per (airport × concern)**.

**Takeaway for CYHZ:** the natural CYHZ folder set is

- `CYHZ` — main visible surface, stand labels, taxiway labels
- `CYHZ TWY DATA` — hidden taxiway-tag polygons (only if/when we wire up taxiway-incursion detection)
- (No closures folder — out of scope per spec §3)
- `CYHZ HELICOPTER`, `CYHZ CARGO`, etc. as optional menu-toggleable layers if Joel wants per-feature toggling

Folder *names* are also load-order organizational. Same-named folders aggregate the maps under them in the menu.

---

## 5. Layering and draw order

**There is no `LAYER:N` directive.** I grep'd for `^LAYER:` across the whole maps file: zero hits. The same is true for `^ZOOM:`, `^STYLE:`, `^LINESTYLE:`, `^FONT*`. The plugin appears to draw in **file order**: maps that appear later in `GRpluginMaps.txt` paint on top of maps that appear earlier.

Concretely, LPPT's file layout is:
1. Lines 1–24: `COLORDEF` palette
2. Lines 25–74: `SYMBOLDEF` blocks
3. Lines 76–86: `MAP:BACKGROUND` (in `FOLDER:DIV`)
4. Lines 88–3875: `MAP:CTR:A`, `MAP:VOR NDB:A`, `MAP:RWY:A`, `MAP:SHORE:A`, `MAP:RIVER:A` — all in `FOLDER:APP` (the approach-scale view)
5. Lines 3876–10174: `MAP:SURFACE` for LPPT (grass + apron + runway + taxiway fills, in compositional order)
6. Lines 10175–10326: `MAP:STAND NUMBER` + `MAP:TAXIWAY NAME` for LPPT (text labels on top)
7. Lines 10327–11226: `LPPT TWY DATA` (hidden taxiway tags)
8. Lines 11228–11355: `LPPT TWY CLOSURES`
9. Lines 11356–15343: same six-section sequence repeated for LPPR, LPFR, LPMA

The visual stack is therefore controlled by ordering polygons from bottom to top inside the `MAP:SURFACE` block: grass first → apron → runway → taxiway → centreline polylines. This gives the appearance of layered rendering even without explicit layer numbers.

**Spec §4 Phase 4 mentions `LAYER:N` directives to control draw order.** That's a misframe — LPPT achieves the same effect by ordering. We should plan to do the same.

---

## 6. Zoom-aware detail

**No `ZOOM:N` directives in LPPT's maps file.** The spec mentions `ZOOM:N` for things like "stand numbers visible only when zoomed in below 200 px/nm". I see no use of this construct.

How LPPT actually handles zoom-aware detail: the `.asr` view file controls which folders are visible in a given view. By splitting the display into many small folders (`LPPT`, `LPPT TWY DATA`, `LPPT TWY CLOSURES`, etc.), and by giving the engine `AIRPORT:<icao>` and `GroundMode:<icao>` context, the engine selects what to show. Fine-grained zoom-bracketed visibility would need to come from another mechanism — either an engine default (e.g., text labels auto-hidden below a font-pixel threshold) or a feature of the GRP version we haven't seen here.

**Action item:** before promising zoom-aware behaviour in Phase 4, verify against the GRP Developer Guide PDF section on map/text scaling.

---

## 7. Per-airport scoping mechanisms

LPPT uses several layered mechanisms to keep airports isolated within one shared maps file:

1. **`AIRPORT:<icao>` on a map block** — 74 hits across the file. Tags each block to its airport so the engine knows which to display per `GroundMode:` ASR setting.
2. **`ACTIVE:LVP:<icao>:0`** — conditional activation: visible only when the named airport is in Low Visibility Procedures. State `0` is the "no LVP" state (so this construct *hides* the map until LVP triggers); other states are presumably available.
3. **`BLOCKS:<icao>:<stand-list>`** — when this map is active, block these stands from being assigned. Used in `TWY F CLOSED` to free up gate range 600–609 when taxiway F is shut. Out of scope for us (we don't do stand assignment), but worth knowing the mechanism exists.
4. **ASR `PLUGIN:Ground Radar plugin:GroundMode:LPPT`** — the active-airport switch in a given view. This is how `TWRLIS.asr` declares "I am the Lisbon tower view; use LPPT context."
5. **`Airport_*` blocks in `GRpluginSettings.txt`** — per-airport settings (`Airport_Elevation`, `Airport_Radius`, `Airport_Runway_End`, `Airport_SMR_*`, `System_*` safety-net flags, per-airport `Label=` overrides).

For CYHZ alone we'd only need the ASR-level `GroundMode` plus an `[CYHZ]` settings block. For the eventual CYHZ + CYQM + CYYT triple, the AIRPORT-tagged-blocks-in-one-shared-file pattern (mirroring LPPT) is the natural extension.

---

## 8. Tag layouts (`GRpluginSettings.txt`)

LPPT's tag layouts give us the model for ground vs tower tag families:

```
Label=GND:DEP:0:ALRT,0,0:ASSR_E,0,1:COMM,0,1
Label=GND:DEP:1:CALLSIGN,0,0:SID,8,0,13
Label=GND:DEP:2:WTC,0,0:ATYP,2,0
Label=GND:DEP:3:RMK,0,0

Label=APP:DEP:0:ALRT,0,0:COMM,0,1
Label=APP:DEP:1:CALLSIGN,0,0
Label=APP:DEP:2:AFL,0,0::VS,4,1:CFL,0,0,14
Label=APP:DEP:3:GS,0,0
```

Grammar: `Label=<MODE>:<STATE>:<LINE>:<field,col,row>[:<field,col,row>...]`.
- `<MODE>` = `GND` (ground) or `APP` (approach/tower)
- `<STATE>` = `DEP` / `ARR` / `OTH` / `UNC` (departure / arrival / other / uncorrelated)
- `<LINE>` = 0..3 (4 lines per tag)
- Each field is `<field-id>,<col-offset>,<row-offset>[,<width>]`

GND mode in LPPT shows callsign + SID (departures) / stand (arrivals) + aircraft type + remarks. APP mode adds altitude/VS/groundspeed instead. Per-airport overrides exist (e.g., LPMA blanks all GND labels — useful when you want minimal display).

**Direct application to CYHZ Phase 5:**
- "Ground mode tag family" → use `Label=GND:*` layout, customized for CZQM operational fields (Joel may want gate or pushback state on line 2)
- "Tower mode tag family" → use `Label=APP:*` layout. Note: in LPPT this is called APP not TWR — GRP appears to use the same APP/GND distinction for tower-radar setups (cf. TWRLIS.asr loading `Label=APP:*`).

Tag colour: from `GRpluginSettings.txt` head — `Color_Arrival=253,236,166` (cream/yellow), `Color_Departure=0,18,153` (dark blue), `Color_Unknown=0,0,0`. Light blue/yellow per spec §5 Phase 5 is achievable by adjusting these.

---

## 9. Safety net configuration

Per-airport `System_*` flags in `GRpluginSettings.txt` enable/disable each safety net:

| Flag | Meaning (inferred) | LPPT | LPPR | LPFR / LPMA |
|---|---|---|---|---|
| `System_APM` | Approach Path Monitoring | global `-1` | (unset) | |
| `System_APW` | Approach Path Warning | `1` | `0` | |
| `System_CBM` | Closed-block Monitoring? | `1` | `0` | |
| `System_ECM` | Emergency Code Monitoring | `1` | (unset) | |
| `System_ICM` | Incursion Conflict Monitoring | `1` | (unset) | |
| `System_OSM` | Outside-Stopbar Monitoring? | `1` | (unset) | |
| `System_RIM` | Runway Incursion Monitoring | `1` | `0` | |
| `System_RUM` | Runway Usage Monitoring | `1` | `0` | |
| `System_RVM` | Runway Visibility Monitoring? | `1` | `0` | |

> Several of these names are my inference from the abbreviation. Confirm against the GRP Developer Guide / Version History PDFs before relying on the semantics.

Global defaults (top of file) set most to `-1` (off). The `[LPPT]` section flips them to `1`. This is the LPPT "showcase quality" pattern — for CYHZ we'll mirror it.

LPPT also sets:
- `Airport_Radius=6.5` (nm)
- `Airport_Runway_End=20:N038.47.50.400:W009.07.38.500` and `02:...` — runway threshold positions (used for RMCA)
- `Airport_SMR_Raw=2`, `Airport_SMR_Track=0` — surface movement radar tuning
- `System_RwyArea=45.0`, `System_RwyBufferArea=90.0` — runway area dimensions (meters? feet? — check Developer Guide)
- `System_RwyArea_LVP=90.0`, `System_RwyBufferArea_LVP=140.0` — same, enlarged for LVP
- `System_GroundMode_AltFilter_AAL=24000` — altitude cap (ft AAL) for showing aircraft on ground display

---

## 10. ASR file pattern

`TWRLIS.asr` (21 lines, the entire file):

```
DisplayTypeName:Ground Radar display
DisplayTypeNeedRadarContent:0
DisplayTypeGeoReferenced:1
SHOWC:1
SHOWSB:0
BELOW:0
ABOVE:0
LEADER:5
SHOWLEADER:0
TURNLEADER:0
HISTORY_DOTS:0
SIMULATION_MODE:2
DISABLEPANNING:0
DISABLEZOOMING:0
DisplayRotation:67.30000
TAGFAMILY:TopSky LP
WINDOWAREA:38.769521:-9.166649:38.794265:-9.108735
PLUGIN:Ground Radar plugin:AirportElevation:374
PLUGIN:Ground Radar plugin:AirportRadius:1.9
PLUGIN:Ground Radar plugin:GroundMode:LPPT
PLUGIN:TopSky plugin:NoDraw:1
```

Key fields for the CYHZ work:
- `DisplayRotation` — LPPT rotates 67.3° to align runway 02/20 (real heading ~035°) closer to vertical on screen. For CYHZ 05/23 (real heading ~055°) and CYHZ 14/32 (~140°) we may want a similar nudge so the dominant runway sits screen-up.
- `WINDOWAREA:<lat-min>:<lon-min>:<lat-max>:<lon-max>` — view extent in decimal degrees.
- `TAGFAMILY:TopSky LP` — Lisbon's tag family. We'll define our own `TopSky CYHZ Ground` / `TopSky CYHZ Tower` (or similar) in Phase 5.
- `PLUGIN:Ground Radar plugin:GroundMode:LPPT` — declares the active airport for GR.
- `PLUGIN:Ground Radar plugin:AirportElevation` / `AirportRadius` — view-local overrides of the settings file. Useful for ground vs tower variants where you might want a different radius.
- `PLUGIN:TopSky plugin:NoDraw:1` — tells TopSky to stand aside when GR is rendering. We'll likely want this on for tower/ground views and off for higher-airspace views.

The `_GND_TSGR.asr` (referenced in the README but not in the repo) is presumably a longer file that lists which folders/items are visible. We'll need to create our own from scratch.

---

## 11. Stands file pattern (`GRpluginStands.txt`)

Per-airport stand metadata with operator-to-stand mappings. Structure:

```
GROUP:<group-name>:<callsign-prefix>:<callsign-prefix>:...
STANDLIST:<ICAO>:<operator-csv>:1000:GROUP_<stand-group>
STAND:<ICAO>:<stand-id>:<lat>:<lon>:<heading>
  WINGSPAN:<m>
  LENGTH:<m>
  USE:BP|A|...        # Boarding Position vs Aircraft type?
  PRIORITY:1..N
  [REMARKS:...]
```

Out of scope for CYHZ per spec §3 (no stand assignment), but the file format is straightforward if Joel ever wants to enable it. The decision-tree we'd need: operator group + aircraft size → matched stand priority.

---

## 12. Remote-update mechanism

`GRpluginSettings.txt` line 96:

```
Maps_URL=https://raw.githubusercontent.com/pinatacolada/lppc-atfm/refs/heads/main/GRpluginMaps.txt
```

LPPC ships the maps file as a remote URL — the plugin can pull updated geometry without reissuing the whole package. The version-controlled file in `LPPC\Plugins\GroundRadar\GRpluginMaps.txt` is a fallback/snapshot.

For CZQM this is a possible Phase 7 enhancement — point `Maps_URL` at `https://raw.githubusercontent.com/skyelaird/CZQM-vACC/main/GroundRadar/CYHZ/GRpluginMaps.txt` once the rebuild is stable. Not required for delivery but useful for the AIRAC update workflow.

---

## 13. Translation notes — spec assumptions vs LPPT reality

Before Phase 2, surface these to Joel:

| Spec language (§3, §4) | LPPT reality | Implication |
|---|---|---|
| "Tag the runway polygons with `AREATYPE` for RMCA" | LPPT has no runway tagging. `AREATYPE` isn't a directive; the family-token is part of `COORDTYPE`. RMCA works off `Airport_Runway_End` in settings. | Phase 2 should be "configure `Airport_Runway_End` + safety-net flags in settings", not "tag geometry." |
| "Tag the taxiway polygons near runways with `TWYTYPE`" | LPPT does this via hidden `MAP:TWY <id>` blocks with `COORDTYPE:TWYTYPE:NONE`. | The pattern is right but the file structure (one hidden block per taxiway) needs to be authored. |
| "Use `LAYER:N` directives to control draw order" | LPPT uses none — draw order is file order. | Plan around ordering; don't expect `LAYER:N` to work. (Worth a one-line confirmation in the Developer Guide PDF.) |
| "Apply zoom-aware detail using `ZOOM:N` directives" | LPPT has no `ZOOM:` directives. Visibility is controlled by folder/ASR. | Verify what zoom controls actually exist in GRP 1.6 before promising auto-hide thresholds. |
| "Replicate LPPT's parked-aircraft symbols" | LPPT has no parked-aircraft symbols defined. Stand labels are plain text. | Either find them elsewhere (TopSky?), or reframe Phase 4 to skip parked-aircraft icons. |
| "Helicopter ramp distinct from airline apron" | LPPT has no helicopter ramp distinction in its palette. | Define a new `SMGS_HELI_APRON` colour for CYHZ. |
| "NOTAM-driven closures out of scope" | LPPT has them implemented via `TWYCLOSED` + `ACTIVE:LVP`. | Note the mechanism in case Joel changes his mind for CYQM/CYYT. |

---

## 14. Open questions surfaced by this analysis (to add to spec §8)

1. **`AREATYPE` literal interpretation:** confirm with the GRP Developer Guide whether `AREATYPE` exists as a directive or whether the spec author meant `COORDTYPE` with `TWYTYPE`/`OTHER` family tokens.
2. **`System_*` flag semantics:** the abbreviations are my inference. Confirm `APM`/`APW`/`CBM`/`ECM`/`OSM`/`RIM`/`RUM`/`RVM` against the Version History PDF before configuring them.
3. **Parked-aircraft symbols:** are these something Joel saw in a LPPT screenshot, or in a different package? If they're not in `topskylppc`, what should we mimic?
4. **`LAYER:N` / `ZOOM:N`:** confirm whether GRP 1.6 supports these at all — the spec asserts they exist; LPPT proves they're at least not required.
5. **Light/dark palette mechanism:** ship two `COLORDEF` files with conditional `#include`-style loading? Two whole maps files? Or per-ASR `PLUGIN:Ground Radar plugin:ColorScheme:` if such a setting exists? Joel's call after Phase 1 review.
6. **Display rotation for CYHZ:** runway 05/23 (real heading ~055°) vs 14/32 (~140°). Pick a `DisplayRotation` that screen-up-aligns one of them. Default suggestion: 305° rotation to put runway 05 across the bottom of the view, since 05 is the primary IFR runway. Joel's call.

---

## 15. Summary recommendation

LPPT is a strong, well-organized reference. The bones we should copy directly:

- The 22-entry `COLORDEF` palette with `SMGS_*` semantic naming (adjusted RGBs for Canadian/dark variant)
- The MAP block grammar with `AIRPORT:<icao>` scoping and (selectively) `ACTIVE:LVP:...` conditional activation
- The folder-per-concern menu structure (`CYHZ`, `CYHZ TWY DATA`)
- The hidden `COORDTYPE:TWYTYPE:NONE` polygon-per-taxiway pattern (for CMAC/incursion monitoring)
- The settings-file pattern: per-airport `Airport_*` and `System_*` blocks, per-airport tag-layout overrides
- The 4-line tag-family pattern (`Label=GND:*:*` and `Label=APP:*:*`)
- The ASR header pattern (`GroundMode`, `AirportRadius`, `DisplayRotation`, `WINDOWAREA`, `TAGFAMILY`)

What to **not** copy from LPPT without rethinking:

- Stand-assignment data (out of scope)
- TWY CLOSURES overlays (out of scope unless Joel changes his mind)
- The huge approach-level `FOLDER:APP` content (CTR/VOR/NDB list) — LPPC has many airports in one file; for CYHZ we'll only need an LPP-equivalent for CZQM TMA, which is a much smaller scope
- The remote `Maps_URL` distribution unless Phase 7 decides it's worth the operational complexity

Phase 2's framing in the spec should be revised based on the "spec vs reality" table in §13 above. Recommended Phase 2 reframe: "configure per-airport `[CYHZ]` block in `GRpluginSettings.txt` with `Airport_Runway_End` declarations and `System_*` safety-net flags; build the hidden `CYHZ TWY DATA` taxiway-tag layer; verify safety nets fire."
