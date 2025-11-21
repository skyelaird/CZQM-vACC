# ACTIVE Syntax Quick Reference & Validator

## Core Syntax (TopSky Developer Guide p.21)

```
ACTIVE:TYPE:Field1:Field2:Field3:Field4
```

**CRITICAL:** Must have exactly 4 fields after the TYPE specifier!

---

## Type: ID (Position-based activation)

```
ACTIVE:ID:YourIdList:NotYourIdList:OnlineIdList:NotOnlineIdList
```

### Examples

**Always visible (no position requirements):**
```
ACTIVE:ID:*:*:*:*              ✅ All fields disregarded
ACTIVE:ID::::                   ✅ All fields empty
```

**Show when YOU are controlling HZT:**
```
ACTIVE:ID:HZT:*:*:*            ✅ You=HZT, others disregarded
```

**Show when HZT is online (regardless of who you are):**
```
ACTIVE:ID:*:*:HZT:*            ✅ HZT must be online
```

**Show when YOU are HZT OR YRT:**
```
ACTIVE:ID:HZT,YRT:*:*:*        ✅ Comma-separated list
```

**Show when HZT online BUT you're NOT controlling it:**
```
ACTIVE:ID:*:HZT:HZT:*          ✅ You≠HZT, HZT=online
```

**Show when BOTH QM and QX are online:**
```
ACTIVE:ID:*:*:QM,QX:*          ✅ Both must be online
```

**Complex: You=HZT AND QM is online:**
```
ACTIVE:ID:HZT:*:QM:*           ✅ You=HZT, QM=online
```

---

## Type: CALLSIGN (Callsign-based)

```
ACTIVE:CALLSIGN:YourCallsignList:NotYourCallsignList:OnlineCallsignList:NotOnlineCallsignList
```

Same 4-field structure, but uses full callsigns instead of position IDs.

**Example:**
```
ACTIVE:CALLSIGN:CZQM_CTR:*:*:*
```

---

## Type: RWY (Runway-based)

```
ACTIVE:RWY:ARR:ArrRwyList:DEP:DepRwyList
```

**Example - Show when CYHZ23 active for arrivals:**
```
ACTIVE:RWY:ARR:CYHZ23:DEP:*
```

**Example - Multiple runways:**
```
ACTIVE:RWY:ARR:CYHZ23,CYHZ32:DEP:*
```

---

## Type: 1 (Auto-activate on load)

```
ACTIVE:1
```

No additional fields needed. Map activates when plugin loads.
**Cannot be combined with other ACTIVE lines.**

---

## AND_ACTIVE (Multiple Conditions)

To require MULTIPLE conditions to be true simultaneously:

```
ACTIVE:ID:QM:*:*:*
AND_ACTIVE:ID:*:*:QX:*
```

This means: Show when YOU are QM **AND** QX is online.

**Both conditions must be true.**

---

## Common Mistakes

### ❌ Missing Fields
```
ACTIVE:ID:HZT:                 ❌ Only 1 field (needs 4!)
ACTIVE:ID:HZT::                ❌ Only 2 fields (needs 4!)
ACTIVE:ID:HZT:::               ❌ Only 3 fields (needs 4!)
```

### ✅ Correct Field Count
```
ACTIVE:ID:HZT:*:*:*            ✅ All 4 fields present
```

---

### ❌ Wrong Map Name Position
```
ACTIVE:CHARLO_CLASS_G:ID:*:*:*:*    ❌ Map name should not be in ACTIVE line!
```

### ✅ Map Name in MAP Line Only
```
MAP:10:CHARLO_CLASS_G          ✅ Map name here
ACTIVE:ID:*:*:*:*              ✅ No map name in ACTIVE
```

---

### ❌ Using Empty Without Colons
```
ACTIVE:ID                      ❌ Missing all 4 field separators
```

### ✅ Empty Fields Need Colons
```
ACTIVE:ID::::                  ✅ 4 colons = 4 empty fields
```

---

## Field Meanings

### Field 1: YourIdList
**"Show this map when I am controlling..."**
- `HZT` = Show when YOU are Halifax Tower
- `HZT,QMT` = Show when YOU are Halifax Tower OR Moncton Tower
- `*` = Disregard (show regardless of who you are)
- `` (empty) = Same as `*`

### Field 2: NotYourIdList
**"Do NOT show this map when I am controlling..."**
- `HZT` = Hide when YOU are Halifax Tower
- `*` = Disregard
- `` (empty) = Same as `*`

### Field 3: OnlineIdList
**"Show this map only when these positions ARE online..."**
- `QM` = QM must be online
- `QM,QX` = BOTH QM and QX must be online
- `*` = Disregard (show regardless)
- `` (empty) = Same as `*`

### Field 4: NotOnlineIdList
**"Show this map only when these positions are NOT online..."**
- `QM` = QM must NOT be online
- `*` = Disregard
- `` (empty) = Same as `*`

---

## Our Use Cases - CENTER CONTROLLER PERSPECTIVE

**Operational Context:** These boundaries provide situational awareness for center controllers (QM/QX) by showing what areas are delegated to subordinate positions.

### Class G Boundaries (Always Visible)
```
MAP:10:CHARLO_CLASS_G
ACTIVE:1
```
Always visible - no position requirements.

### TWR Boundaries (Delegation Awareness)
```
MAP:12:CYHZ_TWR
ACTIVE:ID:*:*:HZT:*
```
Show when HZT is **online** (anyone controlling it).  
**Why:** When controlling QM, you see "Halifax Tower is active, that area is delegated."

### APP Boundaries (Delegation Awareness)
```
MAP:12:CYHZ_APP
ACTIVE:ID:*:*:HZA:*
```
Show when HZA is **online** (anyone controlling it).  
**Why:** When controlling QM, you see "Halifax Approach is active, that area is delegated."

### Terminal Circles (Delegation Awareness)
```
MAP:12:CYQX_TERMINAL
ACTIVE:ID:*:*:QXA:*
```
Show when QXA is **online** (anyone controlling it).  
**Why:** When controlling QM, you see "Gander Approach is active, that terminal is delegated."

### Sector Boundaries (Delegation Awareness)
```
MAP:12:CB_SECTOR
ACTIVE:ID:*:*:CB:*
```
Show when CB is **online** (anyone controlling it).  
**Why:** When controlling QM, you see "Cape Breton sector is staffed, I don't control that."

---

## IMPORTANT: Field Selection Logic

**Field 1 (YourIdList) = "When I am..."**
- Use when boundary should show based on YOUR position
- Example: "Show MY boundary when I'm controlling APP"

**Field 3 (OnlineIdList) = "When they are..."**  
- Use when boundary should show based on OTHER positions online
- Example: "Show TWR boundary when TWR position is online"

**For CENTER awareness displays:** Use Field 3 (OnlineIdList)  
**For position-specific displays:** Use Field 1 (YourIdList) - TBD for APP/TWR modes

### Cold Neighbor (Always Visible)
```
MAP:11:CZUL_BOUNDARY
ACTIVE:ID:*:*:*:*
```
Always visible in light grey.

### Hot Neighbor (When Neighbor Online)
```
MAP:13:CZUL_BOUNDARY_HOT
ACTIVE:ID:*:*:UL:*
```
Show when UL (Montreal) position is online.

### QM/QX Split (Both Online)
```
MAP:14:QM_QX_BOUNDARY
ACTIVE:ID:*:*:QM,QX:*
```
Show when BOTH QM and QX are online.

Or with AND_ACTIVE:
```
ACTIVE:ID:*:*:QM:*
AND_ACTIVE:ID:*:*:QX:*
```

---

## Validation Checklist

When writing ACTIVE lines:

- [ ] **Field count:** Exactly 4 fields after TYPE?
- [ ] **Map name:** Only in MAP line, not in ACTIVE?
- [ ] **Colons:** Right number of colons for fields?
- [ ] **Logic:** Does the activation logic make sense?
- [ ] **Wildcards:** Using `*` where appropriate?
- [ ] **Lists:** Comma-separated without spaces?

---

## Quick Syntax Validator

**Count the colons after the type specifier:**

```
ACTIVE:ID:*:*:*:*
        └─┴─┴─┴─ MUST have 4 colons = 4 fields ✅
```

```
ACTIVE:ID:HZT::
        └─┴── Only 2 colons = WRONG ❌
```

**Formula:** `ACTIVE:TYPE:` + **4 fields separated by 3 colons** = **4 colons total after TYPE**

---

## Testing Your ACTIVE Lines

In EuroScope, check:
1. **Load errors** - Message tab shows syntax errors
2. **Activation test** - Log on as position, does map appear?
3. **Deactivation test** - Log off, does map disappear?
4. **Conflict test** - Do multiple maps conflict?

---

## References

- TopSky Developer Guide, page 21 (Areas file)
- TopSky Developer Guide, page 37 (Maps file)
- EuroScope Users Manual, AIRSPACE section

---

**When in doubt: COUNT THE COLONS!** ☝️
