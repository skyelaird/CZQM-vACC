# TopSky Architecture Correction Summary
## Critical Structure Fix Applied

**Date:** 2025-11-23  
**Issue:** Incorrect understanding of MAP/FOLDER/LAYER relationship  
**Status:** ✅ CORRECTED in all files

---

## What Was Wrong

### ❌ Previous Incorrect Understanding
```
MAP:0:BoundaryName          // Layer number in MAP line - WRONG
COLOR:ColorName
ACTIVE:ID::
COORDPOLY:                  // Indented coordinates - WRONG
  Lat:Lon
  Lat:Lon
END                         // END tag - WRONG
```

**Misconception:** Thought "Layer 0" was part of the MAP definition

---

## What Is Correct

### ✅ Proper TopSky Structure
```
MAP:BoundaryName            // Map name only
FOLDER:FolderName           // Which folder contains this map
LAYER:0                     // Optional: which drawing layer
COLOR:ColorName
ACTIVE:ID::
COORD:Lat:Lon               // Individual COORD lines
COORD:Lat:Lon
COORDPOLY:0                 // Draw polygon (no END tag)
```

**Understanding:**
- **LAYERS** = Drawing order (global concept, -999 to 999)
- **FOLDERS** = UI organization (per-map assignment)
- **MAPS** = Individual elements (belong to one folder, draw on one layer)

---

## Key Distinctions

### Layers vs Folders

| Concept | Purpose | Scope | Syntax |
|---------|---------|-------|--------|
| **LAYER** | Drawing order | Global rendering | `LAYER:0` |
| **FOLDER** | Organization | Maps Window UI | `FOLDER:CLASS-G` |
| **MAP** | Definition | Single element | `MAP:CZQX-CLASS-G-PART1` |

### Critical Points
1. Layers control what draws on top (higher = later = visible)
2. Folders control where maps appear in UI
3. One map → one folder → one layer (optional)
4. Same folder can have maps on different layers
5. Same layer can have maps from different folders

---

## Files Corrected

### ✅ Updated Files
1. **czqx_class_g_calculator.py** - Output generator fixed
2. **czqx_class_g_output.txt** - Regenerated with correct syntax
3. **TOPSKYMAPS_TODO.md** - Project documentation corrected
4. **CZQX_Class_G_Documentation.md** - Technical docs updated
5. **TOPSKY_STRUCTURE_REFERENCE.md** - NEW: Comprehensive reference created

### 📋 Verification Steps Completed
- [x] Reviewed TopSky Developer Guide pages 32-33
- [x] Understood MAP/FOLDER/LAYER independence
- [x] Fixed Python script output generation
- [x] Regenerated all output files
- [x] Updated project TODO file
- [x] Created comprehensive structure reference
- [x] Updated all documentation

---

## Example: Layer 0 Static Uncontrolled

### Before (Incorrect)
```
MAP:0:CZQX-CLASS-G-PART1
COLOR:UNCONTROLLED_STATIC
ACTIVE:ID::
COORDPOLY:
  N045.00.00.000:W053.00.00.000
  N046.00.00.000:W054.00.00.000
END
```

### After (Correct)
```
MAP:CZQX-CLASS-G-PART1
FOLDER:CLASS-G
LAYER:0
COLOR:UNCONTROLLED_STATIC
ACTIVE:ID::
COORD:N045.00.00.000:W053.00.00.000
COORD:N046.00.00.000:W054.00.00.000
COORDPOLY:0
```

**Changes:**
1. ✅ MAP line: name only, no layer number
2. ✅ Added FOLDER line (required)
3. ✅ Added LAYER line (optional but explicit)
4. ✅ COORD lines: not indented, separate lines
5. ✅ COORDPOLY: fill pattern specified, no END tag

---

## Complete CZQM/CZQX Architecture

### Folder/Layer Organization

```
FOLDER: CLASS-G          (Layer 0)
├── CZQX-CLASS-G-PART1
├── CZQX-CLASS-G-PART2
├── CZQX-CLASS-G-PART3
├── CZQX-CLASS-G-PART4
├── CZQX-CLASS-G-PART5
├── CZQX-CLASS-G-PART6
└── CHARLO-NO-CONTROL

FOLDER: NEIGHBORS        (Layer 1)
├── CZUL-BOUNDARY
├── ZBW-BOUNDARY
└── BIRD-BOUNDARY

FOLDER: DELEGATIONS      (Layer 2)
├── CYHZ-APP
├── CYHZ-TWR
├── CYQM-APP
└── CYQM-TWR

FOLDER: NEIGHBORS-HOT    (Layer 3)
├── CZUL-BOUNDARY-LIVE
├── ZBW-BOUNDARY-LIVE
└── BIRD-BOUNDARY-LIVE

FOLDER: FIR-SPLIT        (Layer 4)
└── CZQM-CZQX-BOUNDARY
```

### Drawing Sequence
```
Paint order (bottom to top):
1. Layer 0: Static uncontrolled baseline
2. Layer 1: Cold neighbors (when not online)
3. Layer 2: Delegations (when positions online)
4. Layer 3: Hot neighbors (overwrites Layer 1)
5. Layer 4: FIR split (when both online)

Higher layers completely overwrite lower layers
```

---

## Integration Impact

### No Change Required In:
- ✅ Coordinate data (unchanged)
- ✅ Color definitions (unchanged)
- ✅ Activation logic (unchanged)
- ✅ Geometric calculations (unchanged)

### Changes Required In:
- ✅ File syntax structure (corrected)
- ✅ Documentation (updated)
- ✅ Understanding of architecture (clarified)

### Result:
- **Same visual output**
- **Same functionality**
- **Correct TopSky syntax**
- **Proper understanding of architecture**

---

## Reference Sources

**TopSky Developer Guide v2.5:**
- Page 33: MAP, FOLDER, LAYER definitions
- Page 45: COORD syntax
- Page 50: COORDPOLY syntax

**Project Files:**
- `TOPSKY_STRUCTURE_REFERENCE.md` - Complete architecture guide
- `TopSky_plugin_for_EuroScope__Developer_Guide.pdf` - Official documentation

---

## Version History

**v1.0 (2025-11-23):** 
- Identified structure misunderstanding
- Corrected all project files
- Created comprehensive reference
- Updated documentation

**Status:** ✅ All files corrected and verified
