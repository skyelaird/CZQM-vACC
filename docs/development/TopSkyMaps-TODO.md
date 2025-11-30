# TopSkyMaps.txt Reorganization - TODO

## Project Status: 📋 PLANNED - Not Started

**Decision Date:** 2025-11-29  
**Priority:** Medium (Quality of Life improvement)  
**Estimated Effort:** 2-3 hours (includes testing)  
**Risk Level:** Medium (fully reversible via Git)

---

## Why This Matters

Current file is 23,798 lines with **illogical organization**:
- Airspace boundaries buried at line 2033 (should be near top!)
- Airports scattered randomly (not alphabetical)
- CYHZ procedures split across multiple distant sections
- Hard for new team members to navigate

**Goal:** Professional, maintainable structure that matches ATC workflow

---

## Prerequisites

- [x] Current file analyzed (done 2025-11-29)
- [x] Reorganization plan created (see TopSkyMaps-Final-Plan.md)
- [ ] Create backup branch in Git
- [ ] Build reorganization script
- [ ] Test in non-production EuroScope environment

---

## Proposed New Structure

### Section 1: Configuration & Setup
- Map overrides
- Symbol definitions  
- Color definitions (already excellent!)

### Section 2: Airspace Structure (FIR Level)
- FIR boundaries (CZQM/CZQX/neighbors)
- Sectorization & delegation layers (10-14)
- TCU/TCA boundaries
- **MOVED FROM:** Currently buried at line 2000+

### Section 3: Major Airports (Full Procedures)
**CYHZ - Halifax Stanfield (Primary)**
- Feeds (distant transitions into STARs)
- STARs
- Approaches (grouped by runway: all ILS/RNAV-Y/RNAV-Z together)
- Holds

**CYYT - St. John's (Secondary)**
- STARs
- Approaches (grouped by runway)

### Section 4: Other Airports (Basic Procedures)
**Alphabetical order:**
- CYFC - Fredericton
- CYQM - Moncton
- CYYR - Goose Bay
- CYSJ - Saint John

Each airport: Approaches grouped by runway

### Section 5: Navigation & Geographic Features
- Waypoints
- Coastlines
- Political boundaries

### Section 6: Generation Metadata
- RF arc generation notes
- Data sources
- Validation timestamps

---

## Implementation Plan

### Phase 1: Preparation (30 min)
- [ ] Create Git branch: `feature/topskymaps-reorganization`
- [ ] Commit current state as checkpoint
- [ ] Build Python reorganization script
- [ ] Script features:
  - Parse current file structure
  - Extract sections intelligently
  - Reorder into new structure
  - Validate data preservation (checksum)
  - Generate table of contents with line numbers
  - Clean formatting (max 2 blank lines, consistent headers)

### Phase 2: Reorganization (15 min)
- [ ] Run script: `python reorganize_topskymaps.py`
- [ ] Script outputs:
  - `TopSkyMaps_v1.3.0.txt` (new organized file)
  - `TopSkyMaps_v1.2.1_BACKUP.txt` (backup)
  - `TopSkyMaps_DIFF.txt` (review changes)
  - `reorganization_report.txt` (validation stats)

### Phase 3: Review (15 min)
- [ ] Review diff file
- [ ] Verify COORD counts match (before: X, after: X)
- [ ] Verify ACTIVE counts match
- [ ] Check table of contents line numbers accurate
- [ ] Spot-check section organization

### Phase 4: Testing (45-60 min)
- [ ] Load `TopSkyMaps_v1.3.0.txt` in test EuroScope
- [ ] Verify each airport section:
  - [ ] CYHZ procedures display correctly
  - [ ] CYYT procedures display correctly
  - [ ] CYFC procedures display correctly
  - [ ] CYQM procedures display correctly
  - [ ] CYSJ procedures display correctly
  - [ ] CYYR procedures display correctly
- [ ] Test airspace layers:
  - [ ] Layer 10 (Class G) activates properly
  - [ ] Layer 11 (Delegated) activates properly
  - [ ] Layer 12 (Internal FIR) activates properly
  - [ ] Layer 13 (Cold neighbors) displays
  - [ ] Layer 14 (Hot neighbors) activates
- [ ] Test with online positions:
  - [ ] Log in as CYHZ_APP - verify local procedures visible
  - [ ] Check delegation layers respond to other positions
  - [ ] Verify colors display correctly
- [ ] Test RNAV-Y RF arcs render correctly

### Phase 5: Deployment (15 min)
- [ ] If all tests pass:
  - [ ] Replace original file with v1.3.0
  - [ ] Update version header to v1.3.0
  - [ ] Commit: "v1.3.0 - Major reorganization for maintainability"
  - [ ] Merge to main branch
  - [ ] Tag release: `TopSky-Data-v2024.12` (if releasing)
- [ ] If tests fail:
  - [ ] Revert to backup
  - [ ] Document issues
  - [ ] Adjust script
  - [ ] Retry

---

## Success Criteria

✅ **All coordinate data preserved** (verified by count)  
✅ **All ACTIVE statements preserved**  
✅ **File loads without errors in EuroScope**  
✅ **Procedures display correctly**  
✅ **Airspace layers activate properly**  
✅ **New team member can find procedures in <1 minute**  

---

## Rollback Plan

If something goes wrong:
1. `git checkout TopSkyMaps_v1.2.1_BACKUP.txt`
2. Restore as `TopSkyMaps.txt`
3. Commit: "Rollback reorganization - issues found"
4. No harm done!

---

## Supporting Documents

📄 **Analysis:** `TopSkyMaps-Cleanup-Plan.md`  
📄 **Strategy:** `TopSkyMaps-Reorganization-Plan.md`  
📄 **Final Plan:** `TopSkyMaps-Final-Plan.md`  

All saved in: `D:\GitHub\CZQM-vACC\docs\development\` (recommended)

---

## Future Enhancements (Post-Reorganization)

Once structure is solid, consider:
- [ ] Add holds for other major airports (CYYT, CYQM)
- [ ] Document each RNAV-Y approach with generation metadata
- [ ] Create quick reference comments at top of each runway section
- [ ] Add "last updated" timestamps to each airport section
- [ ] Consider splitting into multiple files if it grows beyond 30K lines

---

## Notes

- **Current file location:** `D:\GitHub\CZQM-vACC\TopSky\source\TS_Beta\plug-ins\TopSky2.5\TopSkyMaps.txt`
- **Single source of truth:** Only this file (orphan copies deleted)
- **File size:** 1.4 MB, 23,798 lines
- **Most complex airport:** CYHZ (feeds, STARs, 4 runways with RF arcs, holds)
- **Format:** TopSky plugin map definition syntax
- **Critical:** No data loss acceptable - all COORDs must transfer intact

---

## When to Do This

**Good times:**
- Off-season / quiet period
- After major event (e.g., after Cross The Pond)
- When adding new procedures (do reorg first, then add)

**Bad times:**
- Week before major event
- During active controller training
- When urgent bug fixes needed

---

## Contact

Questions or ready to execute?  
→ Ask Joel or Claude to build the script! 🚀

---

**Status Updated:** 2025-11-29  
**Next Review:** When ready to tackle (no rush!)
