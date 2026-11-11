# CZQM / CZQX Airspace 3D

Interactive 3D view of the Moncton and Gander FIR sector volumes, built from the CZQQ EuroScope sector file.

**Open it:** https://skyelaird.github.io/CZQM-vACC/Airspace3D/

- Drag to pan, scroll to zoom, right-drag or Ctrl-drag to tilt and rotate.
- Layers: CZQM/CZQX High and Low, terminals, tower zones, ground/delivery, Gander Oceanic, neighbours.
- Click a volume for its floor, ceiling and the top-down owner order with callsigns and frequencies.
- Altitude filter: show only the volumes active at a chosen level; colour by layer or by owning position (VATGlasses-style).
- Height-stretch slider (default x5) so the stacking is visible; satellite or map background; optional terrain.

Built on [CesiumJS](https://cesium.com/platform/cesiumjs/) 1.120 (Apache 2.0). Satellite imagery and terrain come through a Cesium ion token restricted to this site; without it the page falls back to OpenStreetMap on a flat globe.

## Updating after an AIRAC

```
python3 tools/parse_ese.py <path-to>.ese sectors.json
python3 -c "t=open('tools/template.html').read(); d=open('sectors.json').read(); open('index.html','w').write(t.replace('__DATA__',d).replace('__AIRAC__','AIRAC xxxx'))"
```

The page must be served over http(s); opened straight from disk, browsers block Cesium's workers and the globe stays black.

For flight simulation use on VATSIM only.
