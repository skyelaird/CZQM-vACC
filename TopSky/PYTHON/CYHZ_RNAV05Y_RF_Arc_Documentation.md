# CYHZ RNAV-Y Runway 05 - RF Arc Implementation

## Overview
This document describes the implementation of Radius to Fix (RF) legs for the CYHZ RNAV-Y Runway 05 approach procedures using TopSky's COORD_AF command.

## Approach Transitions

The CYHZ RNAV-Y Rwy 05 approach has three Initial Approach Fixes (IAFs):

1. **GOSUG** - Northwest transition
2. **ODKAS** - Southwest transition  
3. **PEPTA** - Southeast transition

All transitions converge at **LOPMA** (Final Approach Point).

## RF Arc Calculations

### Methodology

For RF (Radius to Fix) legs, we need to determine:
- Arc center point coordinates
- Arc radius
- Start angle (bearing from center to start waypoint)
- End angle (bearing from center to end waypoint)  
- Turn direction (clockwise ">" or counterclockwise "<")

The calculation process:
1. Extract waypoint coordinates from ESE .sct file
2. Calculate entry track bearing (from previous TF leg)
3. Test standard RNAV procedure radii (1.0, 2.0, 2.5, 3.0, 4.0, 5.0, 7.0, 10.0 NM)
4. Find radius that minimizes error (distance from arc center to end waypoint vs. radius)
5. Calculate arc center perpendicular to entry track
6. Determine start/end angles and sweep

### Waypoint Coordinates

From CZQQ .sct file [FIXES] section:

```
AVIGU   N044.45.43.329 W063.29.11.140  (44.762036°, -63.486428°)
ETMEP   N044.48.38.919 W063.40.44.270  (44.810811°, -63.678964°)
GOSUG   N044.53.13.919 W063.45.00.619  (44.887200°, -63.750172°)
LOPMA   N044.48.35.661 W063.34.55.930  (44.809906°, -63.582203°)
ODKAS   N044.43.40.789 W063.39.45.781  (not used in RF calculations)
PEPTA   N044.47.36.211 W063.27.19.731  (44.793392°, -63.455481°)
```

## Arc #1: ETMEP to LOPMA

### Geometry
- **Entry track**: 146.51° (from GOSUG to ETMEP)
- **Direct bearing**: 90.72° (ETMEP to LOPMA)
- **Direct distance**: 4.12 NM
- **Turn direction**: LEFT (counterclockwise)

### Radius Testing Results
| Radius | Error  | Sweep   | Notes |
|--------|--------|---------|-------|
| 1.0 NM | 2.343  | 136.11° | Too tight |
| 2.0 NM | 0.712  | 121.30° | Close |
| 2.5 NM | 0.011  | 111.42° | **BEST FIT** |
| 3.0 NM | 0.647  | 100.01° | Acceptable |
| 4.0 NM | 1.609  | 75.69°  | Too large |

### Selected Parameters
- **Radius**: 2.5 NM
- **Arc center**: N044.50.01.584 W063.37.47.976
- **Start angle**: 236.5° (from center to ETMEP)
- **End angle**: 125.1° (from center to LOPMA)
- **Sweep**: 111.4°
- **Direction**: < (counterclockwise)
- **Error**: 0.011 NM

### TopSky Command
```
COORD_AF:N044.50.01.584:W063.37.47.976:2.5:1.0:236.5:<:125.1
```

## Arc #2: AVIGU to LOPMA

### Geometry
- **Entry track**: 215.03° (from PEPTA to AVIGU)
- **Direct bearing**: 305.19° (AVIGU to LOPMA)
- **Direct distance**: 4.99 NM
- **Turn direction**: RIGHT (clockwise)

### Radius Testing Results
| Radius | Error  | Sweep   | Turn | Notes |
|--------|--------|---------|------|-------|
| 2.5 NM | 4.992  | 359.89° | L    | Nearly full circle - wrong direction |
| 1.0 NM | 2.992  | 180.20° | R    | Too tight |
| 2.0 NM | 0.992  | 180.27° | R    | Close |
| 2.5 NM | 0.008  | 180.33° | R    | **BEST FIT** |
| 3.0 NM | 1.008  | 180.41° | R    | Acceptable |

### Selected Parameters
- **Radius**: 2.5 NM
- **Arc center**: N044.47.09.325 W063.32.04.093
- **Start angle**: 125.0° (from center to AVIGU)
- **End angle**: 305.3° (from center to LOPMA)
- **Sweep**: 180.3° (nearly semicircle)
- **Direction**: > (clockwise)
- **Error**: 0.008 NM

### TopSky Command
```
COORD_AF:N044.47.09.325:W063.32.04.093:2.5:1.0:125.0:>:305.3
```

## Implementation Notes

### Key Findings

1. **Uniform radius**: Both RF arcs use the same 2.5 NM radius, which is consistent with RNAV procedure design standards.

2. **Turn direction discovery**: Initial assumption was that AVIGU-LOPMA was a left turn, but geometry analysis revealed it's actually a right turn. The left turn option would require a nearly 360° sweep, which is unrealistic for approach procedures.

3. **Error tolerance**: Both arcs achieve < 0.02 NM error, well within acceptable tolerance for procedure definition.

### COORD_AF Syntax

```
COORD_AF:CenterLat:CenterLon:Radius:Spacing:StartAngle:Direction:EndAngle
```

Where:
- **CenterLat/Lon**: Arc center in sector file format (Nddd.mm.ss.sss Wddd.mm.ss.sss)
- **Radius**: In nautical miles
- **Spacing**: Vertex radial spacing in degrees (1.0 = smooth rendering)
- **StartAngle**: True bearing from center to arc start point
- **Direction**: "<" for counterclockwise, ">" for clockwise
- **EndAngle**: True bearing from center to arc end point

### Activation Logic

The approach procedures are activated when Halifax Tower (CYHZ_APP) or Moncton ACC Halifax Approach (CZQM_HZ_APP) positions are online:

```
ACTIVE:CYHZ_APP:APP:ACTIVE
ACTIVE:CZQM_HZ_APP:APP:ACTIVE
```

## Testing Recommendations

1. Load the definitions in EuroScope with TopSky plugin
2. Verify arc rendering smoothness (adjust spacing if needed)
3. Confirm arcs align with published approach charts
4. Test activation/deactivation with different controller positions
5. Verify color scheme matches other approach procedures (purple_approach)

## Future Work

- RNAV-Y Runway 23 (LEROS transition visible on chart)
- Other Halifax approach procedures with RF legs
- Expansion to other airports in CZQM FIR with RNAV approaches

## References

- TopSky Developer Guide v2.5, pages 46-47 (COORD_AF syntax)
- CZQQ ESE file (FIXES section for waypoint coordinates)
- CYHZ RNAV (RNP) Y Runway 05 approach chart (13 OCT 23)
- Designated Airspace Handbook (DAH)

---

*Calculated: November 2024*
*Joel Lavoie - VATCAN CZQM vACC*
