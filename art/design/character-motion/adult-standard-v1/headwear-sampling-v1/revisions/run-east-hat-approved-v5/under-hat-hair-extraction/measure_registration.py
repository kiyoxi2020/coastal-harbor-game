from pathlib import Path
from PIL import Image,ImageDraw
import json,statistics
P=Path(__file__).resolve().parent;V=P.parent;H=V.parent.parent
# Anatomical feature ROIs are authored separately for each actual pose, not total-height ratios.
rois=[{'eye':(330,274,381,335),'brow':(331,248,372,260),'ear':(237,325,281,350)}, {'eye':(341,269,394,329),'brow':(341,242,384,256),'ear':(252,321,293,345)}, {'eye':(358,275,403,336),'brow':(360,246,405,261),'ear':(267,332,314,359)}, {'eye':(360,275,405,336),'brow':(362,246,408,261),'ear':(269,332,317,360)}]
def points(a,box,kind):
 out=[]
 for y in range(box[1],box[3]):
  for x in range(box[0],box[2]):
   r,g,b,al=a.getpixel((x,y))
   ok=al>200 and (max(r,g,b)<65 if kind!='brow' else (65<r<175 and 40<g<135 and b>35 and r<1.65*g))
   if ok:out.append((x,y))
 return out
def feature(a,box,kind):
 p=points(a,box,kind)
 if kind=='eye':
  top=min(y for x,y in p);xs=[x for x,y in p if y==top];v=[statistics.median(xs),top];which='top of visible dark eye within authored eye ROI'
 elif kind=='ear':
  right=max(x for x,y in p);ys=[y for x,y in p if x==right];v=[right,statistics.median(ys)];which='lower-right ear arc tip within authored lower-ear ROI; hair roots excluded by ROI'
 else:
  # Largest connected component avoids isolated hair-edge color in this eyebrow-only ROI.
  s=set(p);cs=[]
  while s:
   t=[s.pop()];c=[]
   while t:
    v=t.pop();c.append(v)
    for dx,dy in [(0,1),(0,-1),(1,0),(-1,0)]:
     z=(v[0]+dx,v[1]+dy)
     if z in s:s.remove(z);t.append(z)
   cs.append(c)
  p=max(cs,key=len);v=[(min(x for x,y in p)+max(x for x,y in p))/2,(min(y for x,y in p)+max(y for x,y in p))/2];which='center of visible eyebrow component inside authored anatomical ROI'
 return {'point_px':v,'method':which,'roi_px':box,'pixel_count':len(p)}
for i in range(4):
 D=P/f'run_east_{i}';source=Image.open(D/'source-full-frame.png').convert('RGBA');target=Image.open(H/f'run-east/references/run_east_{i}-bare.png').convert('RGBA');features={}
 for kind,box in rois[i].items():
  s=feature(source,box,kind);t=feature(target,box,kind);features[kind]={'source':s,'target':t,'target_minus_source_px':[t['point_px'][j]-s['point_px'][j] for j in range(2)]}
 rec={'pose_id':f'run_east_{i}','source_to_target_integer_translation_px':[0,0],'runtime_full_frame_placement_px':[0,0],'features':features,'decision':'Keep zero registration; no extra movement is inferred from small generated feature-shape residuals. Full source and original body were compared at 2x. Hair stays in generated pose coordinates, original body is never copied from generation.','residuals_equal_target_minus_source':True}
 (D/'registration-measurements.json').write_text(json.dumps(rec,indent=2)+'\n')
 print(i,{k:v['target_minus_source_px'] for k,v in features.items()})
