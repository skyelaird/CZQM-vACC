"""rwy_markings.py - ICAO Annex 14 runway markings generated from the sector-file thresholds, drawn filled
(threshold stripes, designation numbers, aiming point, touchdown zone) plus centreline and side stripes.
Shown only when zoomed in (ZOOM). Usage: python rwy_markings.py [ICAO ...]   (default CYHZ)
Refs: Annex 14 Vol I 5.2.2 designation (9 m high numbers, Fig 5-3), 5.2.3 centre line (30 m stripe / 20 m gap,
0.45 m), 5.2.4 threshold (stripes 30 m x 1.8 m, 1.8 m spacing, 6 m in; count by width), 5.2.5 aiming point
(Table 5-1), 5.2.6 touchdown zone (pairs at 150 m, count by LDA, pattern A), 5.2.7 side stripes."""
import math, os, sys, shutil, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import hold_lines as H
from shapely.geometry import Polygon, LineString, box
from shapely.ops import unary_union
from shapely import affinity
ZOOM_FINE = 700      # px/NM below which the markings are not drawn
# ---- digits: 3 m x 9 m cell, 0.75 m strokes (7-segment rendering of Annex 14 Fig 5-3 proportions)
W, Hh, S = 3.0, 9.0, 0.75
SEG = {'a': box(0, Hh - S, W, Hh), 'g': box(0, Hh / 2 - S / 2, W, Hh / 2 + S / 2), 'd': box(0, 0, W, S),
       'f': box(0, Hh / 2, S, Hh), 'b': box(W - S, Hh / 2, W, Hh), 'e': box(0, 0, S, Hh / 2), 'c': box(W - S, 0, W, Hh / 2),
       'm': box(W / 2 - S / 2, 0, W / 2 + S / 2, Hh)}
DIG = {'0': 'abcdef', '1': 'm', '2': 'abged', '3': 'abgcd', '4': 'fgbc', '5': 'afgcd', '6': 'afgedc', '7': 'abc', '8': 'abcdefg', '9': 'abcdfg'}
def number(txt):      # polygons in a local frame: x across (right of centreline +), y along from the base line
    gap = 1.5; tot = len(txt) * W + (len(txt) - 1) * gap; x0 = -tot / 2; out = []
    for i, ch in enumerate(txt):
        if ch in DIG: out += [affinity.translate(SEG[s], x0 + i * (W + gap), 0) for s in DIG[ch]]   # one polygon per stroke: GRP fills ignore holes (0, 6, 8, 9)
    return out
def aim_tdz(lda):     # (aiming point dist, aim length, aim width, inner spacing, number of TDZ pairs)
    if lda < 800: return 150, 30, 4, 6, 1
    if lda < 1200: return 250, 45, 6, 9, 2
    if lda < 1500: return 300, 60, 9, 18, 3
    if lda < 2400: return 300, 60, 9, 18, 4
    return 400, 60, 9, 18, 6
def stripes_for(width):
    return 4 if width < 22.5 else 6 if width < 30 else 8 if width < 45 else 12 if width < 60 else 16
NOT_PAVE = ('COLOR_GrasSurface', 'COLOR_Building', 'COLOR_Labels', 'COLOR_Water', 'COLOR_Grass')
def pavement(icao, xy):
    import re
    sec = None; regs = []; g = None
    for l in open(H.SCT, encoding='latin-1'):
        if l.startswith('['): sec = l.strip(); continue
        if sec != '[REGIONS]': continue
        if l.startswith('REGIONNAME'): g = {'n': l[11:].strip(), 'c': None, 'p': []}; regs.append(g); continue
        m = re.findall(r'([NS]\d{3}\.\d\d\.\d\d\.\d+)\s+([EW]\d{3}\.\d\d\.\d\d\.\d+)', l)
        if g and m:
            if g['c'] is None: g['c'] = l.split()[0]
            g['p'] += [xy(H.P(a), H.P(b)) for a, b in m]
    P = [Polygon(q['p']).buffer(0) for q in regs if q['n'].startswith(icao) and q['c'] not in NOT_PAVE and len(q['p']) > 2]
    return unary_union(P) if P else None
def main():
    icaos = [a.upper() for a in sys.argv[1:]] or ['CYHZ']
    rws = {}
    for l in open(H.SCT, encoding='latin-1'):
        p = l.split()
        if len(p) >= 9 and p[8] in H.WIDTH_FT: rws.setdefault(p[8], []).append(p)
    M = open(H.MAPS, encoding='latin-1').read().replace('\r\n', '\n').split('\n')
    for icao in icaos:
        p0 = rws[icao][0]; la0 = H.P(p0[4]); lo0 = H.P(p0[5]); k = math.cos(math.radians(la0))
        xy = lambda la, lo: ((lo - lo0) * 111320 * k, (la - la0) * 110574); ll = lambda X, Y: (Y / 110574 + la0, X / (111320 * k) + lo0)
        R = []
        for p in rws[icao]:
            a = xy(H.P(p[4]), H.P(p[5])); b = xy(H.P(p[6]), H.P(p[7])); w = H.WIDTH_FT[icao].get(min(p[0], p[1]), 200) * 0.3048
            n = math.dist(a, b); u = ((b[0] - a[0]) / n, (b[1] - a[1]) / n)
            da = H.DISPLACED.get(icao, {}).get(p[0], 0) * 0.3048; db = H.DISPLACED.get(icao, {}).get(p[1], 0) * 0.3048
            pa = (a[0] - u[0] * da, a[1] - u[1] * da); pb = (b[0] + u[0] * db, b[1] + u[1] * db)   # pavement ends
            R.append(dict(ends=[(p[0], a, u, n), (p[1], b, (-u[0], -u[1]), n)], w=w, pa=pa, pb=pb, len=math.dist(pa, pb),
                          strip=LineString([pa, pb]).buffer(w / 2, cap_style='flat')))
        primary = max(R, key=lambda r: r['len'])
        polys, lines = [], []
        for r in R:
            others = unary_union([o['strip'] for o in R if o is not r]) if len(R) > 1 else Polygon()
            w = r['w']; hw = w / 2
            for name, t, u, lda in r['ends']:
                v = (-u[1], u[0])                                   # across-runway unit vector
                def rect(s0, s1, x0, x1):                           # along s0..s1 from threshold, across x0..x1 from CL
                    return Polygon([(t[0] + u[0] * s + v[0] * x, t[1] + u[1] * s + v[1] * x) for s, x in ((s0, x0), (s1, x0), (s1, x1), (s0, x1))])
                def place(g, s_base):                               # local number frame -> world (base toward threshold, read on approach)
                    return Polygon([(t[0] + u[0] * (s_base + y) + v[0] * (-x), t[1] + u[1] * (s_base + y) + v[1] * (-x)) for x, y in g.exterior.coords])
                # threshold stripes
                ns = stripes_for(w); sw = 1.8; half = ns // 2
                for i in range(half):
                    x0 = 1.8 + i * 3.6; polys += [rect(6, 36, x0, x0 + sw), rect(6, 36, -x0 - sw, -x0)]
                # designation number, 12 m beyond the stripes
                for g in number(name.lstrip('0') if len(name) == 3 else name): polys.append(place(g, 48))
                # aiming point + touchdown zone (pattern A: 3,2,2,1,1,1 stripes at 150 m steps)
                ad, al, aw, sp, pairs = aim_tdz(lda)
                cand = [rect(ad, ad + al, sp / 2, sp / 2 + aw), rect(ad, ad + al, -sp / 2 - aw, -sp / 2)]
                pattern = [3, 2, 2, 1, 1, 1]; placed = 0; s = 150
                while placed < pairs and s < lda / 2:
                    if abs(s - ad) > 50:          # pairs within 50 m of the aiming point are deleted (5.2.6.4)
                        nb = pattern[min(placed, 5)]
                        for j in range(nb):
                            x0 = sp / 2 + j * 3.3
                            cand += [rect(s, s + 22.5, x0, x0 + 1.8), rect(s, s + 22.5, -x0 - 1.8, -x0)]
                    placed += 1; s += 150
                polys += [c for c in cand if not c.intersects(others)]
            # centre line (30 m stripe, 20 m gap) between the numbers; side stripes threshold to threshold
            (n1, t1, u1, L), (n2, t2, _, _) = r['ends']; s = 70.0
            while s + 30 <= L - 70:
                seg = LineString([(t1[0] + u1[0] * s, t1[1] + u1[1] * s), (t1[0] + u1[0] * (s + 30), t1[1] + u1[1] * (s + 30))])
                if r is primary or not seg.intersects(others): lines.append(seg)
                s += 50
            v1 = (-u1[1], u1[0])
            for sg in (1, -1):
                e = LineString([(t1[0] + v1[0] * sg * (hw - 0.45), t1[1] + v1[1] * sg * (hw - 0.45)), (t2[0] + v1[0] * sg * (hw - 0.45), t2[1] + v1[1] * sg * (hw - 0.45))])
                d = e.difference(others.buffer(1)) if r is not primary else e
                lines += [q for q in (d.geoms if hasattr(d, 'geoms') else [d]) if q.length > 5]
        pave = pavement(icao, xy)
        if pave is not None and not pave.is_empty:      # drop anything the sector file shows off the paved surface
            pz = pave.buffer(1.5); nb = len(polys)
            polys = [q for q in polys if q.intersection(pz).area >= 0.9 * q.area]
            cl = []
            for q in lines:
                x = q.intersection(pz); cl += [g for g in (x.geoms if hasattr(x, 'geoms') else [x]) if g.geom_type == 'LineString' and g.length > 5]
            lines = cl
            if nb - len(polys): print(f'  {icao}: {nb - len(polys)} markings off the paved surface dropped')
        C = lambda q: f"{H.dms(q[0], 'N', 'S')}:{H.dms(q[1], 'E', 'W')}"
        B = [f'//>>>> GENERATED RWY MARKINGS {icao} - tools\\\\rwy_markings.py: ICAO Annex 14 5.2 from sector-file thresholds (Joel 2026-10-24)',
             f'MAP:{icao} Runway Markings', f'FOLDER:{icao}', f'AIRPORT:{icao}', 'ACTIVE:1', 'HIDDEN', 'LAYER:6', 'COLOR:THR_WHITE', f'ZOOM:{ZOOM_FINE}', 'STYLE:SOLID:1']
        for q in lines:
            c = list(q.coords); B.append(f'LINE:{C(ll(*c[0]))}:{C(ll(*c[-1]))}')
        for q in polys:
            B.append('COORDTYPE:OTHER:REGION_FILLONLY'); B += [f'COORD:{C(ll(*c))}' for c in list(q.exterior.coords)[:-1]]
        B.append(f'//<<<< END GENERATED RWY MARKINGS {icao}')
        i = next((x for x, l in enumerate(M) if l.startswith(f'//>>>> GENERATED RWY MARKINGS {icao}')), None)
        if i is not None: j = M.index(f'//<<<< END GENERATED RWY MARKINGS {icao}', i); del M[i:j + 1]; M[i:i] = B
        else: i = next((x for x, l in enumerate(M) if l.startswith(f'//>>>> GENERATED HOLD LINES {icao}')), len(M)); M[i:i] = B + ['']
        print(f'{icao}: {len(polys)} filled markings, {len(lines)} line segments')
    shutil.copy(H.MAPS, os.path.join(H.GRP, '_bak', 'GRpluginMaps.txt' + time.strftime('.bak_%Y%m%d_%H%M%S')))
    open(H.MAPS, 'w', encoding='latin-1', newline='\r\n').write('\n'.join(M))
if __name__ == '__main__': main()
