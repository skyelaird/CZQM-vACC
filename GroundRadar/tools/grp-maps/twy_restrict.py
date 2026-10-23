"""twy_restrict.py ICAO "C,D" "23.9,35.9" "CFS note" - taxiway wingspan restriction areas from OSM taxiways (ref, or ESE label within 25 m), runways and aprons cut out."""
import sys,json,os,math,shutil,time,urllib.request,xml.etree.ElementTree as ET
from shapely.geometry import LineString,Point,Polygon
from shapely.ops import unary_union
icao=sys.argv[1];letters=sys.argv[2].split(',');spans=[float(x) for x in sys.argv[3].split(',')];note=sys.argv[4]
BB={'CYFC':(-66.572,45.848,-66.502,45.892),'CYQM':(-64.714,46.090,-64.644,46.134),'CYQX':(-54.603,48.915,-54.533,48.959)}
w,s,e,n=BB[icao]
x=urllib.request.urlopen(urllib.request.Request(f'https://api.openstreetmap.org/api/0.6/map?bbox={w},{s},{e},{n}',headers={'User-Agent':'GRPmapBuilder/1.0'}),timeout=55).read()
r=ET.fromstring(x);N={q.get('id'):(float(q.get('lat')),float(q.get('lon'))) for q in r.iter('node')}
la0,lo0=(s+n)/2,(w+e)/2;k=math.cos(math.radians(la0))
xy=lambda la,lo:((lo-lo0)*111320*k,(la-la0)*110574);ll=lambda X,Y:(Y/110574+la0,X/(111320*k)+lo0)
def P(c):
    h=c[0];d,m,a,b=c[1:].split('.');v=int(d)+int(m)/60+float(a+'.'+b)/3600
    return -v if h in 'SW' else v
def dms(v,p,q):
    h=p if v>=0 else q;v=abs(v);d=int(v);m=int((v-d)*60);sec=round((v-d-m/60)*3600,3)
    if sec>=60: sec-=60;m+=1
    if m==60: m=0;d+=1
    return f"{h}{d:03d}.{m:02d}.{sec:06.3f}"
tw=[];rw=[];ap=[]
for wy in r.iter('way'):
    t={g.get('k'):g.get('v') for g in wy.findall('tag')};pts=[xy(*N[q.get('ref')]) for q in wy.findall('nd') if q.get('ref') in N]
    if len(pts)<2: continue
    a=t.get('aeroway')
    if a=='taxiway': tw.append((wy.get('id'),t.get('ref'),LineString(pts)))
    elif a=='runway' and t.get('ref'): rw.append(LineString(pts).buffer(float(t.get('width','61'))/2+10,cap_style='flat'))
    elif a=='apron' and len(pts)>2: ap.append(Polygon(pts).buffer(0))
f=r'C:\Users\JoelMorin\AppData\Roaming\EuroScope\CZQQ\Plugins\GRP\GRpluginMaps.txt'
M=open(f,encoding='latin-1').read().replace('\r\n','\n').split('\n')
i=M.index(f'MAP:{icao} Labels Taxiways');lab=[]
for l in M[i+1:]:
    if l.startswith('MAP:') or l.startswith('//<<<<'): break
    if l.startswith('TEXT:'): q=l.split(':');lab.append((q[3].split(' ')[0],Point(xy(P(q[1]),P(q[2])))))
cut=unary_union(rw+[a.buffer(5) for a in ap])
blk=[f'//>>>> {icao} TAXIWAY RESTRICTIONS - CFS TWY CERT: {note} (Joel 2026-10-23) - tools\\twy_restrict.py',
     '// Areas = OSM taxiway centrelines (ref-tagged, or unnamed segments carrying the sector-file label) +-15 m; runway strips and aprons cut out',
     f'MAP:{icao} Taxiway Restrictions','HIDDEN',f'FOLDER:{icao}',f'AIRPORT:{icao}','ACTIVE:1']
for L_,ws in zip(letters,spans):
    sel=[g for wid,ref,g in tw if ref==L_ or (ref is None and any(nm==L_ and g.distance(p)<25 for nm,p in lab))]
    if not sel: print('no geometry for',L_);continue
    A=unary_union([g.buffer(15.0) for g in sel]).difference(cut)
    polys=[p for p in (A.geoms if hasattr(A,'geoms') else [A]) if p.area>50]
    blk+=[f'// Twy {L_}: max wingspan {ws} m ({len(sel)} OSM segments, {sum(g.length for g in sel):.0f} m)',f'RESTRICTION:MAXWINGSPAN:{ws}']
    for p in polys:
        blk.append('COORDTYPE:TWYTYPE:NONE')
        blk+=[f"COORD:{dms(a,'N','S')}:{dms(b,'E','W')}" for a,b in (ll(*c) for c in list(p.simplify(0.5).exterior.coords)[:-1])]
    print(f'{icao} Twy {L_}: {len(sel)} segments, {len(polys)} areas, max wingspan {ws}')
blk.append(f'//<<<< END {icao} TAXIWAY RESTRICTIONS')
shutil.copy(f,os.path.join(os.path.dirname(f),'_bak','GRpluginMaps.txt'+time.strftime('.bak_%Y%m%d_%H%M%S')))
x0=next((q for q,l in enumerate(M) if l.startswith(f'//>>>> {icao} TAXIWAY RESTRICTIONS')),None)
if x0 is not None: j=M.index(f'//<<<< END {icao} TAXIWAY RESTRICTIONS',x0);del M[x0:j+1]
else: x0=next(q for q,l in enumerate(M) if l==f'MAP:{icao} Runway Arrows')
M[x0:x0]=blk+['']
open(f,'w',encoding='latin-1',newline='\r\n').write('\n'.join(M))
