"""rwy_overrun.py - repaint runway-coloured pavement beyond each runway's end (turn pads, overruns, blast pads drawn
as runway in the sector file) in the apron/taxiway colour, so the runway shows only from threshold to threshold
(displaced sections kept as runway). Always on and hidden from the menu (Joel 2026-10-24).
Usage: python rwy_overrun.py [ICAO ...]"""
import re, math, os, sys, shutil, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import hold_lines as H
from shapely.geometry import Polygon, LineString
from shapely.ops import unary_union
RWY_COLOUR = 'COLOR_HardSurface3'; MIN_AREA = 250.0   # ignore edge slivers
def main():
    icaos = [a.upper() for a in sys.argv[1:]] or [i for i in H.WIDTH_FT if i != 'LFVP']
    sec = None; regs = []; g = None
    for l in open(H.SCT, encoding='latin-1'):
        if l.startswith('['): sec = l.strip(); continue
        if sec != '[REGIONS]': continue
        if l.startswith('REGIONNAME'): g = {'n': l[11:].strip(), 'c': None, 'p': []}; regs.append(g); continue
        m = re.findall(r'([NS]\d{3}\.\d\d\.\d\d\.\d+)\s+([EW]\d{3}\.\d\d\.\d\d\.\d+)', l)
        if g and m:
            if g['c'] is None: g['c'] = l.split()[0]
            g['p'] += [(H.P(a), H.P(b)) for a, b in m]
    rws = {}
    for l in open(H.SCT, encoding='latin-1'):
        p = l.split()
        if len(p) >= 9 and p[8] in H.WIDTH_FT: rws.setdefault(p[8], []).append(p)
    M = open(H.MAPS, encoding='latin-1').read().replace('\r\n', '\n').split('\n')
    for icao in icaos:
        p0 = rws[icao][0]; la0 = H.P(p0[4]); lo0 = H.P(p0[5]); k = math.cos(math.radians(la0))
        xy = lambda la, lo: ((lo - lo0) * 111320 * k, (la - la0) * 110574); ll = lambda X, Y: (Y / 110574 + la0, X / (111320 * k) + lo0)
        R = unary_union([Polygon([xy(*c) for c in q['p']]).buffer(0) for q in regs if q['n'].startswith(icao) and q['c'] == RWY_COLOUR and len(q['p']) > 2])
        # runway proper: threshold-to-threshold strips (extended over displaced sections)
        strips, ends = [], []
        for p in rws[icao]:
            a = xy(H.P(p[4]), H.P(p[5])); b = xy(H.P(p[6]), H.P(p[7])); n = math.dist(a, b); u = ((b[0] - a[0]) / n, (b[1] - a[1]) / n)
            da = H.DISPLACED.get(icao, {}).get(p[0], 0) * 0.3048; db = H.DISPLACED.get(icao, {}).get(p[1], 0) * 0.3048
            a2 = (a[0] - u[0] * da, a[1] - u[1] * da); b2 = (b[0] + u[0] * db, b[1] + u[1] * db)
            w = H.WIDTH_FT[icao].get(min(p[0], p[1]), 200) * 0.3048
            strips.append(LineString([a2, b2]).buffer(w / 2 + 25, cap_style='flat'))
            for e, o, nm in ((a2, (-u[0], -u[1]), p[0]), (b2, u, p[1])):      # outward box beyond each end
                nx, ny = -o[1], o[0]; hw = w / 2 + 80
                ends.append((nm, Polygon([(e[0] + nx * hw, e[1] + ny * hw), (e[0] + nx * hw + o[0] * 400, e[1] + ny * hw + o[1] * 400),
                                          (e[0] - nx * hw + o[0] * 400, e[1] - ny * hw + o[1] * 400), (e[0] - nx * hw, e[1] - ny * hw)])))
        keep = unary_union(strips)
        B = [f'//>>>> GENERATED RWY OVERRUN {icao} - tools\\\\rwy_overrun.py: sector-file runway pavement beyond the runway ends repainted as apron/taxiway (always on, hidden from the menu)',
             f'MAP:{icao} Runway End Pavement', f'FOLDER:{icao}', f'AIRPORT:{icao}', 'ACTIVE:1', 'HIDDEN', 'LAYER:2', 'COLOR:OVERRUN']
        rep = []
        for nm, box in ends:
            x = R.intersection(box).difference(keep)
            parts = [q for q in (x.geoms if hasattr(x, 'geoms') else [x]) if q.geom_type == 'Polygon' and q.area > MIN_AREA]
            if parts: rep.append(f'{nm} {round(sum(q.area for q in parts))} m2')
            for q in parts:
                B.append(f'// beyond RWY {nm}'); B.append('COORDTYPE:OTHER:REGION_FILLONLY')
                B += [f"COORD:{H.dms(a, 'N', 'S')}:{H.dms(b, 'E', 'W')}" for a, b in (ll(*c) for c in list(q.simplify(0.3).exterior.coords)[:-1])]
        B.append(f'//<<<< END GENERATED RWY OVERRUN {icao}')
        i = next((x for x, l in enumerate(M) if l.startswith(f'//>>>> GENERATED RWY OVERRUN {icao}')), None)
        if i is not None: j = M.index(f'//<<<< END GENERATED RWY OVERRUN {icao}', i); del M[i:j + 1]; ins = []
        else: i = next((x for x, l in enumerate(M) if l.startswith(f'//>>>> GENERATED HOLD LINES {icao}')), len(M)); ins = ['']
        if rep: M[i:i] = B + ins
        print(icao, ', '.join(rep) or 'nothing beyond the runway ends')
    if not any(l.startswith('COLORDEF:OVERRUN') for l in M):
        M.insert(next(x for x, l in enumerate(M) if l.startswith('COLORDEF:HOLD_BAR')) + 1, 'COLORDEF:OVERRUN:47:47:47')   # = sector-file COLOR_ApronSurface
    shutil.copy(H.MAPS, os.path.join(H.GRP, '_bak', 'GRpluginMaps.txt' + time.strftime('.bak_%Y%m%d_%H%M%S')))
    open(H.MAPS, 'w', encoding='latin-1', newline='\r\n').write('\n'.join(M))
if __name__ == '__main__': main()
