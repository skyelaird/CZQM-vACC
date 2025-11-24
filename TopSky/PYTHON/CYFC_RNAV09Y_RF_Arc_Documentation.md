# CYFC RNAV Y Runway 09 - RF Arc Implementation

## Overview
This document describes the implementation of three Radius to Fix (RF) legs for the CYFC RNAV Y Runway 09 approach procedures using TopSky's COORD_AF command.

## Approach Transitions

The CYFC RNAV Y Rwy 09 approach has two Initial Approach Fixes (IAFs):

1. **VESBI** - Northeast transition (has TWO consecutive RF arcs!)
2. **ANERA** - Southwest transition (has ONE RF arc)

Both transitions converge at **VYSTA** (Final Approach Point).

## Waypoint Coordinates

From CZQQ .sct file [FIXES] section:

```
ANERA   N045.39.40.611 W066.44.52.800  (45.661281°, -66.748000°)
UKNUM   N045.55.20.308 W066.40.01.801  (45.922308°, -66.667167°)
URPUS   N045.49.11.870 W066.39.39.819  (45.819964°, -66.661061°)
URTIT   N045.50.44.368 W066.40.20.539  (45.845658°, -66.672372°)
VESBI   N045.56.53.361 W066.33.58.651  (45.948156°, -66.566292°)
VYSTA   N045.50.38.810 W066.37.33.610  (45.844114°, -66.626003°)
```

## Arc #1: UKNUM to URTIT

### Geometry
- **Entry track**: 249.81° (from VESBI to UKNUM)
- **Turn direction**: LEFT (counterclockwise)
- **Radius**: 2.5 NM
- **Sweep**: 134.2°

### Calculated Parameters
- **Arc center**: N045.52.59.613 W066.38.47.484
  - (45.883226°, -66.646523°)
- **Start angle**: 339.8° (from center to UKNUM)
- **End angle**: 205.6° (from center to URTIT)
- **Error**: < 0.001 NM

### TopSky Command
```
COORD_AF:N045.52.59.613:W066.38.47.484:2.5:1.0:339.8:<:205.6
```

## Arc #2: URTIT to VYSTA

### Geometry
- **Entry track**: 182.71° (from UKNUM to URTIT)
- **Turn direction**: LEFT (counterclockwise)
- **Radius**: 1.0 NM
- **Sweep**: 180.0° (semicircle!)

### Calculated Parameters
- **Arc center**: N045.50.41.526 W066.38.54.561
  - (45.844868°, -66.648489°)
- **Start angle**: 272.7° (from center to URTIT)
- **End angle**: 92.7° (from center to VYSTA)
- **Error**: 0.058 NM

### TopSky Command
```
COORD_AF:N045.50.41.526:W066.38.54.561:1.0:1.0:272.7:<:92.7
```

### Special Note
This is a **semicircular arc** (180° turn) with a tight 1.0 NM radius. This creates a dramatic turn from a southbound track to an eastbound track, essentially a "hairpin" turn onto final approach.

## Arc #3: URPUS to VYSTA

### Geometry
- **Entry track**: 20.89° (from ANERA to URPUS)
- **Turn direction**: RIGHT (clockwise)
- **Radius**: 2.5 NM
- **Sweep**: 48.7°

### Calculated Parameters
- **Arc center**: N045.48.18.361 W066.36.18.928
  - (45.805100°, -66.605258°)
- **Start angle**: 290.9° (from center to URPUS)
- **End angle**: 339.7° (from center to VYSTA)
- **Error**: 0.002 NM

### TopSky Command
```
COORD_AF:N045.48.18.361:W066.36.18.928:2.5:1.0:290.9:>:339.7
```

## Track Analysis

### Transition 1: VESBI - UKNUM - URTIT - VYSTA

```
VESBI -> UKNUM:  249.81° (straight, 4.49 NM)
UKNUM -> URTIT:  RF arc, 2.5 NM radius, LEFT turn, 134° sweep
URTIT -> VYSTA:  RF arc, 1.0 NM radius, LEFT turn, 180° sweep
```

This transition features **two consecutive RF arcs** with different radii. The sequence creates a smooth S-turn that brings aircraft from the northeast down and around to align with the final approach course.

### Transition 2: ANERA - URPUS - VYSTA

```
ANERA -> URPUS:  20.89° (straight, 10.20 NM)
URPUS -> VYSTA:  RF arc, 2.5 NM radius, RIGHT turn, 49° sweep
```

This is a simpler transition with a single gentle right turn to align with final approach.

## Key Findings

1. **Consecutive RF arcs**: The VESBI transition is notable for having two RF arcs in sequence, which is less common but perfectly valid for RNAV procedures.

2. **Semicircular arc**: The URTIT-VYSTA arc is a 180° turn (semicircle), creating a dramatic reversal that aligns aircraft with the runway.

3. **Mixed radii**: The procedure uses both 1.0 NM (tight) and 2.5 NM (moderate) radii depending on the required turn.

4. **Turn direction variety**: Uses both left (counterclockwise) and right (clockwise) turns to accommodate different arrival directions.

## Implementation Notes

### COORD_AF Syntax

```
COORD_AF:CenterLat:CenterLon:Radius:Spacing:StartAngle:Direction:EndAngle
```

Where:
- **CenterLat/Lon**: Arc center in sector file format
- **Radius**: In nautical miles
- **Spacing**: Vertex radial spacing (1.0° recommended for smooth arcs)
- **StartAngle**: True bearing from center to arc start point
- **Direction**: "<" for counterclockwise, ">" for clockwise
- **EndAngle**: True bearing from center to arc end point

### Activation Logic

The approach procedures are activated when Fredericton Tower (CYFC_TWR) or Moncton ACC Fredericton Approach (CZQM_FC_APP) positions are online:

```
ACTIVE:CYFC_TWR:TWR:ACTIVE
ACTIVE:CZQM_FC_APP:APP:ACTIVE
```

## Testing Recommendations

1. **Verify arc smoothness**: With 1.0° spacing, arcs should render smoothly
2. **Check consecutive arcs**: Ensure smooth transition between UKNUM-URTIT and URTIT-VYSTA arcs
3. **Verify the 180° arc**: The URTIT-VYSTA semicircle should appear as a clean half-circle
4. **Test activation**: Confirm appearance/disappearance with controller position changes
5. **Visual alignment**: Compare rendered arcs with published approach charts

## Comparison with CYHZ

CYFC shows different characteristics than the CYHZ approach we analyzed earlier:

| Feature | CYHZ RNAV Y Rwy 05 | CYFC RNAV Y Rwy 09 |
|---------|-------------------|-------------------|
| RF arcs per procedure | 1 per transition | Up to 2 per transition |
| Arc radii | 2.5 NM | 1.0 NM and 2.5 NM |
| Turn types | Left and right | Left and right |
| Maximum sweep | 180° | 180° |
| Consecutive arcs | No | Yes (VESBI transition) |

## Future Work

- Other CYFC approach procedures (different runways)
- Expansion to other airports in CZQM FIR with RNAV approaches
- Analysis of minimum turn radius requirements for different aircraft categories

## References

- TopSky Developer Guide v2.5, pages 46-47 (COORD_AF syntax)
- CZQQ ESE file (FIXES section for waypoint coordinates)
- CYFC RNAV (RNP) Y Runway 09 approach chart
- Designated Airspace Handbook (DAH)

---

*Calculated: November 2024*
*Joel Lavoie - VATCAN CZQM vACC*
