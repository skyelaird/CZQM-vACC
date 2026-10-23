"""
fixed_maps.py - map blocks built once from published sources (DAH control zones, CFS VFR calling points,
CYHZ de-icing bay numbers, CYYT apron restrictions, CYFC uncontrolled shading) kept as data in
tools\\fixed_maps\\<name>.txt and (re)applied to GRpluginMaps.txt.

  python fixed_maps.py            apply: replace each block in place, or insert it if missing
  python fixed_maps.py extract    refresh tools\\fixed_maps\\ from the current GRpluginMaps.txt

Edit the .txt files (they are the source of truth), then apply. A block is everything from its
'//>>>> NAME' line to its '//<<<< END NAME' line; the file name is NAME with spaces as underscores.
"""
import os, re, shutil, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); GRP = os.path.dirname(HERE)
MAPS = os.path.join(GRP, 'GRpluginMaps.txt'); DIR = os.path.join(HERE, 'fixed_maps')
NAMES = re.compile(r'^//>>>> ((?:CY..|LFVP) (?:CONTROL ZONE|VFR CALLING POINTS|DE-ICING BAYS|APRON RESTRICTIONS)|CYFC UNCONTROLLED)\b')

def load(): return open(MAPS, encoding='latin-1').read().replace('\r\n', '\n').split('\n')
def save(M):
    shutil.copy(MAPS, os.path.join(GRP, '_bak', 'GRpluginMaps.txt' + time.strftime('.bak_%Y%m%d_%H%M%S')))
    open(MAPS, 'w', encoding='latin-1', newline='\r\n').write('\n'.join(M))
def span(M, name):
    i = next((k for k, l in enumerate(M) if l.startswith('//>>>> ' + name + ' ') or l == '//>>>> ' + name), None)
    return (i, M.index('//<<<< END ' + name, i)) if i is not None else (None, None)

def extract():
    os.makedirs(DIR, exist_ok=True); M = load(); n = 0
    for l in M:
        m = NAMES.match(l)
        if not m: continue
        name = m.group(1); i, j = span(M, name)
        open(os.path.join(DIR, name.replace(' ', '_') + '.txt'), 'w', encoding='latin-1', newline='\r\n').write('\n'.join(M[i:j + 1]) + '\n'); n += 1
    print(f'extracted {n} blocks to {DIR}')

def apply():
    M = load(); done = []
    for f in sorted(os.listdir(DIR)):
        if not f.endswith('.txt'): continue
        B = open(os.path.join(DIR, f), encoding='latin-1').read().replace('\r\n', '\n').rstrip('\n').split('\n')
        name = re.match(r'^//>>>> (.*?)(?: - .*)?$', B[0]).group(1); name = NAMES.match(B[0]).group(1)
        i, j = span(M, name)
        if i is not None: M[i:j + 1] = B; done.append(name + ' (replaced)')
        else:
            icao = name.split()[0]
            k = next((x for x, l in enumerate(M) if l.startswith(f'//>>>> GENERATED HOLD LINES {icao}')), len(M))
            M[k:k] = B + ['']; done.append(name + ' (inserted)')
    save(M); print('\n'.join(done))

if __name__ == '__main__': extract() if sys.argv[1:] == ['extract'] else apply()
