# GRP map tools (multi-airport)

Generators for the Ground Radar Plugin files used by the CZQM/CZQX GRP ASRs
(CYHZ, CYFC, CYQM, CYQX, CYYR, CYYT, CYZX, LFVP). They edit the live
`GRpluginMaps.txt` / `GRpluginStands.txt` in
`%APPDATA%\EuroScope\CZQQ\Plugins\GRP\` in place, between `//>>>> ... //<<<<`
markers, and back the file up to `_bak\` first.

The CYHZ stand file section is generated separately by `../osm-to-grp/extract.py`.

**Run from** `%APPDATA%\EuroScope\CZQQ\Plugins\GRP\tools\` (scripts locate the GRP folder
and the newest `CZQQ-CZQM-*.sct` relative to themselves). This folder is a backup copy;
copy changes back there before running. OSM responses are cached in `tools\osm_cache\`
(not committed).

| Script | Produces |
|---|---|
| build_ground.py | Per-airport ground layers from the sector file, runway designators, CYZX/LFVP runway arrows, SCT colours |
| lvp_routes.py | CYHZ LVP route areas |
| helipads.py | Refreshes the OSM cache (parking positions, gates, helipads) and writes helipad symbols; replaces osm_stands.py (retired) |
| nav_stands.py + stand_rules.json | Stands for non-CYHZ airports (Navigraph names, OSM/MSFS positions from the cache) |
| stand_markers.py | Stand marker circles, nose ticks, numbers |
| twy_restrict.py | Taxiway wingspan/weight restriction areas (CFS) |
| uncontrolled.py | Uncontrolled-area shading (CFS notes) |
| cyhz_uncontrolled.py | CYHZ main apron / cargo uncontrolled shading (hand-tuned; Windows-temp paths inside) |
| cyqm_unc.py | CYQM south aprons out to the Twy A corridor (A/B/C controlled 50 ft each side) |
| cyyr_unc.py | CYYR: Twy J controlled, everything south of J plus Aprons V/VI uncontrolled (replaces the uncontrolled.py CYYR block) |
| cyfc_aprons.py | Adds CYFC Aprons I-V to the CYFC uncontrolled shading |
| hold_lines.py | Runway holding-position bars, 200 ft from runway edge (CFS widths), all airports |
| fixed_maps.py + fixed_maps\ | Blocks built once from published sources (DAH control zones, CFS VFR calling points, CYHZ de-icing bays, CYYT apron restrictions, CYFC shading) kept as editable data; `extract` refreshes the data from the live file, no argument re-applies it |
| displaced.py | Displaced-threshold bar + arrows (CYHZ 23, LFVP 26; Navigraph AIRAC 2610) |

Suggested order after a new sector file: build_ground, lvp_routes, helipads, nav_stands, stand_markers,
twy_restrict, uncontrolled (+ cyhz_uncontrolled, cyqm_unc, cyfc_aprons, cyyr_unc), hold_lines, displaced, fixed_maps. Run `fixed_maps.py extract` after hand-editing any of its blocks in the live file.

`../../grp-live/` holds a snapshot of the installed plugin files and GRP ASRs.
