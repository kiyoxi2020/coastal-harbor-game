from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib,importlib.util
P=Path(__file__).resolve().parent;H=P.parents[2];O=H/'hoe-west';D=P/'idle_west_0';D.mkdir(exist_ok=True)
spec=importlib.util.spec_from_file_location('approved_compose',H/'revisions/run-east-hat-approved-v5/build_approved.py');std=importlib.util.module_from_spec(spec);spec.loader.exec_module(std)
f=json.loads((O/'sample.json').read_text())['idle'];r=json.loads((O/'registration.json').read_text())['idle']['hat'];raw=Image.open(O/r['source']).convert('RGBA');src=raw.crop(tuple(r['source_box_px']));body=Image.open(O/f['states']['bare']['file']).convert('RGBA');hair=Image.open(O/f['parts']['hair']['registered_file']).convert('RGBA');sem=Image.new('L',src.size);ImageDraw.Draw(sem).polygon([tuple(p) for p in r['polygon']],fill=255);sp=src.load()
# Source lower black lip: dense source seam measurements within a reviewed narrow
# anatomical strip. Freeze this result; it is not inferred during later rebuilds.
seam={}
for x in range(145,351):
 cy=x/3+160;c=[y for y in range(round(cy)-8,round(cy)+9) if max(sp[x,y][:3])<80 and sp[x,y][3]>=200]
 seam[x]=max(c) if c else round(cy)
for x in range(53,446):
 if x<145:
  points=[(53,177),(80,186),(110,195),(132,200),(140,203),(145,seam[145])]
  for aa,bb in zip(points,points[1:]):
   if aa[0]<=x<=bb[0]:seam[x]=round(aa[1]+(x-aa[0])*(bb[1]-aa[1])/(bb[0]-aa[0]));break
  if x>=136:
   while seam[x]>195 and max(sp[x,seam[x]][:3])>=80:seam[x]-=1
 elif x>350:seam[x]=round(seam[350]+(x-350)/3)
near=Image.new('L',src.size);far=Image.new('L',src.size);n=near.load();ff=far.load();ss=sem.load()
farpoly=[(371,281),(369,285),(365,291),(362,297),(359,302),(358,307),(362,312),(373,317),(390,321),(437,320),(447,311),(448,300),(441,289),(421,281)]
rear=Image.new('L',src.size);ImageDraw.Draw(rear).polygon(farpoly,fill=255);rp=rear.load()
for y in range(src.height):
 for x in range(src.width):
  if not(ss[x,y] and sp[x,y][3]):continue
  lip=seam.get(x,-1)
  if y<=lip:n[x,y]=255
  elif x<136 or rp[x,y]:ff[x,y]=255
own=Image.new('L',src.size);op=own.load()
for y in range(src.height):
 for x in range(src.width):op[x,y]=255 if n[x,y] or ff[x,y] else 0
# Frozen ownership is the production authority, not source color or alpha alone.
def rows(mask):
 a=mask.load();out=[]
 for y in range(mask.height):
  runs=[];x=0
  while x<mask.width:
   if a[x,y]:
    lo=x
    while x<mask.width and a[x,y]:x+=1
    runs.append([lo,x-1])
   else:x+=1
  if runs:out.append({'y':y,'inclusive_x_runs':runs})
 return out
for name,im in [('source-full-frame.png',src),('source-ownership.png',own),('registered-ownership.png',own),('source-near-ownership.png',near),('near-ownership.png',near),('source-far-ownership.png',far),('far-ownership.png',far),('original-body.png',body),('full-original-hair.png',hair)]:im.save(D/name)
def part(mask):
 out=Image.new('RGBA',src.size);out.paste(src,(0,0),mask);return out
np=part(near);fp=part(far);plate=part(own);np.save(D/'hat-near.png');fp.save(D/'hat-far.png');plate.save(D/'hat-complete-plate.png');comp,_=std.compose(body,np,fp);both,_=std.compose(body,np,fp,hair);comp.save(D/'composite.png');both.save(D/'hair-hat-composite.png')
(D/'source-contours.json').write_text(json.dumps({'pose_id':'idle_west_0','source_crop_px':r['source_box_px'],'source_crop_canvas_px':list(src.size),'near_black_lip_inclusive_y_by_x':seam,'far_rear_geometry_polygon_px':farpoly,'source_ownership':rows(own),'near_ownership':rows(near),'far_ownership':rows(far),'exclusion_basis':'Source forehead/skin diagonal band and generated vertical face line below true black hat lip are not hat. Rear inner face contact is excluded; only actual hat underside geometry belongs far.'},indent=2)+'\n')
board=Image.new('RGB',(1320,880),(225,231,235));dr=ImageDraw.Draw(board)
for j,(im,label) in enumerate([(src,'actual wearing source'),(plate,'true hat plate'),(comp,'original body + hat'),(both,'original body + full hair + hat')]):
 bg=Image.new('RGBA',im.size,(225,231,235,255));bg.alpha_composite(im);crop=bg.crop((50,65,455,385)).resize((660,520),Image.Resampling.NEAREST);x=(j%2)*660;y=(j//2)*440;board.paste(crop.convert('RGB'),(x,y+20));dr.text((x+5,y+3),label,fill='black')
board.save(D/'source-plate-body-hair-review.png')
print('idle source/near/far/body/full-hair candidate extracted; no runtime permission implied')
