# Complex Boundary Patterns - Internal Reference

## Pattern: Lines + Arcs (Mixed Geometry)

**Example from legacy CYZX APP:**

```
MAP:CYZX APP
FOLDER:LOW SECTORS QM
COLOR:APCH
STYLE:Alternate

LINE:N044.35.38:W065.08.48:N044.21.43:W065.16.37
COORD_AF:N44.58.49:W064.55.40:40:1:202:>:243
LINE:N044.40.31:W065.45.39:N044.47.26:W065.26.58
COORD_AF:N044.58.49:W064.55.40:25:1:243:>:202

COORDPOLY:10
```

### Breakdown:

**MAP:CYZX APP**
- Map name (no layer = default layer, likely 0)
- This is legacy content, predates layered approach

**FOLDER:LOW SECTORS QM**
- Places in "LOW SECTORS QM" folder in display

**COLOR:APCH**
- Uses APCH color (defined earlier: RGB 120,120,120)

**STYLE:Alternate**
- Line style: alternating dash-dot pattern
- Makes boundary visually distinct

**LINE:StartLat:StartLon:EndLat:EndLon**
- Straight line segment
- First line: From N044.35.38:W065.08.48 to N044.21.43:W065.16.37

**COORD_AF:CenterLat:CenterLon:Radius:Spacing:StartAngle:Direction:EndAngle**
- Arc (partial circle) segment
- Center: N44.58.49:W064.55.40 (CYZX airport)
- Radius: 40 NM
- Spacing: 1° (fine detail)
- Start: 202° (bearing from center)
- Direction: ">" = clockwise
- End: 243° (bearing from center)
- This creates a 41° arc segment

**Second LINE**
- Connects arc end to next point

**Second COORD_AF**
- Smaller arc: 25 NM radius
- From 243° back to 202° (completing the boundary)

**COORDPOLY:10**
- Make filled polygon with 10% fill
- All previous geometry (2 lines + 2 arcs) forms closed boundary

---

## Key Insights:

### Order Matters
Geometry commands must connect:
1. Line ends where arc begins
2. Arc ends where next line begins
3. Last element connects back to first (closed polygon)

### COORD_AF Direction
- **">"** = Clockwise
- **"<"** = Counterclockwise
- Critical for proper arc direction

### Fill Pattern
- Must match operational needs
- 0 = outline only
- 10 = 10% fill (subtle awareness)
- 100 = solid fill

### COORDPOLY Position
- Always LAST after all geometry
- Consumes all previously defined coordinates
- After COORDPOLY, coordinates are discarded

---

## Usage Pattern for APP Extraction:

When extracting APP boundaries from ESE:

1. **Identify sectorlines** in BORDER definition
2. **Extract each sectorline's coordinates**
3. **Determine if straight or arc**:
   - Straight → Use LINE:
   - Circular segment → Use COORD_AF:
4. **Assemble in order** ensuring continuity
5. **Close with COORDPOLY:10**

---

## COORD_AF Parameters Explained:

```
COORD_AF:CenterLat:CenterLon:Radius:Spacing:StartAngle:Direction:EndAngle
```

### Center
- Usually an airport or navaid
- Can be explicit coordinates

### Radius
- Distance in nautical miles
- Common values: 7, 10, 25, 40, 87 NM

### Spacing
- Degrees between plotted points
- 1° = fine detail (recommended for arcs)
- 5° = coarse (faster, less smooth)
- 10° = very coarse (only for large circles)

### Angles
- Bearings from center (0-359°)
- 0° = North, 90° = East, 180° = South, 270° = West
- StartAngle → EndAngle defines arc span

### Direction
- ">" = Clockwise (most common)
- "<" = Counterclockwise
- Choose based on which way around the arc you need

---

## Example: 40 NM DME Arc

**Scenario:** Aircraft on 40 DME arc from CYZX, from 202° to 243° radial

```
COORD_AF:N44.58.49:W064.55.40:40:1:202:>:243
```

**Visualization:**
- Center at CYZX
- 40 NM radius
- Start at 202° radial (SSW)
- Go clockwise (">")
- End at 243° radial (WSW)
- Total arc: 41°

This creates the curved outer edge of the APP boundary.

---

## Multiple Arcs

Can have multiple arcs in same boundary:

```
COORD_AF:Center:40:1:202:>:243   // Outer arc
LINE:...                         // Connecting line
COORD_AF:Center:25:1:243:>:202   // Inner arc (opposite direction)
COORDPOLY:10
```

Creates a "ring" or "slice" between two radii.

---

## Converting ESE Sectorlines to TopSky

**ESE Format:**
```
SECTORLINE:BOUNDARY_NAME
COORD:N044.35.38:W065.08.48
COORD:N044.21.43:W065.16.37
```

**TopSky Format:**
```
LINE:N044.35.38:W065.08.48:N044.21.43:W065.16.37
```

**If many coordinates (>10):**
Could use raw coordinate list, but LINE segments are clearer for readability.

---

## Best Practices:

1. **Document each segment** - Comment what each line/arc represents
2. **Test continuity** - Ensure end points connect
3. **Use appropriate spacing** - 1° for arcs, don't need for lines
4. **Choose fill wisely** - 10% for awareness, 0% for just outline
5. **Match existing style** - Use STYLE:Alternate for consistency with legacy content

---

## Reference: Full Pattern

```
MAP:LayerNumber:BoundaryName
FOLDER:FolderName
COLOR:ColorName
STYLE:StyleName
ACTIVE:ID:*:*:PositionID:*

// Segment 1: Straight line
LINE:StartLat:StartLon:EndLat:EndLon

// Segment 2: Arc
COORD_AF:CenterLat:CenterLon:Radius:Spacing:StartAngle:Direction:EndAngle

// Segment 3: Another line
LINE:StartLat:StartLon:EndLat:EndLon

// Segment 4: Closing arc
COORD_AF:CenterLat:CenterLon:Radius:Spacing:StartAngle:Direction:EndAngle

// Make it a filled polygon
COORDPOLY:10
```

---

This pattern is used for complex APP boundaries that combine:
- Straight boundaries (political/geographical)
- DME arcs (distance-based)
- Creating realistic terminal control areas
