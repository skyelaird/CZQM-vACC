"""cyyr_unc.py - CYYR uncontrolled shading (Joel 2026-10-23): Twy J controlled (50 ft each side); everything
south(east) of J is uncontrolled apron (Aprons III/IIIB/IV/IVB, Twys H, K and G south of J); Aprons V and VI
north of J uncontrolled; G and H north of J controlled. Pavement from the sector-file regions, aprons/taxiways from OSM."""
import re,sys,os,math,shutil,time,urllib.request,xml.etree.ElementTree as ET
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import hold_lines as H
from shapely.geometry import Polygon,LineString,Point
from shapely.ops import unary_union,linemerge as _lm
def linemerge(g): return _lm(g) if g.geom_type=='MultiLineString' else g
CTL=50*0.3048
APRON_SOUTH=['1102382427','1102382428']; APRON_V_VI=['178416861','1102382426']
la0,lo0=53.31,-60.405;k=math.cos(math.radians(la0))
xy=lambda la,lo:((lo-lo0)*111320*k,(la-la0)*110574);ll=lambda X,Y:(Y/110574+la0,X/(111320*k)+lo0)
x=urllib.request.urlopen(urllib.request.Request('https://api.openstreetmap.org/api/0.6/map?bbox=-60.445,53.300,-60.390,53.318',headers={'User-Agent':'GRPmapBuilder/1.0'}),timeout=55).read()
r=ET.fromstring(x);N={n.get('id'):(float(n.get('lat')),float(n.get('lon'))) for n in r.iter('node')}
ap={};tw=[];rw=[]
for w in r.iter('way'):
    t={g.get('k'):g.get('v') for g in w.findall('tag')};p=[xy(*N[q.get('ref')]) for q in w.findall('nd') if q.get('ref') in N]
    if len(p)<2: continue
    a=t.get('aeroway')
    if a=='apron' and len(p)>2: ap[w.get('id')]=Polygon(p).buffer(0)
    if a=='taxiway': tw.append((t.get('ref'),LineString(p)))
    if a=='runway': rw.append(LineString(p).buffer(float(t.get('width','61'))/2+10,cap_style='flat'))
sec=None;regs=[];g=None
for l in open(H.SCT,encoding='latin-1'):
    if l.startswith('['): sec=l.strip();continue
    if sec!='[REGIONS]': continue
    if l.startswith('REGIONNAME'): g={'n':l[11:].strip(),'c':None,'p':[]};regs.append(g);continue
    m=re.findall(r'([NS]\d{3}\.\d\d\.\d\d\.\d+)\s+([EW]\d{3}\.\d\d\.\d\d\.\d+)',l)
    if g and m:
        if g['c'] is None: g['c']=l.split()[0]
        g['p']+=[xy(H.P(a),H.P(b)) for a,b in m]
reg=lambda cols:unary_union([Polygon(q['p']).buffer(0) for q in regs if q['n'].startswith('CYYR') and q['c'] in cols and len(q['p'])>2])
pave=reg(('COLOR_ApronSurface','COLOR_HardSurface3','COLOR_TaxiwayYellow','COLOR_HardSurface1','COLOR_HardSurface2'));block=reg(('COLOR_GrasSurface','COLOR_Building'))
J=linemerge(unary_union([g for r_,g in tw if r_=='J'])); J=J if J.geom_type=='LineString' else max(J.geoms,key=lambda q:q.length)
south=unary_union([ap[i] for i in APRON_SOUTH if i in ap])
sides=[J.buffer(450,single_sided=True,cap_style='flat'),J.buffer(-450,single_sided=True,cap_style='flat')]
SE=max(sides,key=lambda p:p.intersection(south).area)
# extend the south side beyond J's ends so H/K/G south of J are included
SE=unary_union([SE,south.buffer(60)]).intersection(J.buffer(700))
complexS=unary_union([south.buffer(45)]+[g.buffer(20) for r_,g in tw if r_ in ('H','K','G') and g.intersects(SE)]).intersection(SE)
zoneS=complexS.intersection(unary_union([pave.buffer(1),south])).difference(block)
vvi=unary_union([ap[i] for i in APRON_V_VI if i in ap])
Jband=J.buffer(CTL,cap_style='flat')
# Aprons I/II: west of G and south of P, both 50 ft off the centreline, west to where the apron narrows to the taxiway
MAIN='955374730'
G=linemerge(unary_union([g for r_,g in tw if r_=='G'])); G=G if G.geom_type=='LineString' else max(G.geoms,key=lambda q:q.length)
P_=linemerge(unary_union([g for r_,g in tw if r_=='P'])); P_=P_ if P_.geom_type=='LineString' else max(P_.geoms,key=lambda q:q.length)
cand=unary_union([ap[MAIN],pave.intersection(P_.buffer(350))]).difference(block).buffer(0.5).buffer(-0.5)
main=unary_union([q for q in (cand.geoms if hasattr(cand,'geoms') else [cand]) if q.intersects(ap[MAIN])])
def farside(line,ref):
    sd=[line.buffer(600,single_sided=True),line.buffer(-600,single_sided=True)]
    return min(sd,key=lambda p:p.intersection(ref).area)
mctl=unary_union([P_.buffer(CTL,cap_style='flat'),G.buffer(CTL,cap_style='flat'),farside(P_,ap[MAIN]),farside(G,ap[MAIN])])
mainU=main.difference(mctl)
# west limit: walk P westwards, measure apron depth on the apron side; cut where it falls below 60 m
import numpy as _np
ds=list(_np.arange(0,P_.length,10)); prof=[]
for d in ds:
    a=P_.interpolate(max(0,d-5)); b=P_.interpolate(min(P_.length,d+5)); dx,dy=b.x-a.x,b.y-a.y; n=math.hypot(dx,dy) or 1
    c=P_.interpolate(d)
    for sg in (1,-1):
        seg=LineString([(c.x,c.y),(c.x-sg*dy/n*250,c.y+sg*dx/n*250)])
        L=seg.intersection(mainU).length
        if L>0: break
    prof.append((d,L,c,(dx/n,dy/n)))
west_is_start=P_.coords[0][0]<P_.coords[-1][0]
d0=P_.project(ap[MAIN].centroid); seq=[q for q in prof if (q[0]<=d0 if west_is_start else q[0]>=d0)]
seq=sorted(seq,key=lambda q:-q[0] if west_is_start else q[0])   # from the apron walking west
edge=None
for k_ in range(len(seq)-2):
    if all(seq[k_+m][1]<60 for m in range(3)): edge=seq[k_-1] if k_>0 else seq[0]; break
if edge:
    d,L,c,(ux,uy)=edge; ux,uy=(-ux,-uy) if west_is_start else (ux,uy)   # unit vector pointing west along P
    cut=Polygon([(c.x+(-uy)*800,c.y+ux*800),(c.x+(-uy)*800+ux*2000,c.y+ux*800+uy*2000),(c.x-(-uy)*800+ux*2000,c.y-ux*800+uy*2000),(c.x-(-uy)*800,c.y-ux*800)])
    mainU=mainU.difference(cut)
    print('Apron I/II west limit at',round(d),'m along P (depth',round(L),'m)')
U=unary_union([zoneS,south,vvi,mainU]).difference(Jband).difference(unary_union(rw)).buffer(0.5).buffer(-0.5)
polys=[p for p in (U.geoms if hasattr(U,'geoms') else [U]) if p.area>150]
print('areas',[round(p.area) for p in polys],'holes',sum(len(p.interiors) for p in polys))
M=open(H.MAPS,encoding='latin-1').read().replace('\r\n','\n').split('\n')
i=next(q for q,l in enumerate(M) if l.startswith('//>>>> CYYR UNCONTROLLED'));j=M.index('//<<<< END CYYR UNCONTROLLED',i)
blk=['//>>>> CYYR UNCONTROLLED - Joel 2026-10-23: Twy J controlled; all pavement south of J (Aprons III/IIIB/IV/IVB, Twys H, K, G south of J) and Aprons V, VI uncontrolled; Aprons I/II 50 ft off G and P - tools\\\\cyyr_unc.py from OSM (c) OSM contributors, ODbL + sector-file pavement',
     'MAP:CYYR Uncontrolled','FOLDER:CYYR','AIRPORT:CYYR','ACTIVE:1','LAYER:3','COLOR:UNCTL/45']
for p in polys:
    rings=[p.exterior] 
    blk.append('COORDTYPE:OTHER:REGION_FILLONLY')
    blk+=[f"COORD:{H.dms(a,'N','S')}:{H.dms(b,'E','W')}" for a,b in (ll(*c) for c in list(p.simplify(0.5).exterior.coords)[:-1])]
blk.append('//<<<< END CYYR UNCONTROLLED')
shutil.copy(H.MAPS,os.path.join(H.GRP,'_bak','GRpluginMaps.txt'+time.strftime('.bak_%Y%m%d_%H%M%S')))
M[i:j+1]=blk; open(H.MAPS,'w',encoding='latin-1',newline='\r\n').write('\n'.join(M))
