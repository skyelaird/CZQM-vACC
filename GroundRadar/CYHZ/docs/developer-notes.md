# CYHZ GRP — Developer Notes

Living document for future maintainers of the CYHZ Ground Radar Plugin configuration. Started 2026-05-15.

## Project location

- **Repo:** `D:\GitHub\CZQM-vACC\`
- **Working subfolder:** `D:\GitHub\CZQM-vACC\GroundRadar\`
- **Branch in flight:** `grp/cyhz-rebuild` (off `main`)
- **Spec (authoritative):** `D:\GitHub\CZQM-vACC\GroundRadar\CLAUDE_CODE_TASK_grp_cyhz.md`
- **LPPT reference clone (read-only, outside the repo):** `D:\GitHub\references\topskylppc\` — `pinatacolada/topskylppc` on GitHub, GPL-3.0

A separate Claude.ai project mirrors this work for design continuity. File-level work happens here in Claude Code; planning may happen on the Claude.ai side.

## Current state of `GroundRadar\` (Phase 1 inventory)

As of 2026-05-15 the working subfolder contains:

```
GroundRadar\
├── CLAUDE_CODE_TASK_grp_cyhz.md        # Spec
├── reference docs\
│   ├── Ground Radar plugin for EuroScope - Developer Guide.pdf
│   ├── Ground Radar plugin for EuroScope - General.pdf
│   ├── Ground Radar plugin for EuroScope - Version History.pdf
│   ├── GRpluginOperatorInfo.txt
│   ├── CZQQ-CZQM-CZQX_20260515002325-260501-0001.sct
│   └── CZQQ-CZQM-CZQX_20260515002325-260501-0001.ese
└── CYHZ\
    └── docs\
        ├── developer-notes.md         # This file
        └── lppt-analysis.md           # LPPT reference analysis
```

**Not yet present** — the current bare-bones CYHZ GRP configuration. Joel will drop a copy of the live GRP files into `D:\GitHub\CZQM-vACC\GroundRadar\current\CYHZ\` so Phase 1's "inventory the current state" step can be completed. Until that happens, this section is a placeholder.

### CZQM sector reference data

The `reference docs\` folder ships the AIRAC 260515 sector file pair (`.sct` / `.ese`) covering CZQQ/CZQM/CZQX. These files are the source of truth for:

- Runway thresholds (CYHZ 05/23, 14/32)
- Navaid positions
- ARTCC and TMA boundaries used by approach-mode display

The OSM tool in Phase 3 will produce surface geometry, but runway end coordinates (needed for `Airport_Runway_End` in `GRpluginSettings.txt` and therefore for RMCA) should be sourced from the sector file rather than OSM to stay consistent with the rest of the controller environment.

## Planned output structure (per spec §4)

Phase 1 has only created `CYHZ/docs/`. The rest of the tree (Phase 2+) will fill in:

```
GroundRadar\
├── README.md                          # Phase 7
├── ATTRIBUTION.md                     # Phase 7
├── CYHZ\
│   ├── GRpluginMaps.txt              # Phase 2 (tag-only) + Phase 3 (rebuild)
│   ├── GRpluginSettings.txt          # Phase 2 + 4
│   ├── GRpluginSymbols.txt           # Phase 4
│   ├── GRpluginAirports.txt          # Phase 2
│   ├── asr\
│   │   ├── CYHZ_Ground_Light.asr     # Phase 4 + 5
│   │   ├── CYHZ_Ground_Dark.asr
│   │   ├── CYHZ_Tower_Light.asr
│   │   └── CYHZ_Tower_Dark.asr
│   └── docs\
│       ├── controllers-guide.md      # Phase 7
│       └── developer-notes.md        # this file (lives across all phases)
├── tools\
│   └── osm-to-grp\                    # Phase 3
└── current\
    └── CYHZ\                          # Pending: copy of live config for Phase 1 inventory
```

## Phase status

| Phase | Status | Deliverable | Notes |
|------:|--------|-------------|-------|
| 1 | In progress | This file + `lppt-analysis.md` | Awaiting `current\CYHZ\` drop to complete "inventory" sub-step |
| 2 | Not started | Safety net tagging on existing geometry | Blocked until Phase 1 review |
| 3 | Not started | OSM-derived geometry rebuild | |
| 4 | Not started | Visual polish (showcase quality) | Requires iterative visual review from Joel |
| 5 | Not started | Ground/tower tag families | |
| 6 | Not started | Position-aware filtering | |
| 7 | Not started | Docs + packaging | |

## Conventions

- Commit style: conventional (`feat(grp): ...`, `fix(grp): ...`, `docs(grp): ...`)
- Branch: `grp/cyhz-rebuild` — do not merge to `main`; do not push to remote without explicit instruction from Joel
- Per-airport ICAO directories under `GroundRadar\` (`CYHZ\`, future `CYQM\`, `CYYT\`)
- License: GPL-3.0 (inherited from the repo and required by `topskylppc` attribution)

## Cross-references

- The LPPT reference analysis lives at [`lppt-analysis.md`](./lppt-analysis.md). Re-read it before starting any geometry or visual-polish work — several spec assumptions need to be translated into LPPT's actual conventions (in particular: `AREATYPE`/`TWYTYPE` are values inside `COORDTYPE`, not standalone directives; `LAYER:` is not used; draw order is file-order).
- Open questions for Joel are in spec §8.
