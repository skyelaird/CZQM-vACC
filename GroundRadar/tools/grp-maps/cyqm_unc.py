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
# Twy A controlled 50 ft either side of the SECTOR-FILE A centreline (the painted yellow line; OSM's A
# runs ~15 m off it), plus everything on the runway side of A. B/C stubs only matter beyond A.
from shapely.ops import linemerge
import re as _re
Aosm=unary_union([g for r,g in tw if r=='A' and g.distance(S)<80])
_M=open(H.MAPS,encoding='latin-1').read().split('\n'); _i=next(k for k,l in enumerate(_M) if l.strip()=='MAP:CYQM Ground Lines')
segs=[]
for l in _M[_i+1:]:
    if l.startswith('MAP:') or l.startswith('//<<<<'): break
    m=_re.match(r'LINE:([NS][\d.]+):([EW][\d.]+):([NS][\d.]+):([EW][\d.]+)',l.strip())
    if m: segs.append(LineString([xy(H.P(m.group(1)),H.P(m.group(2))),xy(H.P(m.group(3)),H.P(m.group(4)))]))
def _near_parallel(s):
    if s.length<0.5 or Aosm.distance(s.centroid)>30: return False
    d=Aosm.project(s.centroid); a=Aosm.interpolate(max(0,d-15)); b=Aosm.interpolate(min(Aosm.length,d+15))
    import math as _m
    t1=_m.atan2(b.y-a.y,b.x-a.x); c=s.coords; t2=_m.atan2(c[1][1]-c[0][1],c[1][0]-c[0][0])
    return abs(_m.sin(t1-t2))<0.35
net=linemerge(unary_union(segs)); net=list(net.geoms) if hasattr(net,'geoms') else [net]
import math as _m
def _dir(g,end):   # unit direction leaving the line at its end (end=1) or start (end=0), going outward
    c=list(g.coords); p,q=(c[-1],c[-2]) if end else (c[0],c[1])
    # use a point ~15 m back for stability
    d=0; k=len(c)-2 if end else 1; step=-1 if end else 1
    while 0<=k<len(c) and _m.dist(c[k],p)<15: k+=step
    k=max(0,min(len(c)-1,k)); q=c[k]; n=_m.dist(p,q) or 1
    return ((p[0]-q[0])/n,(p[1]-q[1])/n),p
seed=max([g for g in net if _near_parallel(LineString(g.coords[:2])) or Aosm.distance(g.centroid)<20],key=lambda g:g.length)
chain=[seed]; used={id(seed)}
for end in (0,1):
    cur,ce=seed,end
    for _ in range(20):
        (ux,uy),p=_dir(cur,ce); best=None
        for g in net:
            if id(g) in used or g.length<3: continue
            for e2 in (0,1):
                q=g.coords[-1] if e2 else g.coords[0]
                if _m.dist(p,q)>1.0: continue
                (vx,vy),_=_dir(g,e2); turn=_m.degrees(_m.acos(max(-1,min(1,-(ux*vx+uy*vy)))))
                if turn<40 and (best is None or turn<best[0]): best=(turn,g,1-e2)
        if not best: break
        _,cur,ce=best; chain.append(cur); used.add(id(cur))
Aparts=chain
sctA=unary_union(Aparts)
Aline=linemerge(sctA) if sctA.geom_type=='MultiLineString' else sctA
Aline=max(list(Aline.geoms),key=lambda g:g.length) if hasattr(Aline,'geoms') else Aline
print('sct A/C centreline chain:',len(Aparts),'pieces,',round(sum(g.length for g in Aparts)),'m')
ctl=unary_union([g.buffer(CTL,cap_style='flat',join_style='mitre') for g in Aparts])
for g in Aparts:
    if g.length<40: continue
    sides=[g.buffer(400,single_sided=True),g.buffer(-400,single_sided=True)]
    far=min(sides,key=lambda p:p.intersection(S).area)
    ctl=unary_union([ctl,far])
rw=[]
for l in open(H.SCT,encoding='latin-1'):
    p=l.split()
    if len(p)>=9 and p[8]=='CYQM': rw.append(LineString([xy(H.P(p[4]),H.P(p[5])),xy(H.P(p[6]),H.P(p[7]))]).buffer(61/2+10,cap_style='flat'))
zone=S.buffer(70).intersection(pave.buffer(1)).difference(block).difference(unary_union(rw))
# keep only what lies on the apron side of the A corridor: split by corridor, keep pieces touching the aprons
cut=unary_union([S,zone]).difference(ctl).difference(block).buffer(0.5).buffer(-0.5)
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
