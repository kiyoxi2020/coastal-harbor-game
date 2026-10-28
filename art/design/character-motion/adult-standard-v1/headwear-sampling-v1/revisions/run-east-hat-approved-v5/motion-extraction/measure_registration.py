from pathlib import Path
from PIL import Image,ImageDraw
import json,statistics
P=Path(__file__).resolve().parent;H=P.parent.parents[1]
orig_ear=[(264,291),(274,286),(293,291),(294,291)];src_ear=[(252,285),(268,283),(279,247),(291,247)];src_eye=[(344,292),(358,289),(368,259),(382,259)];src_brow=[(340,246),(352,244),(365,208),(378,208)]
def comps(a,box,pred):
 x0,y0,x1,y1=box;s={(x,y) for y in range(y0,y1) for x in range(x0,x1) if pred(a.getpixel((x,y)))};out=[]
 while s:
  seed=s.pop();q=[seed];pts=[]
  while q:
   x,y=q.pop();pts.append((x,y))
   for dx,dy in [(0,1),(1,0),(0,-1),(-1,0),(-1,-1),(-1,1),(1,-1),(1,1)]:
    v=(x+dx,y+dy)
    if v in s:s.remove(v);q.append(v)
  xs=[v[0] for v in pts];ys=[v[1] for v in pts];bb=[min(xs),min(ys),max(xs)+1,max(ys)+1];out.append((pts,bb))
 return out
def dark(p):return p[3]>=200 and max(p[:3])<80
def feature(a,typ,approx):
 x,y=approx
 if typ=='ear':
  candidates=comps(a,(x-42,y-10,x+43,y+75),dark);candidates=[c for c in candidates if c[1][2]-c[1][0]>=28 and c[1][3]-c[1][1]>=35]
 elif typ=='eye':
  candidates=comps(a,(x-30,y-40,x+31,y+50),dark);candidates=[c for c in candidates if c[1][2]-c[1][0]>=18 and c[1][3]-c[1][1]>=25]
 else:
  pred=lambda p:p[3]>=200 and 50<p[0]<175 and 20<p[1]<145 and p[2]<115 and p[0]>p[1]*1.2
  candidates=comps(a,(x-28,y-8,x+29,y+9),pred);candidates=[c for c in candidates if c[1][2]-c[1][0]>=25 and c[1][3]-c[1][1]<=16]
 if not candidates:raise ValueError((typ,approx,'no component'))
 pts,bb=min(candidates,key=lambda c:abs((c[1][0]+c[1][2])/2-x)+abs(c[1][1]-(y if typ!='eye' else y-20)))
 if typ=='brow':point=[(bb[0]+bb[2]-1)/2,(bb[1]+bb[3]-1)/2]
 else:
  top=min(v[1] for v in pts);xs=[xx for xx,yy in pts if yy==top];point=[(min(xs)+max(xs))/2,top]
 return {'point_px':point,'component_bbox_px':bb,'component_pixels':len(pts),'method':'Color-assisted connected feature within manually identified anatomical ROI; subject to overlay visual review.'}
records=[]
for i in range(4):
 q=P/f'run_east_{i}';a=Image.open(q/'source-window.png').convert('RGBA');b=Image.open(q/'original-body.png').convert('RGBA');oe=orig_ear[i]
 refs={'ear':(oe,src_ear[i]),'eye':((oe[0]+90,oe[1]+15),src_eye[i]),'brow':((oe[0]+87,oe[1]-38),src_brow[i])};result={}
 for typ,(ta,sa) in refs.items():
  t=feature(b,typ,ta);s=feature(a,typ,sa);result[typ]={'target':t,'source':s,'delta_px':[t['point_px'][j]-s['point_px'][j] for j in range(2)]}
 offset=[round(statistics.median(v['delta_px'][j] for v in result.values())) for j in range(2)]
 for v in result.values():v['residual_after_integer_translation_px']=[v['delta_px'][j]-offset[j] for j in range(2)]
 rec={'pose_id':f'run_east_{i}','status':'measurement-candidate-needs-human-review','features':result,'candidate_integer_translation_px':offset};records.append(rec)
 board=Image.new('RGB',(1024,340),'#d6e0e7')
 for col,im in enumerate([b,a]):
  bg=Image.new('RGBA',im.size,'#d6e0e7');bg.alpha_composite(im);board.paste(bg.crop((0,60,512,400)).convert('RGB'),(col*512,0))
 d=ImageDraw.Draw(board)
 for name,v in result.items():
  for col,k in enumerate(['target','source']):
   x,y=v[k]['point_px'];x+=512*col;y-=60;d.ellipse((x-3,y-3,x+3,y+3),outline='red',width=1);d.text((x+4,y-8),name,fill='blue')
 board.save(q/'landmarks-source-target.png')
 (q/'registration-measurements.json').write_text(json.dumps(rec,indent=2)+'\n')
(P/'registration-measurements.json').write_text(json.dumps(records,indent=2)+'\n');print(json.dumps(records,indent=2))
