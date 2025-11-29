# Repository Reorganization Instructions

## Already Done:
✅ RunwayAdvisor/ created and populated  
✅ README.md updated with product table  
✅ .gitignore created  
✅ docs/ folder created  

## Understanding the Structure

**EuroScope setup:**
```
AppData/Roaming/EuroScope/
├── CZQM TopSky TEST.prf    ← Entry point (loads everything)
├── TS_Beta/                 ← Our TopSky package
│   ├── ASR/                 ← Radar screen files
│   ├── plug-ins/            ← TopSky, GRP, MAESTRO, etc.
│   ├── Settings/            ← Position-specific settings
│   └── sounds/              ← Audio files
└── CZQQ/                    ← Sector files (VATCAN-provided, separate)
```

**For releases:**
- **TopSky Complete** = .prf file + entire TS_Beta folder (zipped)
- **TopSky Data Update** = just the updated .txt files from plug-ins/TopSky2.5/
- **Ground Radar Plugin** = plug-ins/GroundRadarPlugin_1.6b4/ folder (zipped)

## Simplified Repo Structure

```
CZQM-vACC/
├── README.md
├── .gitignore
├── RunwayAdvisor/           # Web tool (GitHub Pages)
├── TopSky/
│   ├── source/              # Keep as-is - this IS TS_Beta
│   │   └── TS_Beta/         # The actual package
│   └── Tools/               # RF arc generator (from PYTHON/)
├── GroundRadar/             # GRP extracted for standalone release
├── docs/
│   ├── references/          # PDFs, manuals
│   └── development/         # Claude Work files
└── dev/
    └── test-sector-files/   # Test packages
```

## Manual Steps

### 1. Create folders:
```
GroundRadar/
TopSky/Tools/rf-arc-generator/
docs/references/
docs/development/
dev/test-sector-files/
```

### 2. Copy/Move content:

**Ground Radar (for standalone release):**
- Copy `TopSky/source/TS_Beta/plug-ins/GroundRadarPlugin_1.6b4/*` → `GroundRadar/`

**RF Arc Generator:**
- Move `TopSky/PYTHON/*` → `TopSky/Tools/rf-arc-generator/`

**Documentation:**
- Move `TopSky/References/*` → `docs/references/`
- Move `TopSky/Claude Work/*` → `docs/development/`

**Test files:**
- Move `TestSectorFiles/*` → `dev/test-sector-files/`

### 3. Delete old/empty folders:
- CZQMRunwayAdvisor/ (empty, replaced by RunwayAdvisor/)
- TopSky/PYTHON/ (moved to Tools/)
- TopSky/References/ (moved to docs/)
- TopSky/Claude Work/ (moved to docs/)
- TopSky/Docs/ (duplicate)
- TopSky/nppBackup/ (ignored by .gitignore anyway)
- TopSky/Test data/ (if not needed)
- TestSectorFiles/ (moved to dev/)

### 4. Git commands:
```bash
git add -A
git commit -m "Reorganize repository structure"
git push
```

### 5. On GitHub:
- Delete TestAIRAC2512 release (Releases page)
- Delete TestAIRAC2512 tag (Tags page)
- Enable GitHub Pages: Settings → Pages → main branch, / (root)

### 6. Delete these instruction files when done:
- reorganize.bat
- REORGANIZE_INSTRUCTIONS.md

---

## Creating Releases

### TopSky Complete (new controllers)
1. Zip together:
   - `CZQM TopSky TEST.prf` (rename to something like `CZQM-TopSky.prf`)
   - Entire `TS_Beta/` folder
2. Create release: `TopSky-Complete-v1.0.0`
3. Upload zip as release asset

### TopSky Data Update (existing users)
1. Zip the updated files from `TS_Beta/plug-ins/TopSky2.5/`:
   - TopSkyMaps.txt
   - TopSkySettings.txt
   - TopSkyAirspace.txt (if changed)
   - Any other changed .txt files
2. Create release: `TopSky-Data-v2024.11`
3. Upload zip as release asset

### Ground Radar Plugin
1. Zip the `GroundRadar/` folder contents
2. Create release: `GRP-CYHZ-v1.0.0`
3. Upload zip as release asset

---

## After Reorganization

Your repo will be clean and releases will be straightforward:
- Source files stay where EuroScope expects them
- Releases are just zips of the appropriate content
- Users download from Releases page, not by cloning the repo
