"""
osm_stands.py - stands (GRpluginStands.txt) and helipad symbols (GRpluginMaps.txt) from OpenStreetMap

Usage:  python osm_stands.py [--refresh] CYFC CYQM ...   (default: all listed below)
Data:   OSM API v0.6 (cached in tools\\osm_cache\\<ICAO>.json); (c) OpenStreetMap contributors, ODbL.
Rules:  stand = aeroway=parking_position (node, or way stop-end + last-segment heading) with ref/name;
        aeroway=gate with ref used only where no parking_position carries that ref.
        'APRON x' named positions become AREA stands. Unnamed positions are skipped (listed in the report).
Each airport is written as a managed block; CYHZ (built by osm-to-grp\\extract.py) is never touched.
"""
import json, math, os, re, shutil, sys, time, urllib.request, xml.etree.ElementTree as ET
HERE = os.path.dirname(os.path.abspath(__file__)); GRP = os.path.dirname(HERE)
STANDS = os.path.join(GRP, 'GRpluginStands.txt'); MAPS = os.path.join(GRP, 'GRpluginMaps.txt')
CACHE = os.path.join(HERE, 'osm_cache'); os.makedirs(CACHE, exist_ok=True)
BBOX = {  # w, s, e, n  (list of boxes; split where the OSM API node limit bites)
 'CYFC': [(-66.572, 45.848, -66.502, 45.892)], 'CYQM': [(-64.714, 46.090, -64.644, 46.134)],
 'CYQX': [(-54.603, 48.915, -54.533, 48.959)], 'CYYR': [(-60.461, 53.297, -60.391, 53.341)],
 'CYYT': [(-52.775, 47.608, -52.750, 47.632), (-52.750, 47.605, -52.725, 47.630)],
 'CYZX': [(-64.953, 44.962, -64.883, 45.006)], 'LFVP': [(-56.209, 46.741, -56.139, 46.785)]}
HELI_SKIP = {'CYYR'}          # CYYR helipads already hand-placed (MAP:CYYR Helipads)
RADIUS, AREA_RADIUS = 20.0, 80.0

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

def brg(a, b):
    k = math.cos(math.radians(a[0])); return math.degrees(math.atan2((b[1] - a[1]) * k, b[0] - a[0])) % 360

def centroid(g): return (sum(p['lat'] for p in g) / len(g), sum(p['lon'] for p in g) / len(g))

def stands_for(icao, els):
    park, gate, skipped, unnamed = {}, {}, 0, []
    for e in els:
        t = e['tags']; a = t.get('aeroway'); name = (t.get('ref') or t.get('name') or '').strip()
        if a not in ('parking_position', 'gate'): continue
        name = re.sub(r'^(Gate|Bay)\s+', lambda m: 'BAY ' if m.group(1) == 'Bay' else '', name).strip().replace(':', '-')
        if not name:
            skipped += 1
            if a == 'parking_position':
                g = [(e['lat'], e['lon'])] if e['type'] == 'node' else [(p['lat'], p['lon']) for p in e['geometry']]
                if g: unnamed.append((g[-1], brg(g[-2], g[-1]) if len(g) > 1 else None))
            continue
        if e['type'] == 'node': pos, hdg = (e['lat'], e['lon']), None
        else:
            g = [(p['lat'], p['lon']) for p in e['geometry']]
            if not g: continue
            pos = g[-1]; hdg = brg(g[-2], g[-1]) if len(g) > 1 else None
        rec = (pos, hdg)
        if a == 'parking_position': park.setdefault(name, rec)
        else: gate.setdefault(name, rec)
    out = dict(park)
    def dist(a, b): return math.hypot((a[1] - b[1]) * 111320 * math.cos(math.radians(a[0])), (a[0] - b[0]) * 110574)
    for k, (gpos, ghdg) in gate.items():
        if k in park or any(re.fullmatch(re.escape(k) + r'[A-Z]', p) for p in park): continue   # gate 1 vs stands 1A/1B
        if '-' in k: out[k] = (gpos, None); continue                                          # gate serving a range -> AREA
        near = sorted(unnamed, key=lambda u: dist(u[0], gpos))
        if near and dist(near[0][0], gpos) < 80: out[k] = near[0]; unnamed.remove(near[0]); skipped -= 1   # aircraft position, not the gate
        else: out[k] = (gpos, ghdg)
    return out, skipped, 0

def natural(s): return [int(x) if x.isdigit() else x for x in re.split(r'(\d+)', s)]

def main():
    args = [a for a in sys.argv[1:] if a != '--refresh']; refresh = '--refresh' in sys.argv
    icaos = [a.upper() for a in args] or list(BBOX)
    S = open(STANDS, encoding='latin-1').read().replace('\r\n', '\n').split('\n')
    M = open(MAPS, encoding='latin-1').read().replace('\r\n', '\n').split('\n')
    for icao in icaos:
        cf = os.path.join(CACHE, icao + '.json')
        els = json.load(open(cf))['elements'] if os.path.exists(cf) and not refresh else fetch(icao)
        st, skipped, dupes = stands_for(icao, els)
        blk = [f'//>>>> GENERATED STANDS {icao} - tools\\osm_stands.py from OpenStreetMap (c) OSM contributors, ODbL; positions/headings from OSM, review use/size', '']
        for name in sorted(st, key=natural):
            (la, lo), hdg = st[name]; area = name.upper().startswith('APRON') or '-' in name
            blk.append(f"STAND:{icao}:{name}:{dms(la, 'N', 'S')}:{dms(lo, 'E', 'W')}:{(40.0 if '-' in name else AREA_RADIUS) if area else RADIUS:.1f}")
            if area: blk.append('AREA')
            elif hdg is not None: blk.append(f'HEADING:{hdg:.1f}:30')
            blk.append('')
        blk.append(f'//<<<< END GENERATED STANDS {icao}')
        i = next((k for k, l in enumerate(S) if l.startswith(f'//>>>> GENERATED STANDS {icao}')), None)
        if i is not None: j = S.index(f'//<<<< END GENERATED STANDS {icao}', i); del S[i:j + 1]
        else: i = len(S); S += ['']; i += 1
        if st: S[i:i] = blk
        heli = [e for e in els if e['tags'].get('aeroway') == 'helipad']
        hb = []
        if heli and icao not in HELI_SKIP:
            hb = [f'//>>>> GENERATED HELIPADS {icao} - tools\\osm_stands.py from OpenStreetMap (c) OSM contributors, ODbL',
                  f'MAP:{icao} Helipads', f'FOLDER:{icao}', f'AIRPORT:{icao}', 'ACTIVE:1', 'LAYER:15', 'COLOR:SMGS_HELI']
            for e in heli:
                la, lo = (e['lat'], e['lon']) if e['type'] == 'node' else centroid(e['geometry'])
                hb.append(f"SYMBOL:HELIPAD:{dms(la, 'N', 'S')}:{dms(lo, 'E', 'W')}")
            hb.append(f'//<<<< END GENERATED HELIPADS {icao}')
        k = next((x for x, l in enumerate(M) if l.startswith(f'//>>>> GENERATED HELIPADS {icao}')), None)
        if k is not None: j = M.index(f'//<<<< END GENERATED HELIPADS {icao}', k); del M[k:j + 1]
        else: k = next((x for x, l in enumerate(M) if l == f'MAP:{icao} Runway Arrows'), len(M))
        if hb: M[k:k] = hb + ['']
        print(f'{icao}: {len(st)} stands ({", ".join(sorted(st, key=natural))})' + (f'; {skipped} unnamed positions skipped' if skipped else '') + (f'; {len(hb) - 8} helipads' if hb else ''))
    bak = os.path.join(GRP, '_bak'); os.makedirs(bak, exist_ok=True); ts = time.strftime('.bak_%Y%m%d_%H%M%S')
    for f, L in ((STANDS, S), (MAPS, M)):
        shutil.copy(f, os.path.join(bak, os.path.basename(f) + ts)); open(f, 'w', encoding='latin-1', newline='\r\n').write('\n'.join(L))

if __name__ == '__main__': main()
