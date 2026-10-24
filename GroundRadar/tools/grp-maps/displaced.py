"""
displaced.py - displaced threshold depiction: a threshold bar across the runway and two arrows in the
displaced section pointing to it. Thresholds from the sector file (landing thresholds); displacements
from Navigraph AIRAC 2610 (Little Navmap runway_end.offset_threshold). Usage: python displaced.py
"""
import math, os, shutil, time
import hold_lines as H
DISPLACED = {'CYHZ': {'23': 361}, 'LFVP': {'26': 197}}   # ft
def main():
    M = open(H.MAPS, encoding='latin-1').read().replace('\r\n', '\n').split('\n')
    rws = {}
    for l in open(H.SCT, encoding='latin-1'):
        p = l.split()
        if len(p) >= 9 and p[8] in DISPLACED: rws.setdefault(p[8], []).append(p)
    for icao, ends in DISPLACED.items():
        p0 = rws[icao][0]; la0 = H.P(p0[4]); lo0 = H.P(p0[5]); k = math.cos(math.radians(la0))
        xy = lambda la, lo: ((lo - lo0) * 111320 * k, (la - la0) * 110574); ll = lambda X, Y: (Y / 110574 + la0, X / (111320 * k) + lo0)
        L = lambda a, b: f"LINE:{H.dms(a[0], 'N', 'S')}:{H.dms(a[1], 'E', 'W')}:{H.dms(b[0], 'N', 'S')}:{H.dms(b[1], 'E', 'W')}"
        B = [f'//>>>> GENERATED DISPLACED THRESHOLDS {icao} - tools\\displaced.py (Navigraph AIRAC 2610)',
             f'MAP:{icao} Displaced Thresholds', f'FOLDER:{icao}', f'AIRPORT:{icao}', 'ACTIVE:1', 'HIDDEN', 'LAYER:16', 'COLOR:THR_WHITE', 'STYLE:SOLID:1']
        for p in rws[icao]:
            for me, other, i in ((p[0], p[1], 4), (p[1], p[0], 6)):
                if me not in ends: continue
                T = xy(H.P(p[i]), H.P(p[i + 1])); O = xy(H.P(p[10 - i]), H.P(p[11 - i]))
                d = math.hypot(T[0] - O[0], T[1] - O[1]); ux, uy = (O[0] - T[0]) / d, (O[1] - T[1]) / d   # into the runway
                nx, ny = -uy, ux; D = ends[me] * 0.3048; hw = H.WIDTH_FT[icao].get(min(p[0], p[1]), 200) * 0.3048 / 2
                E = (T[0] - ux * D, T[1] - uy * D)                                                            # pavement end
                at = lambda s, n=0: ll(E[0] + ux * s + nx * n, E[1] + uy * s + ny * n)
                B.append(f'// RWY {me} displaced {ends[me]} ft: threshold bar')
                B.append('STYLE:SOLID:3'); B.append(L(at(D, hw), at(D, -hw))); B.append('STYLE:SOLID:1')
                al = 0.3 * D; hl = min(10, al * 0.4); hwid = hl * 0.7
                for c in (0.3 * D, 0.72 * D):
                    s0, s1 = c - al / 2, c + al / 2
                    B.append(f'// RWY {me} arrow'); B.append(L(at(s0), at(s1)))
                    B.append(L(at(s1), at(s1 - hl, hwid))); B.append(L(at(s1), at(s1 - hl, -hwid)))
        B.append(f'//<<<< END GENERATED DISPLACED THRESHOLDS {icao}')
        i = next((x for x, l in enumerate(M) if l.startswith(f'//>>>> GENERATED DISPLACED THRESHOLDS {icao}')), None)
        if i is not None: j = M.index(f'//<<<< END GENERATED DISPLACED THRESHOLDS {icao}', i); del M[i:j + 1]
        else: i = M.index(f'//<<<< END GENERATED HOLD LINES {icao}') + 1
        M[i:i] = B
        print(icao, 'done')
    if not any(l.startswith('COLORDEF:THR_WHITE') for l in M):
        M.insert(next(x for x, l in enumerate(M) if l.startswith('COLORDEF:HOLD_BAR')) + 1, 'COLORDEF:THR_WHITE:150:155:160')
    shutil.copy(H.MAPS, os.path.join(H.GRP, '_bak', 'GRpluginMaps.txt' + time.strftime('.bak_%Y%m%d_%H%M%S')))
    open(H.MAPS, 'w', encoding='latin-1', newline='\r\n').write('\n'.join(M))
if __name__ == '__main__': main()
