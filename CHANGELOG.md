# Changelog

All notable changes to CZQM/CZQX vACC controller resources will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html) for software releases,
and AIRAC dating (YYYY.MM) for data updates.

---

## [Unreleased]

### MAESTRO — Arrival Management System
- Node.js server implementation (v1.0.0-alpha)
- Master/Slave coordination system
- REST API for EuroScope plugin integration
- Comprehensive training materials
- Deployment documentation for VPS hosting
- Integration guide (4 implementation options)

### TopSky Complete
- Performance optimizations in progress
- Additional ASR profiles under development
- UK Controller Plugin integration testing

### Ground Radar Plugin
- Additional airport profiles in development (CYQM, CYYT, CYSJ, CYFC)
- Stand assignment lists
- Taxi route definitions

---

## [v0.9.03] - 2025-12-07 (Beta)

### TopSky Complete v0.9.03 (Beta)

#### Added
Updated Mapping / ASRs

### TopSky Data v2025.12.07

#### Added
Updated Mapping / ASRs

---

## [v0.9.02] - 2025-12-02 (Beta)

### TopSky Complete v0.9.02 (Beta)

#### Added
Improved TopSkyMaps

### TopSky Data v2025.12.02

#### Added
Improved TopSkyMaps

---

## [v0.9.01] - 2025-12-02 (Beta)

Second beta release with updated airspace boundaries and ground network tools.

### TopSky Complete v0.9.01 (Beta)

#### Added
- Updated CZUL airspace sector boundaries (High/Low sectors)
- Additional TopSky polygon definitions for complex airspace
- OSM-to-EuroScope ground network converter tools
- Direct EuroScope format output (bypassing KML/GNG workflow)
- EuroScope line-to-TopSky polygon converter

#### Changed
- Improved coordinate conversion utilities
- Enhanced documentation for automated ground network generation
- Streamlined workflow for airport ground layout development

#### Tools Added
- `osm_to_euroscope.py` — Direct OSM to EuroScope converter
- `euroscope_to_topsky.py` — Line segment to TopSky polygon converter
- Automated boundary filtering for aerodrome-specific data

### TopSky Data v2025.12.01 (AIRAC 2512)

#### Added
- Updated CZUL airspace sector boundaries (High/Low)
- New TopSky polygon definitions for sector visualization
- OSM-based airport ground layout data for CYHZ
- Enhanced coordinate conversion for DMS format

#### Changed
- Refined airspace visualization layers
- Updated coordination procedures
- Improved polygon structure for complex boundaries

---

## [v0.9.0] - 2024-11-28 (Beta)

This is the first public beta release of the CZQM/CZQX vACC controller resource packages.

### TopSky Complete v0.9.0 (Beta)

#### Added
- Complete EuroScope plugin package with pre-configured profile
- **Plugins Included:**
  - TopSky 2.5 — Primary radar display
  - MAESTRO 1.1 — Arrival manager
  - Ground Radar Plugin 1.6b4 — Surface movement radar
  - vSMR 1.5 — Alternative SMR
  - CCAMS — Squawk code manager
  - EuroNAT — NAT track display
  - VCH — Voice channel helper
  - UK Controller Plugin — Coordination tools (optional)
- **ASR Profiles:**
  - ZQM_CTR.asr — Center position
  - YQM_APP profiles — Multiple APP configurations
  - YHZ_TWR profiles — Runway-specific tower profiles
  - CYHZ-GND_GRP.asr — Ground with GRP
  - YHZ_GND.asr — Standard ground profile
- **Configuration Files:**
  - TopSkyMaps.txt (2.1MB) — Airspace, procedures, RF arcs
  - TopSkySettings.txt — Optimized display settings
  - TopSkyAirspace.txt — Sector definitions
  - TopSkyAreas.txt — Special use airspace
- Custom alert sounds for handoffs, conflicts, coordination
- Custom cursor set for TopSky interface
- CZQM-TopSky.prf profile file for easy startup

#### Known Issues
- UK Controller Plugin compatibility requires further testing
- Some ASR profiles need optimization for specific scenarios
- MAESTRO plugin included but server infrastructure not yet deployed

### Ground Radar Plugin v0.9.0 (Beta)

#### Added
- GRplugin.dll v1.6b4
- ICAO_Aircraft.json aircraft type database
- CYHZ-GND_GRP.asr ground radar profile
- CYHZ-TWR-GRP.asr tower radar profile
- Complete documentation PDFs:
  - Ground Radar plugin for EuroScope - General.pdf
  - Ground Radar plugin for EuroScope - Developer Guide.pdf
  - Ground Radar plugin for EuroScope - Version History.pdf

#### Known Issues
- Only CYHZ airport configured
- Stand assignments not yet implemented
- Taxi routes not yet defined

### RunwayAdvisor Web Application

#### Added
- Initial public release
- Real-time wind analysis
- Runway recommendation based on crosswind/tailwind limits
- METAR display integration
- Responsive design for desktop and mobile
- Offline capability after first load
- Apple touch icons for iOS home screen

#### Features
- Automatic runway selection based on wind conditions
- Crosswind and tailwind limit warnings
- Visual wind indicator
- Current conditions display

---

## [v2024.11] - 2024-11-01 (AIRAC 2411)

### TopSky Data v2024.11

#### Added
- **RNAV RF Arcs** for all major airports:
  - CYFC (Fredericton) — RNAV-Y 09/15/27/33
  - CYHZ (Halifax) — RNAV-Y 05/14/23/32
  - CYQM (Moncton) — RNAV-Y 06/11/24/29
  - CYSJ (Saint John) — RNAV-Y 05/14/23/32
  - CYYT (St. John's) — RNAV-Y 10/16/28/34
- **Class G Airspace Boundaries** with dynamic display
  - Automatically shown/hidden based on zoom level
  - Clear visual distinction from controlled airspace
- **Updated Sector Definitions** for CZQM/CZQX
- **Improved Airspace Visualization**
  - Better layer organization
  - Optimized display performance
  - Reduced visual clutter

#### Changed
- Reorganized TopSkyMaps.txt structure for better maintainability
- Updated coordination procedures in TopSkySettings.txt
- Optimized map layer priorities
- Improved color schemes for better contrast

#### Fixed
- Corrected several waypoint coordinates
- Fixed airspace boundary overlaps
- Resolved display issues with certain zoom levels

---

## [v1.3.0] - 2024-11-27 (Development)

### TopSky Data v1.3.0 (Development)

This was an internal development version that led to v2024.11.

#### Added
- Initial RF arc implementation
- Automated RF arc generation tool (Python)
- RNAV approach procedure definitions

#### Changed
- Major reorganization of TopSkyMaps.txt
- Improved map generation workflow

---

## [v1.2.6] - 2024-11-20 (Internal)

### TopSky Data v1.2.6 (Cleaned)

#### Changed
- Cleaned up copyright concerns in map data
- Removed proprietary NAV CANADA data
- Standardized coordinate formats
- Reorganized file structure

---

## [v1.2.1] - 2024-11-15 (Internal)

### TopSky Data v1.2.1 (Backup)

#### Added
- Initial working backup of TopSkyMaps.txt
- Basic airspace boundaries
- Standard instrument departures (SIDs)
- Standard terminal arrivals (STARs)

---

## Development Tools

### RF Arc Generator v2.2.1 - 2024-11-27

#### Added
- Automatic RF arc generation from sector file waypoints
- Multiple output format support (COORD, COORDPOLY, COORDLINE)
- Validation against CIFP data
- Runway-specific arc generation
- Batch processing for multiple airports/runways

#### Features
- Command-line interface with comprehensive arguments
- Detailed logging and error reporting
- Arc radius validation
- Automatic turn direction detection

#### Fixed
- COORDLINE format bug corrected in v2.2.1
- Improved coordinate precision handling

---

## Future Releases

### Planned for v1.0.0 (Production Release)

#### TopSky Complete
- [ ] Full UK Controller Plugin integration
- [ ] Optimized ASR profiles for all positions
- [ ] Complete documentation set
- [ ] Video tutorials
- [ ] Known issues resolved

#### Ground Radar Plugin
- [ ] CYQM (Moncton) profiles
- [ ] CYYT (St. John's) profiles
- [ ] CYSJ (Saint John) profiles
- [ ] CYFC (Fredericton) profiles
- [ ] Stand assignment database
- [ ] Taxi route definitions
- [ ] Conflict detection configuration

#### MAESTRO
- [ ] Production server deployment
- [ ] EuroScope plugin integration
- [ ] Beta testing with controllers
- [ ] Training videos
- [ ] First operational use during CTP event

#### TopSky Data
- [ ] AIRAC 2412 update (December 2024)
- [ ] Additional special use airspace definitions
- [ ] Improved coordination procedures
- [ ] Military airspace integration

### Planned for v1.1.0

#### TopSky Complete
- [ ] Additional plugins (TBD based on feedback)
- [ ] Enhanced coordination tools
- [ ] Improved conflict detection settings

#### Ground Radar Plugin
- [ ] Additional Atlantic Canada airports
- [ ] Gate/stand management integration
- [ ] Custom label configurations

#### MAESTRO
- [ ] Multi-airport coordination
- [ ] Enhanced delay calculations
- [ ] Integration with real-world traffic data sources

---

## Version History Summary

| Version | Release Date | Type | Description |
|---------|--------------|------|-------------|
| v0.9.03 | 2025-12-07 | Beta | Updated release |
| v2025.12.07 | 2025-12-07 | Data | AIRAC data update |
| v0.9.02 | 2025-12-02 | Beta | Updated release |
| v2025.12.02 | 2025-12-02 | Data | AIRAC data update |
| v0.9.01 | 2025-12-02 | Beta | Second beta with airspace updates |
| v2025.12.01 | 2025-12-02 | Data | AIRAC 2512 data update |
| v0.9.0 | 2024-11-28 | Beta | First public beta release |
| v2024.11 | 2024-11-01 | Data | AIRAC 2411 data update |
| v1.3.0 | 2024-11-27 | Dev | RF arc implementation |
| v1.2.6 | 2024-11-20 | Internal | Copyright cleanup |
| v1.2.1 | 2024-11-15 | Internal | Initial backup |

---

## Notes

### Version Numbering
- **Software packages** (TopSky Complete, GRP, MAESTRO): Semantic versioning (Major.Minor.Patch)
- **Data packages** (TopSky Data): AIRAC dating (YYYY.MM)
- **v0.x.x** = Beta/pre-release versions
- **v1.0.0+** = Production-ready releases

### AIRAC Cycles
TopSky Data releases follow AIRAC cycle dates. See [AIRAC Calendar](https://www.nm.eurocontrol.int/RAD/common/airac_dates.html) for reference.

### Beta Testing
Beta versions (v0.x.x) are released for testing purposes. Please report issues via [GitHub Issues](https://github.com/skyelaird/CZQM-vACC/issues).

### Contributing
See [README.md](README.md) for contribution guidelines.

---

*This changelog is maintained manually. Last updated: December 07, 2025*
