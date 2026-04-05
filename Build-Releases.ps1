# CZQM vACC Release Builder
# Run this script from the CZQM-vACC repository root directory

param(
    [string]$OutputPath = ".\releases"
)

Write-Host "CZQM vACC Release Package Builder" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Create output directory
New-Item -ItemType Directory -Force -Path $OutputPath | Out-Null
Write-Host "Output directory: $OutputPath" -ForegroundColor Green

# ============================================================================
# RELEASE 1: TopSky Complete v0.9.05
# ============================================================================
Write-Host "`nBuilding TopSky-Complete-v0.9.05" -ForegroundColor Yellow

$tsComplete = Join-Path $OutputPath "TopSky-Complete-v0.9.05"
New-Item -ItemType Directory -Force -Path $tsComplete | Out-Null

# Copy ALL contents from source folder
Get-ChildItem ".\TopSky\source" | Copy-Item -Destination $tsComplete -Recurse -Force

# Add README
@"
CZQM / CZQX vACC - TopSky Complete Package v0.9.05
==================================================

INSTALLATION INSTRUCTIONS FOR NEW CONTROLLERS
----------------------------------------------

1. PREREQUISITES
   - EuroScope installed (latest version recommended)
   - VATCAN sector files (CZQQ folder) from VATCAN website
   - Windows 7 or later

2. INSTALLATION
   a) Locate your EuroScope folder:
      - Default: C:\Users\[YourName]\AppData\Roaming\EuroScope\
      - Or wherever you installed EuroScope

   b) Extract this package:
      - Copy "CZQM TopSky TEST.prf" to your EuroScope root folder
      - Copy the entire TS_Beta folder to your EuroScope root folder

   c) Your folder structure should look like:
      EuroScope/
      ├── CZQM TopSky TEST.prf
      ├── TS_Beta/
      └── CZQQ/ (VATCAN sector files - install separately)

3. FIRST RUN
   a) Open EuroScope
   b) Click "Open SCT" and select the "CZQM TopSky TEST.prf" file
   c) All plugins and settings will load automatically

4. WHAT'S INCLUDED
   - TopSky 2.5 - Primary radar display
   - MAESTRO - Arrival manager
   - Ground Radar Plugin - SMR for tower/ground
   - vSMR - Surface movement radar
   - CCAMS - Squawk code management
   - EuroNAT - North Atlantic track display
   - VCH - Voice channel helper
   - Pre-configured ASR files for all positions
   - Custom alert sounds
   - Optimized settings for CZQM/CZQX operations

5. UPDATING
   - For map/settings updates only, download "TopSky Data Update" packages
   - For major version updates, download new Complete packages

6. SUPPORT
   GitHub: https://github.com/skyelaird/CZQM-vACC
   
   For VATSIM use only
   CZQM/CZQX vACC - VATCAN Division
   
Installation Date: $(Get-Date -Format "MMMM yyyy")
Package Version: v0.9.01
"@ | Out-File -FilePath (Join-Path $tsComplete "README.txt") -Encoding UTF8

Write-Host "  ✓ TopSky Complete package created" -ForegroundColor Green

# ============================================================================
# RELEASE 2: TopSky Data Update v2026.04.05
# ============================================================================
Write-Host "`nBuilding TopSky-Data-v2026.04.05" -ForegroundColor Yellow

$tsData = Join-Path $OutputPath "TopSky-Data-v2026.04.05"
$tsDataPlugin = Join-Path $tsData "TopSky2.5"
New-Item -ItemType Directory -Force -Path $tsDataPlugin | Out-Null

# Copy the three main data files
Copy-Item ".\TopSky\source\TS_Beta\plug-ins\TopSky2.5\TopSkyMaps.txt" -Destination $tsDataPlugin
Copy-Item ".\TopSky\source\TS_Beta\plug-ins\TopSky2.5\TopSkySettings.txt" -Destination $tsDataPlugin
Copy-Item ".\TopSky\source\TS_Beta\plug-ins\TopSky2.5\TopSkyAirspace.txt" -Destination $tsDataPlugin

# Add README
@"
CZQM / CZQX vACC - TopSky Data Update v2026.04.05
=================================================

MAP & SETTINGS UPDATE FOR EXISTING USERS
-----------------------------------------

1. WHAT THIS UPDATE CONTAINS
   - TopSkyMaps.txt - Updated airspace boundaries, approach charts, Class G areas
   - TopSkySettings.txt - Optimized display settings
   - TopSkyAirspace.txt - Sector definitions

2. WHO SHOULD INSTALL THIS
   ✓ You already have TopSky Complete installed
   ✓ You want the latest maps and settings
   ✗ New users should download TopSky Complete instead

3. INSTALLATION
   a) Close EuroScope if running

   b) Locate your TopSky folder:
      - Default: C:\Users\[YourName]\AppData\Roaming\EuroScope\TS_Beta\plug-ins\TopSky2.5\

   c) BACKUP YOUR CURRENT FILES (recommended):
      - Copy your existing TopSkyMaps.txt, TopSkySettings.txt, and TopSkyAirspace.txt 
        to a backup folder in case you need to revert

   d) Extract and copy the three files from this package to your TopSky2.5 folder:
      - TopSkyMaps.txt
      - TopSkySettings.txt  
      - TopSkyAirspace.txt

   e) Restart EuroScope

4. WHAT'S NEW IN v2025.12.01
   - Updated CZUL airspace sector boundaries (High/Low)
   - New TopSky polygon definitions
   - OSM-based airport ground layout data
   - Enhanced approach chart references
   - Optimized sector display settings

5. REVERTING
   - If you experience issues, restore your backed-up files
   - Report issues on GitHub

6. SUPPORT
   GitHub: https://github.com/skyelaird/CZQM-vACC

   For VATSIM use only
   CZQM/CZQX vACC - VATCAN Division

Release Date: April 2026
Package Version: v2026.04.05
"@ | Out-File -FilePath (Join-Path $tsData "README.txt") -Encoding UTF8

Write-Host "  ✓ TopSky Data Update package created" -ForegroundColor Green

# ============================================================================
# RELEASE 3: Ground Radar Plugin v0.9.0
# ============================================================================
Write-Host "`nBuilding GRP-CYHZ-v0.9.0..." -ForegroundColor Yellow

$grp = Join-Path $OutputPath "GRP-CYHZ-v0.9.0"
$grpProfiles = Join-Path $grp "Profiles"
New-Item -ItemType Directory -Force -Path $grpProfiles | Out-Null

# Copy GRP files
$grpSource = ".\TopSky\source\TS_Beta\plug-ins\GroundRadarPlugin_1.6b4"
Copy-Item (Join-Path $grpSource "GRplugin.dll") -Destination $grp
Copy-Item (Join-Path $grpSource "ICAO_Aircraft.json") -Destination $grp

# Copy CYHZ profiles
Copy-Item ".\TopSky\source\TS_Beta\ASR\GRD\CYHZ-GND_GRP.asr" -Destination $grpProfiles
Copy-Item ".\TopSky\source\TS_Beta\ASR\GRD\CYHZ-TWR-GRP.asr" -Destination $grpProfiles

# Add README
@"
CZQM / CZQX vACC - Ground Radar Plugin for CYHZ v0.9.0
======================================================

GROUND/TOWER SMR DISPLAY FOR HALIFAX
------------------------------------

1. WHAT THIS PACKAGE CONTAINS
   - GRplugin.dll v1.6b4 - Ground Radar Plugin
   - ICAO_Aircraft.json - Aircraft type database
   - CYHZ-GND_GRP.asr - Ground radar profile
   - CYHZ-TWR-GRP.asr - Tower radar profile

2. WHO SHOULD INSTALL THIS
   ✓ Tower/Ground controllers at CYHZ
   ✓ Users who want standalone GRP without full TopSky package
   ✗ If you have TopSky Complete, GRP is already included

3. INSTALLATION
   a) Close EuroScope if running

   b) Locate your EuroScope plug-ins folder:
      - Default: C:\Users\[YourName]\AppData\Roaming\EuroScope\plug-ins\
      - Or create it if it doesn't exist

   c) Extract and copy files:
      - GRplugin.dll → plug-ins\GroundRadarPlugin\
      - ICAO_Aircraft.json → plug-ins\GroundRadarPlugin\
      - Both .asr files → your ASR folder (or anywhere you keep ASR files)

   d) Load the plugin in EuroScope:
      - OTHER SET → Plug-ins → Load
      - Browse to GRplugin.dll
      - Click Open

4. USING THE PLUGIN
   a) Load one of the ASR files:
      - CYHZ-GND_GRP.asr for Ground position
      - CYHZ-TWR-GRP.asr for Tower position

   b) The Surface Movement Radar will display:
      - Aircraft positions on taxiways/runways
      - Conflict alerts
      - Runway status indicators

5. PROFILES INCLUDED
   - CYHZ Ground - Full airport SMR view
   - CYHZ Tower - Tower-optimized SMR view

6. DOCUMENTATION
   Full plugin documentation available in TopSky Complete package
   or from the Ground Radar Plugin developer

7. SUPPORT
   GitHub: https://github.com/skyelaird/CZQM-vACC

   For VATSIM use only
   CZQM/CZQX vACC - VATCAN Division

Release Date: $(Get-Date -Format "MMMM yyyy")
Package Version: v0.9.0
Plugin Version: GRplugin 1.6b4
"@ | Out-File -FilePath (Join-Path $grp "README.txt") -Encoding UTF8

Write-Host "  ✓ Ground Radar Plugin package created" -ForegroundColor Green

# ============================================================================
# Create ZIP archives
# ============================================================================
Write-Host "`nCreating ZIP archives..." -ForegroundColor Yellow

$releases = @(
    "TopSky-Complete-v0.9.05",
    "TopSky-Data-v2026.04.05",
    "GRP-CYHZ-v0.9.0"
)

foreach ($release in $releases) {
    $sourcePath = Join-Path $OutputPath $release
    $zipPath = Join-Path $OutputPath "$release.zip"
    
    Compress-Archive -Path $sourcePath -DestinationPath $zipPath -Force
    Write-Host "  ✓ Created $release.zip" -ForegroundColor Green
}

# ============================================================================
# Summary
# ============================================================================
Write-Host "`n==================================" -ForegroundColor Cyan
Write-Host "Release packages created:" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan

Get-ChildItem -Path $OutputPath -Filter "*.zip" | ForEach-Object {
    $sizeMB = [math]::Round($_.Length / 1MB, 2)
    Write-Host "  $($_.Name) - $sizeMB MB" -ForegroundColor White
}

Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "  1. Test each package by extracting and verifying contents"
Write-Host "  2. Create GitHub releases:"
Write-Host "     - Go to https://github.com/skyelaird/CZQM-vACC/releases"
Write-Host "     - Click 'Create a new release'"
Write-Host "     - Create tags: TopSky-Complete-v0.9.05, TopSky-Data-v2026.04.05, GRP-CYHZ-v0.9.0"
Write-Host "     - Upload corresponding ZIP files"
Write-Host "  3. The README.md release links will work automatically once published"
Write-Host ""
Write-Host "Done!" -ForegroundColor Green
