# Claude Code Task: GRP Adaptation for CYHZ (and pipeline for CYQM/CYYT)

**Author:** Joel Morin (CZQM/CZQX vACC Operations Lead)
**Repo:** `D:\GitHub\CZQM-vACC\`
**Target subfolder:** `GroundRadar\`
**Date:** May 2026
**Status:** Draft for execution

---

## 1. Context

CZQM/CZQX vACC operates the EuroScope-based controller environment for the Moncton and Gander FIRs on VATSIM. The current ground radar setup (GRP — Holopainen's Ground Radar Plugin) for CYHZ is bare-bones: it provides a basic visual diagram but does not exercise GRP's safety nets, doesn't differentiate visually between surface types, and doesn't adapt to top-down working (where one controller bandboxes CTR through GND simultaneously).

This task is to rebuild the CYHZ GRP configuration to:

- Make full use of GRP's functional capabilities (safety nets, conformance monitoring, position-aware filtering)
- Achieve showcase-quality visual presentation (using LPPT/LPPC's GRP work as the primary aesthetic reference)
- Support both light and dark color variants
- Support top-down working (where attention is divided across many positions)
- Support tower-mode and ground-mode tag families
- Establish a reusable pipeline for applying the same patterns to CYQM and CYYT in a future phase

CYHZ is the test case. If successful, the pipeline scales to CYQM and CYYT with significantly less per-airport effort.

## 2. Reference inspiration

**Primary reference:** `pinatacolada/topskylppc` on GitHub — Portugal vACC's TopSky/GRP package, GPL-3.0 licensed, actively maintained.

This package has done the aesthetic and structural work we want to learn from. It uses pure GRP vector primitives (no satellite imagery underlay) and achieves a visually rich, functionally complete surface display for LPMA, LPFR, LPPR, and LPPT.

**Specific approach:** Use LPPT as the primary reference. LPPT is the most polished and most complex of the LPPC airports. We're using it as inspiration, not as a template to mechanically port. Dig deeper into LPMA/LPFR/LPPR if specific patterns at LPPT don't translate cleanly.

**Attribution:** Because of GPL-3.0, our derived work in `GroundRadar\` must also be GPL-3.0 licensed (which is consistent with the CZQM-vACC repo's existing model). Attribution to pinatacolada and LPPC contributors must appear in:
- The `GRpluginMaps.txt` header comments
- The README in `GroundRadar\`
- Any documentation produced

## 3. Scope

### In scope

- Complete rebuild of CYHZ GRP configuration (geometry, safety nets, symbols, color palette)
- Light and dark color variants (same geometry, different `COLORDEF` blocks via separate `.asr` files)
- Tower-mode and ground-mode tag families
- Position-aware filtering (`FILTER_CALLSIGN` / `FILTER_ID`) to adapt display based on staffing
- Safety net configuration:
  - RMCA (Runway Monitoring and Conflict Alerting) — runway monitoring zones for CYHZ runway pairs
  - CMAC (Conformance Monitoring Alerts for Controllers) — no-takeoff-clearance, runway incursion, emergency code monitoring
  - ICM (Incursion Conflict Monitoring) — new in v1.6
  - APM (Approach Path Monitoring) — new in v1.6
- Holding points marked as functional GRP symbols (not just decorative)
- Helicopter ramp and cargo apron distinct visually from main GA/airline apron
- Multi-layer composition for visual depth (base surface → markings → labels)
- Documentation: README explaining the setup, attribution, how to update

### Out of scope (explicit non-goals)

- **NOTAM-driven closure overlays** — we don't model maintenance/closure events. Skip RWYCLOSED/TWYCLOSED dynamic overlays.
- **Stand assignment** — CZQM/CZQX doesn't assign gates. Stand geometry may be visually present, but the auto-assignment logic stays off. The `GRpluginStands.txt` should remain minimal or absent.
- **DCL/PDC** — out of scope for GRP work (handled elsewhere by TopSky if at all).
- **Real-time imagery underlays** — we're doing pure vector composition, not satellite imagery.
- **Per-airport AIRAC updates** — this task delivers a working configuration at one point in time. Future AIRAC updates are a separate process not covered here.

## 4. Repository conventions

### Paths

All paths in this task are on Joel's Windows machine. Use UNC-style paths for NAS access where relevant, but the working files live on the local drive.

- **Repository root:** `D:\GitHub\CZQM-vACC\`
- **Target subfolder:** `D:\GitHub\CZQM-vACC\GroundRadar\`
- **Reference clone (read-only):** `D:\GitHub\references\topskylppc\` (clone fresh; don't modify)

### Git discipline

- Create a feature branch `grp/cyhz-rebuild` from `main`
- Commit progressively at phase boundaries (one commit per completed phase minimum)
- Do not merge to `main` — leave that decision to Joel after testing
- Commit messages: conventional style (e.g., "feat(grp): add CYHZ runway monitoring zones", "fix(grp): correct taxiway B holding point position")
- PR description (when ready) should summarize what was done and reference this spec file

### Output structure

```
D:\GitHub\CZQM-vACC\GroundRadar\
├── README.md                          # Overview, attribution, how to install/update
├── CYHZ\
│   ├── GRpluginMaps.txt              # Master maps file for CYHZ
│   ├── GRpluginSettings.txt          # CYHZ-specific settings (safety nets, runway config)
│   ├── GRpluginSymbols.txt           # Custom symbols (holding points, aircraft, etc.)
│   ├── GRpluginAirports.txt          # Airport reference data
│   ├── asr\
│   │   ├── CYHZ_Ground_Light.asr     # Ground controller view, light palette
│   │   ├── CYHZ_Ground_Dark.asr      # Ground controller view, dark palette
│   │   ├── CYHZ_Tower_Light.asr      # Tower controller view, light palette
│   │   └── CYHZ_Tower_Dark.asr       # Tower controller view, dark palette
│   └── docs\
│       ├── controllers-guide.md      # For controllers using the config
│       └── developer-notes.md        # For future maintainers
├── tools\
│   └── osm-to-grp\
│       ├── README.md                 # How to use the OSM extractor
│       ├── extract.py                # OSM → GRP geometry converter
│       ├── requirements.txt
│       └── config\
│           └── cyhz.yaml             # Per-airport configuration
└── ATTRIBUTION.md                    # GPL-3.0 + LPPC attribution
```

### Coding standards

- Python scripts (if any): use modern Python 3 idioms, type hints, docstrings
- Output text files (`.txt`): match the formatting conventions visible in LPPC's files (whitespace, comment style)
- Comments in `GRpluginMaps.txt`: use `//` prefix consistently, attribute any patterns copied from LPPC

## 5. Phases

### Phase 1: Inventory and assessment

**Goal:** Understand what's currently in place and confirm reference patterns.

**Actions:**

1. Read everything currently in `D:\GitHub\CZQM-vACC\GroundRadar\` and document the current state in `docs/developer-notes.md`.
2. Clone `pinatacolada/topskylppc` to `D:\GitHub\references\topskylppc\` (or wherever convenient outside the CZQM repo).
3. Study LPPT's GRP configuration in detail:
   - `GRpluginMaps.txt` — geometry, layers, folder structure
   - `GRpluginSettings.txt` — safety net configuration, color definitions
   - `GRpluginSymbols.txt` — custom symbols (especially the parked aircraft if present)
   - Any LPPT-specific `.asr` files for ground operations
4. Produce a short analysis document (`docs/lppt-analysis.md`) summarizing:
   - Color palette used (RGB values for the main `COLORDEF` lines)
   - Layer ordering conventions
   - Symbol definition patterns
   - How they handle different surface types visually (runway vs taxiway vs apron vs grass)
   - Folder organization for the maps menu
5. Confirm with Joel (via a commit/PR comment, or just produce the analysis and stop for review) before proceeding to Phase 2.

**Deliverable:** Two documents in `docs/`. No code changes yet. Branch created.

### Phase 2: Tag the existing config for safety nets (quick-win)

**Goal:** Get RMCA, CMAC, ICM, APM working at CYHZ using whatever geometry is already in place, without rebuilding.

**Actions:**

1. Read GRP 1.6 Developer Guide sections on:
   - `AREATYPE` and `TWYTYPE` declarations
   - RMCA configuration (`TopSkyMaps.txt` runway monitoring zones)
   - CMAC settings in `GRpluginSettings.txt`
   - ICM and APM (new in v1.6) — refer to the Version History PDF
2. Add safety net tagging to the existing CYHZ geometry:
   - Tag the runway polygons with `AREATYPE` for RMCA
   - Tag the taxiway polygons near runways with `TWYTYPE` for runway incursion detection
   - Configure CMAC alerts (no-takeoff-clearance, runway incursion, emergency code monitoring) in settings
   - Configure ICM if applicable to CYHZ
   - Configure APM with the appropriate approach paths for runway pairs 05/23 and 14/32
3. Test that the safety nets fire correctly in a sweatbox or observer mode (Joel will run this test; Claude Code documents what to test).
4. Commit as "feat(grp): add safety net tagging to existing CYHZ config".

**Deliverable:** Working safety nets on the existing visual geometry. Joel can use this immediately even if Phases 3+ are deferred.

### Phase 3: OSM-sourced geometry rebuild for CYHZ

**Goal:** Replace the existing CYHZ geometry with a clean, OSM-derived, well-tagged set of polygons that supports the showcase polish in later phases.

**Actions:**

1. Build the `osm-to-grp` Python tool in `tools/osm-to-grp/`:
   - Pull airport features from OpenStreetMap via Overpass API
   - Bounding box for CYHZ: roughly `-63.55,44.85,-63.45,44.92` (refine as needed)
   - Extract features tagged with `aeroway=*`: runway, taxiway, apron, helipad, holding_position, parking_position, taxiway_centerline
   - Convert coordinates to GRP's expected format (decimal degrees with N/W prefix)
   - Emit `MAP:` blocks with appropriate `COORDTYPE`, names, and tagging
   - Apply a tagging strategy that maps OSM `aeroway` values to GRP area types:
     - `aeroway=runway` → `AREATYPE:OTHER:REGION_FILLONLY` with runway color, plus `AREATYPE:AREATYPE` for RMCA tagging
     - `aeroway=taxiway` → `AREATYPE:OTHER:REGION` with taxiway color, plus `AREATYPE:TWYTYPE` for incursion monitoring where appropriate
     - `aeroway=apron` → `AREATYPE:OTHER:REGION_FILLONLY` with apron color
     - `aeroway=helipad` → distinct symbol or polygon
     - `aeroway=holding_position` → `SYMBOL` placement
   - Generate folder hierarchy matching LPPT conventions
2. Run the tool for CYHZ, producing `CYHZ\GRpluginMaps.txt`.
3. Manual review and cleanup:
   - Verify polygon orientation (some OSM ways are clockwise, GRP may need counterclockwise)
   - Check that runway numbers and taxiway letters are positioned correctly
   - Add any operational features OSM lacks (preferred holding lines, ILS critical areas if applicable)
4. Initial visual smoke test — load the file in EuroScope, take a screenshot, confirm geometry is sensible. Iterate if needed.
5. Re-apply the Phase 2 safety net tagging to the new geometry.
6. Commit as "feat(grp): OSM-sourced CYHZ geometry rebuild".

**Deliverable:** Clean `GRpluginMaps.txt` for CYHZ. Reusable OSM tool in `tools/osm-to-grp/`.

### Phase 4: Visual polish (showcase quality)

**Goal:** Apply LPPT-inspired aesthetic to the CYHZ geometry. This is the phase that takes the longest and benefits most from iteration with Joel.

**Actions:**

1. Define color palette in `GRpluginSettings.txt`:
   - Adapt LPPT's `COLORDEF` values, adjusted for Canadian context (slightly cooler tones consistent with the Maritime aesthetic if appropriate)
   - Define both a light and a dark palette as separate setting profiles (or as separate `.asr` files referencing different overlay maps)
2. Layer the geometry:
   - Base surface layer (runways, taxiways, aprons) as `REGION_FILLONLY`
   - Outline/edge layer (`POLYLINE` traces along surface edges for visual definition)
   - Markings layer (centerline dashes, holding point lines, runway thresholds) using `LAYER:N` directives to control draw order
   - Labels on top
3. Define custom symbols in `GRpluginSymbols.txt`:
   - Holding point markers (LPPT-style or Canadian variant)
   - Stand symbols (decorative aircraft icons at typical stand positions — pulled from LPPT and adapted)
   - Helipad symbols
   - ILS critical area markers if applicable
4. Differentiate surface types:
   - Helicopter ramp distinct from airline apron (different fill color or hatching)
   - Cargo apron distinct from terminal apron
   - Grass areas with subtle differentiation
5. Apply zoom-aware detail using `ZOOM:N` directives:
   - Stand numbers visible only when zoomed in below 200 pixels/nm
   - Taxiway letters visible at moderate zoom
   - Runway numbers always visible
6. Build the four `.asr` files:
   - `CYHZ_Ground_Light.asr` — ground controller view, light palette, full ground detail
   - `CYHZ_Ground_Dark.asr` — ground controller view, dark palette
   - `CYHZ_Tower_Light.asr` — tower controller view, light palette, slightly reduced ground detail
   - `CYHZ_Tower_Dark.asr` — tower controller view, dark palette
7. Iterate: screenshot → Joel reviews → adjust → repeat. This may take multiple sessions.
8. Commit progressively as iterations stabilize.

**Deliverable:** Showcase-quality CYHZ in two palettes, two tag layouts (4 ASR files).

### Phase 5: Tag families for ground and tower modes

**Goal:** Different track tag layouts for ground-mode vs tower-mode controllers.

**Actions:**

1. Define two tag families in the EuroScope sector file or `.asr` configuration:
   - **Ground mode tag:**
     - Line 1: Callsign + Aircraft type
     - Line 2: Departure runway or destination
     - Line 3: Ground state (PUSH/TAXI/HOLD/CROSS) + Remarks
   - **Tower mode tag:**
     - Line 1: Callsign + Aircraft type
     - Line 2: Departure runway / Arrival runway / SID code
     - Line 3: Cleared altitude or initial climb instruction
2. Define tag colors:
   - Departures: light blue or yellow (matching LPPT convention, or per Joel's preference)
   - Arrivals: yellow or amber
   - Overflights/uncorrelated: light grey
3. Ensure tag families are referenced correctly in the four `.asr` files from Phase 4.
4. Commit as "feat(grp): add ground and tower tag families for CYHZ".

**Deliverable:** Position-appropriate tag layouts.

### Phase 6: Position-aware filtering

**Goal:** Adapt what's displayed based on which controller positions are online.

**Actions:**

1. Define filter rules in `GRpluginMaps.txt`:
   - `FILTER_CALLSIGN` for showing/hiding certain map elements based on logged-on controllers
   - `FILTER_ID` for the same, by controller position ID
2. Specific behaviors:
   - When `CYHZ_GND` is online: show full ground detail (stand numbers, taxiway letters, holding points)
   - When `CYHZ_GND` is bandboxed into `CYHZ_TWR`: reduce ground detail to essential surface awareness
   - When `CZQM_CTR` is providing top-down service to CYHZ (CYHZ_TWR offline): show minimal surface display (just runway state, no taxi detail)
3. Test the transitions: simulate different position states and verify the display adapts correctly.
4. Commit as "feat(grp): add position-aware filtering for top-down work".

**Deliverable:** A configuration that adapts gracefully to staffing levels.

### Phase 7: Documentation and packaging

**Goal:** Make the work usable, maintainable, and ready for the CYQM/CYYT expansion.

**Actions:**

1. Write `GroundRadar/README.md`:
   - Overview of the setup
   - Attribution (LPPT, GRP author Holopainen, GPL-3.0 license note)
   - Installation instructions for end users
   - How to update for future AIRAC cycles
2. Write `CYHZ/docs/controllers-guide.md`:
   - How to load the right `.asr` file for your position
   - How to switch between light and dark variants
   - What the safety net alerts mean and how to acknowledge them
   - Common gotchas
3. Write `CYHZ/docs/developer-notes.md`:
   - How the configuration is structured
   - How to add a new feature (e.g., a new holding point)
   - How to regenerate from OSM if needed
   - How the position-aware filtering works
4. Write `tools/osm-to-grp/README.md`:
   - How to run the tool for a new airport
   - Configuration file format
   - Known limitations and workarounds
5. Write `ATTRIBUTION.md`:
   - GPL-3.0 license notice
   - Acknowledgment of pinatacolada/topskylppc inspiration
   - GRP plugin author credit (Juha Holopainen)
6. Commit as "docs(grp): add documentation and attribution for CYHZ rebuild".

**Deliverable:** A complete, documented, reusable configuration ready for review.

## 6. Quality checklist

Before declaring the CYHZ rebuild complete, verify:

- [ ] Phase 1 inventory and LPPT analysis documents exist and are clear
- [ ] All safety nets (RMCA, CMAC, ICM, APM) fire correctly in sweatbox testing
- [ ] Visual quality: side-by-side comparison with LPPT screenshot shows comparable polish (it doesn't have to be identical — Canadian context is fine — but it should be in the same quality league)
- [ ] Light and dark variants both load and render correctly
- [ ] Ground and tower tag families both display the expected fields
- [ ] Position-aware filtering: display adapts when positions go online/offline
- [ ] No EuroScope errors or warnings in the message log when loading any of the four `.asr` files
- [ ] Performance: no noticeable frame-rate drop at typical zoom levels with realistic traffic
- [ ] OSM tool produces valid GRP output for CYHZ and can be re-run if OSM data changes
- [ ] All commits have clear messages
- [ ] Documentation is complete and accurate
- [ ] Attribution is in place per GPL-3.0 requirements

## 7. Iteration cadence

Default: **Pause for Joel's review at phase boundaries.** Specifically:

- After Phase 1: review the LPPT analysis before any code is touched
- After Phase 2: confirm safety nets are working before geometry rebuild
- After Phase 3: confirm OSM geometry is acceptable before polish phase
- During Phase 4: iterate frequently (every 2-3 visual changes, Joel screenshots and reviews)
- After Phases 5, 6, 7: review each in turn

If a phase reveals an unexpected problem (e.g., LPPT uses a technique we can't easily replicate, OSM data is missing critical features, etc.), pause and surface the question rather than improvising.

## 8. Open questions for Joel

These are decisions Claude Code should not make alone. Surface them when they come up:

1. **Color palette:** Closer to LPPT's exact colors, or adjusted for Canadian context? Joel's preference once Phase 1 analysis is done.
2. **Runway naming convention:** `CYHZ05` vs `CYHZ_05` vs `CYHZ-05`. Default to `CYHZ05` unless Joel says otherwise.
3. **Helicopter ramp treatment:** Distinct color, distinct hatching, or just a label? Joel's call once the visual sketch exists.
4. **Cargo apron treatment:** Same question.
5. **Stand decorations:** Replicate LPPT's parked-aircraft symbols, or simpler (just stand numbers)? Joel's call after Phase 1.
6. **ASR file naming:** The proposal above uses `CYHZ_Ground_Light.asr` etc. — confirm or adjust.
7. **Top-down minimum display:** What's the absolute minimum CYHZ surface info needed when a controller is working CZQM_CTR top-down without staffing CYHZ_TWR/GND? Joel's operational call.

## 9. Post-mortem (for the CYQM/CYYT expansion)

After Phase 7 is complete and Joel has reviewed the work, produce a short retrospective in `docs/post-mortem-cyhz.md`:

- What worked well in the LPPT-inspired approach
- What took longer than expected
- What patterns generalize cleanly to CYQM and CYYT
- What CYHZ-specific work won't transfer (and what should be redesigned for the other airports)
- Estimated effort for CYQM (smaller, simpler) and CYYT (larger, busier)
- Recommended adjustments to this spec before applying it to the other airports

This becomes the input to the next spec (`CLAUDE_CODE_TASK_grp_cyqm_cyyt.md`) when Joel decides to expand the work.

## 10. Boundaries and escalation

- **Don't merge to `main`.** Leave merge decisions to Joel.
- **Don't push to remote without explicit instruction.** Commit locally; let Joel push.
- **Don't modify anything outside `D:\GitHub\CZQM-vACC\GroundRadar\`** without explicit instruction.
- **Don't redistribute LPPT files.** Reference them in a separate clone location; don't copy them into the CZQM repo.
- **If a phase looks like it'll take more than ~3x the rough estimate, stop and surface the issue.** The estimates in this spec are rough — if reality diverges significantly, that's a sign to recalibrate, not to keep pushing.
- **Image processing limitation:** Claude Code cannot directly view EuroScope screenshots to evaluate visual quality. Joel will need to provide visual feedback during Phase 4 iteration.

---

**End of spec.**

For the next conversation (or session continuation), Joel will start by saying something like "begin Phase 1" or "review the Phase 1 output". Each phase should produce specific deliverables before moving on.
