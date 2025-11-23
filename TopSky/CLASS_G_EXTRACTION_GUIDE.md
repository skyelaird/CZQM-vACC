# CLASS G AIRSPACE IDENTIFICATION & EXTRACTION GUIDE
## TopSkyMaps.txt Build - CZQM/CZQX vACC

**Document Version:** 1.0  
**Created:** 2025-11-22  
**Purpose:** Guide for identifying and extracting Class G airspace coordinates from LO charts and DAH

---

## OVERVIEW

This guide provides methodology for identifying uncontrolled (Class G) airspace above 2200' in the Gander (CZQX) and Moncton (CZQM) FIRs, then creating TopSky polygon definitions.

**Target Areas:**
1. Northern Labrador Class G - Beyond CYYR 87 NM MTCA  
2. St. Anthony Class G - Beyond CYAY 5 NM Control Zone

**Current Status:**
- ✅ CHARLO Class G - COMPLETED (67 coordinate points, line 1585-1680)
- ⏳ Northern Labrador - PENDING coordinate extraction
- ⏳ St. Anthony - PENDING coordinate extraction

---

## Key Information

### Northern Labrador Class G
- **Legal Ref:** NAV CANADA DAH Section 3.7.4-6 (CAE Number Thirteen)
- **Description:** Beyond CYYR 87 NM MTCA + airways YYR-DENSO, YYR-YWK
- **Chart:** LO_07 (shows green hatched area beyond 87 NM circle)
- **Altitude:** SFC-12,500' MSL

### St. Anthony Class G
- **Legal Ref:** NAV CANADA DAH Section 3.7.6-13/14
- **Description:** Beyond CYAY 5 NM control zone
- **Chart:** LO_08 (shows green hatched area around St. Anthony)
- **Altitude:** SFC-12,500' MSL

---

## Next Steps

1. Open LO_07 and LO_08 charts
2. Identify green hatched Class G boundaries
3. Extract coordinates using methods in CLASS_G_POLYGONS_ADDITION.txt
4. Replace template coordinates with actual chart-derived positions
5. Insert completed polygons into TopSkyMaps.txt after CHARLO_CLASS_G
6. Test load in EuroScope
7. Update version to 1.3.0

See CLASS_G_POLYGONS_ADDITION.txt for detailed templates and instructions.

---

For full extraction methodology, coordinate conversion rules, and troubleshooting, see the complete guide on Claude's computer at /home/claude/CLASS_G_EXTRACTION_GUIDE.md
