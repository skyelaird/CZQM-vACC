import glob,json,math,re,os,shutil,time
from shapely.geometry import Polygon,LineString
from shapely.ops import unary_union
sct=sorted(glob.glob(r'C:\Users\JoelMorin\AppData\Roaming\EuroScope\CZQQ-CZQM-*.sct'))[-1]
def P(s):
    h=s[0];d,m,a,b=s[1:].split('.');v=int(d)+int(m)/60+float(a+'.'+b)/3600
    return -v if h in 'SW' else v
la0,lo0=44.881,-63.51;k=math.cos(math.radians(la0));xy=lambda la,lo:((lo-lo0)*111320*k,(la-la0)*110574);ll=lambda X,Y:(Y/110574+la0,X/(111320*k)+lo0)
def dms(v,p,q):
    h=p if v>=0 else q;v=abs(v);d=int(v);m=int((v-d)*60);sec=round((v-d-m/60)*3600,3)
    if sec>=60: sec-=60;m+=1
    if m==60: m=0;d+=1
    return f"{h}{d:03d}.{m:02d}.{sec:06.3f}"
sec=None;regs=[];cur=None
for l in open(sct,encoding='latin-1').read().split('\n'):
    if l.startswith('['): sec=l.strip();continue
    if sec!='[REGIONS]': continue
    if l.startswith('REGIONNAME'): cur={'name':l[11:].strip(),'col':None,'pts':[]};regs.append(cur);continue
    m=re.findall(r'([NS]\d{3}\.\d\d\.\d\d\.\d+)\s+([EW]\d{3}\.\d\d\.\d\d\.\d+)',l)
    if cur and m:
        if cur['col'] is None: cur['col']=l.split()[0]
        cur['pts']+=[xy(P(a),P(b)) for a,b in m]
pavement=unary_union([Polygon(r['pts']).buffer(0) for r in regs if r['name'].startswith('CYHZ') and r['col'] in ('COLOR_ApronSurface','COLOR_HardSurface3') and len(r['pts'])>2])
blockers=unary_union([Polygon(r['pts']).buffer(0) for r in regs if r['name'].startswith('CYHZ') and r['col'] in ('COLOR_GrasSurface','COLOR_Building') and len(r['pts'])>2])
raw=json.load(open(r'D:\GitHub\CZQM-vACC\GroundRadar\tools\osm-to-grp\data\cyhz_raw.json'));E=raw.get('elements',raw);els={(e['type'],e['id']):e for e in E}
def poly(i): return Polygon([xy(q['lat'],q['lon']) for q in els[('way',i)]['geometry']]).buffer(0)
tw=[(e.get('tags',{}).get('ref'),LineString([xy(q['lat'],q['lon']) for q in e['geometry']])) for e in E if (e.get('tags') or {}).get('aeroway')=='taxiway' and e.get('geometry') and len(e['geometry'])>1]
rw=unary_union([LineString([xy(q['lat'],q['lon']) for q in e['geometry']]).buffer(float(e['tags'].get('width','61'))/2+10,cap_style='flat') for e in E if (e.get('tags') or {}).get('aeroway')=='runway' and (e.get('tags') or {}).get('ref') and e.get('geometry')])
e2=(-397,257);s3=(-320,368);ux,uy=s3[0]-e2[0],s3[1]-e2[1];Ln=math.hypot(ux,uy);ux,uy=ux/Ln,uy/Ln;o=(e2[0]-20*ux,e2[1]-20*uy);nx,ny=-uy,ux;F=5000
half=Polygon([(o[0]+nx*F,o[1]+ny*F),(o[0]+nx*F+ux*F,o[1]+ny*F+uy*F),(o[0]-nx*F+ux*F,o[1]-ny*F+uy*F),(o[0]-nx*F,o[1]-ny*F)])
def grow(base,clip=None,band=70):
    zone=base.buffer(band)
    if clip is not None: zone=zone.intersection(clip)
    lane=[g for r,g in tw if g.intersection(zone).length>0.5*g.length]          # taxilanes running along the apron
    others=unary_union([g.buffer(14) for r,g in tw if g not in lane]).difference(base.buffer(45))
    ext=zone.intersection(pavement).difference(blockers).difference(rw).difference(others)
    A=unary_union([base.intersection(pavement.buffer(3)),ext]).buffer(0.5).buffer(-0.5)
    parts=[p for p in (A.geoms if hasattr(A,'geoms') else [A]) if p.intersects(base) and p.area>200]
    return unary_union(parts)
main=poly(1271831708).intersection(half);deice=unary_union([poly(1271831709),poly(1271831710)]);cargo=poly(878197441)
G=unary_union([g.buffer(15) for r,g in tw if r=='G'])
from shapely.geometry import Point,box
from shapely import affinity
st={}
for l in open(r'C:\Users\JoelMorin\AppData\Roaming\EuroScope\CZQQ\Plugins\GRP\GRpluginStands.txt',encoding='latin-1'):
    if l.startswith('STAND:CYHZ:'): p=l.split(':');st[p[2]]=xy(P(p[3]),P(p[4]))
def hp(pt,d,keep_side_pt,size=4000):
    """half-plane through pt, perpendicular to unit d, on the side of keep_side_pt"""
    nx,ny=-d[1],d[0];sgn=1 if ((keep_side_pt[0]-pt[0])*d[0]+(keep_side_pt[1]-pt[1])*d[1])>=0 else -1
    dx,dy=d[0]*sgn,d[1]*sgn
    return Polygon([(pt[0]+nx*size,pt[1]+ny*size),(pt[0]+nx*size+dx*size,pt[1]+ny*size+dy*size),(pt[0]-nx*size+dx*size,pt[1]-ny*size+dy*size),(pt[0]-nx*size,pt[1]-ny*size)])
def twy(ref): return unary_union([g for r,g in tw if r==ref])
def tangent(line,pt):
    d=line.project(Point(pt));a=line.interpolate(max(0,d-10));b=line.interpolate(min(line.length,d+10))
    L=math.hypot(b.x-a.x,b.y-a.y);return ((b.x-a.x)/L,(b.y-a.y)/L)
def straight_cut(region,ref,apron,local=180):
    """cut the region straight across taxiway <ref> where it leaves the apron (grass-edge line)"""
    t=twy(ref);segs=list(t.geoms) if hasattr(t,'geoms') else [t]
    for g in segs:
        x=g.intersection(apron.exterior)
        pts=[x] if x.geom_type=='Point' else (list(x.geoms) if hasattr(x,'geoms') else [])
        for p in pts:
            d=tangent(g,(p.x,p.y));c=apron.centroid
            keep=hp((p.x,p.y),d,(c.x,c.y))
            region=region.difference(Point(p.x,p.y).buffer(local).difference(keep))
    return region
from shapely.ops import linemerge
lane_ids=[94029904,94029884,94029835,94029880,94029897,94029938,94029929]
lane=linemerge(unary_union([LineString([xy(q['lat'],q['lon']) for q in els[('way',i)]['geometry']]) for i in lane_ids]))
grass=unary_union([Polygon(r['pts']).buffer(0) for r in regs if r['name'].startswith('CYHZ') and r['col']=='COLOR_GrasSurface' and len(r['pts'])>2])
edge=lane.buffer(38,cap_style='flat',join_style='mitre').intersection(pavement.buffer(1)).difference(grass)
mainA=unary_union([main.intersection(half).intersection(pavement.buffer(3)),edge]).buffer(1).buffer(-1)
mainA=mainA.intersection(half)
# G: include the G corridor between the de-icing pads, up to the pads' east edge
Gl=twy('G');pads_e=max(deice.exterior.coords if deice.geom_type=='Polygon' else [c for g in deice.geoms for c in g.exterior.coords],key=lambda c:c[0])
gd=tangent(Gl if Gl.geom_type=='LineString' else max(Gl.geoms,key=lambda g:g.length),pads_e)
Gzone=unary_union([Gl.buffer(25).intersection(pavement),deice]).convex_hull.difference(grass).intersection(hp(pads_e,gd,(main.centroid.x,main.centroid.y)))
mainA=unary_union([mainA,deice,Gzone])
Hb=twy('H').buffer(20).difference(main.buffer(2));print('H overlap before',round(mainA.intersection(Hb).area))
for ref in ('D','H'): mainA=straight_cut(mainA,ref,main)
Hl=twy('H');Hl=Hl if Hl.geom_type=='LineString' else max(Hl.geoms,key=lambda g:g.length)
if Point(Hl.coords[-1]).distance(main)<Point(Hl.coords[0]).distance(main): Hl=LineString(Hl.coords[::-1])
for cut_at in (25,30,35):
    pc=Hl.interpolate(cut_at);dH=tangent(Hl,(pc.x,pc.y))
    print('cut',cut_at,'grass within 20m of cut line', round(LineString([(pc.x-dH[1]*40,pc.y+dH[0]*40),(pc.x+dH[1]*40,pc.y-dH[0]*40)]).intersection(grass).length))
pc=Hl.interpolate(30);dH=tangent(Hl,(pc.x,pc.y))
mainA=mainA.difference(Point(pc.x,pc.y).buffer(400).difference(hp((pc.x,pc.y),dH,(main.centroid.x,main.centroid.y))))   # H is controlled: cut straight across at the grass edge
Aw=unary_union([g for r,g in tw if r=='A']).intersection(half)
Aband=Aw.buffer(38,cap_style='flat',join_style='mitre').intersection(pavement.buffer(1)).difference(grass).difference(rw).intersection(half)
print('A band added',round(Aband.difference(mainA).area))
mainA=unary_union([mainA,Aband]).buffer(1).buffer(-1)   # A behind the 2s is uncontrolled too
print('H overlap after',round(mainA.intersection(Hb).area))
# north limit: no further than the 34-46 apron
ux2,uy2=st['46'][0]-st['2E'][0],st['46'][1]-st['2E'][1];L2=math.hypot(ux2,uy2);u2=(ux2/L2,uy2/L2)
far=max(st[s] for s in ('34','36','38','40','42','44','46') if s in st) if False else max((st[s] for s in ('34','36','38','40','42','44','46')),key=lambda q:q[0]*u2[0]+q[1]*u2[1])
lim=(far[0]+u2[0]*45,far[1]+u2[1]*45)
mainA=mainA.intersection(hp(lim,u2,st['2E']))
# cargo: all parking incl. 308/308F
cs=[st[s] for s in ('301','302','303','304','305','306','307','308','308F') if s in st]
cargoA=unary_union([grow(cargo)]+[Point(*q).buffer(45).intersection(pavement.buffer(2)) for q in cs])
A=unary_union([mainA,cargoA])
polys=[p for p in (A.geoms if hasattr(A,'geoms') else [A]) if p.area>1500]
print('areas',[round(p.area) for p in polys])
blk=['//>>>> CYHZ UNCONTROLLED - main apron from Gate 2E northwards incl. edge taxilane to the grass, de-icing pads and Twy G between them; cut straight across D and H; north to the 34-46 apron; cargo apron (Ramp 3) incl. all parking 301-308F (Joel 2026-10-23; H controlled - cut at the apron edge; A behind the 2s uncontrolled)',
     '// built from OSM aprons/taxiways (c) OSM contributors, ODbL, bounded by the sector-file grass and building regions',
     'MAP:CYHZ Uncontrolled','FOLDER:CYHZ','AIRPORT:CYHZ','ACTIVE:1','LAYER:3','COLOR:UNCTL/45']
for p in polys:
    blk.append('COORDTYPE:OTHER:REGION_FILLONLY')
    blk+=[f"COORD:{dms(a,'N','S')}:{dms(b,'E','W')}" for a,b in (ll(*c) for c in list(p.simplify(0.8).exterior.coords)[:-1])]
    if p.interiors: print('holes dropped',[round(Polygon(h).area) for h in p.interiors])
blk.append('//<<<< END CYHZ UNCONTROLLED')
Gd=r'C:\Users\JoelMorin\AppData\Roaming\EuroScope\CZQQ\Plugins\GRP';f=os.path.join(Gd,'GRpluginMaps.txt')
shutil.copy(f,os.path.join(Gd,'_bak','GRpluginMaps.txt'+time.strftime('.bak_%Y%m%d_%H%M%S')))
M=open(f,encoding='latin-1').read().replace('\r\n','\n').split('\n')
x=next(q for q,l in enumerate(M) if l.startswith('//>>>> CYHZ UNCONTROLLED'));j=M.index('//<<<< END CYHZ UNCONTROLLED',x);M[x:j+1]=blk
open(f,'w',encoding='latin-1',newline='\r\n').write('\n'.join(M));print('points',sum(1 for l in blk if l.startswith('COORD:')))




