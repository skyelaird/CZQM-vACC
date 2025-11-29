CZQM / CZQX vACC - Ground Radar Plugin for CYHZ v1.0.0
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

Release Date: November 2025
Package Version: v1.0.0
Plugin Version: GRplugin 1.6b4
