"""
build_ground.py - generate GRP ground layers for an airport from the current sector file

Usage:  python build_ground.py CYFC [CYQM ...]      (or: python build_ground.py ALL)

Writes, per airport, a managed block in GRpluginMaps.txt between
  //>>>> GENERATED GROUND <ICAO>   and   //<<<< END GENERATED <ICAO>
containing:  Surfaces (SCTFILEDATA REGIONS, auto-updating), Ground Lines,
Parking Lines (faded), Markings (optional), Labels Taxiways / Stands / Buildings.
Lines and labels are static copies of the sector-file GEO / ESE FREETEXT data,
split by colour/type - rerun after each sector-file update.
A timestamped backup of GRpluginMaps.txt is written on every run.
"""
import glob, os, re, shutil, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
MAPS = os.path.normpath(os.path.join(HERE, '..', 'GRpluginMaps.txt'))
ES = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..'))   # ...\EuroScope
SECTOR = sorted(glob.glob(os.path.join(ES, 'CZQQ-CZQM-*.sct')))[-1]
ESEFILE = SECTOR[:-4] + '.ese'

AIRPORTS = {
  'CYFC': dict(region='CYFC Fredericton', geo=['CYFC Groundlayout Fredericton']),
  'CYQM': dict(region='CYQM Moncton',     geo=['CYQM Groundlayout Moncton', 'CYQM Groundlayout CYQM Parking']),
  'CYQX': dict(region='CYQX Gander',      geo=['CYQX Groundlayout Gander']),
  'CYYR': dict(region='CYYR Goose Bay',   geo=['CYYR Groundlayout Goose Bay']),
  'CYYT': dict(region='CYYT St Johns',    geo=['CYYT Groundlayout ST JOHNS']),
  'CYZX': dict(region='CYZX Greenwood',   geo=[]),
  'LFVP': dict(region='LFVP St Pierre',   geo=[]),
}
PARKING = {'COLOR_ParkPos', 'COLOR_ParkPosUnused'}
MARKINGS = {'COLOR_ApronMarking', 'COLOR_RestrictedArea', 'COLOR_Labels', 'COLOR_OtherMarking', 'COLOR_RunwayMarking'}
TWY_RE = re.compile(r'^[A-Z][0-9]?$')
STAND_RE = re.compile(r'^([0-9]+[A-Z]?|[IVX]+)$')

def read(p): return open(p, encoding='latin-1').read().split('\n')

WARN = []
def fix(c, where=''):
    """Normalise a DMS coordinate whose minutes/seconds overflow 60 (bad source data) and warn."""
    m = re.match(r'^([NSEW])(\d{3})\.(\d\d)\.(\d\d)\.(\d+)$', c.strip())
    if not m: return c.strip()
    h, d, mi, se, fr = m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4)), m.group(5)
    if mi < 60 and se < 60: return c.strip()
    tot = d * 3600 + mi * 60 + se
    d, rem = divmod(tot, 3600); mi, se = divmod(rem, 60)
    out = f'{h}{d:03d}.{mi:02d}.{se:02d}.{fr}'
    WARN.append(f'  bad coordinate {c.strip()} -> {out} {where}')
    return out

def sector_data():
    L = read(SECTOR); defs = {}; geo = {}; sec = None; cur = None
    for l in L:
        if l.startswith('#define'):
            p = l.split()
            if len(p) >= 3 and p[2].isdigit(): defs[p[1]] = int(p[2])
            continue
        if l.startswith('['): sec = l.strip(); cur = None; continue
        if sec != '[GEO]' or not l.strip() or l.lstrip().startswith(';'): continue
        m = re.match(r'^(\S.*?)\s+([NS]\d{3}\.\d\d\.\d\d\.\d+)\s+([EW]\d{3}\.\d\d\.\d\d\.\d+)\s+([NS]\d{3}\.\d\d\.\d\d\.\d+)\s+([EW]\d{3}\.\d\d\.\d\d\.\d+)\s*(\S*)', l)
        if m: cur = m.group(1).strip(); g = m.groups()[1:]
        else:
            m = re.match(r'^\s+([NS]\d{3}\.\d\d\.\d\d\.\d+)\s+([EW]\d{3}\.\d\d\.\d\d\.\d+)\s+([NS]\d{3}\.\d\d\.\d\d\.\d+)\s+([EW]\d{3}\.\d\d\.\d\d\.\d+)\s*(\S*)', l)
            if not m or cur is None: continue
            g = m.groups()
        geo.setdefault(cur, []).append(tuple(fix(x, f'(GEO {cur})') for x in g[:4]) + (g[4],))
    return defs, geo

def freetext():
    out = {}; ins = False
    for l in read(ESEFILE):
        if l.startswith('[FREETEXT]'): ins = True; continue
        if ins and l.startswith('['): break
        if ins and l[:1] in 'NS' and l.count(':') >= 3:
            la, lo, grp, txt = l.split(':', 3)
            txt = re.sub(r'\s+', ' ', txt).strip()
            out.setdefault(grp.strip(), []).append((fix(la, f'(ESE {grp.strip()} {txt})'), fix(lo, f'(ESE {grp.strip()} {txt})'), txt))
    return out

RWY_AIRPORTS = ['CYHZ', 'CYFC', 'CYQM', 'CYQX', 'CYYR', 'CYYT', 'CYZX', 'LFVP']
ARROW_AIRPORTS = ['CYZX', 'LFVP']   # others have hand-tuned arrow maps outside the generated blocks
DISPLACED = {'CYHZ': {'23': 361}, 'LFVP': {'26': 197}}   # ft, Navigraph AIRAC 2610
RWY_OUTSIDE_M = 80.0      # designator placed this far beyond the threshold on the extended centreline

def runways():
    import math
    out = {}; sec = None
    for l in read(SECTOR):
        if l.startswith('['): sec = l.strip(); continue
        p = l.split()
        if sec == '[RUNWAY]' and len(p) >= 9 and not l.startswith(';'):
            out.setdefault(p[8], []).append((p[0], p[1], fix(p[4]), fix(p[5]), fix(p[6]), fix(p[7])))
    return out

def dms(v, pos, neg):
    h = pos if v >= 0 else neg; v = abs(v); d = int(v); m = int((v - d) * 60); s = round((v - d - m / 60) * 3600, 3)
    if s >= 60: s -= 60; m += 1
    if m == 60: m = 0; d += 1
    return f"{h}{d:03d}.{m:02d}.{s:06.3f}"

def deg(c):
    h = c[0]; d, m, a, b = c[1:].split('.'); v = int(d) + int(m) / 60 + float(a + '.' + b) / 3600
    return -v if h in 'SW' else v

def build_rwy(icao, rw):
    import math
    B = [f'//>>>> GENERATED RUNWAYS {icao} - built by tools\\build_ground.py from {os.path.basename(SECTOR)}; rerun the tool instead of editing',
         f'MAP:{icao} Runway Designators', f'FOLDER:{icao}', f'AIRPORT:{icao}', 'ACTIVE:1', 'LAYER:20', 'COLOR:RWY_DESIG',
         f'// designator {RWY_OUTSIDE_M:g} m beyond each threshold on the extended centreline']
    for d1, d2, la1, lo1, la2, lo2 in rw:
        A = (deg(la1), deg(lo1)); C = (deg(la2), deg(lo2)); k = math.cos(math.radians(A[0]))
        dx = (C[1] - A[1]) * 111320 * k; dy = (C[0] - A[0]) * 110574; L = math.hypot(dx, dy); ux, uy = dx / L, dy / L
        for name, (la, lo), sgn in ((d1, A, -1), (d2, C, 1)):
            off = RWY_OUTSIDE_M + DISPLACED.get(icao, {}).get(name, 0) * 0.3048   # beyond the pavement end, not the displaced threshold
            x = sgn * ux * off; y = sgn * uy * off
            B.append(f"TEXT:{dms(la + y / 110574, 'N', 'S')}:{dms(lo + x / (111320 * k), 'E', 'W')}:{name}")
    if icao in ARROW_AIRPORTS:
        S = 0.1 * 1852
        B += ['', f'MAP:{icao} Runway Arrows', f'FOLDER:{icao}', f'AIRPORT:{icao}', 'ACTIVE:1', 'LAYER:10',
              '// drawn only when that runway is active; usable length = (n+0.5) x 0.1 NM -> no partial arrows']
        for d1, d2, la1, lo1, la2, lo2 in rw:
            A = (deg(la1), deg(lo1)); C = (deg(la2), deg(lo2)); k = math.cos(math.radians(A[0]))
            L = math.hypot((C[1] - A[1]) * 111320 * k, (C[0] - A[0]) * 110574); eff0 = L - 300
            n = math.floor(eff0 / S - 0.5); off = 150 + (eff0 - (n + 0.5) * S) / 2
            B.append(f'RWY_ARROWS:{icao}{d1}:{la1}:{lo1}:{la2}:{lo2}:45:{off:.1f}:-{off:.1f}:0.1:0.3')
            B.append(f'RWY_ARROWS:{icao}{d2}:{la2}:{lo2}:{la1}:{lo1}:45:{off:.1f}:-{off:.1f}:0.1:0.3')
    B.append(f'//<<<< END GENERATED RUNWAYS {icao}')
    return B

def cname(c): return 'SCT_' + c[6:] if c.startswith('COLOR_') else 'SCT_' + c

def build(icao, defs, geo, ft, used):
    a = AIRPORTS[icao]; segs = []
    for n in a['geo']: segs += geo.get(n, [])
    lines, park, mark = {}, [], {}
    for la1, lo1, la2, lo2, col in segs:
        L = f'LINE:{la1}:{lo1}:{la2}:{lo2}'
        if col in PARKING: park.append(L)
        elif col in MARKINGS: mark.setdefault(col, []).append(L)
        else: lines.setdefault(col or 'COLOR_TaxiwayYellow', []).append(L)
    labels = ft.get(f'{icao} {icao} TAXIWAY', [])
    roman = [x for x in labels if re.match(r'^[IVX]+$', x[2])]
    roman = roman if len(roman) >= 2 else []          # a set of roman numerals = hangar/stand ids, even 'V'
    twy = [x for x in labels if x not in roman and TWY_RE.match(x[2].split(' [')[0])]
    std = [x for x in labels if x not in twy and STAND_RE.match(x[2])]
    bld = [x for x in labels if x not in twy and x not in std]
    B = [f'//>>>> GENERATED GROUND {icao} - built by tools\\build_ground.py from {os.path.basename(SECTOR)}; rerun the tool instead of editing', '']
    def head(name, on, layer):
        B.extend([f'MAP:{icao} {name}', f'FOLDER:{icao}', f'AIRPORT:{icao}'] + (['ACTIVE:1'] if on else []) + [f'LAYER:{layer}'])
    head('Surfaces', True, 1); B += [f"SCTFILEDATA:REGIONS\\{a['region']}", '']
    if lines:
        head('Ground Lines', True, 5)
        for col, ls in lines.items(): used.add(col); B.append('COLOR:' + cname(col)); B += ls
        B.append('')
    if park:
        head('Parking Lines', False, 5); B += ['COLOR:PARKLINE_DIM'] + park + ['']
    if mark:
        head('Markings', False, 5)   # superseded by rwy_markings.py
        for col, ls in mark.items(): used.add(col); B.append('COLOR:THR_WHITE'); B += ls   # runway paint = displaced-threshold mark colour (Joel)
        B.append('')
    if twy:
        head('Labels Taxiways', True, 20); B.append('COLOR:DEV'); B += [f'TEXT:{la}:{lo}:{t}' for la, lo, t in twy]; B.append('')
    if std:
        head('Labels Stands', False, 20); B += ['COLOR:SMGS_PARKING', 'FONTSIZE:-:2', 'ZOOM:500'] + [f'TEXT:{la}:{lo}:{t}' for la, lo, t in std] + ['']
    if bld:
        head('Labels Buildings', False, 20); B.append('COLOR:LINE'); B += [f'TEXT:{la}:{lo}:{t}' for la, lo, t in bld]; B.append('')
    B.append(f'//<<<< END GENERATED {icao}')
    stats = dict(lines=sum(map(len, lines.values())), parking=len(park), markings=sum(map(len, mark.values())), twy=len(twy), stands=len(std), bldg=len(bld))
    return B, stats

def drop_block(L, start, stop):
    pos = None
    while True:
        i = next((k for k, l in enumerate(L) if l.startswith(start)), None)
        if i is None: return pos
        j = L.index(stop, i); del L[i:j + 1]
        while i < len(L) and L[i] == '' and i > 0 and L[i - 1] == '': del L[i]
        pos = i if pos is None else min(pos, i)

def drop_map(L, name):
    if 'MAP:' + name in L:
        i = L.index('MAP:' + name); j = i
        while j < len(L) and L[j].strip() != '': j += 1
        del L[i:j + 1]; return True
    return False

def main():
    req = [x.upper() for x in sys.argv[1:]] or ['ALL']
    icaos = list(AIRPORTS) if req == ['ALL'] else [i for i in req if i in AIRPORTS]
    defs, geo = sector_data(); ft = freetext(); rws = runways()
    L = open(MAPS).read().split('\n'); used = set()
    for name in ('CYYR Groundlayout', 'CYYR Geo'):
        if 'CYYR' in icaos and drop_map(L, name): print('removed old map', name)
    for icao in icaos:
        blk, st = build(icao, defs, geo, ft, used)
        pos = drop_block(L, f'//>>>> GENERATED GROUND {icao}', f'//<<<< END GENERATED {icao}')
        if pos is None:
            pos = next((i for i, l in enumerate(L) if l == f'MAP:{icao} Runway Arrows'), len(L))
        L[pos:pos] = blk + ['']
        print(icao, st)
    for icao in (RWY_AIRPORTS if req == ['ALL'] else [i for i in icaos if i in RWY_AIRPORTS]):
        blk = build_rwy(icao, rws.get(icao, []))
        pos = drop_block(L, f'//>>>> GENERATED RUNWAYS {icao}', f'//<<<< END GENERATED RUNWAYS {icao}')
        if pos is None:
            pos = next((i for i, l in enumerate(L) if l == f'MAP:{icao} Runway Arrows'), len(L))
        L[pos:pos] = blk + ['']
        print(icao, 'runway designators/arrows:', sum(1 for x in blk if x.startswith('TEXT:')), sum(1 for x in blk if x.startswith('RWY_ARROWS')))
    if not any(l.startswith('COLORDEF:RWY_DESIG') for l in L):
        L.insert(next(k for k, l in enumerate(L) if l.startswith('COLORDEF:PARKLINE_DIM')) + 1, 'COLORDEF:RWY_DESIG:205:190:95')
    # colour definitions for sector-file colours (managed block)
    have = set()
    if '//>>>> GENERATED SCT COLOURS' in L:
        i = L.index('//>>>> GENERATED SCT COLOURS'); j = L.index('//<<<< END GENERATED SCT COLOURS', i)
        have = {l.split(':')[1] for l in L[i + 1:j]}; del L[i:j + 1]
    else:
        i = next(k for k, l in enumerate(L) if l.startswith('COLORDEF:PARKLINE_DIM')) + 1
    names = sorted(have | {cname(c) for c in used})
    cd = ['//>>>> GENERATED SCT COLOURS']
    for n in names:
        v = defs.get('COLOR_' + n[4:], 0xFFFFFF); r, g, b = v & 255, (v >> 8) & 255, (v >> 16) & 255
        cd.append(f'COLORDEF:{n}:{r}:{g}:{b}')
    cd.append('//<<<< END GENERATED SCT COLOURS')
    L[i:i] = cd
    bak = os.path.join(os.path.dirname(MAPS), '_bak'); os.makedirs(bak, exist_ok=True)
    shutil.copy(MAPS, os.path.join(bak, os.path.basename(MAPS) + time.strftime('.bak_%Y%m%d_%H%M%S')))
    open(MAPS, 'w', newline='\r\n').write('\n'.join(L))
    print('sector file:', os.path.basename(SECTOR))
    W = sorted({w for w in WARN if any(i in w for i in icaos)})
    if W: print('SOURCE DATA ERRORS in airport data (auto-corrected here; fix in the sector-file source):'); print('\n'.join(W))

if __name__ == '__main__':
    main()
