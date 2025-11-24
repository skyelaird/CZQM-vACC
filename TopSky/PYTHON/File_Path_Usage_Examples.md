# TopSky RF Arc Generator - File Path Usage Examples

## Scenario 1: .sct File in Current Directory

### If your terminal is already in the directory with the .sct file:

```bash
cd D:\GitHub\CZQM-vACC\TopSky\References
python3 topsky_rf_generator.py
```

**The tool will automatically detect and list .sct files:**
```
================================================================================
TopSky RF Arc Generator
================================================================================

Found .sct file(s) in current directory:
  - CZQQ-DO-NOT-USE_20251107023304-251101-0017.sct

Enter .sct filename or full path (or 'quit'):
>
```

**Just type the filename:**
```
> CZQQ-DO-NOT-USE_20251107023304-251101-0017.sct
```

**Or even simpler, if there's only one .sct file, just:**
```
> CZQQ-DO-NOT-USE_20251107023304-251101-0017.sct
Loading waypoints from CZQQ-DO-NOT-USE_20251107023304-251101-0017.sct...
Loaded 4700 waypoints
```

---

## Scenario 2: .sct File in Different Directory

### If you run from anywhere else:

```bash
cd D:\GitHub\CZQM-vACC\TopSky\
python3 topsky_rf_generator.py
```

**Provide full path:**
```
Enter full path to .sct file (or 'quit'):
> D:\GitHub\CZQM-vACC\TopSky\References\CZQQ-DO-NOT-USE_20251107023304-251101-0017.sct
```

**Or relative path from current location:**
```
> References\CZQQ-DO-NOT-USE_20251107023304-251101-0017.sct
```

---

## Scenario 3: Pre-load .sct File at Startup

### Best for efficiency:

```bash
cd D:\GitHub\CZQM-vACC\TopSky\References
python3 topsky_rf_generator.py CZQQ-DO-NOT-USE_20251107023304-251101-0017.sct
```

**Or with full path from anywhere:**
```bash
python3 topsky_rf_generator.py "D:\GitHub\CZQM-vACC\TopSky\References\CZQQ-DO-NOT-USE_20251107023304-251101-0017.sct"
```

The tool will skip the file prompt and go straight to approach entry!

---

## File Path Tips

### Windows Paths
- **Backslashes**: `D:\GitHub\CZQM-vACC\TopSky\References\file.sct`
- **Forward slashes**: `D:/GitHub/CZQM-vACC/TopSky/References/file.sct` (also works!)
- **Quotes**: Use if path has spaces: `"D:\My Files\CZQM\file.sct"`

### Linux/Mac Paths
- **Absolute**: `/home/user/vatcan/czqm/file.sct`
- **Relative**: `./References/file.sct` or `../file.sct`
- **Home**: `~/vatcan/czqm/file.sct`

### Current Directory Shortcuts
- **Same directory**: Just the filename: `file.sct`
- **Dot notation**: `./file.sct`
- **Windows current**: `.\file.sct`

---

## Recommended Workflow

### Option A: Work from References Directory (Easiest)
```bash
# Navigate to where your .sct file is
cd D:\GitHub\CZQM-vACC\TopSky\References

# Run tool - it will find and list .sct files
python3 topsky_rf_generator.py

# Just type the filename when prompted
> CZQQ-DO-NOT-USE_20251107023304-251101-0017.sct
```

### Option B: Pre-load and Process Multiple Approaches
```bash
# Load .sct once, then process many approaches
cd D:\GitHub\CZQM-vACC\TopSky\References
python3 topsky_rf_generator.py CZQQ-DO-NOT-USE_20251107023304-251101-0017.sct

# Now just enter approach data:
Airport: CYHZ
Runway: 05
Transitions...

# Generate another
Airport: CYFC
Runway: 09
Transitions...

# etc...
```

### Option C: Keep Tool with Your Data
```bash
# Copy the tool to your working directory
cp topsky_rf_generator.py D:\GitHub\CZQM-vACC\TopSky\References\

# Run from there
cd D:\GitHub\CZQM-vACC\TopSky\References
python3 topsky_rf_generator.py
```

---

## Auto-Detection Feature

The updated tool now:

✓ **Scans current directory** for .sct files on startup  
✓ **Lists available files** if any are found  
✓ **Accepts just filename** if file is in current directory  
✓ **Accepts full/relative paths** from anywhere  
✓ **Handles quoted paths** with spaces  

---

## Troubleshooting

### "File not found" error

**Problem**: Tool can't locate your .sct file

**Solutions**:
1. Check spelling (case-sensitive on Linux/Mac)
2. Use full path if relative path doesn't work
3. Verify file actually exists: `ls file.sct` (Linux/Mac) or `dir file.sct` (Windows)
4. Try with quotes if path has spaces

### Tool doesn't list .sct files in current directory

**Possible causes**:
- You're not in the right directory (use `pwd` or `cd` to check)
- .sct file has different extension (.SCT vs .sct)
- File is in subdirectory

**Solution**: Use full path or `cd` to correct directory

### Path with spaces doesn't work

**Solution**: Use quotes:
```
> "D:\My Documents\VATCAN\CZQM Files\file.sct"
```

---

## Quick Reference

| Situation | Command |
|-----------|---------|
| .sct in current dir | Just type filename |
| .sct in subdirectory | `References\file.sct` |
| .sct elsewhere | Full path |
| Pre-load at startup | `python3 tool.py file.sct` |
| Path with spaces | Use "quotes" |

---

## Examples

### Example 1: Simple (Current Directory)
```bash
$ cd /mnt/data/vatcan/czqm
$ ls *.sct
CZQQ.sct

$ python3 topsky_rf_generator.py
Found .sct file(s) in current directory:
  - CZQQ.sct
> CZQQ.sct
✓ Loaded 4700 waypoints
```

### Example 2: Full Path
```bash
$ python3 topsky_rf_generator.py
> D:\GitHub\CZQM-vACC\TopSky\References\CZQQ.sct
✓ Loaded 4700 waypoints
```

### Example 3: Pre-loaded
```bash
$ python3 topsky_rf_generator.py ./CZQQ.sct
Loading waypoints from ./CZQQ.sct...
Loaded 4700 waypoints

Generate new approach procedure (or 'quit' to exit)
Airport: _
```

---

Perfect! Now the tool is smart about file paths and makes it easy to work from your current directory.
