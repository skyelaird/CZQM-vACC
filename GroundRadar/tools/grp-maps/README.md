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
| osm_stands.py / nav_stands.py + stand_rules.json | Stands for non-CYHZ airports (Navigraph names, OSM/MSFS positions) |
| stand_markers.py | Stand marker circles, nose ticks, numbers |
| twy_restrict.py | Taxiway wingspan/weight restriction areas (CFS) |
| uncontrolled.py | Uncontrolled-area shading (CFS notes) |
| cyhz_uncontrolled.py | CYHZ main apron / cargo uncontrolled shading (hand-tuned; Windows-temp paths inside) |
| cyqm_unc.py | CYQM south aprons out to the Twy A corridor (A/B/C controlled 50 ft each side) |
| cyfc_aprons.py | Adds CYFC Aprons I-V to the CYFC uncontrolled shading |
| hold_lines.py | Runway holding-position bars, 200 ft from runway edge (CFS widths), all airports |
| displaced.py | Displaced-threshold bar + arrows (CYHZ 23, LFVP 26; Navigraph AIRAC 2610) |

Suggested order after a new sector file: build_ground, lvp_routes, nav_stands, stand_markers,
twy_restrict, uncontrolled (+ cyhz_uncontrolled, cyqm_unc, cyfc_aprons), hold_lines, displaced.

`../../grp-live/` holds a snapshot of the installed plugin files and GRP ASRs.
