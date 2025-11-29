# CZQM / CZQX vACC — Controller Resources

Tools and data packages for CZQM (Moncton) and CZQX (Gander) FIR controllers on VATSIM.

---

## 📦 Downloads

| Product | Description | Latest | For |
|---------|-------------|--------|-----|
| **TopSky Complete** | Full EuroScope/TopSky package | [v0.9.0 (Beta)](../../releases/tag/TopSky-Complete-v0.9.0) | New controllers |
| **TopSky Data Update** | Maps & settings updates | [v2024.11](../../releases/tag/TopSky-Data-v2024.11) | Existing users |
| **Ground Radar Plugin** | GRP with CYHZ profiles | [v0.9.0 (Beta)](../../releases/tag/GRP-CYHZ-v0.9.0) | Tower/Ground |
| **Runway Advisor** | Wind-based runway selection | [Use Online](https://skyelaird.github.io/CZQM-vACC/RunwayAdvisor/) | All controllers |

> **Note:** v0.9.0 releases are beta versions. Feedback welcome before v1.0.0 final release.

---

## 🚀 Quick Start

### New Controllers — TopSky Complete
1. Download **TopSky Complete** from [Releases](../../releases)
2. Extract to your EuroScope folder (`AppData/Roaming/EuroScope/`)
3. You'll get:
   - `CZQM-TopSky.prf` — The startup profile
   - `TS_Beta/` — All plugins, settings, and resources
4. Open EuroScope and load the `.prf` file
5. You still need VATCAN sector files (`CZQQ/` folder) — get these from VATCAN

### Existing Users — Data Update
1. Download **TopSky Data Update** from [Releases](../../releases)
2. Extract and copy files to your `TS_Beta/plug-ins/TopSky2.5/` folder
3. Restart EuroScope

### Tower/Ground Controllers — Ground Radar Plugin
1. Download **Ground Radar Plugin** from [Releases](../../releases)
2. Extract to your `plug-ins/` folder
3. Load the plugin in EuroScope

---

## 🛠️ Tools

### Runway Advisor
Web-based tool for runway selection based on current winds. No installation required.

**[Launch Runway Advisor →](https://skyelaird.github.io/CZQM-vACC/RunwayAdvisor/)**

### RF Arc Generator
Python tool for generating RNAV approach RF arc definitions for TopSkyMaps.

Located in `TopSky/Tools/rf-arc-generator/`

---

## 📋 What's Included

### TopSky Complete
- **Profile file** (`.prf`) — EuroScope startup configuration
- **TopSky 2.5** — Primary radar display plugin with CZQM/CZQX configuration
- **MAESTRO** — Arrival manager
- **Ground Radar Plugin** — SMR display for tower/ground
- **vSMR** — Surface movement radar
- **CCAMS** — Squawk code management
- **EuroNAT** — North Atlantic track display
- **VCH** — Voice channel helper
- **Pre-configured ASR files** — CTR, APP, TWR, GND positions
- **Custom sounds** — Handoff, conflict, message alerts

### TopSky Data Update
- `TopSkyMaps.txt` — Dynamic airspace boundaries, approach charts, Class G areas
- `TopSkySettings.txt` — Optimized display settings
- `TopSkyAirspace.txt` — Sector definitions

### Ground Radar Plugin
- `GRplugin.dll` v1.6b4
- CYHZ ground/tower radar profiles
- Aircraft type database

---

## 📁 Repository Structure

```
CZQM-vACC/
├── RunwayAdvisor/          # Web-based runway selection tool
├── TopSky/
│   ├── source/TS_Beta/     # Complete EuroScope package
│   └── Tools/              # RF arc generator, utilities
├── GroundRadar/            # GRP standalone package
├── docs/                   # References and documentation
└── dev/                    # Development/test files
```

---

## 🏷️ Release Naming

| Product | Format | Example |
|---------|--------|---------|
| TopSky Complete | `TopSky-Complete-vX.Y.Z` | `TopSky-Complete-v0.9.0` |
| TopSky Data | `TopSky-Data-vYYYY.MM` | `TopSky-Data-v2024.11` |
| Ground Radar | `GRP-CYHZ-vX.Y.Z` | `GRP-CYHZ-v0.9.0` |

Pre-release/beta versions (v0.x.x) are marked in GitHub and won't appear as "Latest".

---

## 📝 Changelog

### TopSky Data
| Version | Date | Changes |
|---------|------|---------|
| v2024.11 | Nov 2024 | Class G boundaries, dynamic airspace display, RNAV RF arcs |

### TopSky Complete
| Version | Date | Changes |
|---------|------|---------|
| v0.9.0 | Nov 2024 | Beta release - Complete package with all plugins and configurations |

### Ground Radar Plugin
| Version | Date | Changes |
|---------|------|---------|
| v0.9.0 | Nov 2024 | Beta release - CYHZ profiles with GRplugin v1.6b4 |

---

## 🤝 Contributing

Issues and suggestions welcome. Other vACCs are free to copy and adapt.

---

## 📫 Contact

**Joel Morin**  
CZQM/CZQX vACC — VATCAN Division

---

*For use with VATSIM network*
