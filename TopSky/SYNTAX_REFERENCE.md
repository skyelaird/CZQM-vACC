# TopSkyMaps Syntax Quick Reference

Based on production file analysis and TopSky Developer Guide.

---

## Color Definitions

```
COLORDEF:ColorName:RedValue:GreenValue:BlueValue
```

**Example:**
```
COLORDEF:DELEGATION:100:100:100
```

---

## Simple Circle Boundaries

**Pattern:**
```
MAP:LayerNumber:MapName
FOLDER:FolderName
COLOR:ColorName
ACTIVE:MapName:PositionID1:PositionID2:...
COORD_CIRCLE:AirportCode:RadiusNM:SpacingDegrees
COORDPOLY:0
```

**Example - Halifax Tower (7 NM):**
```
MAP:12:CYHZ_TWR
FOLDER:AIRSPACE BOUNDARIES
COLOR:DELEGATION
ACTIVE:CYHZ_TWR:HZT
COORD_CIRCLE:CYHZ:7:10
COORDPOLY:0
```

**Key Points:**
- COORD_CIRCLE comes BEFORE COORDPOLY:0
- COORDPOLY:0 means "use previous coords as filled polygon"
- Spacing 10° is good for circles under 20 NM
- Spacing 5° better for larger circles (more smoothness)

---

## Complex Boundaries (Lines + Arcs)

**Pattern:**
```
MAP:LayerNumber:MapName
FOLDER:FolderName
COLOR:ColorName
ACTIVE:MapName:PositionID
LINE:Lat1:Lon1:Lat2:Lon2
COORD_AF:CenterLat:CenterLon:Radius:Spacing:StartAngle:Direction:EndAngle
LINE:Lat3:Lon3:Lat4:Lon4
COORD_AF:CenterLat:CenterLon:Radius:Spacing:StartAngle:Direction:EndAngle
COORDPOLY:0
```

**Example - CYZX APP (from file lines 1413-1424):**
```
MAP:CYZX APP
FOLDER:LOW SECTORS QM
COLOR:APCH
STYLE:Alternate

LINE:N044.35.38:W065.08.48:N044.21.43:W065.16.37
COORD_AF:N44.58.49:W064.55.40:40:1:202:>:243
LINE:N044.40.31:W065.45.39:N044.47.26:W065.26.58
COORD_AF:N044.58.49:W064.55.40:25:1:243:>:202

COORDPOLY:0
```

**Key Points:**
- Mix LINE and COORD_AF to build complex shapes
- COORD_AF: direction ">" = clockwise, "<" = counterclockwise
- All geometry commands before COORDPOLY:0

---

## Raw Coordinate Polygons

**Pattern:**
```
MAP:LayerNumber:MapName
FOLDER:FolderName
COLOR:ColorName
ACTIVE:MapName:PositionID
COORDPOLY:
Lat1:Lon1
Lat2:Lon2
Lat3:Lon3
...
END
```

**Example - CHARLO Class G:**
```
MAP:10:CHARLO_CLASS_G
FOLDER:AIRSPACE BOUNDARIES
COLOR:UNCONTROLLED
ACTIVE:CHARLO_CLASS_G::
COORDPOLY:
N047.50.54.000:W064.37.20.000
N047.24.01.000:W065.00.37.000
...67 coordinates total...
N047.59.59.850:W065.56.26.620
END
```

**Key Points:**
- COORDPOLY: (no zero) for raw coordinates
- Must close polygon (last coord connects to first)
- END statement required
- One coordinate per line

---

## Holds (Using COORD_HM)

**Pattern:**
```
COORD_HM:PointName:InbdCrs:TurnDir:Length:Radius:Spacing
COORDLINE
```

**Example - from file:**
```
COORD_HM:ETGAR:084M:L:1.5MIN:265KTS:5
COORDLINE
```

**Key Points:**
- InbdCrs with "M" suffix = magnetic
- TurnDir: "L" or "R"
- Length: can use "MIN" suffix for time-based
- Radius: can use "KTS" suffix for speed-based
- COORDLINE (not COORDPOLY) for lines

---

## MVA Circles (Non-Filled)

**Pattern:**
```
COORD_CIRCLE:AirportCode:RadiusNM:Spacing
COORDLINE
```

**Example - from file:**
```
COORD_CIRCLE:CYHZ:100.0:5.0
COORDLINE
```

**Key Points:**
- COORDLINE = draw outline only (not filled)
- COORDPOLY:0 = filled polygon
- Used for reference circles like MVA

---

## Activation Logic

### Single Position
```
ACTIVE:MapName:PositionID
```
Shows when PositionID is online.

### Multiple Positions (OR logic)
```
ACTIVE:MapName:POS1:POS2:POS3
```
Shows when ANY of these positions are online.

### Always Visible
```
ACTIVE:MapName::
```
Empty position lists = always visible.

### Neighbor Detection
```
ACTIVE:MapName:::OnlineID1:OnlineID2
```
Third field (after ::) = show when these neighbors are online.

### Both Online (AND logic)
```
ACTIVE:MapName:QM,QX::
AND_ACTIVE:MapName
```
Shows only when BOTH QM AND QX are online.

---

## Layer Numbers

**Recommended Strategy:**
- **0-9:** Legacy/default layers (existing content)
- **10:** Static uncontrolled (Class G)
- **11:** Cold neighbors (always visible)
- **12:** Internal delegations (APP/TWR/sectors)
- **13:** Hot neighbors (overwrites Layer 11)
- **14:** Special states (QM/QX split)

**Rule:** Higher layer overwrites lower layer (non-translucent).

---

## Folder Organization

```
FOLDER:FolderName
```

Groups maps in EuroScope display.

**Recommended Folders:**
- `AIRSPACE BOUNDARIES` - New dynamic boundaries
- `LOW SECTORS QM` - Legacy low sectors
- `MINIMUM VECTORING` - MVA circles
- `FREQ` - Frequency displays

---

## Common Geometry Functions

### COORD_CIRCLE
```
COORD_CIRCLE:CenterPoint:RadiusNM:SpacingDegrees
```
Perfect for: TWR boundaries, MTCA, terminal circles.

### COORD_AF (Arc/Partial Circle)
```
COORD_AF:CenterLat:CenterLon:Radius:Spacing:StartAngle:Direction:EndAngle
```
Perfect for: Curved APP boundaries, partial circles.

### COORD_PBD (Point/Bearing/Distance)
```
COORD_PBD:PointName:Bearing:DistanceNM
```
Perfect for: Radials, simple offsets.

### COORD_HM (Holding Pattern)
```
COORD_HM:PointName:InbdCrs:TurnDir:Length:Radius:Spacing
```
Perfect for: Published holds.

### LINE (Straight Line)
```
LINE:StartLat:StartLon:EndLat:EndLon
```
Perfect for: Straight boundaries, connecting points.

---

## Style Options

```
STYLE:StyleName:Width
```

**Available Styles:**
- `Solid` - Continuous line
- `Dash` - Dashed line
- `Dot` - Dotted line
- `Alternate` - Alternating dash-dot

**Width:** 1-5 (pixel width)

---

## Text Labels

```
TEXT:Lat:Lon:TextContent
TEXT/L:Lat:Lon:TextContent   // Left aligned
TEXT/R:Lat:Lon:TextContent   // Right aligned
TEXT/T:Lat:Lon:TextContent   // Top aligned
TEXT/B:Lat:Lon:TextContent   // Bottom aligned
```

---

## Zoom Levels

```
ZOOM:Level
```

**Levels:** 1-20 (higher = more zoomed in)
- 1-3: Far out (FIR level)
- 4-7: Medium (terminal areas)
- 8-15: Close in (airport areas)
- 16-20: Very close (SMR)

Affects when maps become visible based on zoom.

---

## Common Mistakes to Avoid

### ❌ Wrong Order
```
COORDPOLY:          // Wrong - polygon before circle
COORD_CIRCLE:CYHZ:7:10
END                 // Wrong - END with circles
```

### ✅ Correct Order
```
COORD_CIRCLE:CYHZ:7:10    // Circle first
COORDPOLY:0               // Then polygon
```

---

### ❌ Wrong Color Syntax
```
COLOR:DELEGATION:100:100:100    // Wrong - COLOR for definition
```

### ✅ Correct Color Syntax
```
COLORDEF:DELEGATION:100:100:100    // Correct - COLORDEF for definition
COLOR:DELEGATION                   // Then COLOR to apply it
```

---

### ❌ Wrong Polygon Close
```
COORDPOLY:         // Wrong - should be no zero
N047.50.54.000:W064.37.20.000
...
// Missing END
```

### ✅ Correct Polygon Close
```
COORDPOLY:         // No zero for raw coords
N047.50.54.000:W064.37.20.000
...
END                // Required END statement
```

---

## Quick Syntax Checker

**Is it a filled area?**
- Yes → Use `COORDPOLY:0` (if using geometry functions)
- Yes → Use `COORDPOLY:` then `END` (if using raw coords)

**Is it just a line?**
- Yes → Use `COORDLINE`

**Does it use COORD_CIRCLE?**
- Yes → `COORD_CIRCLE` first, then `COORDPOLY:0`
- No END statement needed

**Does it use raw coordinates?**
- Yes → `COORDPOLY:` then coordinates then `END`

**Does it mix lines and arcs?**
- Yes → List all geometry, then `COORDPOLY:0` at end

---

## Reference Files

- **Your Working File:** TopSkyMaps.txt
- **Developer Guide:** TopSky_plugin_for_EuroScope__Developer_Guide.pdf
- **Good Examples in Your File:**
  - Lines 1357-1358: MVA circle (COORDLINE)
  - Lines 1410-1411: CYHZ APP circle (COORDPOLY:0)
  - Lines 1419-1424: CYZX APP complex (LINE + COORD_AF)
  - Lines 1516-1593: CHARLO raw coords (COORDPOLY: ... END)

---

**When in doubt, look at working examples in your existing file!**
