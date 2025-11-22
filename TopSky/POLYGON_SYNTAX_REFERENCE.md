# TopSky Polygon Syntax Reference

**Quick reference for proper COORD/COORDPOLY syntax**

## ✅ Correct Syntax

```
MAP:10:EXAMPLE_POLYGON
FOLDER:AIRSPACE BOUNDARIES
COLOR:UNCONTROLLED
ACTIVE:ID::
COORD:N047.50.54.000:W064.37.20.000
COORD:N047.24.01.000:W065.00.37.000
COORD:N047.07.43.000:W067.04.48.000
COORD:N047.08.26.000:W067.05.07.000
...more coordinates...
COORDPOLY:0
```

## Key Rules

1. **Each coordinate needs `COORD:` prefix**
   - Stack multiple `COORD:` lines
   - Coordinates define vertices
   - Order matters - defines polygon path

2. **`COORDPOLY:FillPattern` draws the polygon**
   - `0` = no fill (outline only)
   - `5`, `10`, `20`, etc. = percentage fill
   - `E0`-`E52` = hatch patterns
   - After drawing, coordinates are discarded

3. **No bare coordinates**
   - ❌ `N047.50.54.000:W064.37.20.000` (invalid)
   - ✅ `COORD:N047.50.54.000:W064.37.20.000` (valid)

4. **`COORDPOLY:` closes and draws**
   - Not a container for coordinates
   - Consumes previously defined `COORD:` lines
   - Must come AFTER all `COORD:` lines

## ❌ Common Mistakes

### Mistake 1: Missing COORD: prefix
```
MAP:10:BAD_EXAMPLE
COORDPOLY:10
N047.50.54.000:W064.37.20.000  ← ERROR: No COORD: prefix
N047.24.01.000:W065.00.37.000  ← ERROR: No COORD: prefix
```

### Mistake 2: COORDPOLY as container
```
MAP:10:BAD_EXAMPLE
COORDPOLY:10                    ← ERROR: Not a container
  N047.50.54.000:W064.37.20.000
  N047.24.01.000:W065.00.37.000
```

### Mistake 3: Using END
```
COORD:N047.50.54.000:W064.37.20.000
COORD:N047.24.01.000:W065.00.37.000
END  ← ERROR: Should be COORDPOLY:0
```

## Other Coordinate Commands

### COORD_CIRCLE - Draw circles
```
COORD_CIRCLE:CYHZ:35:10
COORDPOLY:0
```
- Center point (lat/lon or fix name)
- Radius in NM
- Spacing in degrees

### COORD_AF - Draw arcs
```
COORD_AF:N44.58.49:W064.55.40:40:1:202:>:243
COORDLINE
```
- Center, radius, spacing
- Start angle, direction, end angle

### LINE - Simple line (not polygons)
```
LINE:POINT1:POINT2
LINE:N044.35.38:W065.08.48:N044.21.43:W065.16.37
```
- Two endpoints only
- For routes, airways, simple boundaries
- Not for filled polygons

## Workflow

1. Stack `COORD:` lines to define vertices
2. Call `COORDPOLY:FillPattern` to draw
3. Coordinates are consumed/discarded
4. Ready for next polygon

## References

- TopSky Developer Guide, pages 45-50
- EuroScope Manual, ESE section
- COMPLEX_BOUNDARY_PATTERNS.md (this repo)

## See Also

- `ACTIVE_SYNTAX_REFERENCE.md` - Activation logic
- `SYNTAX_REFERENCE.md` - General TopSky syntax
- `CHANGES_v1.2.0.md` - Implementation examples

---

**Last Updated:** 2025-11-21 (v1.2.1 bugfix)
