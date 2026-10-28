"""Frozen source-owned idle under-hat visible hair. No image generation or hair trim.
--draft locates candidates in a reviewed anatomical envelope; default reconstructs
only frozen source pixel runs. Crop return [40,50] is not part registration.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
import json,hashlib,sys,shutil,importlib.util
if '--draft' not in sys.argv or '--allow-replace-frozen' not in sys.argv: raise SystemExit('Draft provenance only. Frozen reconstruction uses extract_idle.py; replacing frozen contours requires an explicit new audit.')
P=Path(__file__).resolve().parent;V=P.parent;SRC=V/'under-hat-hair-sources';HAT=V/'extraction/idle_west_0';D=P/'idle_west_0';D.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def js(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
source=Image.open(SRC/'idle_west_0-v1-full-frame.png').convert('RGBA');shutil.copyfile(SRC/'idle_west_0-v1-full-frame.png',D/'source-full-frame.png');sp=source.load()
polygon=[(136,204),(375,279),(380,299),(369,317),(362,330),(351,341),(344,343),(343,335),(334,345),(325,351),(318,352),(316,346),(307,356),(300,359),(291,357),(291,344),(305,337),(314,329),(319,318),(319,305),(314,294),(305,286),(294,284),(282,289),(274,299),(270,310),(263,320),(258,313),(257,300),(251,302),(250,292),(254,282),(252,270),(247,260),(238,252),(229,245),(224,236),(216,231),(210,229),(203,227),(198,228),(196,243),(200,250),(196,256),(189,251),(181,244),(177,231),(174,231),(172,243),(166,249),(165,261),(160,268),(156,268),(151,259),(146,247),(141,242),(140,233),(137,227),(131,235),(125,232),(127,222),(132,212)]
if '--draft' in sys.argv:
 semantic=Image.new('L',source.size);ImageDraw.Draw(semantic).polygon(polygon,fill=255)
 ImageDraw.Draw(semantic).polygon([(136,201),(375,276),(375,279),(136,204)],fill=255)
 sem=semantic.load();brown=Image.new('L',source.size);bp=brown.load()
 for y in range(198,362):
  for x in range(120,383):
   r,g,b,a=sp[x,y]
   if sem[x,y] and a and 24<r<180 and 13<g<130 and 1.48*g<r<2.5*g and .42*g<b<.99*g:bp[x,y]=255
 near=brown.filter(ImageFilter.MaxFilter(7)).load();rootnear=brown.filter(ImageFilter.MaxFilter(11)).load();tight=brown.filter(ImageFilter.MaxFilter(3)).load();mask=Image.new('L',source.size);mp=mask.load()
 for y in range(198,362):
  for x in range(120,383):
   r,g,b,a=sp[x,y];ear=260<=x<=326 and 280<=y<=346
   root_outline=130<=x<=151 and 205<=y<=235 and rootnear[x,y]
   if sem[x,y] and (bp[x,y] or (max(r,g,b)<65 and (near[x,y] or root_outline) and not ear and (x>167 or root_outline or tight[x,y] and y<=268))):mp[x,y]=255
 # Source neck/face shadow below the actual nape-hair return is body, not hair.
 nape=[(330,317),(336,313),(340,308),(344,304),(347,302),(350,310)]
 for y in range(330,362):
  limit=400 if y>350 else 317
  for aa,bb in zip(nape,nape[1:]):
   if aa[0]<=y<=bb[0]:limit=aa[1]+(y-aa[0])*(bb[1]-aa[1])/(bb[0]-aa[0]);break
  for x in range(120,383):
   if x<limit:mp[x,y]=0
 # A source black pixel on the exact existing near-hat support is not claimed as hair.
 # This source is only a visible hat-compatible fringe/side/back view.
 formalnear=Image.open(HAT/'hat-near.png').convert('RGBA').load()
 for y in range(198,362):
  for x in range(120,383):
   if formalnear[x,y][3]>=200 and max(sp[x,y][:3])<65:mp[x,y]=0
 # The generated eyebrow is not hair, including its blended ends.
 for y in range(233,254):
  for x in range(179,226):
   r,g,b,a=sp[x,y]
   if g>55 and r<1.65*g:mp[x,y]=0
 # Remove disconnected brow/face residue, not isolated actual hair tips.
 selected={(x,y) for y in range(198,362) for x in range(120,383) if mp[x,y]};seen=set()
 for seed in list(selected):
  if seed in seen:continue
  seen.add(seed);q=[seed];c=[]
  while q:
   xx,yy=q.pop();c.append((xx,yy))
   for dx,dy in [(0,1),(0,-1),(1,0),(-1,0)]:
    z=(xx+dx,yy+dy)
    if z in selected and z not in seen:seen.add(z);q.append(z)
  if len(c)<35:
   for xx,yy in c:mp[xx,yy]=0
 rows=[]
 for y in range(source.height):
  runs=[];x=0
  while x<source.width:
   if mp[x,y]:
    lo=x
    while x<source.width and mp[x,y]:x+=1
    runs.append([lo,x-1])
   else:x+=1
  if runs:rows.append({'y':y,'inclusive_x_runs':runs})
 js(D/'source-contours.json',{'pose_id':'idle_west_0','space':'512x768 source full-frame with420-square returned to[40,50]','source_full_frame_sha256':sha(D/'source-full-frame.png'),'draft_anatomical_envelope_px':polygon,'scope':'only real compact fringe/side/back/nape visible in this exact hat','excluded':['hat and its black lip','generated skin/ear arc/brow/eye/face contour/clothes/background'],'rows':rows,'authority':'Frozen reviewed pixel runs; production never classifies colors or uses a max-y crop.'})
c=json.loads((D/'source-contours.json').read_text());mask=Image.new('L',source.size);md=ImageDraw.Draw(mask)
for row in c['rows']:
 for lo,hi in row['inclusive_x_runs']:md.line((lo,row['y'],hi,row['y']),fill=255)
mask.save(D/'source-ownership.png');mask.save(D/'registered-ownership.png');plate=Image.new('RGBA',source.size);plate.paste(source,(0,0),mask);plate.save(D/'hair-registered.png')
spec=importlib.util.spec_from_file_location('same_v5_composer',V.parent/'run-east-hat-approved-v5/build_approved.py');std=importlib.util.module_from_spec(spec);spec.loader.exec_module(std)
body=Image.open(HAT/'original-body.png').convert('RGBA');nearhat=Image.open(HAT/'hat-near.png').convert('RGBA');farhat=Image.open(HAT/'hat-far.png').convert('RGBA');comp,_=std.compose(body,nearhat,farhat,plate);comp.save(D/'hair-hat-composite.png')
board=Image.new('RGB',(1740,390),(220,228,234));dr=ImageDraw.Draw(board)
for j,(im,title) in enumerate([(source,'generated source'),(plate,'source-owned hair only'),(comp,'original body + formal hat + hair')]):
 bg=Image.new('RGBA',im.size,(220,228,234,255));bg.alpha_composite(im);crop=bg.crop((115,185,405,370)).resize((580,370),Image.Resampling.NEAREST);board.paste(crop.convert('RGB'),(j*580,20));dr.text((j*580+3,2),title,fill='black')
board.save(D/'source-mask-composite-head-2x.png')
print('idle frozen hair candidate built, zero part registration')
