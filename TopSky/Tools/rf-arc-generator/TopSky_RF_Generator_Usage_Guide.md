# TopSky RF Arc Generator - Usage Guide

## Overview

This tool automatically analyzes RNAV approach procedures and generates TopSky map definitions with correctly formatted RF (Radius to Fix) arcs. It reads waypoint coordinates from your ESE .sct file, detects which legs are RF arcs based on geometry, and outputs production-ready TopSky map definitions.

## Features

- **Automatic RF arc detection**: Analyzes leg geometry to identify RF arcs
- **Best-fit radius calculation**: Tests standard RNAV radii (1.0-10.0 NM) and selects optimal fit
- **Turn direction detection**: Automatically determines left/right turns
- **Session persistence**: Loads .sct file once, use for multiple approaches
- **Proper TopSky syntax**: Generates correctly formatted MAP definitions
- **Error checking**: Validates waypoints exist before processing

## Installation

No installation required - just Python 3.x. The script is self-contained.

## Usage

### Interactive Mode (Recommended)

```bash
python3 topsky_rf_generator.py
```

Or with pre-loaded .sct file:

```bash
python3 topsky_rf_generator.py /path/to/your.sct
```

### Interactive Prompts

1. **SCT File Path**: 
   ```
   Enter path to .sct file: D:\GitHub\CZQM-vACC\TopSky\References\CZQQ.sct
   ```
   - The tool loads all waypoints from the [FIXES] section
   - This file persists for the entire session

2. **Airport Code**:
   ```
   Airport code (e.g., CYFC): CYFC
   ```
   - 4-letter ICAO code

3. **Runway**:
   ```
   Runway (e.g., 09): 09
   ```
   - Just the runway number (no RWY prefix)

4. **Transitions**:
   ```
   Transition 1: VESBI UKNUM URTIT VYSTA
   Transition 2: ANERA URPUS VYSTA
   Transition 3: [blank line to finish]
   ```
   - One transition per line
   - Format: IF_POINT waypoint1 waypoint2 ... FAP
   - First waypoint becomes the transition name
   - Press Enter with no input when done

### Example Session

```
$ python3 topsky_rf_generator.py

================================================================================
TopSky RF Arc Generator
================================================================================

Enter path to .sct file: /mnt/user-data/uploads/CZQQ.sct
Loading waypoints from /mnt/user-data/uploads/CZQQ.sct...
Loaded 4700 waypoints

================================================================================
Generate new approach procedure (or 'quit' to exit)
================================================================================

Airport code (e.g., CYFC): CYFC
Runway (e.g., 09): 09

Enter transitions (one per line)
Format: IF_POINT waypoint1 waypoint2 ... FAP
Example: VESBI UKNUM URTIT VYSTA
Enter blank line when done
Transition 1: VESBI UKNUM URTIT VYSTA
Transition 2: ANERA URPUS VYSTA
Transition 3: 

Generating TopSky maps...

Analyzing transition: VESBI
  Route: VESBI - UKNUM - URTIT - VYSTA
  Found 2 RF arc(s):
    UKNUM → URTIT: R=2.5 NM, sweep=134.2°, dir=<
    URTIT → VYSTA: R=1.0 NM, sweep=180.0°, dir=<

Analyzing transition: ANERA
  Route: ANERA - URPUS - VYSTA
  Found 1 RF arc(s):
    URPUS → VYSTA: R=2.5 NM, sweep=48.7°, dir=>

✓ Saved to: CYFC_RNAV-Y-09_TopSkyMaps.txt

Generate another approach? (y/n): y
```

## Output Format

The tool generates properly formatted TopSky map definitions:

```
MAP:RNAV-Y-09-VESBI
FOLDER:CYFC
ACTIVE:RWY:ARR:CYFC09:DEP:*
COLOR:TEXTLABEL
SYMBOL:FIX:VESBI
SYMBOL:FIX:UKNUM
SYMBOL:FIX:URTIT
SYMBOL:FIX:VYSTA
COLOR:RNPAR
COORD:VESBI
COORD:UKNUM
COORD_AF:N045.52.59.613:W066.38.47.484:2.5:1.0:339.8:<:205.6
COORD:URTIT
COORD_AF:N045.50.41.526:W066.38.54.561:1.0:1.0:272.7:<:92.7
COORD:VYSTA
COORDLINE
```

### Output Naming

Files are automatically named: `{AIRPORT}_RNAV-Y-{RUNWAY}_TopSkyMaps.txt`

Example: `CYFC_RNAV-Y-09_TopSkyMaps.txt`

## RF Arc Detection Logic

The tool automatically detects RF arcs by:

1. **Testing standard radii**: 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 7.0, 10.0 NM
2. **Testing both turn directions**: Left (counterclockwise <) and Right (clockwise >)
3. **Calculating geometric fit**: Finds radius where arc center is equidistant from start/end
4. **Validating results**:
   - Error must be < 0.5 NM
   - Sweep must be between 10° and 270°
   - Selects best fit (minimum error)

### When RF Arcs Are Detected

An RF arc is identified when:
- There's a significant track change between consecutive legs (> 10°)
- A circular arc with standard radius fits the geometry
- The turn is geometrically valid (not too tight, not too wide)

### When Straight Legs Are Used

A straight TF (Track to Fix) leg is used when:
- No track change between consecutive legs
- No standard radius fits the geometry adequately
- It's the first leg of the transition (no entry track to reference)

## Error Handling

### Missing Waypoints

```
ERROR: Missing waypoints: XXXXX, YYYYY
```
→ Check spelling, ensure waypoints exist in your .sct file

### Invalid File Path

```
ERROR: File not found: /path/to/file.sct
```
→ Verify path is correct, use full path if relative path fails

### No Waypoints Loaded

```
ERROR: No waypoints loaded from file
```
→ Verify .sct file has a [FIXES] section with waypoint definitions

## Tips & Best Practices

1. **Use full file paths**: Avoid relative paths that might cause confusion
2. **Check waypoint spelling**: Waypoint names are case-sensitive
3. **Verify transitions on charts**: Compare tool output with published approach charts
4. **Test radii**: The tool tests standard values; unusual procedures might need manual adjustment
5. **Review consecutive arcs**: Some procedures (like CYFC) have multiple RF arcs in sequence

## Integration with TopSky

1. Copy output file contents into your `TopSkyMaps.txt`
2. Test in EuroScope with TopSky plugin loaded
3. Verify arcs render smoothly (1.0° spacing should be smooth)
4. Check activation logic with different controller positions
5. Compare visual output with approach charts

## Tested Approaches

Successfully tested with:
- **CYHZ RNAV Y Rwy 05**: 2 transitions, 2 RF arcs (2.5 NM radius)
- **CYFC RNAV Y Rwy 09**: 2 transitions, 3 RF arcs (1.0 and 2.5 NM radii)

## Technical Details

### Coordinate Systems

- Input: Sector file format (N044.53.13.919 W063.45.00.619)
- Internal: Decimal degrees for calculations
- Output: Sector file format for TopSky

### Geometry Calculations

- **Bearing**: True bearing using Haversine formula
- **Distance**: Great circle distance in nautical miles
- **Arc center**: Perpendicular to entry track at radius distance
- **Angles**: Bearing from arc center to waypoints

### Standard Test Radii

Based on RNAV procedure design standards:
- **1.0 NM**: Tight turns, often near airports
- **1.5-2.5 NM**: Common for terminal area procedures
- **3.0-5.0 NM**: Moderate turns
- **7.0-10.0 NM**: Wide, gentle turns

## Troubleshooting

### Arc looks wrong in EuroScope

1. Verify waypoint coordinates in .sct file match published data
2. Check if manual radius adjustment needed (rare)
3. Ensure spacing is 1.0° for smooth rendering
4. Compare start/end angles with chart geometry

### No RF arcs detected

1. Verify there are actually curved legs (check approach chart)
2. May be all straight TF legs (valid for some procedures)
3. Check if turns are too gradual (< 10° track change)

### Wrong turn direction

The tool tests both directions automatically. If output seems wrong:
1. Check approach chart for intended turn direction
2. Verify entry track calculation is correct
3. May need manual adjustment for unusual procedures

## Support Files

The tool includes comprehensive error checking and helpful output:
- Waypoint verification before processing
- Clear error messages for missing data
- Summary of detected arcs with key parameters
- Automatic file naming with approach details

## Future Enhancements

Potential additions:
- Support for holding patterns
- DME arc definitions
- Visual preview of generated procedures
- Batch processing of multiple approaches
- Configuration file for custom test radii

## Credits

**Author**: Joel Lavoie - VATCAN CZQM vACC  
**Version**: 1.0  
**Date**: November 2024  
**Based on**: Analysis of CYHZ and CYFC RNAV approaches

## References

- TopSky Developer Guide v2.5 (COORD_AF syntax, pages 46-47)
- FAA RNAV Procedure Design Standards
- ICAO PBN Manual (Doc 9613)

---

For questions or issues, contact Joel Lavoie through VATCAN channels.
