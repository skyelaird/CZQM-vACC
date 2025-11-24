# TopSky RF Arc Generator - Quick Reference

## Quick Start

```bash
python3 topsky_rf_generator.py
```

## Input Format

```
SCT File: /path/to/your.sct
Airport: CYFC
Runway: 09
Transitions:
  VESBI UKNUM URTIT VYSTA
  ANERA URPUS VYSTA
  [blank line]
```

## Output Format

```
MAP:RNAV-Y-{RWY}-{IF_POINT}
FOLDER:{AIRPORT}
ACTIVE:RWY:ARR:{AIRPORT}{RWY}:DEP:*
COLOR:TEXTLABEL
SYMBOL:FIX:{waypoint}
...
COLOR:RNPAR
COORD:{waypoint}
COORD_AF:{center_lat}:{center_lon}:{radius}:{spacing}:{start}:{dir}:{end}
...
COORDLINE
```

## RF Arc Detection

**Automatic Detection:**
- Tests radii: 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 7.0, 10.0 NM
- Tests both L (counterclockwise <) and R (clockwise >) turns
- Selects best fit (error < 0.5 NM, sweep 10-270°)

**What You'll See:**
```
Found 2 RF arc(s):
  UKNUM → URTIT: R=2.5 NM, sweep=134.2°, dir=<
  URTIT → VYSTA: R=1.0 NM, sweep=180.0°, dir=<
```

## Common Issues

| Issue | Solution |
|-------|----------|
| Missing waypoints | Check spelling, verify in .sct file |
| File not found | Use full path to .sct file |
| No arcs detected | Verify procedure has curved legs |
| Wrong turn direction | Check approach chart, may need manual fix |

## COORD_AF Syntax

```
COORD_AF:CenterLat:CenterLon:Radius:Spacing:StartAngle:Direction:EndAngle
         ↓         ↓         ↓      ↓       ↓          ↓         ↓
         sector    sector    NM     degrees degrees    <>        degrees
         format    format
```

- **Direction**: `<` = counterclockwise (left), `>` = clockwise (right)
- **Spacing**: 1.0° recommended for smooth arcs
- **Angles**: True bearings from arc center to waypoints

## Tested Examples

### CYHZ RNAV Y Rwy 05
```
GOSUG ETMEP LOPMA     → 1 RF arc (2.5 NM, 111°)
PEPTA AVIGU LOPMA     → 1 RF arc (2.5 NM, 180°)
```

### CYFC RNAV Y Rwy 09
```
VESBI UKNUM URTIT VYSTA  → 2 RF arcs (2.5 NM, 1.0 NM)
ANERA URPUS VYSTA        → 1 RF arc (2.5 NM)
```

## File Output

**Automatic naming:** `{AIRPORT}_RNAV-Y-{RWY}_TopSkyMaps.txt`

Example: `CYFC_RNAV-Y-09_TopSkyMaps.txt`

## Tips

✓ Use full file paths  
✓ Check waypoint spelling (case-sensitive)  
✓ Verify output against approach charts  
✓ Test in EuroScope before deploying  
✓ Session persists - process multiple approaches with one .sct load  

## Exit

Type `quit` at any prompt or `n` when asked to generate another approach.

---

**Quick Help**: Run `python3 topsky_rf_generator.py` and follow prompts  
**Full Guide**: See TopSky_RF_Generator_Usage_Guide.md  
**Author**: Joel Lavoie - VATCAN CZQM vACC
