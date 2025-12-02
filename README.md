# CZQM / CZQX vACC — Controller Resources

Professional tools and data packages for Moncton (CZQM) and Gander (CZQX) FIR controllers on VATSIM.

[![VATSIM](https://img.shields.io/badge/VATSIM-VATCAN-blue)](https://vatcan.ca)
[![Latest Release](https://img.shields.io/github/v/release/skyelaird/CZQM-vACC?include_prereleases)](https://github.com/skyelaird/CZQM-vACC/releases)
[![License](https://img.shields.io/badge/license-GPL--3.0-green)](LICENSE)

---

## 🎯 Projects in This Repository

### [MAESTRO](MAESTRO/) — Arrival Management System
Multi-user arrival sequencing system for coordinated flow management during busy periods and Cross the Pond events.

- **Status:** In Development
- **For:** APP/ACC Controllers
- **Features:** Master/Slave coordination, automatic ETA calculation, runway rate management

### [TopSky](TopSky/) — Radar Display Configuration
Complete TopSky 2.5 plugin configuration for CZQM/CZQX airspace with custom maps, settings, and profiles.

- **Status:** Production (v0.9.02 Beta)
- **For:** All radar positions (CTR, APP, TWR, GND)
- **Features:** Dynamic airspace, RNAV RF arcs, custom coordination setup

### [RunwayAdvisor](RunwayAdvisor/) — Web Application
Real-time runway selection tool considering wind, weather, traffic, and noise abatement.

- **Status:** Production
- **For:** All controllers
- **[Launch Tool →](https://skyelaird.github.io/CZQM-vACC/RunwayAdvisor/)**

### [GroundRadar](GroundRadar/) — Ground Radar Plugin
EuroScope Ground Radar plugin configurations for surface movement operations.

- **Status:** Beta (v0.9.0)
- **For:** Tower/Ground positions
- **Features:** CYHZ SMR profiles, aircraft type database

---

## 📦 Downloads

| Product | Description | Latest | Quick Link |
|---------|-------------|--------|------------|
| **TopSky Complete** | Full EuroScope/TopSky package | [v0.9.02 (Beta)](../../releases/tag/TopSky-Complete-v0.9.02) | For new controllers |
| **TopSky Data Update** | Maps & settings only (AIRAC-dated) | [v2025.12.02](../../releases/tag/TopSky-Data-v2025.12.02) | For existing users |
| **Ground Radar Plugin** | GRP with CYHZ profiles | [v0.9.0 (Beta)](../../releases/tag/GRP-CYHZ-v0.9.0) | Tower/Ground positions |
| **MAESTRO** | Arrival manager (server + docs) | Coming Soon | Stay tuned |

> **Note:** v0.9.x releases are beta versions. Please report issues before v1.0.0 final release.

**[📥 View All Releases →](../../releases)**

---

## 🚀 Quick Start

### New Controllers — TopSky Complete

1. **Download** [TopSky Complete v0.9.02](../../releases/tag/TopSky-Complete-v0.9.01)
2. **Extract** to your EuroScope folder:
   ```
   %APPDATA%\EuroScope\
   ```
3. **You'll get:**
   - `CZQM-TopSky.prf` — Main profile file
   - `TS_Beta/` folder — All plugins, settings, ASR files
4. **Open** EuroScope and load `CZQM-TopSky.prf`
5. **Note:** You still need VATCAN sector files (`CZQQ/`) — get from [VATCAN](https://vatcan.ca)

### Existing Users — Data Update Only

1. **Download** [TopSky Data v2025.12.02](../../releases/tag/TopSky-Data-v2025.12.01)
2. **Extract** and copy files to your existing `TS_Beta/plug-ins/TopSky2.5/` folder
3. **Restart** EuroScope
4. **Changes:**
   - Updated `TopSkyMaps.txt` (new airspace, RF arcs)
   - Updated `TopSkySettings.txt` (optimized display)
   - Updated `TopSkyAirspace.txt` (sector definitions)

### Tower/Ground — Ground Radar Plugin

1. **Download** [Ground Radar Plugin v0.9.0](../../releases/tag/GRP-CYHZ-v0.9.0)
2. **Extract** to your `plug-ins/GroundRadarPlugin_1.6b4/` folder
3. **Load** the plugin in EuroScope
4. **Load** the CYHZ GND or TWR ASR profile included in package

---

## 🛠️ Tools & Utilities

### Runway Advisor — Web Application
No installation required. Works on desktop and mobile.

**Features:**
- Real-time wind analysis
- Runway recommendation based on crosswind/tailwind limits
- METAR display
- Works offline after first load

**[🚀 Launch Runway Advisor →](https://skyelaird.github.io/CZQM-vACC/RunwayAdvisor/)**

### RF Arc Generator — Python Tool
Generate TopSky map definitions for RNAV approach RF (radius-to-fix) legs.

**Location:** `TopSky/Tools/rf-arc-generator/`

**Features:**
- Automatic arc generation from sector file waypoints
- Validation against CIFP data
- Multiple output formats (COORD, COORDPOLY, COORDLINE)

**Usage:**
```bash
python topsky_rf_generator.py --sct CZQQ.sct --airport CYHZ --runway 05
```

**[📖 Full Documentation →](TopSky/Tools/rf-arc-generator/TopSky_RF_Generator_Usage_Guide.md)**

---

## 📋 What's Included in Each Package

<details>
<summary><strong>TopSky Complete — Full Controller Package</strong></summary>

### Core Files
- `CZQM-TopSky.prf` — EuroScope startup profile
- Complete `TS_Beta/` folder structure

### Plugins Included
- **TopSky 2.5** — Primary radar display (customized for CZQM/CZQX)
- **MAESTRO 1.1** — Arrival manager plugin
- **Ground Radar Plugin 1.6b4** — Surface movement radar
- **vSMR 1.5** — Surface movement radar (alternative)
- **CCAMS** — Squawk code assignment manager
- **EuroNAT** — North Atlantic track display
- **VCH** — Voice channel helper
- **UK Controller Plugin** — Optional (for coordination)

### Position Profiles (ASR)
- **CTR:** ZQM_CTR.asr
- **APP:** YQM_APP profiles (multiple configurations)
- **TWR:** YHZ_TWR profiles (runway-specific)
- **GND:** CYHZ-GND_GRP.asr, YHZ_GND.asr

### Configuration Files
- `TopSkyMaps.txt` — 2.1MB of airspace definitions, RNAV RF arcs, approach charts
- `TopSkySettings.txt` — Display settings optimized for CZQM/CZQX
- `TopSkyAirspace.txt` — Sector definitions and boundaries
- `TopSkyAreas.txt` — Special use airspace
- Pre-configured coordination lists and tags

### Sounds & Assets
- Custom alert sounds (handoff, conflict, coordination, CPDLC)
- Custom cursors for TopSky interface

</details>

<details>
<summary><strong>TopSky Data Update — AIRAC Updates Only</strong></summary>

### What's Updated
- `TopSkyMaps.txt` — Latest airspace, procedures, RF arcs
- `TopSkySettings.txt` — Optimized settings
- `TopSkyAirspace.txt` — Current sector definitions

### What's NOT Included
- Plugins (TopSky.dll, MAESTRO.dll, etc.)
- ASR files
- Sounds
- EuroScope profile

**Best for:** Controllers who already have TopSky Complete and just need data updates.

</details>

<details>
<summary><strong>Ground Radar Plugin — Tower/Ground Package</strong></summary>

### What's Included
- `GRplugin.dll` v1.6b4
- `ICAO_Aircraft.json` — Aircraft type database
- `CYHZ-GND_GRP.asr` — Ground position profile
- `CYHZ-TWR-GRP.asr` — Tower position profile
- Documentation PDFs

### Airports Configured
- **CYHZ** (Halifax) — Complete GND/TWR setup

**Note:** More airports coming in future releases.

</details>

---

## 📁 Repository Structure

```
CZQM-vACC/
│
├── MAESTRO/                    # Arrival Management System
│   ├── server/                 # Node.js backend server
│   ├── sync-tool/              # EuroScope integration tool
│   ├── docs/                   # Training guides, deployment
│   └── README.md
│
├── TopSky/                     # Radar Display Configuration
│   ├── source/                 # Working files
│   │   ├── TS_Beta/            # Complete EuroScope package
│   │   └── CZQM TopSky.prf     # Main profile file
│   └── Tools/                  # Utilities
│       └── rf-arc-generator/   # RNAV RF arc tool
│
├── RunwayAdvisor/              # Web Application
│   ├── index.html
│   ├── script.js
│   ├── styles.css
│   └── README.pdf
│
├── GroundRadar/                # Ground Radar Plugin (future releases)
│
├── releases/                   # Pre-built release packages
│   ├── TopSky-Complete-v0.9.0/
│   ├── TopSky-Data-v2024.11/
│   └── GRP-CYHZ-v0.9.0/
│
├── docs/                       # Documentation & references
│   ├── development/            # Development notes
│   └── references/             # Logos, images
│
├── dev/                        # Development & testing
│   └── TestSectorFiles/
│
├── Build-Releases.ps1          # Automated release builder
└── README.md                   # This file
```

---

## 🏷️ Version Naming Convention

| Product | Format | Example | Meaning |
|---------|--------|---------|---------|
| **TopSky Complete** | `TopSky-Complete-vX.Y.Z` | `v0.9.0` | Major.Minor.Patch |
| **TopSky Data** | `TopSky-Data-vYYYY.MM` | `v2024.11` | AIRAC effective date |
| **Ground Radar** | `GRP-CYHZ-vX.Y.Z` | `v0.9.0` | Major.Minor.Patch |
| **MAESTRO** | `MAESTRO-vX.Y.Z` | `v1.0.0` | Major.Minor.Patch |

**Pre-release versions** (v0.x.x) are beta releases for testing. Version 1.0.0 will be the first production-ready release.

---

## 📝 Changelog

### MAESTRO — In Development
- [Roadmap](MAESTRO/NEXT_STEPS.md) — 6-month implementation plan
- Server implementation complete (Node.js + Express)
- Training materials complete
- Integration with TopSky plugin pending

### TopSky Complete

#### [v0.9.01] — 2025-12-02 (Beta)
**Added:**
- Updated airspace boundaries (CZUL High/Low)
- Additional TopSky polygon definitions
- OSM-to-EuroScope ground network converter tools

**Changed:**
- Improved coordinate conversion utilities
- Enhanced documentation

#### [v0.9.0] — 2024-11-28 (Beta)
**Added:**
- Initial beta release
- Complete plugin package with TopSky 2.5, MAESTRO, GRP, vSMR, CCAMS, EuroNAT, VCH
- Pre-configured ASR files for CTR, APP, TWR, GND positions
- Custom sounds and alert configuration
- CZQM-TopSky.prf profile file

**Known Issues:**
- UK Controller Plugin compatibility not fully tested
- Some ASR profiles need further optimization

### TopSky Data

#### [v2025.12.01] — 2025-12-02 (AIRAC 2512)
**Added:**
- Updated CZUL airspace sector boundaries
- New TopSky polygon definitions for High/Low sectors
- OSM-based airport ground layout data

**Changed:**
- Refined airspace visualization layers
- Updated coordination procedures

#### [v2024.11] — 2024-11-01 (AIRAC 2411)
**Added:**
- Complete TopSkyMaps.txt with RNAV RF arcs for all major airports
- Class G airspace boundaries with dynamic display
- Updated sector definitions
- Optimized display settings

**Changed:**
- Reorganized map layers for better performance
- Updated coordination procedures

#### [v1.3.0] — 2024-11-27 (Development)
**Added:**
- RF arcs for CYFC, CYHZ, CYQM, CYSJ, CYYT RNAV approaches
- Improved airspace visualization

### Ground Radar Plugin

#### [v0.9.0] — 2024-11-28 (Beta)
**Added:**
- Initial beta release
- GRplugin.dll v1.6b4
- CYHZ ground and tower radar profiles
- Aircraft type database (JSON format)
- Documentation PDFs

**Planned for v1.0.0:**
- Additional airport profiles (CYQM, CYYT, CYSJ, CYFC)
- Stand assignment lists
- Taxi route definitions

---

## 🤝 Contributing & Feedback

### Reporting Issues
Found a bug or have a suggestion? Please use the [Issues](../../issues) tab.

**When reporting, please include:**
- Product and version (e.g., "TopSky Complete v0.9.0")
- EuroScope version
- Steps to reproduce
- Screenshots if applicable

### Contributing
Contributions are welcome! Other vACCs are free to copy, adapt, and improve these resources.

**Ways to contribute:**
- Report bugs and suggest features
- Submit pull requests for fixes
- Share your ASR profiles or custom configurations
- Improve documentation

### License
This project is licensed under the GNU General Public License v3.0. See [LICENSE](LICENSE) for details.

---

## 🔗 Related Projects & Resources

### VATSIM Resources
- **[VATCAN](https://vatcan.ca)** — VATSIM Canada Division
- **[CZQM/CZQX vACC](https://czqm.ca)** — Moncton/Gander vACC
- **[VATSIM](https://vatsim.net)** — Virtual Air Traffic Simulation Network

### TopSky Resources
- **[Alias Discord](https://discord.gg/topsky)** — TopSky plugin support
- **[TopSky Documentation](TopSky/source/TS_Beta/plug-ins/TopSky2.5/Documentation/)** — Included in package

### Other Tools
- **[EuroScope](https://euroscope.hu/)** — ATC radar simulation software
- **[VATSIM Audio for VATSIM](https://audio.vatsim.net/)** — Voice client

---

## 📧 Contact & Support

**Maintained by:** Joel Laird (VE1ATM)  
**Role:** CZQM/CZQX vACC Staff  
**VATSIM:** VATCAN Division

**For support:**
- Open an [Issue](../../issues) on GitHub
- Contact via CZQM/CZQX vACC Discord
- Email: [Contact through VATCAN](https://vatcan.ca)

---

## ⭐ Acknowledgments

**Special thanks to:**
- **TopSky Development Team** — For the excellent radar display plugin
- **Gergely Csernak** — For EuroScope
- **VATCAN Staff** — For sector file development and support
- **CZQM/CZQX Controllers** — For beta testing and feedback
- **VATSIM UK** — For UK Controller Plugin inspiration

---

## 📜 Legal

### For Use With VATSIM Network
These resources are developed for use on the VATSIM network only. Not for use with real-world air traffic control.

### Copyright Notice
TopSky plugin, MAESTRO plugin, Ground Radar plugin, and EuroScope are copyright their respective authors. This repository contains only configuration files and documentation.

Airspace data and procedures are based on publicly available NAV CANADA data and are used for flight simulation purposes only.

---

*Last updated: December 02, 2025*
