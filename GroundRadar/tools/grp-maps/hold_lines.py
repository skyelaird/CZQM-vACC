"""
hold_lines.py - runway holding position bars: 200 ft (61 m) from the runway edge on every taxiway that
leaves a runway, and across intersecting runways. Taxiway centrelines from OSM (c) OSM contributors, ODbL;
runway thresholds from the sector file; runway widths from the CFS.
Usage: python hold_lines.py [ICAO ...]   (default: all)
"""
import glob, json, math, os, re, shutil, sys, time, urllib.request, xml.etree.ElementTree as ET
from shapely.geometry import LineString, Point, MultiPoint, MultiLineString
from shapely.ops import unary_union
HERE = os.path.dirname(os.path.abspath(__file__)); GRP = os.path.dirname(HERE); MAPS = os.path.join(GRP, 'GRpluginMaps.txt')
CACHE = os.path.join(HERE, 'osm_cache'); os.makedirs(CACHE, exist_ok=True)
SCT = sorted(glob.glob(os.path.join(GRP, '..', '..', '..', 'CZQQ-CZQM-*.sct')))[-1]
HOLD_FT = 200.0; BAR_HALF = 13.0
HOLD_CL_FT = {'CYHZ': {('L', '05/23'): 525, ('C', '05/23'): 376, ('K', '05/23'): 375}}   # charted hold distances from runway centreline (Joel); default = edge + 200 ft
SKIP = {'CYYR': [(53.31290, -60.42860)]}   # (lat, lon) of bars to suppress (within 40 m): CYYR unnamed way N of C = maintenance road (Joel)
DISPLACED = {'CYHZ': {'23': 361}, 'LFVP': {'26': 197}}   # ft, Navigraph AIRAC 2610 - sector file thresholds are the landing thresholds
WIDTH_FT = {'CYHZ': {'05': 200, '14': 200}, 'CYFC': {'09': 200, '15': 150}, 'CYQM': {'06': 200, '11': 200}, 'CYQX': {'03': 200, '13': 200},
            'CYYR': {'08': 200, '15': 200}, 'CYYT': {'10': 200, '16': 200}, 'CYZX': {'08': 200, '12': 200}, 'LFVP': {'08': 148}}   # CFS RWY DATA
BBOX = {'CYHZ': [(-63.545, 44.862, -63.480, 44.905)], 'CYFC': [(-66.572, 45.848, -66.502, 45.892)], 'CYQM': [(-64.714, 46.090, -64.644, 46.134)],
        'CYQX': [(-54.603, 48.915, -54.533, 48.959)], 'CYYR': [(-60.461, 53.297, -60.391, 53.341)],
        'CYYT': [(-52.775, 47.608, -52.750, 47.632), (-52.750, 47.605, -52.725, 47.630)],
        'CYZX': [(-64.953, 44.962, -64.883, 45.006)], 'LFVP': [(-56.209, 46.741, -56.139, 46.785)]}
def P(s):
    h = s[0]; d, m, a, b = s[1:].split('.'); v = int(d) + int(m) / 60 + float(a + '.' + b) / 3600
    return -v if h in 'SW' else v
def dms(v, p, n):
    h = p if v >= 0 else n; v = abs(v); d = int(v); m = int((v - d) * 60); s = round((v - d - m / 60) * 3600, 3)
    if s >= 60: s -= 60; m += 1
    if m == 60: m = 0; d += 1
    return f'{h}{d:03d}.{m:02d}.{s:06.3f}'
def taxiways(icao):
    f = os.path.join(CACHE, icao + '_taxiways.json')
    if os.path.exists(f): return json.load(open(f))
    out = []
    for w, s, e, n in BBOX[icao]:
        x = urllib.request.urlopen(urllib.request.Request(f'https://api.openstreetmap.org/api/0.6/map?bbox={w},{s},{e},{n}', headers={'User-Agent': 'GRPmapBuilder/1.0'}), timeout=55).read()
        r = ET.fromstring(x); N = {q.get('id'): (float(q.get('lat')), float(q.get('lon'))) for q in r.iter('node')}
        for wy in r.iter('way'):
            t = {g.get('k'): g.get('v') for g in wy.findall('tag')}
            if t.get('aeroway') == 'taxiway':
                out.append({'id': wy.get('id'), 'ref': t.get('ref'), 'pts': [N[q.get('ref')] for q in wy.findall('nd') if q.get('ref') in N]})
    json.dump(out, open(f, 'w')); return out
def main():
    icaos = [a.upper() for a in sys.argv[1:]] or list(WIDTH_FT)
    rws = {}; sec = None
    for l in open(SCT, encoding='latin-1'):
        if l.startswith('['): sec = l.strip(); continue
        p = l.split()
        if sec == '[RUNWAY]' and len(p) >= 9 and p[8] in WIDTH_FT: rws.setdefault(p[8], []).append(p)
    M = open(MAPS, encoding='latin-1').read().replace('\r\n', '\n').split('\n')
    for icao in icaos:
        rw = rws[icao]; la0 = P(rw[0][4]); lo0 = P(rw[0][5]); k = math.cos(math.radians(la0))
        xy = lambda la, lo: ((lo - lo0) * 111320 * k, (la - la0) * 110574); ll = lambda X, Y: (Y / 110574 + la0, X / (111320 * k) + lo0)
        R = []
        for p in rw:
            wd = WIDTH_FT[icao].get(p[0], 200) * 0.3048
            a = xy(P(p[4]), P(p[5])); b = xy(P(p[6]), P(p[7])); n = math.dist(a, b); u = ((b[0] - a[0]) / n, (b[1] - a[1]) / n)
            da = DISPLACED.get(icao, {}).get(p[0], 0) * 0.3048; db = DISPLACED.get(icao, {}).get(p[1], 0) * 0.3048   # out to the pavement ends
            line = LineString([(a[0] - u[0] * da, a[1] - u[1] * da), (b[0] + u[0] * db, b[1] + u[1] * db)])
            R.append({'id': f'{p[0]}/{p[1]}', 'line': line, 'w': wd, 'ring': MultiLineString([line.parallel_offset(wd / 2 + HOLD_FT * 0.3048, s) for s in ('left', 'right')])})   # sides only: no bars beyond the runway ends
        cross = []   # (point, direction, half length, label)
        for t in taxiways(icao):
            if len(t['pts']) < 2: continue
            g = LineString([xy(*q) for q in t['pts']])
            for r in R:
                dcl = HOLD_CL_FT.get(icao, {}).get((t['ref'], r['id']))      # charted distance from the runway centreline
                D = dcl * 0.3048 if dcl else r['w'] / 2 + HOLD_FT * 0.3048
                ring = MultiLineString([r['line'].parallel_offset(D, s) for s in ('left', 'right')])
                x = g.intersection(ring)
                for pt in ([x] if x.geom_type == 'Point' else list(getattr(x, 'geoms', []))):
                    if any(o['line'].buffer(o['w'] / 2 + 5).contains(pt) for o in R): continue      # point lies on another runway
                    # bar perpendicular to the taxiway, moved outward until its NEAREST end is at D (oblique crossings)
                    d = g.project(pt); step = 1.0 if g.interpolate(min(g.length, d + 1)).distance(r['line']) > pt.distance(r['line']) else -1.0
                    for _ in range(80):
                        c = g.interpolate(d); a = g.interpolate(max(0, d - 5)); b = g.interpolate(min(g.length, d + 5))
                        dx, dy = b.x - a.x, b.y - a.y; L = math.hypot(dx, dy) or 1; nx, ny = -dy / L, dx / L
                        e1 = Point(c.x + nx * BAR_HALF, c.y + ny * BAR_HALF); e2 = Point(c.x - nx * BAR_HALF, c.y - ny * BAR_HALF)
                        if min(e1.distance(r['line']), e2.distance(r['line'])) >= D - 0.3 or not (0 < d < g.length): break
                        d += step * 0.5
                    cross.append((c, (dx, dy), BAR_HALF, f"twy {t['ref'] or '-'} / rwy {r['id']}" + (f' ({dcl:g} ft CL, charted)' if dcl else '')))
        for r in R:
            for o in R:
                if o is r: continue
                x = o['line'].intersection(r['ring'])
                for pt in ([x] if x.geom_type == 'Point' else list(getattr(x, 'geoms', []))):
                    c = o['line'].coords; cross.append((pt, (c[1][0] - c[0][0], c[1][1] - c[0][1]), o['w'] / 2, f"rwy {o['id']} / rwy {r['id']}"))
        bars, used = [], []
        skip = [Point(xy(a, b)) for a, b in SKIP.get(icao, [])]
        for pt, (dx, dy), half, lab in cross:
            if any(pt.distance(u) < 20 for u in used) or any(pt.distance(q) < 40 for q in skip): continue
            used.append(pt); L = math.hypot(dx, dy); nx, ny = -dy / L, dx / L
            a = ll(pt.x + nx * half, pt.y + ny * half); b = ll(pt.x - nx * half, pt.y - ny * half)
            bars.append((lab, a, b))
        B = [f'//>>>> GENERATED HOLD LINES {icao} - tools\\hold_lines.py: {HOLD_FT:g} ft from runway edge (CFS widths), taxiways from OSM (c) OSM contributors, ODbL',
             f'MAP:{icao} Hold Lines', f'FOLDER:{icao}', f'AIRPORT:{icao}', 'ACTIVE:1', 'LAYER:15', 'COLOR:HOLD_BAR', 'STYLE:SOLID:2']
        for lab, a, b in bars:
            B.append(f'// {lab}'); B.append(f"LINE:{dms(a[0], 'N', 'S')}:{dms(a[1], 'E', 'W')}:{dms(b[0], 'N', 'S')}:{dms(b[1], 'E', 'W')}")
        B.append(f'//<<<< END GENERATED HOLD LINES {icao}')
        i = next((x for x, l in enumerate(M) if l.startswith(f'//>>>> GENERATED HOLD LINES {icao}')), None)
        if i is not None: j = M.index(f'//<<<< END GENERATED HOLD LINES {icao}', i); del M[i:j + 1]
        else: i = next((x for x, l in enumerate(M) if l == f'MAP:{icao} Runway Arrows'), len(M))
        M[i:i] = B + ['']
        print(f'{icao}: {len(bars)} hold lines ({sum(1 for b in bars if b[0].startswith("rwy"))} at runway intersections)')
    if not any(l.startswith('COLORDEF:HOLD_BAR') for l in M):
        M.insert(next(x for x, l in enumerate(M) if l.startswith('COLORDEF:PARKLINE_DIM')) + 1, 'COLORDEF:HOLD_BAR:165:145:70')
    bak = os.path.join(GRP, '_bak'); shutil.copy(MAPS, os.path.join(bak, 'GRpluginMaps.txt' + time.strftime('.bak_%Y%m%d_%H%M%S')))
    open(MAPS, 'w', encoding='latin-1', newline='\r\n').write('\n'.join(M))
if __name__ == '__main__': main()
