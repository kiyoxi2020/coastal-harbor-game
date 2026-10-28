"""Read source/target geometry and search whole-view integer registration only.
No pixel painting, body erasure, hair cutting or runtime offsets. All writes here.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops
import json,hashlib,importlib.util,math
P=Path(__file__).resolve().parent;H=P.parents[2];OLD=H/'hoe-west';V5=H/'revisions/run-east-hat-approved-v5'
spec=importlib.util.spec_from_file_location('approved_compose',V5/'build_approved.py');standard=importlib.util.module_from_spec(spec);spec.loader.exec_module(standard)
S=json.loads((OLD/'sample.json').read_text());R=json.loads((OLD/'registration.json').read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def js(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def segments(mask):
 px=mask.load();out=[]
 for y in range(mask.height):
  runs=[];x=0
  while x<mask.width:
   if px[x,y]:
    a=x
    while x<mask.width and px[x,y]:x+=1
    runs.append([a,x-1])
   else:x+=1
  if runs:out.append({'y':y,'inclusive_x_runs':runs})
 return out
# Split only the actual brown underside lobes. Shared black lip belongs near.
seams=[{'left':[(43,412),(95,432),(173,474),(190,482)],'right':[(490,619),(535,638),(585,657),(630,674),(684,695)]},
 {'left':[(30,480),(85,507),(168,550),(190,563)],'right':[(480,704),(500,710),(525,717),(565,733),(638,743),(684,743)]},
 {'left':[(35,424),(90,449),(173,496),(190,506)],'right':[(480,640),(500,648),(560,669),(625,688),(680,704)]},
 {'left':[(36,410),(95,443),(175,493),(190,501)],'right':[(450,630),(470,643),(500,652),(560,669),(625,685),(692,702)]}]
def interpolate(poly,x):
 if x<=poly[0][0]:return poly[0][1]
 if x>=poly[-1][0]:return poly[-1][1]
 for a,b in zip(poly,poly[1:]):
  if a[0]<=x<=b[0]:return a[1]+(x-a[0])*(b[1]-a[1])/(b[0]-a[0])
def parts_motion(i):
 cfg=R['motion'][i];raw=Image.open(OLD/R['motion_sources']['hat']).convert('RGBA');normal=raw.resize(tuple(R['atlas_px']),Image.Resampling.NEAREST);src=normal.crop(tuple(cfg['atlas_box_px']));sem=Image.new('L',src.size);ImageDraw.Draw(sem).polygon([tuple(x) for x in cfg['hat']['polygon']],fill=255)
 own=Image.new('L',src.size);a=src.load();o=own.load();q=sem.load()
 for y in range(src.height):
  for x in range(src.width):
   if q[x,y] and a[x,y][3]:o[x,y]=255
 near=own.copy();far=Image.new('L',src.size);n=near.load();f=far.load()
 for y in range(src.height):
  for x in range(src.width):
   lower=False
   for side,poly in seams[i].items():
    authorized=(x<=poly[-1][0] if side=='left' else x>=poly[0][0])
    if authorized and y>interpolate(poly,x):lower=True
   if o[x,y] and lower:f[x,y]=255;n[x,y]=0
 return src,own,near,far

def feature_points(body,box,kind):
 px=body.load();s=set()
 for y in range(box[1],box[3]):
  for x in range(box[0],box[2]):
   r,g,b,a=px[x,y]
   match=max(r,g,b)<80 if kind!='brow' else (50<r<180 and 20<g<130 and b<100 and r>1.2*g)
   if a>=200 and match:s.add((x,y))
 cs=[]
 while s:
  q=[s.pop()];c=[]
  while q:
   v=q.pop();c.append(v)
   for dx,dy in [(0,1),(1,0),(-1,0),(0,-1)]:
    z=(v[0]+dx,v[1]+dy)
    if z in s:s.remove(z);q.append(z)
  if len(c)>20:cs.append(c)
 # Feature ROIs explicitly exclude the external head contour.
 c=max(cs,key=len);xs=[x for x,y in c];ys=[y for x,y in c]
 return c,[min(xs),min(ys),max(xs)+1,max(ys)+1]

def probe(i):
 f=S['frames'][i];pose=f['pose_id'];D=P/pose;D.mkdir(exist_ok=True);src,own,nm,fm=parts_motion(i);body=Image.open(OLD/f['states']['bare']['file']).convert('RGBA');hair=Image.open(OLD/f['parts']['hair']['registered_file']).convert('RGBA');px=body.load();np=nm.load();sp=src.load();hp=hair.load();cfg=R['motion'][i]['hat'];old=cfg['offset_px'];target=cfg['target_anchor_px'];earref=R['motion'][i]['hair']['target_anchor_px']
 # Authored anatomical ROIs around actual original eyebrows, eyes and ear arcs.
 boxes={'brow':(target[0]-60,target[1]+3,target[0]+65,target[1]+45),'eye':(target[0]-55,target[1]+55,target[0]+40,target[1]+160),'ear':(earref[0]-35,earref[1]-10,earref[0]+135,earref[1]+155)}
 features={k:feature_points(body,b,k) for k,b in boxes.items()}
 print(pose,'FEATURES',{k:v[1] for k,v in features.items()},flush=True)
 y0=next(y for y in range(100,600) if any(px[x,y][3]>=200 for x in range(380,910)));upper=[];headpoints=[]
 # Dense actual original-body upper head contour and bounded head surface. Protected face features are not inferred from a height fraction.
 for y in range(y0,min(features['ear'][1][1]+15,850)):
  xs=[x for x in range(375,915) if px[x,y][3]>=200]
  if not xs:continue
  upper.append((min(xs),y));upper.append((max(xs),y))
  if y%6==0:
   headpoints.extend((x,y) for x in range(min(xs),max(xs)+1,6) if px[x,y][3]>=200)
 top=[z for z in upper if z[1]<=y0+60]
 hair_outline=[]
 hb=hair.getbbox()
 for yy in range(hb[1],hb[3],2):
  xx=[x for x in range(hb[0],hb[2]) if hp[x,yy][3]>=200]
  if xx:hair_outline.extend([(min(xx),yy),(max(xx),yy)])
 for xx in range(hb[0],hb[2],2):
  yy=[y for y in range(hb[1],hb[3]) if hp[xx,y][3]>=200]
  if yy:hair_outline.append((xx,min(yy)))
 profile={x:max([y for y in range(src.height) if np[x,y] and sp[x,y][3]>=200],default=-1) for x in range(src.width)}
 def at(x,y,ox,oy):
  sx,sy=x-ox,y-oy
  return 0<=sx<src.width and 0<=sy<src.height and np[sx,sy] and sp[sx,sy][3]>=200
 def mouth(x,ox,oy):return profile.get(x-ox,-10000)+oy
 def assess(ox,oy,precise=False):
  topmiss=sum(not at(x,y,ox,oy) for x,y in top)
  arc=[(x,y) for x,y in upper if y<=mouth(x,ox,oy)]
  missing=sum(not at(x,y,ox,oy) for x,y in arc)
  surface=sum(not at(x,y,ox,oy) for x,y in headpoints if y<=mouth(x,ox,oy))
  collisions={k:sum(at(x,y,ox,oy) for x,y in v[0]) for k,v in features.items()}
  hair_miss=sum(not at(x,y,ox,oy) for x,y in hair_outline if y<=mouth(x,ox,oy))
  contact=sum(0<=x+ox<body.width and 0<=yy+oy<body.height and px[x+ox,yy+oy][3]>=200 for x,yy in profile.items() if yy>=0)
  return {'sampled_upper_hair_missing':hair_miss,'top_missing':topmiss,'arc_missing':missing,'sampled_cavity_missing':surface,'protected_collisions':collisions,'lip_on_original_head_columns':contact,'score':(topmiss+missing+surface+sum(collisions.values())+max(0,200-contact))*1000000+hair_miss*100}
 results=[]
 for dx in range(-20,125,4):
  for dy in range(-25,66,4):
   ox,oy=old[0]+dx,old[1]+dy;a=assess(ox,oy);results.append((a['score'],dx*dx+dy*dy,ox,oy,a))
 results.sort(key=lambda t:(t[0],t[1]));_,_,cx,cy,_=results[0]
 fine=[]
 for ox in range(cx-4,cx+5):
  for oy in range(cy-4,cy+5):
   a=assess(ox,oy);fine.append((a['score'],(ox-old[0])**2+(oy-old[1])**2,ox,oy,a))
 fine.sort(key=lambda t:(t[0],t[1]));best=fine[0];ox,oy=best[2:4];geometry=best[4]
 # No fitness score itself authorizes a runtime candidate; exact source/body/hair checks and visual review follow.
 js(D/'registration-probe.json',{'pose_id':pose,'old_translation_px':old,'candidate_translation_px':[ox,oy],'search_bound_relative_to_old_px':[-20,124,-25,65],'constraint_basis':'All actual original-body top arc, dense upper side contour/cavity sample, protected original eyebrow/eye/ear feature pixels, real near-lip source columns in physical contact with original head. No body erasure, no max-y hair mask. Profile used only as finite geometric measurement of actual near source surface.','features':{k:{'authored_roi_px':boxes[k],'actual_bbox_px':v[1],'pixels':len(v[0])} for k,v in features.items()},'geometry':geometry,'top_candidates':[{'translation_px':[t[2],t[3]],'geometry':t[4]} for t in fine[:5]]})
 for name,a in [('source-full-frame.png',src),('source-ownership.png',own),('source-near-ownership.png',nm),('source-far-ownership.png',fm)]:a.save(D/name)
 js(D/'source-contours.json',{'pose_id':pose,'source_crop_px':R['motion'][i]['atlas_box_px'],'source_crop_canvas_px':list(src.size),'source_ownership':segments(own),'near_ownership':segments(nm),'far_ownership':segments(fm),'near_far_basis':seams[i],'source_rgba_policy':'Unchanged actual source pixels; frozen masks only.'})
 def reg(mask):
  plate=Image.new('RGBA',src.size);plate.paste(src,(0,0),mask);out=Image.new('RGBA',body.size);out.paste(plate,(ox,oy));return out
 near=reg(nm);far=reg(fm);plate=reg(own);near.save(D/'hat-near.png');far.save(D/'hat-far.png');plate.save(D/'hat-complete-plate.png');body.save(D/'original-body.png');hair.save(D/'full-original-hair.png')
 for name,mask in [('registered-ownership.png',own),('near-ownership.png',nm),('far-ownership.png',fm)]:
  out=Image.new('L',body.size);out.paste(mask,(ox,oy));out.save(D/name)
 comp,_=standard.compose(body,near,far);both,_=standard.compose(body,near,far,hair);comp.save(D/'composite.png');both.save(D/'hair-hat-composite.png')
 # Full original hair is deliberately intact; no cap-volume subtract is performed.
 crown=[]
 for y in range(max(0,hair.getbbox()[1]),min(hair.height,hair.getbbox()[3])):
  for x in range(hair.getbbox()[0],hair.getbbox()[2]):
   if hp[x,y][3]>=200 and y<=mouth(x,ox,oy) and not at(x,y,ox,oy):crown.append((x,y))
 js(D/'hair-compatibility-probe.json',{'full_original_hair_preserved_sha256':sha(OLD/f['parts']['hair']['registered_file']),'non_surface_upper_hair_pixels':len(crown),'examples_px':crown[::max(1,len(crown)//12)][:12],'full_hair_compatible':False if crown else None,'meaning':'Hair pixels above actual near lip but outside actual near hat surface. Audit only; hair is never cut by this profile. Visual semantic review decides whether a point is a crown protrusion or legitimately visible fringe.'})
 board=Image.new('RGB',(1536,960),(224,230,234));d=ImageDraw.Draw(board);box=(300,100,1030,900)
 for j,im in enumerate([comp,both]):
  bg=Image.new('RGBA',im.size,(224,230,234,255));bg.alpha_composite(im);crop=bg.crop(box);crop.thumbnail((730,850),Image.Resampling.NEAREST);board.paste(crop.convert('RGB'),(j*768,30));d.text((j*768+10,4),pose+(' hat ' if j==0 else ' intact full-hair + hat ')+str([ox,oy]),fill='black')
 board.save(D/'geometry-probe-board.png')
 print(pose,'BEST',[ox,oy],geometry,'upper outside hair',len(crown),flush=True)
 return {'pose_id':pose,'translation_px':[ox,oy],'geometry':geometry,'upper_outside_hair_count':len(crown)}
if __name__=='__main__':
 import sys
 indices=[int(x) for x in sys.argv[1:]] or list(range(4));results=[probe(i) for i in indices];js(P/'motion-probe-summary.json',results)
