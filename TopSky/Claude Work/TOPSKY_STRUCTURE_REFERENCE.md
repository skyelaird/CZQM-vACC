# TopSky Structure Reference
## Corrected Architecture Understanding

**Date:** 2025-11-23  
**Source:** TopSky Developer Guide v2.5, Pages 32-33

---

## Core Concepts (CRITICAL)

### 1. LAYERS (Drawing Order)
**Purpose:** Control rendering sequence - higher numbers draw on top  
**Scope:** Global rendering order across ALL maps  
**Syntax:** `LAYER:LayerNumber` (standalone line)  
**Valid Range:** -999 to -1, and 1 to 999  
**Default:** Layer 1 if not specified  
**Special:** Layer 0 reserved for TopSkyAreas.txt content

**Layer Characteristics:**
- Higher layers completely overwrite lower layers (no transparency)
- Independent of folder organization
- Optional - omit LAYER line to default to Layer 1
- Drawing sequence: -999 → -1 → 0 → 1 → 999

### 2. FOLDERS (Organization)
**Purpose:** Organize maps in the Maps Window UI  
**Scope:** User interface grouping only  
**Syntax:** `FOLDER:FolderName` (standalone line, REQUIRED)  
**Rules:**
- Every map MUST belong to exactly one folder
- No leading spaces in name
- No backslash (\) character in name
- Reserved names: AUTO, LMAPS

**Special Folder Names:**
Maps in these folders do NOT appear in Maps Window:
- ARTCC HIGH, ARTCC, ARTCC LOW
- GEO, SID, STAR, FREE TEXT
- AIRWAYS H, AIRWAYS L
- REGIONS

### 3. MAPS (Individual Definitions)
**Purpose:** Define individual map elements  
**Scope:** Single drawable entity  
**Syntax:** `MAP:MapName` (standalone line, REQUIRED)  
**Rules:**
- Must have unique name
- Must specify FOLDER
- Can optionally specify LAYER
- Contains drawing commands (COORD, LINE, etc.)

---

## Correct Syntax Structure

### Minimal Map Definition
```
MAP:BoundaryName
FOLDER:MyFolder
COLOR:MyColor
COORD:N045.00.00.000:W053.00.00.000
COORD:N046.00.00.000:W054.00.00.000
COORDPOLY:0
```

### Complete Map Definition
```
MAP:BoundaryName
FOLDER:MyFolder
LAYER:2
COLOR:MyColor
ACTIVE:ID:QM:*:*:*
COORD:N045.00.00.000:W053.00.00.000
COORD:N046.00.00.000:W054.00.00.000
COORD:N047.00.00.000:W055.00.00.000
COORDPOLY:0
```

### Multiple Maps in Same Folder, Different Layers
```
; First map - Layer 1 (cold state)
MAP:CZUL-BOUNDARY-COLD
FOLDER:NEIGHBORS
LAYER:1
COLOR:COLD_NEIGHBOR
ACTIVE:ID::*:*:UL
COORD:...
COORDPOLY:0

; Second map - Layer 3 (hot state, overwrites Layer 1)
MAP:CZUL-BOUNDARY-HOT
FOLDER:NEIGHBORS-HOT
LAYER:3
COLOR:HOT_NEIGHBOR
ACTIVE:ID::*:UL:*
COORD:...
COORDPOLY:0
```

---

## Common Mistakes (AVOID)

### ❌ WRONG: Combining layer with map name
```
MAP:0:BoundaryName          // INCORRECT - layer in MAP line
FOLDER:MyFolder
COLOR:MyColor
```

### ✅ RIGHT: Separate standalone lines
```
MAP:BoundaryName            // Map name only
FOLDER:MyFolder             // Folder assignment
LAYER:0                     // Optional layer number
COLOR:MyColor
```

### ❌ WRONG: Indented coordinates with END tag
```
MAP:BoundaryName
FOLDER:MyFolder
COORDPOLY:
  N045.00.00.000:W053.00.00.000    // INCORRECT
  N046.00.00.000:W054.00.00.000
END                                // INCORRECT
```

### ✅ RIGHT: COORD lines then COORDPOLY
```
MAP:BoundaryName
FOLDER:MyFolder
COORD:N045.00.00.000:W053.00.00.000
COORD:N046.00.00.000:W054.00.00.000
COORDPOLY:0
```

### ❌ WRONG: Confusing layers with folders
```
; Wrong thinking: "Layer 0 folder"
FOLDER:LAYER-0              // INCORRECT concept
```

### ✅ RIGHT: Separate concepts
```
; Layers = drawing order (global)
; Folders = UI organization (per map)
FOLDER:CLASS-G              // Folder for organization
LAYER:0                     // Layer for drawing order
```

---

## CZQM/CZQX Architecture

### Folder Structure
```
CLASS-G/              → Static uncontrolled airspace
  - CZQX-CLASS-G-PART1
  - CZQX-CLASS-G-PART2
  - CHARLO-NO-CONTROL
  
NEIGHBORS/            → Cold state boundaries
  - CZUL-BOUNDARY
  - ZBW-BOUNDARY
  - BIRD-BOUNDARY
  
NEIGHBORS-HOT/        → Hot state boundaries
  - CZUL-BOUNDARY-LIVE
  - ZBW-BOUNDARY-LIVE
  - BIRD-BOUNDARY-LIVE
  
DELEGATIONS/          → Internal APP/TWR
  - CYHZ-APP-BOUNDARY
  - CYHZ-TWR-BOUNDARY
  - CYQM-APP-BOUNDARY
  
FIR-SPLIT/            → Center split line
  - CZQM-CZQX-BOUNDARY
```

### Layer Assignment
```
Layer 0:  CLASS-G folder maps (always visible baseline)
Layer 1:  NEIGHBORS folder maps (cold state, default layer)
Layer 2:  DELEGATIONS folder maps (when positions online)
Layer 3:  NEIGHBORS-HOT folder maps (overwrites Layer 1)
Layer 4:  FIR-SPLIT folder maps (when both centers online)
```

### Drawing Sequence
```
1. Layer 0 draws first (CLASS-G baseline)
2. Layer 1 draws second (cold neighbors) - may be hidden by higher layers
3. Layer 2 draws third (delegations) - overwrites Layers 0-1 in areas
4. Layer 3 draws fourth (hot neighbors) - overwrites Layers 0-2 in areas
5. Layer 4 draws last (FIR split) - overwrites all lower layers

Result: User sees composite of all active layers,
        with higher layers visually on top
```

---

## COORDPOLY Fill Patterns

**Syntax:** `COORDPOLY:FillPattern`

### Fill Pattern Values
```
0              = No fill (outline only) - RECOMMENDED for boundaries
5-100          = Percentage fill (5%, 10%, 20%, ..., 100%)
E0-E52         = Hatch patterns (GDI+ HatchStyle enumeration)
```

### Common Usage
```
COORDPOLY:0    = Boundary outline only (Class G, delegations)
COORDPOLY:20   = 20% fill (special use airspace)
COORDPOLY:E0   = Horizontal hatch
COORDPOLY:E6   = 5% hatch (same as COORDPOLY:5)
```

---

## Activation Logic

### Always Visible (No Activation)
```
ACTIVE:ID::
; No requirements - always shows
```

### Position-Based Activation
```
; Show when MY position ID is QM
ACTIVE:ID:QM:*:*:*

; Show when someone ELSE is logged in as UL
ACTIVE:ID::*:UL:*

; Show when BOTH QM and QX are online
ACTIVE:ID:*:*:QM,QX:*

; Show when I am NOT QM (someone else is center)
ACTIVE:ID::QM:*:*
```

### Combined Conditions (AND logic)
```
ACTIVE:ID:QM:*:*:*
AND_ACTIVE:ID:*:*:QX:*
; Shows when I am QM AND QX is online
```

---

## File Organization

### TopSkyMaps.txt Structure
```
; ============================================
; COLOR DEFINITIONS
; ============================================
COLORDEF:UNCONTROLLED_STATIC:95:95:95
COLORDEF:COLD_NEIGHBOR:110:110:110
COLORDEF:HOT_NEIGHBOR:140:140:140

; ============================================
; LAYER 0 - STATIC UNCONTROLLED
; ============================================
MAP:CZQX-CLASS-G-PART1
FOLDER:CLASS-G
LAYER:0
COLOR:UNCONTROLLED_STATIC
ACTIVE:ID::
COORD:...
COORDPOLY:0

; ============================================
; LAYER 1 - COLD NEIGHBORS
; ============================================
MAP:CZUL-BOUNDARY
FOLDER:NEIGHBORS
LAYER:1
COLOR:COLD_NEIGHBOR
ACTIVE:ID::
COORD:...
COORDPOLY:0

; ============================================
; LAYER 3 - HOT NEIGHBORS
; ============================================
MAP:CZUL-BOUNDARY-LIVE
FOLDER:NEIGHBORS-HOT
LAYER:3
COLOR:HOT_NEIGHBOR
ACTIVE:ID::*:UL:*
COORD:...
COORDPOLY:0
```

---

## Reference

**Source:** TopSky plugin for EuroScope Developer Guide v2.5
- Page 33: MAP, FOLDER, LAYER definitions
- Page 45: COORD coordinate definitions
- Page 50: COORDPOLY polygon drawing

**Key Principle:** 
Layers control WHAT draws on top.  
Folders control WHERE it appears in the UI.  
They are completely independent concepts.

---

## Version History

**v1.0 (2025-11-23):** Initial corrected architecture documentation  
**Status:** ✅ Verified against TopSky Developer Guide v2.5
