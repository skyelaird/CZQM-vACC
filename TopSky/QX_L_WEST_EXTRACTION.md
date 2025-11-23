# QX_L_WEST Polygon Extraction

## Overview
This document details the extraction of the QX_L_WEST sector polygon from the ESE file for use in TopSkyMaps.txt.

## Source Information
- **ESE File**: CZQQ-DO-NOT-USE_20251107023304-251101-0017.ese
- **Sector Name**: CZQX·QX_L_WEST·000·285
- **Altitude Range**: Surface (00000) to FL285 (28500)
- **Extraction Date**: 2025-11-22

## Sector Definition
```
SECTOR:CZQX·QX_L_WEST·000·285:00000:28500
OWNER:QL:QX:QM
BORDER:164:271:82:278:279:201:141:140:137:136:135:134:94:93:92:168:167:166:161:160:159:113:112
```

## Owner Priority
1. **QL** - Primary owner (Halifax/Moncton Low position)
2. **QX** - Secondary owner (Gander East Center)
3. **QM** - Tertiary owner (Moncton Center)

## Polygon Details
- **Total Coordinates**: 25 unique boundary points
- **Polygon Type**: Closed polygon (first point matches last, removed for TopSky)
- **Border Sectorlines**: 23 sectorline segments

### Sectorline Processing
The extraction script automatically:
1. Retrieved all 23 sectorline definitions from the ESE file
2. Chained coordinates in proper sequence
3. Reversed sectorlines where necessary to maintain continuity
4. Removed duplicate coordinates at sectorline junctions
5. Verified polygon closure (first == last coordinate)

## TopSky Implementation

### Polygon Definition
```
[QX_L_WEST_POLYGON]
ACTIVE:QX_L_WEST:QL
ACTIVE:QX_L_WEST:QX
ACTIVE:QX_L_WEST:QM
COORD:N046.21.00.000:W056.44.42.000
COORD:N045.56.00.000:W056.35.00.000
COORD:N045.36.43.000:W056.28.25.000
COORD:N046.58.03.440:W058.56.09.540
COORD:N048.30.00.000:W062.00.00.000
COORD:N049.18.00.000:W061.00.00.000
COORD:N049.32.00.000:W061.00.00.000
COORD:N050.31.17.749:W058.58.42.770
COORD:N050.14.30.000:W058.46.31.000
COORD:N050.01.48.060:W058.37.01.040
COORD:N049.55.00.000:W058.32.11.000
COORD:N049.36.49.000:W058.18.34.000
COORD:N049.16.54.000:W058.04.09.000
COORD:N049.05.39.000:W057.56.06.000
COORD:N048.52.37.000:W057.46.48.000
COORD:N048.43.21.000:W057.42.13.000
COORD:N048.31.51.000:W057.37.27.000
COORD:N048.25.46.000:W057.34.53.000
COORD:N048.11.04.000:W057.28.42.000
COORD:N047.44.28.000:W057.17.51.000
COORD:N047.41.20.000:W057.16.50.000
COORD:N047.24.21.000:W057.09.47.000
COORD:N047.02.11.000:W057.01.05.000
COORD:N046.52.56.000:W056.57.24.000
COORD:N046.42.00.000:W056.52.55.000
COORDPOLY:0
```

### Activation Logic
The polygon will display when any of these positions are online:
- **QL** (Halifax/Moncton Low Level) - Primary activation
- **QX** (Gander East Center) - Covers low level when QL offline
- **QM** (Moncton Center) - Covers both FIRs when alone

## Geographic Coverage
The QX_L_WEST sector covers the western portion of the CZQX Gander FIR at low levels (surface to FL285), including:
- Airspace west of approximately 57°W longitude
- Northern boundary at approximately 50.5°N latitude
- Southern boundary near the CZQM FIR border (~45.5°N)
- Western boundary extending to approximately 62°W

## Operational Notes
- This sector represents low-level controlled airspace
- Boundary coordinates are extracted directly from the official ESE sectorfile
- The polygon should display with a subtle style to inform controllers without obscuring aircraft tags
- Consider color coding to distinguish from high-level sectors (FL285+)

## Integration Checklist
- [ ] Add polygon to TopSkyMaps.txt
- [ ] Verify polygon displays correctly in EuroScope
- [ ] Test activation with QL, QX, and QM positions
- [ ] Verify no syntax errors in TopSkyMaps.txt
- [ ] Confirm polygon does not conflict with other boundaries
- [ ] Update version number and changelog

## Related Sectors
This polygon should be coordinated with:
- **QX_L_EAST** - Eastern low level sector
- **CZQM sectors** - Southern FIR boundary alignment
- **High level sectors** - Above FL285

## Version History
- **v1.0** (2025-11-22): Initial extraction from ESE file
  - 25 coordinate polygon
  - Verified closure
  - Production-ready format
