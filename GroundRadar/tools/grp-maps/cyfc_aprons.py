"""cyfc_aprons.py - add CYFC terminal-area aprons (OSM aeroway=apron near the terminal) to the CYFC Uncontrolled shading."""
import re,sys,os,math,shutil,time,urllib.request,xml.etree.ElementTree as ET
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import hold_lines as H
from shapely.geometry import Polygon,LineString
from shapely.ops import unary_union
la0,lo0=45.87,-66.53;k=math.cos(math.radians(la0))
xy=lambda la,lo:((lo-lo0)*111320*k,(la-la0)*110574);ll=lambda X,Y:(Y/110574+la0,X/(111320*k)+lo0)
x=urllib.request.urlopen(urllib.request.Request('https://api.openstreetmap.org/api/0.6/map?bbox=-66.572,45.848,-66.502,45.892',headers={'User-Agent':'GRPmapBuilder/1.0'}),timeout=55).read()
r=ET.fromstring(x);N={n.get('id'):(float(n.get('lat')),float(n.get('lon'))) for n in r.iter('node')}
ap=[];rw=[]
for w in r.iter('way'):
    t={g.get('k'):g.get('v') for g in w.findall('tag')};p=[xy(*N[q.get('ref')]) for q in w.findall('nd') if q.get('ref') in N]
    if t.get('aeroway')=='apron' and len(p)>2: ap.append(Polygon(p).buffer(0))
    if t.get('aeroway')=='runway' and len(p)>1: rw.append(LineString(p).buffer(float(t.get('width','46'))/2+10,cap_style='flat'))
A=unary_union(ap).difference(unary_union(rw))
M=open(H.MAPS,encoding='latin-1').read().replace('\r\n','\n').split('\n')
i=next(q for q,l in enumerate(M) if l.startswith('//>>>> CYFC UNCONTROLLED'));j=M.index('//<<<< END CYFC UNCONTROLLED',i)
old=[];cur=None
for l in M[i:j]:
    if l.startswith('COORDTYPE'): cur=[];old.append(cur)
    m=re.match(r'COORD:([NS][\d.]+):([EW][\d.]+)',l)
    if m: cur.append(xy(H.P(m.group(1)),H.P(m.group(2))))
U=unary_union([Polygon(p).buffer(0) for p in old]+[A]).buffer(0.5).buffer(-0.5)
polys=[p for p in (U.geoms if hasattr(U,'geoms') else [U]) if p.area>100]
print('aprons',len(ap),'apron area',round(A.area),'areas',[round(p.area) for p in polys],'holes',sum(len(p.interiors) for p in polys))
blk=[l for l in M[i:j] if not l.startswith(('COORDTYPE','COORD:'))]
blk[0]=blk[0].replace(' - from OSM',' + terminal-area Aprons I-V (Joel 2026-10-23) - from OSM')
for p in polys:
    blk.append('COORDTYPE:OTHER:REGION_FILLONLY')
    blk+=[f"COORD:{H.dms(a,'N','S')}:{H.dms(b,'E','W')}" for a,b in (ll(*c) for c in list(p.simplify(0.5).exterior.coords)[:-1])]
blk.append('//<<<< END CYFC UNCONTROLLED')
shutil.copy(H.MAPS,os.path.join(H.GRP,'_bak','GRpluginMaps.txt'+time.strftime('.bak_%Y%m%d_%H%M%S')))
M[i:j+1]=blk; open(H.MAPS,'w',encoding='latin-1',newline='\r\n').write('\n'.join(M))
