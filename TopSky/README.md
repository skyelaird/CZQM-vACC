# CZQM/CZQX TopSkyMaps Configuration

Dynamic airspace boundary display for EuroScope with TopSky plugin.

## Overview

This configuration provides activation-aware boundary display for CZQM/CZQX vACC operations. Boundaries appear and change color based on which positions are online, helping controllers maintain situational awareness.

## Features

- **Dynamic activation**: Boundaries show/hide based on position staffing
- **State visualization**: Same boundary, different colors = different operational states
- **Subtle design**: Boundaries inform without overwhelming - aircraft tags remain priority
- **Smart geometry**: Uses COORD_CIRCLE for clean circle definitions

## Installation

1. Place `TopSkyMaps.txt` in your TopSky plugin folder
2. Load in EuroScope via TopSky settings
3. Boundaries will activate automatically based on online positions

## Design Philosophy

### Color Strategy (Shades of Grey)
- **Darkest (80,80,80)**: Your controlled airspace
- **Light (95,95,95)**: Uncontrolled (Class G) - "no service here"
- **Medium (100,100,100)**: Delegated areas (APP/TWR carved out)
- **Lighter (110,110,110)**: Cold neighbors - "exists but unstaffed"
- **Brightest (140,140,140)**: Hot neighbors - "ACTIVE, coordinate!"

### Layer Strategy
- **Layer 0**: Static uncontrolled areas (always visible)
- **Layer 1**: Cold neighbor boundaries (always visible, subtle)
- **Layer 2**: Internal delegations (appear when positions online)
- **Layer 3**: Hot neighbors (overwrites Layer 1 when neighbor staffs)
- **Layer 4**: CZQM/CZQX split (only when both centers online)

## Current Status

**Version:** 1.0.0  
**Build Date:** 2025-11-20  
**Progress:** Layer 0 in development

### Implemented
- ✅ CHARLO-NO-CONTROL Class G boundary (SFC-12,500')
- ✅ Color palette and layer structure
- ✅ TWR circle examples (commented, ready to activate)

### In Progress
- 🔨 Northern Labrador Class G
- 🔨 St. Anthony Class G
- ⏳ Internal delegations (APP/TWR/DG/CB)
- ⏳ Neighbor boundaries (CZUL/ZBW/BIRD/CZEG/CZQXO)
- ⏳ CZQM/CZQX internal boundary

## File Structure

```
TopSkyMaps.txt
├── Header (versioning, changelog)
├── Color Definitions
├── Layer 0: Static Uncontrolled Airspace
│   └── CHARLO-NO-CONTROL (complete)
├── Layer 1: Cold Neighbor Boundaries (future)
├── Layer 2: Internal Delegations
│   └── TWR circle examples (commented)
├── Layer 3: Hot Neighbor Boundaries (future)
└── Layer 4: CZQM/CZQX Split (future)
```

## Technical Reference

### Geometry Patterns

**Simple Circles (TWR, MTCA):**
```
COORD_CIRCLE:CYHZ:7:10        // Halifax Tower, 7 NM, 10° spacing
COORD_CIRCLE:CYYR:87:5        // Goose Bay MTCA, 87 NM, 5° spacing
```

**Arcs (Curved segments):**
```
COORD_AF:Lat:Lon:Radius:Spacing:StartAngle:Direction:EndAngle
```

**Complex Polygons:**
Explicit coordinate lists for FIR boundaries and irregular shapes.

### Activation Logic

**Always visible:**
```
ACTIVE:ID::
```

**Position-based:**
```
ACTIVE:ID:HZT:QMT:...        // Show when these positions online
```

**Neighbor-based:**
```
ACTIVE:ID::UL:ZBW:...        // Show when neighbor FIRs staffed
```

**Combined (both centers):**
```
ACTIVE:ID:QM,QX::
AND_ACTIVE:ID
```

## Source Files

- **ESE:** CZQQ-DO-NOT-USE_20251107023304-251101-0017.ese
- **DAH:** DAH_en_20250807.pdf (Designated Airspace Handbook)
- **Charts:** LO_07 (Goose area), LO_08 (North)
- **Airspace Manual:** CZQM FIR Centre Airspace Manual v2 draft 3

## Contributing

This file is under active development. Changes should:
1. Maintain semantic versioning in header
2. Update changelog with each commit
3. Follow the established color and layer strategy
4. Include comprehensive comments for complex boundaries
5. Use intelligent geometry (COORD_CIRCLE, COORD_AF) where appropriate

## Version History

### 1.0.0 (2025-11-20)
- Initial build with Layer 0 foundation
- CHARLO-NO-CONTROL Class G boundary implemented
- TWR circle pattern established
- Version control and documentation structure

## License

For use with CZQM/CZQX vACC on VATSIM network.

## Contact

CZQM/CZQX vACC - VATCAN Division
