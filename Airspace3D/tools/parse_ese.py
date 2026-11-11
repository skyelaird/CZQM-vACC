import re, json, math, sys
ese_path, out_path = sys.argv[1], sys.argv[2]
txt = open(ese_path, encoding='latin-1').read().replace('\r', '')
lines = txt.split('\n')

AIRPORTS = {  # from the .sct [AIRPORT] section
 'CYFC': (45.868878, -66.537219), 'CYHZ': (44.879683, -63.510192), 'CYQM': (46.115986, -64.678606),
 'CYZX': (44.984167, -64.9175), 'CYQX': (48.936944, -54.568056), 'CYYR': (53.319167, -60.425833),
 'CYYT': (47.618619, -52.752419), 'LFVP': (46.763056, -56.174167), 'CYSJ': (45.316, -65.8901),
}

def dms(s):
    m = re.match(r'([NSEW])(\d+)\.(\d+)\.(\d+)\.(\d+)', s)
    h, d, mi, se, frac = m.groups()
    v = int(d) + int(mi) / 60 + float(f'{se}.{frac}') / 3600
    return -v if h in 'SW' else v

# positions
pos = {}
in_pos = False
for l in lines:
    if l.startswith('[POSITIONS]'): in_pos = True; continue
    if in_pos and l.startswith('['): break
    if in_pos and l and not l.startswith(';'):
        f = l.split(':')
        if len(f) > 3 and f[3]: pos[f[3]] = {'cs': f[0], 'rtf': f[1], 'freq': f[2]}

# airspace section
start = next(i for i, l in enumerate(lines) if l.startswith('[AIRSPACE]'))
end = next(i for i, l in enumerate(lines) if i > start and l.startswith('[') and not l.startswith('[AIRSPACE]'))
seclines, cur = {}, None
circles = {}
sectors = []
for l in lines[start + 1:end]:
    if l.startswith('SECTORLINE:'):
        cur = l.split(':', 1)[1].strip(); seclines[cur] = []
    elif l.startswith('COORD:') and cur is not None:
        _, la, lo = l.split(':')[:3]; seclines[cur].append((dms(la), dms(lo)))
    elif l.startswith('CIRCLE_SECTORLINE:'):
        f = l.split(':')[1:]
        name = f[0]
        if len(f) == 3: c = AIRPORTS.get(f[1]); r = float(f[2])
        else: c = (dms(f[1]), dms(f[2])); r = float(f[3])
        if c: circles[name] = (c, r)
        cur = None
    elif l.startswith('SECTOR:'):
        f = l.split(':')
        sectors.append({'id': f[1], 'floor': int(f[2]), 'ceil': int(f[3]), 'owner': [], 'border': []}); cur = None
    elif l.startswith('OWNER:') and sectors:
        sectors[-1]['owner'] = l.split(':')[1:]
    elif l.startswith('BORDER:') and sectors:
        sectors[-1]['border'] = [b for b in l.split(':')[1:] if b]
    elif l.startswith('ALTOWNER:') and sectors:
        sectors[-1].setdefault('alt', []).append(l.split(':')[1:])
    elif l.startswith(('DISPLAY', 'GUEST', 'DEPAPT', 'ARRAPT', 'ACTIVE', 'COPX', 'FIR_COPX', 'MSAW', ';')) or not l.strip():
        cur = None if not l.startswith('COORD') else cur

def circle(c, r_nm, n=72):
    lat0, lon0 = map(math.radians, c); d = r_nm / 3440.065
    pts = []
    for k in range(n):
        b = 2 * math.pi * k / n
        lat = math.asin(math.sin(lat0) * math.cos(d) + math.cos(lat0) * math.sin(d) * math.cos(b))
        lon = lon0 + math.atan2(math.sin(b) * math.sin(d) * math.cos(lat0), math.cos(d) - math.sin(lat0) * math.sin(lat))
        pts.append((math.degrees(lat), math.degrees(lon)))
    return pts

def chain(names):
    segs = [list(seclines[n]) for n in names if n in seclines and seclines[n]]
    if not segs: return None
    poly = segs.pop(0)
    while segs:
        tail = poly[-1]
        best, bi, rev = None, None, False
        for i, s in enumerate(segs):
            for r, p in ((False, s[0]), (True, s[-1])):
                d = (p[0] - tail[0]) ** 2 + (p[1] - tail[1]) ** 2
                if best is None or d < best: best, bi, rev = d, i, r
        s = segs.pop(bi)
        if rev: s = s[::-1]
        poly += s[1:] if s[0] == tail else s
    return poly

def group(fir, name, owners):
    n = name.upper()
    if fir not in ('CZQM', 'CZQX', 'CZQXO'): return 'Neighbours'
    if not owners and n != 'GANDER OCA FIR': return 'Uncontrolled'
    if fir == 'CZQXO' or 'OCA' in n or 'CZQO' in n: return 'Oceanic (CZQO)'
    if re.search(r'_(GND|DEL)$', n): return 'Ground / Delivery'
    if n.endswith('_TWR'): return 'Tower zones'
    if n.endswith('_APP') or n.endswith('-UNI'): return 'Terminals'
    if 'HI' in n.split('-')[-1] or n.startswith(('MONCTON-HI', 'GANDER-HI')): return f'{fir} High'
    return f'{fir} Low'

out = []
missing = []
for s in sectors:
    parts = s['id'].split('·')
    fir, name = parts[0], parts[1] if len(parts) > 1 else s['id']
    if len(s['border']) == 1 and s['border'][0] in circles and s['border'][0] not in seclines:
        c, r = circles[s['border'][0]]; poly = circle(c, r)
    else:
        poly = chain(s['border'])
        if poly is None and s['border'] and s['border'][0] in circles:
            c, r = circles[s['border'][0]]; poly = circle(c, r)
    if not poly: missing.append(s['id']); continue
    owners = [{'code': o, **pos.get(o, {'cs': o, 'rtf': '', 'freq': ''})} for o in s['owner']]
    out.append({'id': s['id'], 'fir': fir, 'name': name, 'group': group(fir, name, s['owner']),
                'floor': s['floor'], 'ceil': min(s['ceil'], 60000), 'owners': owners,
                'poly': [[round(p[1], 5), round(p[0], 5)] for p in poly]})
json.dump(out, open(out_path, 'w'), separators=(',', ':'))
from collections import Counter
print(len(out), 'sectors;', 'missing:', missing)
print(Counter(o['group'] for o in out))
