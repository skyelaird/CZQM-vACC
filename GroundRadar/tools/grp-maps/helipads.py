"""
helipads.py - OSM cache refresh (parking positions, gates, helipads) + helipad symbols in GRpluginMaps.txt.
Replaces osm_stands.py: stands now come from nav_stands.py, which reads the cache this script writes.

Usage:  python helipads.py [--refresh] CYFC CYQM ...   (default: all listed below)
Data:   OSM API v0.6, cached in tools\\osm_cache\\<ICAO>.json; (c) OpenStreetMap contributors, ODbL.
"""
import json, math, os, re, shutil, sys, time, urllib.request, xml.etree.ElementTree as ET
HERE = os.path.dirname(os.path.abspath(__file__)); GRP = os.path.dirname(HERE)
MAPS = os.path.join(GRP, 'GRpluginMaps.txt')
CACHE = os.path.join(HERE, 'osm_cache'); os.makedirs(CACHE, exist_ok=True)
BBOX = {  # w, s, e, n  (list of boxes; split where the OSM API node limit bites)
 'CYFC': [(-66.572, 45.848, -66.502, 45.892)], 'CYQM': [(-64.714, 46.090, -64.644, 46.134)],
 'CYQX': [(-54.603, 48.915, -54.533, 48.959)], 'CYYR': [(-60.461, 53.297, -60.391, 53.341)],
 'CYYT': [(-52.775, 47.608, -52.750, 47.632), (-52.750, 47.605, -52.725, 47.630)],
 'CYZX': [(-64.953, 44.962, -64.883, 45.006)], 'LFVP': [(-56.209, 46.741, -56.139, 46.785)]}
HELI_SKIP = {'CYYR'}          # CYYR helipads already hand-placed (MAP:CYYR Helipads)

def fetch(icao):
    els, seen = [], set()
    for w, s, e, n in BBOX[icao]:
        u = f'https://api.openstreetmap.org/api/0.6/map?bbox={w},{s},{e},{n}'
        x = urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'GRPmapBuilder/1.0'}), timeout=50).read()
        root = ET.fromstring(x); nodes = {k.get('id'): (float(k.get('lat')), float(k.get('lon'))) for k in root.iter('node')}
        for el in list(root.iter('node')) + list(root.iter('way')):
            t = {g.get('k'): g.get('v') for g in el.findall('tag')}
            if t.get('aeroway') not in ('parking_position', 'gate', 'helipad') or (el.tag, el.get('id')) in seen: continue
            seen.add((el.tag, el.get('id'))); d = {'type': el.tag, 'id': int(el.get('id')), 'tags': t}
            if el.tag == 'node': d['lat'], d['lon'] = nodes[el.get('id')]
            else: d['geometry'] = [{'lat': nodes[r.get('ref')][0], 'lon': nodes[r.get('ref')][1]} for r in el.findall('nd') if r.get('ref') in nodes]
            els.append(d)
    json.dump({'elements': els}, open(os.path.join(CACHE, icao + '.json'), 'w')); return els

def dms(v, p, n):
    h = p if v >= 0 else n; v = abs(v); d = int(v); m = int((v - d) * 60); s = round((v - d - m / 60) * 3600, 3)
    if s >= 60: s -= 60; m += 1
    if m == 60: m = 0; d += 1
    return f'{h}{d:03d}.{m:02d}.{s:06.3f}'

def centroid(g): return (sum(p['lat'] for p in g) / len(g), sum(p['lon'] for p in g) / len(g))

def natural(s): return [int(x) if x.isdigit() else x for x in re.split(r'(\d+)', s)]

def main():
    args = [a for a in sys.argv[1:] if a != '--refresh']; refresh = '--refresh' in sys.argv
    icaos = [a.upper() for a in args] or list(BBOX)
    M = open(MAPS, encoding='latin-1').read().replace('\r\n', '\n').split('\n')
    for icao in icaos:
        cf = os.path.join(CACHE, icao + '.json')
        els = json.load(open(cf))['elements'] if os.path.exists(cf) and not refresh else fetch(icao)
        heli = [e for e in els if e['tags'].get('aeroway') == 'helipad']
        hb = []
        if heli and icao not in HELI_SKIP:
            hb = [f'//>>>> GENERATED HELIPADS {icao} - tools\\helipads.py from OpenStreetMap (c) OSM contributors, ODbL',
                  f'MAP:{icao} Helipads', f'FOLDER:{icao}', f'AIRPORT:{icao}', 'ACTIVE:1', 'LAYER:15', 'COLOR:SMGS_HELI']
            for e in heli:
                la, lo = (e['lat'], e['lon']) if e['type'] == 'node' else centroid(e['geometry'])
                hb.append(f"SYMBOL:HELIPAD:{dms(la, 'N', 'S')}:{dms(lo, 'E', 'W')}")
            hb.append(f'//<<<< END GENERATED HELIPADS {icao}')
        k = next((x for x, l in enumerate(M) if l.startswith(f'//>>>> GENERATED HELIPADS {icao}')), None)
        new = k is None
        if not new: j = M.index(f'//<<<< END GENERATED HELIPADS {icao}', k); del M[k:j + 1]
        else: k = next((x for x, l in enumerate(M) if l == f'MAP:{icao} Runway Arrows'), len(M))
        if hb: M[k:k] = hb + ([''] if new else [])
        print(f'{icao}: {len(heli)} helipads in OSM' + (' (skipped: hand-placed map)' if icao in HELI_SKIP else ''))
    bak = os.path.join(GRP, '_bak'); os.makedirs(bak, exist_ok=True); ts = time.strftime('.bak_%Y%m%d_%H%M%S')
    for f, L in ((MAPS, M),):
        shutil.copy(f, os.path.join(bak, os.path.basename(f) + ts)); open(f, 'w', encoding='latin-1', newline='\r\n').write('\n'.join(L))

if __name__ == '__main__': main()
