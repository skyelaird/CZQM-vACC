"""uncontrolled.py - faint shading of uncontrolled movement areas (CFS TWY/APRON notes) from OSM aprons/taxiways.
Usage: python uncontrolled.py ICAO "apron refs|ALL|NONE" "taxiway refs" "CFS note" ["controlled taxiways to cut out"]   e.g.  CYYT ALL K "All aprons + Twy K uncontrolled, 121.9"
"""
import sys,json,os,math,shutil,time,urllib.request,xml.etree.ElementTree as ET
from shapely.geometry import LineString,Polygon
from shapely.ops import unary_union
icao,apr,twy,note=sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4]
excl=set(sys.argv[5].split(',')) if len(sys.argv)>5 and sys.argv[5] else set()   # controlled taxiways to keep unshaded
BB={'CYYT':[(-52.775,47.608,-52.750,47.632),(-52.750,47.605,-52.725,47.630)],'CYQM':[(-64.714,46.090,-64.644,46.134)],'CYYR':[(-60.461,53.297,-60.391,53.341)]}
ways={};N={}
for w,s,e,n in BB[icao]:
    x=urllib.request.urlopen(urllib.request.Request(f'https://api.openstreetmap.org/api/0.6/map?bbox={w},{s},{e},{n}',headers={'User-Agent':'GRPmapBuilder/1.0'}),timeout=28).read()
    r=ET.fromstring(x)
    for q in r.iter('node'): N[q.get('id')]=(float(q.get('lat')),float(q.get('lon')))
    for wy in r.iter('way'):
        t={g.get('k'):g.get('v') for g in wy.findall('tag')}
        if t.get('aeroway') in ('apron','taxiway','runway'): ways[wy.get('id')]=(t,[q.get('ref') for q in wy.findall('nd')])
la0=sum(b[1]+b[3] for b in BB[icao])/(2*len(BB[icao]));lo0=sum(b[0]+b[2] for b in BB[icao])/(2*len(BB[icao]));k=math.cos(math.radians(la0))
xy=lambda la,lo:((lo-lo0)*111320*k,(la-la0)*110574);ll=lambda X,Y:(Y/110574+la0,X/(111320*k)+lo0)
def dms(v,p,q):
    h=p if v>=0 else q;v=abs(v);d=int(v);m=int((v-d)*60);sec=round((v-d-m/60)*3600,3)
    if sec>=60: sec-=60;m+=1
    if m==60: m=0;d+=1
    return f"{h}{d:03d}.{m:02d}.{sec:06.3f}"
shapes=[];used=[];rw=[];ex=[]
want_ap=None if apr=='ALL' else set(apr.split(','));want_tw=set(twy.split(',')) if twy else set()
for wid,(t,nd) in ways.items():
    pts=[xy(*N[q]) for q in nd if q in N]
    if len(pts)<2: continue
    a=t.get('aeroway');nm=t.get('ref') or t.get('name') or ''
    if a=='runway' and t.get('ref'): rw.append(LineString(pts).buffer(float(t.get('width','61'))/2+10,cap_style='flat'))
    if a=='apron' and len(pts)>2 and 'glidepath' not in nm.lower() and (want_ap is None or nm in want_ap or t.get('ref') in want_ap):
        shapes.append(Polygon(pts).buffer(0));used.append(f'apron {nm or wid}')
    if a=='taxiway' and t.get('ref') in excl: ex.append(LineString(pts).buffer(15,cap_style='round'))
    if a=='taxiway' and t.get('ref') in want_tw: shapes.append(LineString(pts).buffer(12,cap_style='round'));used.append(f"twy {t['ref']}")
A=unary_union(shapes).difference(unary_union(rw+ex)) if (rw or ex) else unary_union(shapes)
polys=[p for p in (A.geoms if hasattr(A,'geoms') else [A]) if p.area>100]
blk=[f'//>>>> {icao} UNCONTROLLED - CFS: {note} - tools\\uncontrolled.py from OSM (c) OSM contributors, ODbL',
     f'MAP:{icao} Uncontrolled',f'FOLDER:{icao}',f'AIRPORT:{icao}','ACTIVE:1','LAYER:3','COLOR:UNCTL/45']
for p in polys:
    blk.append('COORDTYPE:OTHER:REGION_FILLONLY')
    blk+=[f"COORD:{dms(a,'N','S')}:{dms(b,'E','W')}" for a,b in (ll(*c) for c in list(p.simplify(0.5).exterior.coords)[:-1])]
blk.append(f'//<<<< END {icao} UNCONTROLLED')
G=r'C:\Users\JoelMorin\AppData\Roaming\EuroScope\CZQQ\Plugins\GRP';f=os.path.join(G,'GRpluginMaps.txt')
shutil.copy(f,os.path.join(G,'_bak','GRpluginMaps.txt'+time.strftime('.bak_%Y%m%d_%H%M%S')))
M=open(f,encoding='latin-1').read().replace('\r\n','\n').split('\n')
if not any(l.startswith('COLORDEF:UNCTL') for l in M):
    M.insert(next(q for q,l in enumerate(M) if l.startswith('COLORDEF:PARKLINE_DIM'))+1,'COLORDEF:UNCTL:90:125:175')
x=next((q for q,l in enumerate(M) if l.startswith(f'//>>>> {icao} UNCONTROLLED')),None)
if x is not None: j=M.index(f'//<<<< END {icao} UNCONTROLLED',x);del M[x:j+1]
else: x=next(q for q,l in enumerate(M) if l==f'MAP:{icao} Runway Arrows')
M[x:x]=blk+['']
open(f,'w',encoding='latin-1',newline='\r\n').write('\n'.join(M))
print(icao,len(polys),'areas from',sorted(set(used)))
