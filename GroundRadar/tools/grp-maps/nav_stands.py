"""
nav_stands.py - stand list per airport: NAMES from the published gate list (Navigraph via Little Navmap,
current AIRAC, read locally - never copied), POSITIONS/headings/sizes from OpenStreetMap (tools\\osm_cache) or
the MSFS 2024 scenery (Little Navmap msfs24 db) within MATCH_M of the published point.
Published stands with no OSM/MSFS spot nearby are placed at the published (AIP) position. Non-numbered OSM areas (APRON x, BAY x) are kept.
Usage: python nav_stands.py CYFC CYQM CYQX CYYR CYYT CYZX
"""
import json, math, os, re, shutil, sqlite3, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); GRP = os.path.dirname(HERE)
STANDS = os.path.join(GRP, 'GRpluginStands.txt'); CACHE = os.path.join(HERE, 'osm_cache')
LNM = os.path.join(os.environ['APPDATA'], 'ABarthel', 'little_navmap_db')
MATCH_M, MIN_R, DEF_R = 25.0, 8.0, 20.0
def code_of(ws): return 'A' if ws < 15 else 'B' if ws < 24 else 'C' if ws < 36 else 'D' if ws < 52 else 'E' if ws < 65 else 'F'
def dms(v, p, n):
    h = p if v >= 0 else n; v = abs(v); d = int(v); m = int((v - d) * 60); s = round((v - d - m / 60) * 3600, 3)
    if s >= 60: s -= 60; m += 1
    if m == 60: m = 0; d += 1
    return f'{h}{d:03d}.{m:02d}.{s:06.3f}'
def brg(a, b):
    k = math.cos(math.radians(a[0])); return math.degrees(math.atan2((b[1] - a[1]) * k, b[0] - a[0])) % 360
nat = lambda s: [int(x) if x.isdigit() else x for x in re.split(r'(\d+)', s)]
RULES = json.load(open(os.path.join(HERE, 'stand_rules.json'))) if os.path.exists(os.path.join(HERE, 'stand_rules.json')) else {}   # per-stand CODE/USE from CFS notes

def main():
    icaos = [a.upper() for a in sys.argv[1:]]
    nav = sqlite3.connect(os.path.join(LNM, 'little_navmap_navigraph.sqlite'))
    cyc = nav.execute('select * from metadata').fetchone()[4]
    ms = sqlite3.connect(os.path.join(LNM, 'little_navmap_msfs24.sqlite'))
    S = open(STANDS, encoding='latin-1').read().replace('\r\n', '\n').split('\n')
    for icao in icaos:
        a = nav.execute('select airport_id from airport where ident=?', (icao,)).fetchone()
        pub = [] if not a else [(n, la, lo) for n, la, lo in nav.execute('select name,laty,lonx from parking where airport_id=?', (a[0],)) if n and n != '0']
        k = math.cos(math.radians(pub[0][1] if pub else 45)); dist = lambda p, q: math.hypot((p[1] - q[1]) * 111320 * k, (p[0] - q[0]) * 110574)
        pool = []   # (lat, lon, heading, radius_m, use, src)
        els = json.load(open(os.path.join(CACHE, icao + '.json')))['elements'] if os.path.exists(os.path.join(CACHE, icao + '.json')) else []
        keep = []
        for e in els:
            t = e['tags']; aw = t.get('aeroway'); nm = (t.get('ref') or t.get('name') or '').strip()
            if aw not in ('parking_position', 'gate'): continue
            if e['type'] == 'node': p, h = (e['lat'], e['lon']), None
            else:
                g = [(q['lat'], q['lon']) for q in e['geometry']]
                if not g: continue
                p, h = g[-1], (brg(g[-2], g[-1]) if len(g) > 1 else None)
            if aw == 'parking_position': pool.append((p[0], p[1], h, None, None, 'OSM'))
            if re.match(r'^(APRON|Bay)\s', nm, re.I): keep.append((re.sub(r'^Bay', 'BAY', nm.upper()), p, h))
        m = ms.execute('select airport_id from airport where ident=?', (icao,)).fetchone()
        if m:
            for ty, r, h, la, lo in ms.execute('select type,radius,heading,laty,lonx from parking where airport_id=?', (m[0],)):
                if ty == 'FUEL': continue
                use = 'C' if ty.startswith('RC') else 'M' if ty.startswith(('RM', 'MIL')) else None
                pool.append((la, lo, h % 360, r * 0.3048, use, 'MSFS'))
        out, miss = [], []
        for n, la, lo in sorted(pub, key=lambda x: nat(x[0])):
            c = sorted(((dist((la, lo), q), q) for q in pool), key=lambda x: x[0])
            c = [q for d, q in c if d <= MATCH_M]
            if not c:
                miss.append(n); out.append([n, la, lo, None, None, None, 'published AIRAC (no OSM/MSFS spot within %g m)' % MATCH_M]); continue
            best = c[0]; h = best[2] if best[2] is not None else next((q[2] for q in c if q[2] is not None), None)
            msq = next((q for q in c if q[5] == 'MSFS'), None)
            out.append([n, best[0], best[1], h, msq[3] if msq else None, msq[4] if msq else None, best[5]])
            pool.remove(best)
        for nm, p, h in keep:
            if nm not in [o[0] for o in out]: out.append([nm, p[0], p[1], h, None, None, 'OSM area'])
        for o in out:
            nn = min([dist((o[1], o[2]), (x[1], x[2])) for x in out if x is not o] or [99])
            base = o[4] if o[4] else DEF_R
            o.append(round(max(MIN_R, min(base, nn / 2)), 1) if not o[0].startswith(('APRON',)) else 60.0)
        blk = [f'//>>>> GENERATED STANDS {icao} - tools\\nav_stands.py: stand numbers per published AIRAC {cyc} gate list; positions from OSM (c) OSM contributors, ODbL / MSFS scenery', '']
        for n, la, lo, h, msr, use, src, r in sorted(out, key=lambda o: nat(o[0])):
            blk.append(f'// {n}: position {src}')
            blk.append(f"STAND:{icao}:{n}:{dms(la, 'N', 'S')}:{dms(lo, 'E', 'W')}:{r}")
            if n.startswith(('APRON',)): blk.append('AREA')
            elif h is not None: blk.append(f'HEADING:{h:.1f}:30')
            rule = RULES.get(icao, {}).get(n, {})
            if rule.get('note'): blk.insert(len(blk) - (2 if (h is not None or n.startswith(('APRON',))) else 1), f"// {n}: {rule['note']}")
            code = rule.get('code') or (code_of(2 * msr) if msr else None)
            if code: blk.append(f'CODE:{code}')
            use = rule.get('use', use)
            if use: blk.append(f'USE:{use}')
            if rule.get('blocks'): blk.append(f"BLOCKS:{rule['blocks']}")
            blk.append('')
        blk.append(f'//<<<< END GENERATED STANDS {icao}')
        i = next((x for x, l in enumerate(S) if l.startswith(f'//>>>> GENERATED STANDS {icao}')), None)
        if i is not None: j = S.index(f'//<<<< END GENERATED STANDS {icao}', i); del S[i:j + 1]
        else: i = len(S)
        if out: S[i:i] = blk
        print(f'{icao}: {len(out)} stands ' + ' '.join(o[0] for o in sorted(out, key=lambda o: nat(o[0]))) + (f'  | placed at published position: {" ".join(miss)}' if miss else ''))
    bak = os.path.join(GRP, '_bak'); os.makedirs(bak, exist_ok=True)
    shutil.copy(STANDS, os.path.join(bak, 'GRpluginStands.txt' + time.strftime('.bak_%Y%m%d_%H%M%S')))
    open(STANDS, 'w', encoding='latin-1', newline='\r\n').write('\n'.join(S))
if __name__ == '__main__': main()
