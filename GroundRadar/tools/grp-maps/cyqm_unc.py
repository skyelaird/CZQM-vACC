"""cyqm_unc.py - CYQM south aprons: shade out to the Twy A corridor (A controlled 50 ft either side of centreline),
B and C stubs likewise; pavement from the sector-file apron/hard-surface regions. North (Apron VIII) block untouched."""
import re,sys,math,os,shutil,time
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__))))
import hold_lines as H
from shapely.geometry import Polygon,LineString
from shapely.ops import unary_union
CTL=50*0.3048
M=open(H.MAPS,encoding='latin-1').read().replace('\r\n','\n').split('\n')
i=next(q for q,l in enumerate(M) if l.startswith('//>>>> CYQM UNCONTROLLED')); j=M.index('//<<<< END CYQM UNCONTROLLED',i)
la0,lo0=46.11,-64.68;k=math.cos(math.radians(la0))
xy=lambda la,lo:((lo-lo0)*111320*k,(la-la0)*110574);ll=lambda X,Y:(Y/110574+la0,X/(111320*k)+lo0)
polys=[];cur=None
for l in M[i:j]:
    if l.startswith('COORDTYPE'): cur=[];polys.append(cur)
    m=re.match(r'COORD:([NS][\d.]+):([EW][\d.]+)',l)
    if m: cur.append(xy(H.P(m.group(1)),H.P(m.group(2))))
P=[Polygon(p).buffer(0) for p in polys]
south=[p for p in P if ll(p.centroid.x,p.centroid.y)[0]<46.11]; north=[p for p in P if p not in south]
sec=None;regs=[];r=None
for l in open(H.SCT,encoding='latin-1'):
    if l.startswith('['): sec=l.strip();continue
    if sec!='[REGIONS]': continue
    if l.startswith('REGIONNAME'): r={'n':l[11:].strip(),'c':None,'p':[]};regs.append(r);continue
    m=re.findall(r'([NS]\d{3}\.\d\d\.\d\d\.\d+)\s+([EW]\d{3}\.\d\d\.\d\d\.\d+)',l)
    if r and m:
        if r['c'] is None: r['c']=l.split()[0]
        r['p']+=[xy(H.P(a),H.P(b)) for a,b in m]
reg=lambda cols:unary_union([Polygon(q['p']).buffer(0) for q in regs if q['n'].startswith('CYQM') and q['c'] in cols and len(q['p'])>2])
pave=reg(('COLOR_ApronSurface','COLOR_HardSurface3','COLOR_TaxiwayYellow'));block=reg(('COLOR_GrasSurface','COLOR_Building'))
tw=[(t['ref'],LineString([xy(*q) for q in t['pts']])) for t in H.taxiways('CYQM') if len(t['pts'])>1]
S=unary_union(south)
ctl=unary_union([g.buffer(CTL,cap_style='flat') for r,g in tw if r in ('A','B','C') and g.distance(S)<80])
rw=[]
for l in open(H.SCT,encoding='latin-1'):
    p=l.split()
    if len(p)>=9 and p[8]=='CYQM': rw.append(LineString([xy(H.P(p[4]),H.P(p[5])),xy(H.P(p[6]),H.P(p[7]))]).buffer(61/2+10,cap_style='flat'))
zone=S.buffer(70).intersection(pave.buffer(1)).difference(block).difference(unary_union(rw))
# keep only what lies on the apron side of the A corridor: split by corridor, keep pieces touching the aprons
cut=unary_union([S,zone]).difference(ctl).buffer(0.5).buffer(-0.5)
keep=[p for p in (cut.geoms if hasattr(cut,'geoms') else [cut]) if p.intersection(S).area>0.3*min(p.area,S.area) or p.intersection(S).area>500]
newS=unary_union(keep)
print('south area',round(S.area),'->',round(newS.area),'pieces',len(keep))
out=north+list(newS.geoms if hasattr(newS,'geoms') else [newS])
blk=M[i:i+8]   # header..COLOR
blk=[l for l in M[i:j] if not l.startswith(('COORDTYPE','COORD:'))]
blk[0]=blk[0].replace(' - tools','; south aprons out to Twy A, A/B/C controlled 50 ft either side of centreline (Joel 2026-10-23) - tools')
for p in out:
    if p.area<150: continue
    blk.append('COORDTYPE:OTHER:REGION_FILLONLY')
    blk+=[f"COORD:{H.dms(a,'N','S')}:{H.dms(b,'E','W')}" for a,b in (ll(*c) for c in list(p.simplify(0.7).exterior.coords)[:-1])]
blk.append('//<<<< END CYQM UNCONTROLLED')
shutil.copy(H.MAPS,os.path.join(H.GRP,'_bak','GRpluginMaps.txt'+time.strftime('.bak_%Y%m%d_%H%M%S')))
M[i:j+1]=blk
open(H.MAPS,'w',encoding='latin-1',newline='\r\n').write('\n'.join(M))
