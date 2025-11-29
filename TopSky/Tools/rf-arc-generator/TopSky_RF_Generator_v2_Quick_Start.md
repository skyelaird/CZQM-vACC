# TopSky RF Arc Generator v2.0 - Quick Start

## 🎯 What's New in v2.0

✅ **Airport-directed turn logic** - Arcs always curve toward airport  
✅ **Smooth consecutive arcs** - Exit track chains to next entry track  
✅ **Single combined map** - All transitions in one MAP definition  
✅ **Fixed geometry** - Eliminates discontinuities and sharp angles  

---

## 🚀 Quick Start

```bash
python3 topsky_rf_generator.py
```

### Example Session

```
Found .sct file(s) in current directory:
  - CZQQ.sct

Enter .sct filename or full path (or 'quit'):
> CZQQ.sct
✓ Loaded 4700 waypoints

Airport code (e.g., CYFC): CYFC
Runway (e.g., 09): 09

Airport coordinates (needed for turn direction detection)
Airport latitude (e.g., N45.52.00.000): N045.52.00.000
Airport longitude (e.g., W066.32.00.000): W066.32.00.000

Enter transitions (one per line)
Transition 1: VESBI UKNUM URTIT VYSTA
Transition 2: ANERA URPUS VYSTA
Transition 3: [blank]

Analyzing transition: VESBI
  Found 2 RF arc(s):
    UKNUM → URTIT: R=2.50 NM, sweep=134.2°, dir=<, error=0.0001 NM
    URTIT → VYSTA: R=2.49 NM, sweep=45.8°, dir=<, error=0.0002 NM

Analyzing transition: ANERA
  Found 1 RF arc(s):
    URPUS → VYSTA: R=2.49 NM, sweep=48.8°, dir=>, error=0.0001 NM

✓ Saved to: CYFC_RNAV-Y-09_TopSkyMaps.txt
```

---

## 📋 Input Requirements

### 1. SCT File
- Can be in current directory (just filename) or full path
- Tool auto-detects .sct files in current directory
- Loads all waypoints from [FIXES] section

### 2. Airport Information
- **Code**: 4-letter ICAO (e.g., CYFC)
- **Runway**: Number only (e.g., 09)
- **Coordinates**: Sector file format (N045.52.00.000 W066.32.00.000)

**Finding Airport Coordinates:**
- Look in your .sct file under [AIRPORT] section
- Or use approximate center of airport
- Precision to nearest minute is sufficient

### 3. Transitions
- One per line
- Format: `IF_POINT waypoint1 waypoint2 ... FAP`
- Blank line when done
- All waypoints must exist in .sct file

---

## 📊 Output Format (v2.0 - Combined)

```
MAP:RNAV-Y-09                    ← Single map for all transitions
FOLDER:CYFC
ACTIVE:RWY:ARR:CYFC09:DEP:*
COLOR:TEXTLABEL
SYMBOL:FIX:ANERA                 ← All waypoints listed once
SYMBOL:FIX:UKNUM
SYMBOL:FIX:URPUS
SYMBOL:FIX:URTIT
SYMBOL:FIX:VESBI
SYMBOL:FIX:VYSTA
COLOR:RNPAR
; Transition: VESBI               ← Comments mark transitions
COORD:VESBI
COORD:UKNUM
COORD_AF:N045.52.59.571:W066.38.47.462:2.5:1.0:339.8:<:205.6
COORD:URTIT
COORD_AF:N045.52.59.186:W066.38.47.650:2.5:1.0:205.6:<:159.8
COORD:VYSTA

; Transition: ANERA
COORD:ANERA
COORD:URPUS
COORD_AF:N045.48.18.492:W066.36.19.419:2.5:1.0:290.9:>:339.8
COORD:VYSTA

COORDLINE                        ← Single COORDLINE at end
```

**Key Improvements:**
- Single MAP definition (not separate per transition)
- All SYMBOL:FIX declarations together
- Transitions separated by comments
- One COORDLINE at end

---

## 🔧 How It Works

### 1. Airport-Directed Turn Detection
```
Entry track: 249.81° (WSW)
Airport bearing: 19.85° (NNE)
Relative bearing: 130.04° (airport is LEFT of track)
→ Turn LEFT to curve toward airport
```

### 2. Arc Center Calculation
Using Transport Canada method:
- Center must be perpendicular to entry track
- Center must be equidistant from start and end fixes
- Binary search finds radius where both conditions are met

### 3. Consecutive Arc Chaining
```
Arc 1: UKNUM → URTIT
  Entry: 249.81° (from VESBI-UKNUM)
  Exit: 115.62° (tangent at URTIT)

Arc 2: URTIT → VYSTA
  Entry: 115.62° (from Arc 1 exit) ← SMOOTH!
  Exit: 69.82° (toward final)
```

**Result**: No discontinuities, smooth transitions!

---

## ⚠️ Troubleshooting

### "ERROR: Missing waypoints"
- Check spelling (case-sensitive)
- Verify waypoints exist in .sct file
- Use: `grep "WAYPOINT_NAME" yourfile.sct`

### "ERROR: Invalid coordinate format"
- Use sector file format: N045.52.00.000
- Include leading zeros: N045 not N45
- Use correct hemisphere: N/S for lat, E/W for lon

### Arcs look wrong in EuroScope
1. Verify airport coordinates are correct
2. Check if approach chart matches generated arcs
3. Ensure all waypoint coordinates are accurate
4. Review turn directions (should curve toward airport)

### Large radius or odd sweep angle
- Check if waypoints are in correct order
- Verify approach chart transition sequence
- Confirm airport coordinates are reasonable

---

## 📈 Quality Metrics

**Good Arc Indicators:**
- ✓ Error < 0.01 NM (excellent)
- ✓ Error < 0.1 NM (acceptable)
- ✓ Sweep angle 10-270° (reasonable)
- ✓ Radius 0.5-10 NM (typical RNAV)

**Warning Signs:**
- ⚠ Error > 0.5 NM (check waypoint coords)
- ⚠ Sweep > 270° (wrong turn direction?)
- ⚠ Radius > 20 NM (geometry issue)
- ⚠ Consecutive arcs with very different radii

---

## 🎓 Understanding the Output

### COORD_AF Syntax
```
COORD_AF:N045.52.59.571:W066.38.47.462:2.5:1.0:339.8:<:205.6
         ↓              ↓              ↓   ↓   ↓     ↓  ↓
         Arc center     Arc center     Rad Spc Start Dir End
         latitude       longitude      NM  deg deg   <>  deg
```

- **Arc center**: Calculated center fix location
- **Radius**: Distance from center to ending fix (NM)
- **Spacing**: Vertex radial spacing (1.0° recommended)
- **Start angle**: Bearing from center to initial fix
- **Direction**: `<` = CCW (left), `>` = CW (right)
- **End angle**: Bearing from center to ending fix

### Example Interpretation
```
COORD_AF:N045.52.59.571:W066.38.47.462:2.5:1.0:339.8:<:205.6
```
- Arc centered at N45°52'59.571" W66°38'47.462"
- Radius 2.5 NM from center
- Starts at 339.8° (NNW from center)
- Turns LEFT (counterclockwise)
- Ends at 205.6° (SSW from center)
- Sweep: 134.2° (from 339.8° CCW to 205.6°)

---

## 📂 File Locations

### Production Tool
- **topsky_rf_generator.py** - Main tool (v2.0)

### Documentation
- **VERSION_2.0_FIXES_APPLIED.md** - Detailed fix documentation
- **File_Path_Usage_Examples.md** - Path handling guide
- **TopSky_RF_Generator_Usage_Guide.md** - Full usage guide
- **TopSky_RF_Generator_Quick_Reference.md** - This file

### Example Outputs
- **CYFC_RNAV-Y-09_TopSkyMaps.txt** - Fixed, production-ready

---

## 🚦 Workflow

### Recommended Process

1. **Prepare**
   ```bash
   cd /your/topsky/directory
   # Have your .sct file here
   ```

2. **Run Tool**
   ```bash
   python3 topsky_rf_generator.py
   ```

3. **Enter Data**
   - SCT filename (if in current directory)
   - Airport code
   - Runway number
   - Airport coordinates
   - All transitions

4. **Review Output**
   - Check error values (< 0.01 NM ideal)
   - Verify turn directions make sense
   - Confirm radii are reasonable

5. **Test in EuroScope**
   - Copy output to TopSkyMaps.txt
   - Load in EuroScope
   - Verify smooth arc rendering
   - Check activation logic works

6. **Deploy**
   - Commit to repository
   - Notify controllers
   - Monitor for issues

---

## 💡 Pro Tips

1. **Current Directory**: Work from your References folder where .sct is located
2. **Batch Processing**: Load .sct once, generate multiple approaches
3. **Visual Comparison**: Keep approach charts handy to verify output
4. **Error Threshold**: Anything < 0.01 NM is effectively perfect
5. **Arc Centers**: Very close centers (< 1 NM apart) for consecutive arcs is normal

---

## 🔄 Version History

### v2.0 (November 24, 2024)
- ✅ Airport-directed turn logic
- ✅ Smooth consecutive arc chaining
- ✅ Single combined map output
- ✅ Fixed exit track calculation
- ✅ Enhanced error reporting

### v1.0 (November 23, 2024)
- ❌ Geometric turn detection (broken)
- ❌ Separate maps per transition
- ❌ Discontinuous arcs
- ❌ Wrong exit track formula

---

## 📞 Support

**Issues or Questions?**
- Check VERSION_2.0_FIXES_APPLIED.md for technical details
- Review Full Usage Guide for comprehensive documentation
- Test with known-good approaches first (CYFC, CYHZ)

**Contact**: Joel Lavoie - VATCAN CZQM vACC

---

**Version**: 2.0  
**Status**: Production Ready ✅  
**Last Updated**: November 24, 2024  
**Key Insight**: "The arc will always be towards the airport"
