"""
stand_markers.py - draws each stand from GRpluginStands.txt as a map layer, so the picture always matches the stand data.
Per stand: a ground-scaled circle (stand detection radius, max 15 m), a nose tick along the stand heading,
and the stand number centred in the circle (numbers hidden when zoomed out). AREA stands: number only.
Usage: python stand_markers.py            (all airports in the stands file)
Writes managed blocks //>>>> GENERATED STAND MARKERS <ICAO> in GRpluginMaps.txt.
"""
import math, os, re, shutil, time
HERE = os.path.dirname(os.path.abspath(__file__)); GRP = os.path.dirname(HERE)
STANDS = os.path.join(GRP, 'GRpluginStands.txt'); MAPS = os.path.join(GRP, 'GRpluginMaps.txt')
MAX_R, SEG, LABEL_ZOOM = 15.0, 16, 800
def P(s):
    h = s[0]; d, m, a, b = s[1:].split('.'); v = int(d) + int(m) / 60 + float(a + '.' + b) / 3600
    return -v if h in 'SW' else v
def dms(v, p, n):
    h = p if v >= 0 else n; v = abs(v); d = int(v); m = int((v - d) * 60); s = round((v - d - m / 60) * 3600, 3)
    if s >= 60: s -= 60; m += 1
    if m == 60: m = 0; d += 1
    return f'{h}{d:03d}.{m:02d}.{s:06.3f}'
def off(la, lo, brg, dist):
    k = math.cos(math.radians(la)); b = math.radians(brg)
    return la + dist * math.cos(b) / 110574, lo + dist * math.sin(b) / (111320 * k)
def C(la, lo): return f"{dms(la, 'N', 'S')}:{dms(lo, 'E', 'W')}"
def main():
    st, cur = {}, None
    for l in open(STANDS, encoding='latin-1').read().replace('\r\n', '\n').split('\n'):
        if l.startswith('STAND:'):
            p = l.split(':')
            if len(p) < 6: continue
            cur = {'n': p[2], 'la': P(p[3]), 'lo': P(p[4]), 'r': float(p[5]), 'h': None, 'area': False}
            st.setdefault(p[1], {})[p[2]] = cur
        elif cur and l.startswith('HEADING:'): cur['h'] = float(l.split(':')[1])
        elif cur and l.strip() == 'AREA': cur['area'] = True
        elif l.startswith('//>>>>') or l.startswith('//<<<<'): cur = None
    M = open(MAPS, encoding='latin-1').read().replace('\r\n', '\n').split('\n')
    for icao, ss in st.items():
        B = [f'//>>>> GENERATED STAND MARKERS {icao} - tools\\stand_markers.py from GRpluginStands.txt; rerun after stand changes',
             f'MAP:{icao} Stand Markers', f'FOLDER:{icao}', f'AIRPORT:{icao}', 'ACTIVE:1', 'LAYER:12',
             'COLOR:STAND_MARK', 'STYLE:SOLID:1']
        for s in ss.values():
            if s['area']: continue
            r = min(MAX_R, s['r'])
            B.append('COORDTYPE:OTHER:POLYGON')
            B += ['COORD:' + C(*off(s['la'], s['lo'], 360 * i / SEG, r)) for i in range(SEG)]
            if s['h'] is not None:
                B.append(f"LINE:{C(*off(s['la'], s['lo'], s['h'], r * 0.35))}:{C(*off(s['la'], s['lo'], s['h'], r * 1.35))}")
        B += [f'ZOOM:{LABEL_ZOOM}', 'COLOR:SMGS_PARKING', 'FONTSIZE:-:3', 'TEXTALIGN:CC']
        B += [f"TEXT:{C(s['la'], s['lo'])}:{s['n']}" for s in ss.values()]
        B.append(f'//<<<< END GENERATED STAND MARKERS {icao}')
        i = next((x for x, l in enumerate(M) if l.startswith(f'//>>>> GENERATED STAND MARKERS {icao}')), None)
        if i is not None: j = M.index(f'//<<<< END GENERATED STAND MARKERS {icao}', i); del M[i:j + 1]
        else: i = next((x for x, l in enumerate(M) if l == f'MAP:{icao} Runway Arrows'), len(M))
        M[i:i] = B + ['']
        print(f'{icao}: {len(ss)} stand markers')
    if not any(l.startswith('COLORDEF:STAND_MARK') for l in M):
        k = next(x for x, l in enumerate(M) if l.startswith('COLORDEF:PARKLINE_DIM')); M.insert(k + 1, 'COLORDEF:STAND_MARK:95:100:105')
    bak = os.path.join(GRP, '_bak'); os.makedirs(bak, exist_ok=True)
    shutil.copy(MAPS, os.path.join(bak, 'GRpluginMaps.txt' + time.strftime('.bak_%Y%m%d_%H%M%S')))
    open(MAPS, 'w', encoding='latin-1', newline='\r\n').write('\n'.join(M))
if __name__ == '__main__': main()
