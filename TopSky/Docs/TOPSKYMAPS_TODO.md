# TopSkyMaps.txt Build Project - CZQM/CZQX vACC

## Project Goal
Build activation-aware TopSkyMaps.txt for dynamic airspace boundary display based on position staffing.

## Design Principles

### Color Philosophy (Shades of Grey)
```
ACTIVE_SECTOR_BASE       = RGB 80 80 80    // Darkest - "Mine, controlled"
UNCONTROLLED_STATIC      = RGB 95 95 95    // Slightly lighter - "Class G, no service"
COLD_NEIGHBOR            = RGB 110 110 110  // Light grey - "Exists but unstaffed"
HOT_NEIGHBOR             = RGB 140 140 140  // Brighter - "LIVE neighbor, coordinate!"
INTERNAL_DELEGATION      = RGB 100 100 100  // Medium - "Carved out from my airspace"
CZQM_CZQX_SPLIT         = RGB 105 105 105  // When both centers online
```

**Key Insight:** Uncontrolled/delegated areas must be LIGHTER than base to convey "you DON'T control this"

### Layer Strategy (Non-Translucent)
Higher layers completely overwrite lower layers - no transparency!

- **Layer 0:** Static uncontrolled (CHARLO-NO-CONTROL, northern Labrador Class G, St. Anthony Class G)
- **Layer 1:** Cold neighbor boundaries (CZUL/ZBW/BIRD/CZEG - always visible, light grey)
- **Layer 2:** Internal delegations (APP/TWR/DG/CB when positions online)
- **Layer 3:** Hot neighbors (same geometry as Layer 1, overwrites when neighbor online)
- **Layer 4:** CZQM/CZQX split (show only when BOTH online)

### Activation Logic Patterns

**Internal Delegation (Layer 2):**
```
ACTIVE:ID:HZA:HZT:QMA:...
```
Show boundary when that position logs on.

**Cold Neighbor Always Visible (Layer 1):**
```
ACTIVE:ID::
```
No online requirement - always shows in light grey.

**Hot Neighbor State Change (Layer 3):**
```
ACTIVE:ID::UL,ZBW,BIRD
```
Overwrites Layer 1 with brighter color when neighbor online.

**CZQM/CZQX Split (Layer 4):**
```
ACTIVE:ID:QM,QX::
AND_ACTIVE:ID
```
Show ONLY when both centers online.

## Boundaries to Build

### ✅ COMPLETED
- [x] Understanding ESE structure (POSITIONS → SECTORs → BORDER → SECTORLINEs)
- [x] Understanding TopSky activation syntax
- [x] Color and layer strategy
- [x] Decoding LO charts (white=controlled, green=Class G)

### 🔨 IN PROGRESS - Class G Uncontrolled Areas (Layer 0)

#### 1. CHARLO-NO-CONTROL (Northern NB)
- **Status:** ESE sector exists: `CZQM·CHARLO-NO-CONTROL·000·120`
- **Action:** Extract SECTORLINE coordinates from BORDER definition
- **Color:** UNCONTROLLED_STATIC (slightly lighter than base)
- **Layer:** 0
- **Activation:** `ACTIVE:ID::` (always visible)

#### 2. Northern Labrador Class G
- **Status:** NOT in ESE - needs to be built from DAH
- **Legal Ref:** DAH Section 3.7.4-6 (CAE Number Thirteen) + 87 NM CYYR exclusion
- **Description:** Beyond CYYR MTCA (87 NM) + airways YYR-DENSO, YYR-YWK
- **Color:** UNCONTROLLED_STATIC
- **Layer:** 0
- **Action:** Build polygon from DAH coordinates

#### 3. St. Anthony Class G (Northern Newfoundland)
- **Status:** NOT in ESE - needs to be built
- **Legal Ref:** DAH Section 3.7.6-13/14 (YAY 5 NM control zone only)
- **Description:** Area around YAY outside the 5 NM control zone
- **Color:** UNCONTROLLED_STATIC
- **Layer:** 0
- **Action:** Build polygon from visual reference + DAH

### 📋 TODO - Internal Delegations (Layer 2)

#### CZQM FIR Positions
- [ ] **CZQM_DG_CTR** (Digby) - Profile ID: DG
  - ESE Sector: `CZQM·DIGBY-SECTOR·000·285`
  - Extract BORDER sectorlines
  
- [ ] **CZQM_CB_CTR** (Cape Breton) - Profile ID: CB
  - ESE Sectors: `CZQM·CAPE-BRETON-SECTOR` and `CZQM·CAPE-BRETON-N-SECTOR`
  - Extract BORDER sectorlines

- [ ] **APP Areas:**
  - CYHZ_APP (HZA) + CYHZ_FI_APP (HA2)
  - CYQM_APP (QMA)
  - CYSJ_APP (SJA)
  - CYZX_APP (ZXA)
  - CZQM_L_APP (QML) - "Mega" terminal
  
- [ ] **TWR Areas:** 7 NM circles (except where noted)
  - CYFC_TWR (FCT) - 7 NM
  - CYHZ_TWR (HZT) - 7 NM
  - CYQM_TWR (QMT) - 7 NM
  - CYZX_TWR (ZXT) - 7 NM

#### CZQX FIR Positions
- [ ] **APP Areas:**
  - CYQX_APP (QXA)
  - CYYR_APP (YRA) - 87 NM MTCA!
  - CYYT_APP (YTA)
  - LFVP_APP (VA)
  
- [ ] **TWR Areas:** Varying radii!
  - CYQX_TWR (QXT) - 7 NM
  - CYYR_TWR (YRT) - 10 NM (larger!)
  - CYYT_TWR (YTT) - 7 NM
  - LFVP_TWR (VT) - 5 NM (smaller!)

### 📋 TODO - Neighbor Boundaries (Layers 1 & 3)

#### Cold State (Layer 1) - Always Visible
- [ ] **CZUL (Montreal)** - especially shelf areas
  - Gulf of St. Lawrence delegation
  - Profile IDs: BJ, BZ, EW, HV, JU, KR, LE, MC, NK, SV
  
- [ ] **ZBW (Boston Center)** - southern boundary
  - Profile IDs: (need to determine)
  
- [ ] **CZEG (Edmonton)** - Sable Island extension
  - Profile IDs: (need to determine)
  
- [ ] **BIRD (Reykjavik)** - northeast
  - Profile IDs: (need to determine)
  
- [ ] **CZQXO (Gander Oceanic)** - east
  - Profile IDs: (need to determine)
  
- [ ] **ZWY (New York Oceanic)** - south
  - Profile IDs: (need to determine)

#### Hot State (Layer 3) - Overwrites Layer 1 When Online
Same geometry as Layer 1, but brighter color and different activation logic.

### 📋 TODO - CZQM/CZQX Internal Boundary (Layer 4)

- [ ] **Low-level boundary** (SFC-FL180) - west of Newfoundland
- [ ] **Mid-level boundary** (FL180-FL290) - different from low-level!
- [ ] **High-level boundary** (FL290-FL600) - through western Newfoundland
- **Activation:** Show ONLY when both QM and QX online
- **Logic:** `ACTIVE:ID:QM,QX::` + `AND_ACTIVE:ID`

## Technical Reference

### Key Files
- ESE: `/mnt/project/CZQQ-DO-NOT-USE_20251107023304-251101-0017.ese`
- DAH: `/mnt/project/DAH_en_20250807.pdf`
- Charts: LO_07 (Goose area), LO_08 (North)
- Airspace Manual: `/mnt/project/CZQM FIR Centre Airspace Manual v2 draft 3.pdf`

### ESE Structure
```
[POSITIONS] → Profile IDs (e.g., QM, HZA, DG)
[SECTORS] → SECTOR:FIR·Name·Alt → OWNER:Profiles → BORDER:SectorlineIDs
[SECTORLINE:ID] → Coordinates
```

### TopSky Activation Syntax
```
MAP:LayerNumber:Name
COLOR:FunctionName
ACTIVE:ID:YourIdList:NotYourIdList:OnlineIdList:NotOnlineIdList
AND_ACTIVE:ID
COORDPOLY:
  Lat:Lon
  ...
END
```

## Current Status
**Phase:** Planning complete, ready to execute coordinate extraction and file building
**Next Actions:**
1. Extract CHARLO-NO-CONTROL SECTORLINE coordinates from ESE
2. Build northern Labrador Class G polygon from DAH
3. Build St. Anthony Class G polygon
4. Begin internal delegation extraction

## Notes
- Subtlety is key - boundaries should inform, not shout
- Aircraft tags are most important - maps are supporting info
- Controllers know the areas, they just need to relate them to aircraft
- State visualization: same geometry, different colors = operational state change
