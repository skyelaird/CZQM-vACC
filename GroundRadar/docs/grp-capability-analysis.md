# GRP capability analysis

Synthesis of the Ground Radar plugin 1.6 manual against the LPPT and Norway implementation patterns, with a CZQM recommendation. Written 2026-05-15 from the three PDFs in `reference docs/`:

- `Ground Radar plugin for EuroScope - Developer Guide.pdf` (73 pages — authoritative spec)
- `Ground Radar plugin for EuroScope - General.pdf` (30 pages — operational concepts)
- `Ground Radar plugin for EuroScope - Version History.pdf` (4 pages — what's new in 1.6)

Text extracts of all three are at `tools/osm-to-grp/data/Ground Radar plugin for EuroScope - *.txt` if you want to re-read passages directly.

## 1. Headline takeaways

1. **Two modes, mutually exclusive per ASR.** Ground mode (based on the SAAB A3000 A-SMGCS surface system) and Tower mode (based on the SAAB RDP air situation display) are alternatives. The Developer Guide §2.1/§2.2 frames them as either/or — one `PLUGIN:Ground Radar plugin:GroundMode:<icao>` *or* one `PLUGIN:Ground Radar plugin:TowerMode:<icao>` per ASR, not both. **Joel's existing `CYHZ-TWR_GRP.asr` has both lines, which is anomalous.** The Norway and LPPT reference ASRs both use one or the other only.
2. **Nine safety nets, all toggleable by `System_*` flag + tunable by `System_*_*` parameters.** They subdivide into RMCA (runway conflicts, controlled by `System_RIM`) and CMAC (clearance/conformance, controlled by multiple flags). See §6 below.
3. **GRP 1.6 supports `LAYER:N`, `ZOOM:N`, `FILTER_ASR/CALLSIGN/ID`, `ACTIVE:LVP/RWY/ID/CALLSIGN/MAP/STAND/GNDSTS`, `AND_ACTIVE`, conditional `OTHER_MAP_ACT`, `HIDDEN`, `SCREEN-SPECIFIC/GLOBAL`** — all in the maps file. My earlier `lppt-analysis.md` claimed several of these don't exist; that's wrong. They exist; LPPT just doesn't use them.
4. **`SCTDATA` and `SCTFILEDATA` let a `MAP:` block pull items directly from the active sector file or a named one.** This is the bridge between the LPPT pattern (GRP-native maps) and the Norway pattern (sector-file geometry) — you can write a GRP-native `MAP:` block whose contents come from `[GEO]`/`[REGIONS]`/`FREETEXT` in the `.sct`.
5. **Safety-net tagging for taxiways/areas requires `COORDTYPE:TWYTYPE:...` or `COORDTYPE:AREATYPE:...` combined with `RESTRICTION:` lines.** A `TWYTYPE:NONE` block with no `RESTRICTION:` lines (which is what LPPT has for each taxiway, and what our current `CYHZ TWY DATA` blocks contain) does **not** trigger RVM alerts. It's a tagging hook ready to receive restrictions; until restrictions are added it's a visual no-op.
6. **The Approach Path Monitoring safety net requires `AppPath=` definitions in `GRpluginSettings.txt`.** Just setting `System_APM=1` is necessary but not sufficient — without `AppPath_APM=` lines defining the approach geometry, APM never fires.

## 2. The two modes

The mode determines the plugin's whole UI and behavior.

| Aspect | Ground mode | Tower mode |
|---|---|---|
| Heritage | SAAB A3000 A-SMGCS (surface) | SAAB RDP (air situation) |
| ASR line | `PLUGIN:Ground Radar plugin:GroundMode:<icao>` | `PLUGIN:Ground Radar plugin:TowerMode:<icao>` |
| Default altitude filter | Hide tracks above airport elev + `System_GroundMode_AltFilter_AAL` (default 5000 ft AAL) | Hide tracks outside `System_TowerMode_AltFilter_Low`/`_High` (defaults -1000 / 99900 ft) |
| Track symbols | PSR / SSR / history dots | PSR / SSR-only / PSR+SSR / ADS-B-only / SPI variants, history dots |
| Track label fields available | `ALRT`, `CALLSIGN`, `ASSR_E`, `COMM`, `WTC`, `ATYP`, `MALRT`, `RMK`, `STAND`, `DRWY`, `DEP`, `FLTID_E`, `TSSR` | `A` (manual alert), `CALLSIGN`, `COMM`, `AFL+VS`, `GS`, `MALRT`, `RMK` |
| Stand assignment system | Available | Not available |
| Windows available | Traffic Situation, Approach, Approach Path, Runway Config, RVR, QNH, METAR, Wind Rose, Clock, Map Selection | Same set (Window menu items active only in ground mode per General §3.3 — but tower-mode ASRs still load APP/APW/TSW if enabled in settings) |
| Lists available | TTT, Departure Timer, Alerts, Arrival, Departure, Stands | Alerts (limited subset) |
| Safety nets | All 9 active | Only emergency-related alerts |

**Implication for CZQM:** The four `.asr` files implied by spec §3 (Ground × Tower × Light × Dark) split cleanly along the GroundMode/TowerMode axis. The `CYHZ_Ground_*.asr` files use `GroundMode:CYHZ`; the `CYHZ_Tower_*.asr` files use `TowerMode:CYHZ`. **Pick one per file, not both.**

## 3. ASR file shape

Minimum viable ASR for a GRP display (from Developer Guide §2):

```
DisplayTypeName:Ground Radar display
DisplayTypeNeedRadarContent:0
DisplayTypeGeoReferenced:1
PLUGIN:Ground Radar plugin:GroundMode:CYHZ      # or TowerMode:CYHZ
PLUGIN:TopSky plugin:NoDraw:1                   # if TopSky is loaded — suppresses TopSky overlay
WINDOWAREA:<lat_min>:<lon_min>:<lat_max>:<lon_max>
TAGFAMILY:<family-name>
```

Optional but commonly added:

| Line | Purpose |
|---|---|
| `PLUGIN:Ground Radar plugin:AirportElevation:<ft>` | Override (the setting can also live in `GRpluginSettings.txt`) |
| `PLUGIN:Ground Radar plugin:AirportRadius:<nm>` | Override (1.1 ENBR, 1.6 ENGM, 1.9 LPPT — tighter than the default 2.5 we used) |
| `DisplayRotation:<deg>` | Screen rotation (counterclockwise positive in EuroScope) |
| `SHOWC`, `SHOWSB`, `BELOW`, `ABOVE`, `LEADER`, `HISTORY_DOTS` | EuroScope display flags |
| `SIMULATION_MODE:1` or `:2` | Sweatbox simulation mode (used by Norway ASRs) |
| `PLUGIN:TopSky plugin:HideMapData:VERTLIMIT` | Hide TopSky's vertical-limit display |
| EuroScope-native `Geo:`, `Regions:`, `Free Text:`, `ARTCC ...:` refs | Items from `.sct` — this is the Norway pattern |

Note: an ASR can both have these standard EuroScope refs AND let the GRP plugin draw its own maps from `GRpluginMaps.txt` on top. They coexist; user can toggle each independently in the respective menus. Visual overlap is the cost.

## 4. Maps grammar (`GRpluginMaps.txt`)

### 4.1 Document-level directives

```
COLORDEF:<name>:<r>:<g>:<b>           # one per named colour, RGB 0-255
SYMBOLDEF:<name>                      # custom symbols (then MOVETO/LINETO/POLYGON/ELLIPSE/FILLARC/SETPIXEL/FILLRECT)
DEFAULT_SCREEN-SPECIFIC               # subsequent maps default to per-screen toggle state
DEFAULT_GLOBAL                        # subsequent maps default to all-screens-synced toggle state
//VERSION:<string>                    # only meaningful with Maps_URL; used to decide whether remote replaces local
```

### 4.2 Per-map directives

A `MAP:` block has one of these structures. Mandatory minimum: `MAP:` + `FOLDER:` + something to draw (drawing primitives, an `RWYCLOSEDARR/DEP` line, or a `BLOCKS/LIMITS` line).

```
MAP:<name>                            # display name in the menu
MAP:<name>:<visibility-flags>         # flags: A=APP window, G=ground main, T=tower, 2=Traffic Sit Window
FOLDER:<name>                         # | separator creates subfolders; no leading space, no \
AIRPORT:<icao,icao,...>               # restricts map to specified airports
LAYER:<n>                             # draw order (-999..-1 and 1..999; layer 0 is reserved; default 1)
ZOOM:<pix/nm>                         # positive: hide lines below this zoom; negative: above; can repeat within map
HIDDEN                                # not shown in menu (requires at least one ACTIVE line)
SCREEN-SPECIFIC | GLOBAL              # per-map visibility scope override
ACTIVE:1                              # always active on plugin load
ACTIVE:<sched>                        # date/time scheduled activation
ACTIVE:RWY:ARR:<list>:DEP:<list>      # active runways match
ACTIVE:ID:<your>:<notYour>:<online>:<notOnline>  # controller IDs match
ACTIVE:CALLSIGN:<your>:<notYour>:<online>:<notOnline>  # callsigns match
ACTIVE:LVP:<icao,...>:<0|1>           # LVP state matches
ACTIVE:MAP:<=|!>:<folder\name>        # tied to another map's state
ACTIVE:STAND:<OCCUPIED|ASSIGNED|BLOCKED|LIMITED>:<found>:<notFound>  # stand status
ACTIVE:GNDSTS:<found>:<sts>:<notFound>:<notSts>  # ground status of occupier
AND_ACTIVE:<same-as-ACTIVE>           # combines with previous ACTIVE rule (multiple AND_ACTIVE allowed in a set)
FILTER_ASR:<itemlist>                 # condition on PLUGIN:TopSky plugin:ShowMapData/HideMapData in ASR
FILTER_CALLSIGN:<your>:<notYour>:<online>:<notOnline>  # subsequent lines drawn only if condition met
FILTER_ID:<your>:<notYour>:<online>:<notOnline>
FILTERS_OFF / FILTER_ASR_OFF / FILTER_CALLSIGN_OFF / FILTER_ID_OFF
OTHER_MAP_ACT:<=|!>:<folder\name>     # toggle another map when this map toggles
OTHER_MAP_ACT:<=|!>:<folder>          # toggle all maps in folder
RWYCLOSEDARR:<icao>:<rwyList>         # mark runways closed-for-arrivals (alerts when assigned)
RWYCLOSEDDEP:<icao>:<rwyList>
BLOCKS:<icao>:<standList>             # block stands from auto-assignment while active
LIMITS:<icao>:<standList>:<spanOrCode>[:<length>]  # limit aircraft size on stands while active
```

### 4.3 Per-map drawing primitives

Style and font (apply to all subsequent items in the map until changed):

```
COLOR:<name>                          # line/text colour
COLOR:<name>:<fillName>               # plus fill colour
COLOR:<name>:<fillName>:<bgName>      # plus hatch-background colour
STYLE:<name>                          # line style (Solid|Alternate|Dash|Dot|DashDot|DashDotDot|Null or custom from LINESTYLEDEF)
STYLE:<name>:<width>
STYLE:<name>/<endCap>/<joinType>:<width>  # endCap: Flat|Round|Square. joinType: Bevel|Miter|Round
LINESTYLEDEF:<name>:<brush>:<hatch>[:<dashArray>]  # define a custom line style
FONTSIZE:<type>:<size>                # type: = (set), - (reduce), + (increase), * (multiply); size 1-99
FONTSIZE:0                            # back to default
FONTSTYLE:<weight>:<italic>:<underline>:<strikethrough>
FONTSTYLE:0
TEXTALIGN:<flags>                     # combine L/C/R (horizontal) and T/C/B (vertical), e.g. "LT"
```

Drawing primitives:

```
LINE:<lat1>:<lon1>:<lat2>:<lon2>
LINE:<pos1>:<pos2>                    # <pos> = sector file id (fix, VOR, NDB, airport, or AIRPORT/RWY)
COORDTYPE:<areaType>:<drawType>[:<hatch>][:<fillType>]
COORD:<lat>:<lon>                     # add vertex to current polygon/polyline
COORD:<pos>
COORD_PBD / COORD_PBX / COORD_AF / COORD_CR / COORD_DF / COORD_FC / COORD_FD /
COORD_HM / COORD_CIRCLE / COORD_TURN / COORD_LIST   # see Developer Guide §3.2 for parameter details
                                                    # — covers polar, bearing-distance, arc, hold pattern,
                                                    # circle, turn, courseradial constructions
RESTRICTION:<type>:<value>            # apply to subsequent AREATYPE/TWYTYPE
                                       # types: MAXWTC, MAXWEIGHT, MAXWINGSPAN, MAXCODE,
                                       # MAXENGINECOUNT, NOTENGINETYPES, NOTATYP
GROUP:<name>:<value:value:...>        # alias for use in RESTRICTION NOTATYP via GROUP_<name>
SCTDATA:<type>[\<name>]               # draw items from active sector file
                                       # type: GEO, ARTCC[_LOW|_HIGH], SID, STAR, LOW AIRWAY,
                                       # HIGH AIRWAY, or FREETEXT\<group>[\<name>]
SCTFILEDATA:<type>[\<name>]           # draw items from a sector file specified by SCTFILEPATH
                                       # adds REGIONS, SECTOR, SECTORLINE support
                                       # use SCTFILEDATA/MONO to force colour override
SCTFILEPATH:<path>                    # absolute or relative; trailing * picks last alphabetically
SYMBOL:<name>:<lat>:<lon>             # place a SYMBOLDEF instance
SYMBOL:<name>:<lat>:<lon>:<label>:<offsetX>:<offsetY>
TEXT:<lat>:<lon>:<text>               # text label
TEXT:<lat>:<lon>:<text>:<offsetX>:<offsetY>
TEXT/<align>:<lat>:<lon>:<text>       # per-label alignment override (e.g. TEXT/LT)
RWY_AREA:<lat1>:<lon1>:<lat2>:<lon2>:<width>[:<startOffset>:<endOffset>]
                                       # rectangular runway-shaped polygon
RWY_ARROWS:<icaoRwy>:<lat1>:<lon1>:<lat2>:<lon2>:<width>[:offsets:spacing:thickness]
                                       # auto-coloured by active runway state
RWY_XS:<lat1>:<lon1>:<lat2>:<lon2>:<width>[:offsets:spacing:thickness]
                                       # closure X-marks
```

### 4.4 COORDTYPE area-type vocabulary (the entire safety-net tagging surface)

| AreaType | Combined with | Purpose |
|---|---|---|
| `OTHER` | any drawType | Just visual — no safety net hook |
| `APW` | usually `REGION_FILLONLY` | Trips Area Proximity Warning when an aircraft enters |
| `RWYCLOSED` | usually `REGION_FILLONLY` | Marks runway area as closed; combine with `RWYCLOSEDARR/DEP` for assignment alerts |
| `TWYCLOSED` | usually `REGION_FILLONLY` | Marks taxiway area as closed |
| `AREATYPE` | preceded by `RESTRICTION:` lines | Restricted area (RVM alerts when aircraft inside violates) |
| `TWYTYPE` | preceded by `RESTRICTION:` lines | Restricted taxiway (RVM alerts when aircraft on it violates) |

DrawType options: `POLYGON`, `POLYLINE`, `REGION` (filled with outline), `REGION_FILLONLY`, `NONE`. The `NONE` drawType makes the polygon invisible — useful for pure tagging.

**Critical:** `COORDTYPE:TWYTYPE:NONE` *without* preceding `RESTRICTION:` lines tags the polygon but enforces nothing. RVM will not fire. This is what LPPT's `LPPT TWY DATA` folder contains, and what our generated `CYHZ TWY DATA` folder contains today. As written, those blocks are visual placeholders — the engine knows "this is taxiway X" but has no restrictions to compare aircraft against.

## 5. Settings grammar (`GRpluginSettings.txt` and `GRpluginSettingsLocal.txt`)

### 5.1 Scoping

Settings load in this order, with later values overriding earlier ones:

1. System-wide from `GRpluginSettings.txt`
2. System-wide from `GRpluginSettingsLocal.txt`
3. Airport-specific from `GRpluginSettings.txt` (under `[<icao>]` headers)
4. Airport-specific from `GRpluginSettingsLocal.txt`

The recommended split (Developer Guide §3.5):
- `GRpluginSettings.txt` ships with the package — system defaults + airport-specific operational data
- `GRpluginSettingsLocal.txt` is user-personal — resolution-specific window positions, GUI scale, etc.

`[<icao>]` headers switch the subsequent lines to airport-scoped. Some settings *must* be airport-specific (`Airport_*`, `Window_APP_CenterPos`, etc.); others can be either.

### 5.2 Per-airport settings that matter for CZQM

```
[CYHZ]
Airport_Elevation=477                 # ft AMSL — overrides ASR's PLUGIN:...:AirportElevation
Airport_Radius=2.5                    # nm — should reduce to ~1.6 per Norway convention
Airport_TransAlt=18000                # ft (Canada)
Airport_MagVar=-18.0                  # degrees east (CYHZ is ~18°W magnetic)
Airport_Refpoint=N044.52.51.620:W063.30.31.430   # override; default comes from .sct [AIRPORT]
Airport_LVP=1                         # 0/1 — enables the LVP toggle for this airport

Airport_Runway_End=05:N044.51.56.318:W063.31.38.110   # from AeroNav .sct [RUNWAY] — required
Airport_Runway_End=23:N044.53.18.250:W063.30.17.200
Airport_Runway_End=14:N044.53.37.388:W063.31.02.769
Airport_Runway_End=32:N044.52.53.691:W063.29.35.278

# Airport_Runway_Thr — only needed if displaced thresholds differ from runway ends
# Airport_Runway_Area_LVP — only if default area isn't a good fit
# Airport_Runway_FinalLength / _LongFinalLength / _FinalXTE — tune Time To Threshold list inclusion

Airport_SMR_Raw=2                     # primary raw video: 0=none, 1=ESE, 2=always
Airport_SMR_Track=0                   # primary tracks: 0=none, 1=ESE, 2=always
Airport_ModeA=1                       # Mode-A SSR: 0=none, 1=ESE, 2=always
Airport_ModeS=1                       # Mode-S SSR

# Window defaults — per-airport
Window_APP=1,1,...                    # APP window state
Window_APP_Scale=10                   # pixels/nm
Window_WindRose=05,2,...
# ... etc.
```

### 5.3 System safety-net flags

These can live system-wide (defaults) and be overridden per airport:

| Flag | Default | Meaning |
|---|---|---|
| `System_APM` | 1 | Approach Path Monitoring. **Requires `AppPath=` + `AppPath_APM=` lines to actually fire.** |
| `System_APW` | 1 | Area Proximity Warning. Requires `COORDTYPE:APW:...` maps to define areas. |
| `System_CBM` | 1 | Clearance Behavior Monitoring (NO TOF CLR, NO TAXI CLR, NO PUSH CLR, HIGH SPEED, STATIONARY RPA, NO CONTACT info, TRANSFER? info). |
| `System_ECM` | 1 | Emergency Code Monitoring (7500/7600/7601/7700). |
| `System_ICM` | 1 | Identification Conflict Monitoring (duplicate squawks within 100 nm). |
| `System_OSM` | 1 | Occupied Stand Monitoring. Requires `GRpluginStands.txt`. |
| `System_RIM` | 1 | Runway Incursion Monitoring + RMCA conflict alerts. Uses `Airport_Runway_End` + `System_RwyArea*`. |
| `System_RUM` | 1 | Runway Usage Monitoring (assigning a runway not active for that direction). |
| `System_RVM` | 1 | Restriction Violation Monitoring. Requires `AREATYPE`/`TWYTYPE` maps with `RESTRICTION:`. |

Each can be set to `0` to switch off but keep the button on the global menu, or `-1` to disable and hide the button entirely.

Tuning parameters exist for each (`System_RMCA_RWY_Closure`, `System_RMCA_APP_Distance`, `System_CMAC_HighSpeed`, `System_CMAC_NoTaxiClr_Speed_Info`, etc.) — Developer Guide §3.5.3 has the full list.

### 5.4 Track label customization (`Label=` lines)

Syntax: `Label=<MODE>:<TYPE>:<LINE>:<field>[:<field>...]`

- MODE: `APP`, `APW`, `GND`, `TWR`, `ALL`
- TYPE: `ARR`, `DEP`, `OTH`, `UNC`, `ALL`
- LINE: `0`-`3`
- Each field: `<name>,<minPos>,<spacesBefore>[,<extraData>]`

Available field names include: `ALRT`, `MALRT`, `A_FLAG`, `ADEP`, `ADES`, `AFL`, `AFL+VS`, `AHDG`, `ARWY`, `ASSR`, `ASSR_E`, `ATYP`, `CALLSIGN`, `CFL`, `COMM`, `DEP`, `DRWY`, `FLTID`, `FLTID_E`, `GS`, `REF`, `REG`, `RMK`, `SI` (sector indicator), `SID`, `STAND`, `STAR`, `STS`, `TSSR`, `TYP`, `VS`, `WTC`, `WTG`, `WTG_EU`.

`ExtraData` is a packed integer with per-field semantics — e.g. for `AFL` the digit groups control digit count, prefix style, and metric divisor.

This is the mechanism for spec §5's ground/tower tag families. Per the LPPT pattern, define the global default and override per-airport under `[CYHZ]` if needed.

### 5.5 Approach Path Monitoring config (the missing piece for APM)

```
AppPath=CYHZ:RNAV 05:N044.51.56.318:W063.31.38.110:053.0:R:477:3.0
AppPath_APM=ABL:0.5:5.0                          # alerts above/below/lateral, range 0.5-5 nm from threshold
AppPath_APM_Vert_Lim=200:5000                     # don't show below-path alerts above 200 ft; no above-path above 5000 ft
```

Without `AppPath_APM=` lines, APM does nothing even if `System_APM=1`.

## 6. Safety nets (definitive table)

This corrects my earlier `lppt-analysis.md §9` where I guessed at the abbreviations.

| Net | Full name | What it monitors | Track-label alert text |
|---|---|---|---|
| **RMCA** | Runway Monitoring and Conflict Alerting | Conflicts on a single runway, or between two crossing runways (closure-rate / time-to-threshold based). Controlled by `System_RIM`. | `CONFLICT` |
| **RIM** | Runway Incursion Monitoring | Aircraft on a runway with wrong ground state for the situation (e.g. departing aircraft on its runway not in `LINE UP` / `DEPA`). | `RWY INCURSION` |
| **CBM** | Clearance Behavior Monitoring | No-takeoff clearance (>20 kts on rwy without DEPA), no-taxi clearance, no-pushback clearance, high speed (>55 kts off runway), stationary in runway protected area, no contact (close to threshold still in TRANSFER IN), transfer? (departing still assumed past defined volume). | `NO TOF CLR`, `HIGH SPEED`, `STATIONARY RPA`, `NO CONTACT`, `TRANSFER?`, etc. |
| **ECM** | Emergency Code Monitoring | Squawks 7500/7600/7601/7700 within 30 nm of airport. | `HIJACK`, `COMFAIL`, `COMFAIL VMC`, `EMERG` |
| **APW** | Area Proximity Warning | Aircraft inside a `COORDTYPE:APW:...` polygon. Also covers RWY CLOSED (via `RWYCLOSEDARR/DEP` + closed runway polygons) and TWY CLOSED (via `TWYCLOSED` polygons). | `RWY CLOSED`, `TWY CLOSED`, `APW` |
| **RVM** | Restriction Violation Monitoring | Aircraft on a runway or taxiway not suitable for its size/type. Uses `AREATYPE`/`TWYTYPE` + `RESTRICTION:` lines, plus `Airport_Runway_Max*` per-runway settings. | `RWY TYPE`, `TWY TYPE`, `RESTRICTION` |
| **APM** | Approach Path Monitoring | Aircraft deviating from a defined approach path (lateral or vertical). Configured via `AppPath=` + `AppPath_APM=`. | `APM` |
| **OSM** | Occupied Stand Monitoring | Arriving aircraft whose assigned stand is occupied. Requires `GRpluginStands.txt`. | `STAND` |
| **ICM** | Identification Conflict Monitoring | Duplicate Mode-A codes within 100 nm. | `DUPE` |
| **RUM** | Runway Usage Monitoring | Aircraft assigned a runway that is not active for that direction. | `ARWY` / `DRWY` (with red background) |

**Implication for CZQM:** of the nine, the ones we can wire up for CYHZ today with the geometry/settings we have:

| Net | Wireable today? | What's needed |
|---|---|---|
| RIM / RMCA | ✓ | `Airport_Runway_End` (already in our settings). Tuning via `System_RwyArea*` (already set). |
| ECM | ✓ | No config needed — works off squawk codes alone. |
| ICM | ✓ | No config needed. |
| RUM | ✓ | Works off EuroScope's active-runway data. |
| CBM | ✓ | Tuning thresholds (`System_CMAC_*`); no map work. |
| APW | partial | Works for `RWYCLOSED`/`TWYCLOSED` only when we author closure polygons. No area-prohibition zones at CYHZ on the table. |
| RVM | not yet | Needs `RESTRICTION:` lines on `AREATYPE`/`TWYTYPE` maps. Our current `TWY DATA` blocks have no restrictions. CYHZ probably needs none unless we want to enforce per-taxiway aircraft size limits. |
| APM | not yet | Needs `AppPath=` definitions for at least RNAV approaches we care about. Significant per-runway work. |
| OSM | not for now | Requires `GRpluginStands.txt` with full stand data — out of CYHZ scope per spec §3. |

## 7. Maps file role — the LPPT vs Norway split

### 7.1 What LPPT actually uses

From my Phase 1 LPPT analysis, refined now that I've read the manual:

- 22 `SMGS_*` and `ASP_*` `COLORDEF`s
- `SYMBOLDEF` for 4 symbols (`VOR`, `NDB`, `RWYMARKER`, `UNCORTGT`); plus 3 plugin-symbol overrides in `GRpluginSymbols.txt`
- Per-airport folder structure: one root folder per airport, plus `<icao> TWY DATA` (hidden) and `<icao> TWY CLOSURES`
- `COORDTYPE` vocabulary used: `OTHER:REGION`, `OTHER:REGION_FILLONLY`, `OTHER:POLYLINE`, `TWYTYPE:NONE`, `TWYCLOSED:REGION_FILLONLY:0:60`
- `AIRPORT:<icao>` on every per-airport map
- `ACTIVE:LVP:<icao>:0` on closure overlays (engage only in LVP)
- `BLOCKS:<icao>:<stands>` on one closure map (TWY F)
- `HIDDEN` on all `TWY DATA` blocks
- `SCTDATA:ARTCC LOW\...` to import CTR boundaries from the active sector file (the `MAP:CTR:A` block uses `SCTDATA:` to pull from `[ARTCC LOW]` sections)
- `LAYER:N` — **not** used. Draw order = file order.
- `ZOOM:N` — **not** used. Detail control via folder/ASR visibility.
- `FILTER_CALLSIGN/ID` — **not** used. (Per LPPT's flat structure.)
- `RESTRICTION:` lines — **not** used. The `TWYTYPE:NONE` blocks are tagging-only with no enforcement.
- `AppPath=` definitions — **not** present in the LPPT settings file I read.

LPPT's GRpluginSettings.txt has per-airport `[LPPT]`/`[LPPR]`/`[LPFR]`/`[LPMA]`/`[LPPS]` blocks with full `Airport_*` and `System_*` configuration. The `[LPPT]` block turns most safety nets on; the others mostly leave defaults. Per-airport tag-layout `Label=` overrides for LPMA/LPPS that blank all ground-mode labels.

The ASR (TWRLIS.asr) is **21 lines**. It declares a ground-mode view (`GroundMode:LPPT`) and the airport overrides. No EuroScope-native `Geo:`/`Regions:`/`Free Text:` references. All geometry comes from `GRpluginMaps.txt`.

### 7.2 What Norway actually uses

The ENGM GROUND.asr and ENBR GROUND.asr are **~1100 lines each**, mostly consisting of:

- ~50 `ARTCC high boundary:` and `ARTCC low boundary:` lines covering Norway's whole airspace
- ~700 `Free Text:<ICAO> <category>\<label>:freetext` lines covering taxiway letters and stand numbers at all Norwegian airports
- ~50 `Geo:<ICAO> Region:` lines covering each airport's surface drawing
- ~19 `Regions:<ICAO>:polygon` lines covering each airport's surface fills
- Header block: `DisplayTypeName:Ground Radar display`, `TAGFAMILY:GRplugin`, `WINDOWAREA:<tight bbox>`, `DisplayRotation:<heavy>`, `AirportElevation`, `AirportRadius:1.1`-`1.6`, `GroundMode:<icao>` (no TowerMode), Virtual Controller Assistant plugin params

So Norway's geometry comes entirely from the sector file via standard EuroScope refs. There's no GRP `MAP:` block structure in evidence (no `GRpluginMaps.txt` visible in what Joel added — only the two ASRs). The GRP plugin is used purely for:

- Tracking, ground-mode display, label customization
- Safety nets driven by `Airport_Runway_End` in their `GRpluginSettings.txt` (not visible in the files Joel added, but inferable)

Norway gets none of the GRP-native capabilities that depend on `MAP:` blocks: no LVP overlay variants tagged via `ACTIVE:LVP:...`, no RVM restrictions, no FILTER_CALLSIGN-driven position-aware visibility. They keep the existing `.sct` geometry and accept the trade-off.

### 7.3 Capabilities matrix

For each GRP capability, which pattern unlocks it:

| Capability | LPPT (MAP-block) | Norway (sector-file) | Notes |
|---|:---:|:---:|---|
| Per-airport `[ICAO]` settings, safety net flags | ✓ | ✓ | Lives in `GRpluginSettings.txt` regardless |
| RIM/RMCA (runway incursion + conflict) | ✓ | ✓ | Needs only `Airport_Runway_End` |
| ECM / ICM / RUM / CBM | ✓ | ✓ | Pure config |
| RVM (taxiway/area restrictions) | ✓ | ✗ | Needs `AREATYPE/TWYTYPE` + `RESTRICTION:` in `MAP:` blocks |
| APW (closed runway/taxiway/area) | ✓ | ✗ | Needs `COORDTYPE:*CLOSED:...` |
| LVP-conditional overlays | ✓ | ✗ | Needs `ACTIVE:LVP:...` on `MAP:` blocks |
| Active-runway-conditional maps | ✓ | ✗ | `ACTIVE:RWY:ARR:...:DEP:...` |
| Position-aware visibility (top-down working) | ✓ | ✗ | `FILTER_CALLSIGN/ID` or `ACTIVE:ID/CALLSIGN` |
| Zoom-aware detail | ✓ | ✗ | `ZOOM:N` |
| Light/dark palette swap | ✓ | partial | LPPT pattern: separate `COLORDEF` blocks. Norway pattern: would require editing the `.sct`'s `#define COLOR_*` — affects all ASRs |
| AppPath APM | ✓ | ✓ | `AppPath=` lives in settings |
| OSM (occupied stand) | ✓ | ✓ | `GRpluginStands.txt` |
| Track label customization | ✓ | ✓ | `Label=` in settings |
| Existing AeroNav `.sct` geometry | bridgeable via `SCTDATA`/`SCTFILEDATA` | directly | Norway gets it for free; LPPT pattern can pull it in via `SCTDATA` |

### 7.4 The bridge — `SCTDATA` and `SCTFILEDATA`

This is the bit I missed earlier and that changes the analysis. The Developer Guide §3.2 (page 13-14) defines two directives that let a GRP-native `MAP:` block import geometry from a sector file:

```
SCTDATA:GEO\CYHZ Groundlayout Halifax
SCTDATA:REGIONS\CYHZ Halifax        # via SCTFILEDATA only — REGIONS not supported by SCTDATA
SCTDATA:FREETEXT\CYHZ CYHZ TAXIWAY\A
SCTFILEDATA:GEO\CYHZ Groundlayout Halifax
SCTFILEDATA:REGIONS\CYHZ Halifax
SCTFILEDATA/MONO:GEO\CYHZ Groundlayout Halifax   # force the current MAP block colour
SCTFILEPATH:..\CZQQ-CZQM-CZQX_*.sct              # specify the sector file to pull from
```

This means a `MAP:` block can contain a single line like `SCTFILEDATA:GEO\CYHZ Groundlayout Halifax` and inherit all ~1,300 hand-drawn taxiway segments from the AeroNav sector file. The `MAP:` block then carries `FOLDER:`, `ACTIVE:`, `AIRPORT:`, `LAYER:`, `ZOOM:`, `FILTER_*`, etc. — i.e. the existing geometry gets the full GRP-native capability set wrapped around it.

This is the key option I want to surface as the recommended path.

## 8. Recommendation for CZQM

### 8.1 Pattern: GRP-native framework, with `SCTFILEDATA` to import polished `.sct` geometry

Rather than choosing pure LPPT (synthesize everything from OSM) or pure Norway (rely on sector-file refs from outside the plugin), use the GRP `MAP:` block framework with `SCTFILEDATA` directives wherever the AeroNav `.sct` already has polished geometry.

```
SCTFILEPATH:..\reference docs\CZQQ-CZQM-CZQX_*.sct

MAP:SURFACE
FOLDER:CYHZ
AIRPORT:CYHZ
ACTIVE:1
COLOR:SMGS_TWY
SCTFILEDATA:GEO\CYHZ Groundlayout Halifax

MAP:GRASS
FOLDER:CYHZ
AIRPORT:CYHZ
ACTIVE:1
COLOR:SMGS_GRASS
SCTFILEDATA:REGIONS\CYHZ Halifax

MAP:LVP SURFACE
FOLDER:CYHZ
AIRPORT:CYHZ
ACTIVE:LVP:CYHZ:1
COLOR:SMGS_LVP
SCTFILEDATA:GEO\CYHZ Groundlayout Halifax - low vis
```

Three `MAP:` blocks, ~10 lines of GRP code, and we have:
- The full hand-drawn CYHZ surface from the AeroNav `.sct`
- The 74 `[REGIONS]` polygons for grass / apron fill
- The low-visibility variant activated only when LVP is on at CYHZ

Plus we keep our OSM-derived blocks for the things the `.sct` doesn't have well-structured:
- Per-taxiway `MAP:TWY <ref>` hidden blocks (for future RVM restrictions, or just for the engine to know taxiway names)
- Helipad fills and "H" markers
- Holding-position marking lines (the `.sct` has them as part of the GEO layer but at the SCTFILEDATA level we can't pull just the holding lines)
- Stand-number `TEXT:` labels — actually, the `.sct` has `FREETEXT:CYHZ CYHZ PARKING\<n>` for each. We can pull those too:

```
MAP:STAND NUMBER
FOLDER:CYHZ
AIRPORT:CYHZ
ACTIVE:1
COLOR:SMGS_LABEL
SCTFILEDATA:FREETEXT\CYHZ CYHZ PARKING
```

Bringing in all 39 hand-positioned stand labels in one line. **This is structurally much better than my OSM-position-based labels** because the AeroNav positions are AIRAC-accurate and editorially placed; OSM positions are mappers' guesses.

### 8.2 Where OSM-derived geometry still helps

- **The per-taxiway `TWYTYPE:NONE` polygons** — these need to be polygonal regions that the engine can map ground-position-to-taxiway-name. The `.sct` `[GEO]` data is line work, not polygon regions, so it can't fill this role. OSM buffered centerlines do.
- **Helipads** — the `.sct` doesn't have helipad-specific tagging. Our OSM override-driven helipad rendering is purpose-built.
- **Future CYQM / CYYT** — if their `.sct` geometry is less polished, OSM provides a uniform mechanical baseline.

### 8.3 Specific changes to the current outputs

The current `CYHZ/GRpluginMaps.txt` was generated as if we had no `.sct` to lean on. Given §8.1 above, the right structure is:

| Current MAP block | Recommended action |
|---|---|
| `BACKGROUND` (FOLDER:DIV) | Keep — defines the panel |
| `APRON` (OSM-derived polygons) | **Replace** with `SCTFILEDATA:REGIONS\CYHZ Halifax` filtered to apron-coloured regions, or keep OSM as a layer underneath |
| `RUNWAY` (OSM-buffered) | **Replace** with `SCTFILEDATA:GEO\CYHZ Groundlayout Halifax` (which includes runway outlines) plus a flat-fill via `Airport_Runway_Area` setting |
| `TAXIWAY` (OSM-buffered) | **Replace** with `SCTFILEDATA:GEO\CYHZ Groundlayout Halifax` |
| `TAXILANE` (OSM-buffered) | **Drop** — covered by the `.sct` GEO |
| `PARKING` (OSM-buffered) | **Replace** with `SCTFILEDATA:GEO\CYHZ Groundlayout Halifax Parking` |
| `BUILDINGS` (OSM hangars) | Keep — the `.sct` doesn't have these as separate items |
| `HOLDING POSITIONS` (OSM) | Keep — the `.sct` has these embedded in GEO; ours surfaces them as a separate toggleable layer |
| `HELIPAD` + `HELIPAD LABEL` (OSM + overrides) | Keep — covers `.sct` gap |
| `STAND NUMBER` (OSM positions) | **Replace** with `SCTFILEDATA:FREETEXT\CYHZ CYHZ PARKING` |
| `TAXIWAY NAME` (OSM midpoints) | **Replace** with `SCTFILEDATA:FREETEXT\CYHZ CYHZ TAXIWAY` |
| `TWY <ref>` (13 hidden OSM-buffered) | Keep — the per-taxiway polygon tagging the `.sct` can't provide |
| New: `LVP SURFACE` | **Add** — `SCTFILEDATA:GEO\CYHZ Groundlayout Halifax - low vis` with `ACTIVE:LVP:CYHZ:1` |

This reduces the OSM tool's primary output significantly. The `.sct` covers most of the visible surface; OSM fills the gaps (per-taxiway tags, helipads, hangars, holding-line surfacing).

### 8.4 ASR structure (the spec's 4-variant scheme)

Following the GRP manual's strict GroundMode/TowerMode separation:

```
CYHZ/asr/
├── CYHZ_Ground_Dark.asr      # GroundMode:CYHZ, dark COLORDEF
├── CYHZ_Ground_Light.asr     # GroundMode:CYHZ, light COLORDEF
├── CYHZ_Tower_Dark.asr       # TowerMode:CYHZ, dark COLORDEF
└── CYHZ_Tower_Light.asr      # TowerMode:CYHZ, light COLORDEF
```

Light/dark via `Setup_LoadMap` for the appropriate palette folder (e.g. a folder named `PALETTE LIGHT` and another `PALETTE DARK` with appropriate `COLORDEF` overrides; the ASR loads exactly one via `Setup_LoadMap:PALETTE DARK`). Or simpler: maintain two `GRpluginMaps.txt` files (`GRpluginMaps_dark.txt` and `GRpluginMaps_light.txt`) and use the `Maps_URL` mechanism to swap. Or simplest: same `MAP:` blocks but tag visibility with `ACTIVE:CALLSIGN:_DARK_:_LIGHT_:*:*` and have the ASR fake the callsign — bad idea, ignore.

Cleanest is two parallel folders inside the same `GRpluginMaps.txt`, each containing a full set of map blocks with one palette. ASR's `Setup_LoadMap` and `Setup_HideMap` switch between them at view-load time. Worth confirming in implementation.

For now (Phase 4 deferred), one starter ASR per mode is enough.

**Recommended changes to our `CYHZ_Ground.asr` today:**

- Remove `PLUGIN:Ground Radar plugin:TowerMode:CYHZ` (use only GroundMode for a ground ASR)
- Reduce `PLUGIN:Ground Radar plugin:AirportRadius:2.5` → `1.6` (matches Norway tighter-zoom convention; tune by feel)
- Keep `TAGFAMILY:TopSky_QM` for now; revisit in Phase 5 when defining ground-specific tag families
- Keep `DisplayRotation:18.0`

### 8.5 Position-aware filtering (the spec §6 "top-down" requirement)

The mechanism is `FILTER_CALLSIGN` / `FILTER_ID` inside the `GRpluginMaps.txt`. Example:

```
MAP:STAND NUMBER
FOLDER:CYHZ
AIRPORT:CYHZ
ACTIVE:1
FILTER_CALLSIGN:CYHZ_GND,CYHZ_TWR:*:CYHZ_GND:*    # only draw when you're CYHZ_GND or CYHZ_TWR AND CYHZ_GND is online
COLOR:SMGS_LABEL
SCTFILEDATA:FREETEXT\CYHZ CYHZ PARKING
FILTER_CALLSIGN_OFF
```

When the controller is `CZQM_CTR` (top-down) and there's no `CYHZ_GND` online, the stand numbers don't render — keeping the top-down view uncluttered. The same mechanism applies to taxiway labels, hidden TWY DATA tagging (which doesn't affect display but might affect performance), and the LVP variant.

### 8.6 Approach Path Monitoring

To activate APM at CYHZ, add to `[CYHZ]` settings:

```
AppPath=CYHZ:RNAV 05:N044.51.56.318:W063.31.38.110:053.0:R:477:3.0
AppPath_APM=ABL:0.5:5.0
AppPath_APM_Vert_Lim=200:5000

AppPath=CYHZ:RNAV 23:N044.53.18.250:W063.30.17.200:233.0:L:477:3.0
AppPath_APM=ABL:0.5:5.0
AppPath_APM_Vert_Lim=200:5000

AppPath=CYHZ:RNAV 14:N044.53.37.388:W063.31.02.769:143.0:R:477:3.0
AppPath_APM=ABL:0.5:5.0
AppPath_APM_Vert_Lim=200:5000

AppPath=CYHZ:RNAV 32:N044.52.53.691:W063.29.35.278:323.0:L:477:3.0
AppPath_APM=ABL:0.5:5.0
AppPath_APM_Vert_Lim=200:5000
```

Four runway ends, all straight-in 3° approaches. End altitudes = airport elevation (477 ft AMSL). XTE limits default to 1 nm either side. APM monitors above/below path (+/- 1° wedge default) and lateral deviation past 20° track error.

Worth doing in Phase 2 alongside the other safety-net config.

## 9. Implications and changes to make

### 9.1 Doc corrections

`CYHZ/docs/lppt-analysis.md` has factual errors that this analysis corrects:

| §13 row | Wrong claim | Correct |
|---|---|---|
| "`AREATYPE` isn't a directive" | Misleading — `AREATYPE` is a valid `COORDTYPE` family token (used with `RESTRICTION:` for RVM) | The first token of `COORDTYPE:<family>:<render>` — `OTHER`, `APW`, `RWYCLOSED`, `TWYCLOSED`, `AREATYPE`, `TWYTYPE` |
| "Use `LAYER:N` directives" — "LPPT doesn't use them; the directive likely doesn't exist" | Wrong about directive existence | `LAYER:N` is supported (range -999..999, 0 reserved, default 1). LPPT just doesn't use it. |
| "no `ZOOM:` directives" | Wrong about directive existence | `ZOOM:N` is supported. Positive = hide below; negative = hide above. Multiple `ZOOM:` lines per map are allowed (order matters). |
| `§9` `System_*` flag table guesses | Several inferences wrong | Replaced by the §6 table in this document |

Will fix `lppt-analysis.md` in a follow-up commit (low priority — this document is the new source of truth).

### 9.2 Tool/output adjustments to consider

In rough priority order:

1. **Switch `CYHZ_Ground.asr` to GroundMode only** (drop `TowerMode:CYHZ`). Reduce `AirportRadius` to 1.6.
2. **Wire `SCTFILEDATA` into the OSM tool** as a templating option per `MAP:` block, so we can mix machine-generated and `.sct`-imported geometry in one file. Add `SCTFILEPATH` at the top of the generated maps file.
3. **Replace the OSM `STAND NUMBER` and `TAXIWAY NAME` blocks with `SCTFILEDATA:FREETEXT:...`** — labels become authoritative AeroNav positions.
4. **Add the `LVP SURFACE` overlay map** that reads from the `.sct`'s low-vis GEO group.
5. **Add `AppPath=` and `AppPath_APM=` lines** to `GRpluginSettings.txt` for all four CYHZ runway ends.
6. **Keep the OSM-derived `TWY <ref>` hidden tagging** but add `RESTRICTION:` lines if/when CYHZ-specific size limits become relevant.
7. **Re-evaluate `Airport_Radius`** in `[CYHZ]` (currently 2.5, Norway uses 1.1-1.6).

Doing 1 + 5 alone (no tool changes) brings most of the safety-net value online without affecting the geometry pipeline.

Doing 2-4 reshapes the OSM tool's output toward "tool produces tagging + tool-only geometry; sector file provides visible surface drawing." That's a meaningful refactor — but not a rewrite.

### 9.3 Open questions

1. Do we want **light and dark palettes** as separate `GRpluginMaps.txt` files (swappable via `Maps_URL`/`Setup_LoadMap`), as a parallel folder structure inside one file, or punted to Phase 4?
2. For the **tower-mode ASR**, what's the right `AirportRadius` and `DisplayRotation`? Tower view typically wants more airspace around the field; ground view wants tight focus on the surface.
3. **APM**: are 3.0° glide slopes correct for all four CYHZ runway ends, or does anyone have a different VPA? (RNAV procedures usually do 3°; ILS procedures depend on the runway.)
4. The `.sct` file the `SCTFILEPATH` should point at: do we want to **bundle a copy in the repo at `reference docs/`** (as we have today) or **rely on the user's EuroScope install path**? Bundled is more deterministic; install-path is closer to "single source of truth."
5. The Norway `Virtual Controller Assistant` plugin — useful for CZQM, or skip?

---

End.
