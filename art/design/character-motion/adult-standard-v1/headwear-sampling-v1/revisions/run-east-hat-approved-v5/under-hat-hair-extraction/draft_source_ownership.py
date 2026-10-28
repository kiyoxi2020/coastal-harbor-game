"""Rebuild source-owned hat-compressed hair from reviewed frozen row contours.
Run --draft only to make initial color-assisted anatomical candidates; production reads
source-contours.json and never classifies colors. All RGB and selected alpha are source.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
import json,hashlib,sys,math
if '--draft' not in sys.argv: raise SystemExit('Draft provenance only: use extract_hair.py to rebuild frozen official contours.')
P=Path(__file__).resolve().parent;V=P.parent;H=V.parent.parent;SRC=V/'under-hat-hair-sources/source-v1-normalized.png'
P=P/'draft-regeneration';P.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def savej(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
polygons=[
[(185,306),(413,221),(421,244),(417,266),(401,284),(392,286),(392,265),(386,251),(380,266),(370,271),(365,248),(355,247),(341,251),(331,259),(327,269),(328,280),(333,292),(336,296),(329,300),(318,296),(316,294),(316,331),(309,331),(297,318),(295,310),(297,332),(289,330),(281,309),(281,350),(280,366),(266,366),(250,360),(239,356),(235,361),(226,357),(213,345),(208,349),(198,342),(189,333),(184,319)],
[(191,298),(423,216),(429,244),(425,263),(410,278),(400,278),(401,255),(393,242),(385,260),(377,267),(369,266),(367,242),(354,241),(341,246),(335,257),(329,267),(330,278),(337,287),(344,292),(339,296),(324,294),(324,328),(316,327),(303,315),(299,305),(301,325),(294,324),(286,306),(286,346),(284,363),(270,362),(254,355),(242,350),(236,354),(229,348),(217,338),(210,341),(202,333),(193,323),(189,311)],
[(205,302),(434,215),(441,245),(436,268),(421,286),(413,281),(413,255),(405,244),(397,261),(389,266),(381,250),(376,239),(366,244),(357,250),(351,260),(346,275),(349,286),(355,297),(356,302),(345,303),(340,296),(339,332),(329,331),(316,318),(309,307),(311,328),(302,326),(294,307),(299,350),(300,366),(285,365),(272,360),(261,357),(255,362),(245,354),(235,348),(228,349),(219,342),(211,331),(205,318)],
[(209,303),(446,216),(448,251),(441,269),(426,287),(418,282),(419,258),(409,243),(402,263),(395,270),(389,267),(386,249),(378,241),(369,246),(357,252),(350,263),(347,275),(349,286),(357,296),(361,301),(353,303),(343,300),(340,333),(331,331),(316,314),(312,309),(314,330),(304,328),(297,310),(299,350),(300,367),(285,365),(272,360),(262,356),(255,363),(245,355),(234,350),(228,353),(219,346),(212,333),(208,319)]
]
# Exclude the entire GENERATED ear arc and its skin, not just the skin color.
# Original-body ear is retained independently below the extracted hair.
ears=[
[(231,291),(251,286),(271,287),(280,291),(288,300),(292,308),(292,326),(285,328),(280,314),(273,302),(266,299),(257,299),(249,305),(246,314),(247,325),(254,332),(265,338),(278,338),(284,341),(281,350),(268,352),(249,345),(236,331),(230,315)],
[(245,289),(262,284),(280,285),(288,289),(297,297),(303,306),(303,322),(297,325),(291,311),(282,301),(276,296),(266,296),(258,301),(255,311),(256,322),(263,330),(276,336),(287,336),(292,339),(288,346),(276,349),(260,343),(248,331),(243,315)],
[(259,294),(276,288),(294,288),(304,292),(314,302),(319,312),(319,327),(312,330),(306,315),(298,303),(290,301),(280,303),(272,309),(270,321),(273,333),(281,340),(296,346),(309,345),(315,348),(309,356),(295,358),(278,351),(265,338),(258,322)],
[(262,295),(278,289),(296,289),(306,293),(316,303),(322,314),(322,329),(315,332),(309,317),(301,305),(292,303),(282,305),(274,312),(272,323),(276,335),(285,342),(298,347),(311,346),(317,349),(311,357),(297,359),(280,352),(267,339),(260,323)]
]
a=Image.open(SRC).convert('RGBA')
for i in range(4):
 pose=f'run_east_{i}';D=P/pose;D.mkdir(exist_ok=True)
 cell=a.crop((i%2*512,i//2*512,(i%2+1)*512,(i//2+1)*512));full=Image.new('RGBA',(512,768));full.paste(cell,(0,0));full.save(D/'source-full-frame.png')
 if '--draft' in sys.argv:
  semantic=Image.new('L',full.size);dr=ImageDraw.Draw(semantic);dr.polygon(polygons[i],fill=255)
  # Root envelope includes actual brown roots; hat-black candidates are excluded separately.
  dr.polygon([(polygons[i][0][0],polygons[i][0][1]-7),(polygons[i][1][0],polygons[i][1][1]-7),polygons[i][1],polygons[i][0]],fill=255)
  brown=Image.new('L',full.size);bp=brown.load();sp=semantic.load();fp=full.load()
  for y in range(210,370):
   for x in range(175,453):
    r,g,b,_=fp[x,y]
    if sp[x,y] and 30<r<170 and 19<g<120 and 1.23*g<r<2.25*g and g*.4<b<g*.97:bp[x,y]=255
  near=brown.filter(ImageFilter.MaxFilter(7));np=near.load();tight=brown.filter(ImageFilter.MaxFilter(3)).load();mask=Image.new('L',full.size);mp=mask.load()
  for y in range(210,370):
   for x in range(175,453):
    r,g,b,_=fp[x,y]
    ear_bounds=[(232,287,295,351),(246,285,306,348),(260,289,323,357),(262,290,325,358)][i]
    ex0,ey0,ex1,ey1=ear_bounds
    in_ear=ex0<=x<=ex1 and ey0<=y<=ey1
    root_y=polygons[i][0][1]+(x-polygons[i][0][0])*(polygons[i][1][1]-polygons[i][0][1])/(polygons[i][1][0]-polygons[i][0][0])
    front_x=[391,399,415,418][i]
    allowed_dark=np[x,y] if x<front_x else tight[x,y]
    if sp[x,y] and (bp[x,y] or (allowed_dark and max(r,g,b)<65 and not in_ear and y>root_y+2)):mp[x,y]=255
  # Anatomically disconnected tiny fragments are brow/ear residue, not separate hair tufts.
  seen=set()
  for y in range(210,370):
   for x in range(175,453):
    if not mp[x,y] or (x,y) in seen:continue
    q=[(x,y)];seen.add((x,y));component=[]
    while q:
     xx,yy=q.pop();component.append((xx,yy))
     for dx,dy in [(0,1),(0,-1),(1,0),(-1,0)]:
      z=(xx+dx,yy+dy)
      if 0<=z[0]<512 and 0<=z[1]<768 and z not in seen and mp[z[0],z[1]]:seen.add(z);q.append(z)
    if len(component)<100:
     for xx,yy in component:mp[xx,yy]=0
  brow_boxes=[(329,248,373,262),(341,243,384,257),(359,246,406,261),(361,246,409,261)]
  bx0,by0,bx1,by1=brow_boxes[i]
  for y in range(by0,by1):
   for x in range(bx0,bx1):
    r,g,b,_=fp[x,y]
    if 65<g and r<1.6*g:mp[x,y]=0
  # Fill fully enclosed mask holes after visual identification as interior hair.
  outside=set();queue=[(0,0)];outside.add((0,0))
  while queue:
   xx,yy=queue.pop()
   for dx,dy in [(0,1),(0,-1),(1,0),(-1,0)]:
    z=(xx+dx,yy+dy)
    if 0<=z[0]<512 and 0<=z[1]<768 and z not in outside and not mp[z[0],z[1]]:outside.add(z);queue.append(z)
  for y in range(210,370):
   for x in range(175,453):
    if (x,y) not in outside:mp[x,y]=255
  # Freeze exact reviewed pixel runs; no color classification is needed thereafter.
  rows=[]
  for y in range(768):
   runs=[];x=0
   while x<512:
    if mp[x,y]:
     x0=x
     while x<512 and mp[x,y]:x+=1
     runs.append([x0,x-1])
    else:x+=1
   if runs:rows.append({'y':y,'inclusive_x_runs':runs})
  savej(D/'source-contours.json',{'pose_id':pose,'coordinate_space':'512x768 source full frame, top-left origin','purpose':'source_ownership only; not body coverage or occlusion','source_sha256':sha(SRC),'semantic_regions':['compact fringe below front brim','temple/side hair outside original ear','short back/nape below rear brim'],'excluded':['hat including black brim/band','generated body/skin/ear arc/brow/eye/face/clothes','background'],'draft_anatomical_polygon_px':polygons[i],'generated_ear_exclusion_polygon_px':ears[i],'rows':rows})
 data=json.loads((D/'source-contours.json').read_text());mask=Image.new('L',full.size);d=ImageDraw.Draw(mask)
 for row in data['rows']:
  for x0,x1 in row['inclusive_x_runs']:d.line((x0,row['y'],x1,row['y']),fill=255)
 mask.save(D/'source-ownership.png');mask.save(D/'registered-ownership.png')
 plate=Image.new('RGBA',full.size);plate.paste(full,(0,0),mask);plate.save(D/'hair-registered.png')
 # Registration is zero, source and target already share pose-frame coordinates.
 body=Image.open(H/f'run-east/references/{pose}-bare.png').convert('RGBA')
 hat_dir=V/('motion-extraction' if i<2 else 'motion-extraction-v2')/pose
 far=Image.open(hat_dir/'hat-far.png').convert('RGBA');near_hat=Image.open(hat_dir/'hat-near.png').convert('RGBA')
 comp=far.copy();comp.alpha_composite(body);comp.alpha_composite(plate);comp.alpha_composite(near_hat);comp.save(D/'composite.png')
 board=Image.new('RGB',(1024,768))
 for col,bg in enumerate([(230,235,239,255),(28,34,44,255)]):
  back=Image.new('RGBA',full.size,bg);back.alpha_composite(comp);board.paste(back.convert('RGB'),(col*512,0))
 board.save(D/'composite-light-dark.png')
 # Side-by-side exact source, ownership overlay, and original-body composite at 2x.
 head=Image.new('RGB',(1536,340));
 for col,im in enumerate([full,plate,comp]):
  bg=Image.new('RGBA',full.size,(205,214,222,255));bg.alpha_composite(im)
  head.paste(bg.crop((180,210,436,380)).resize((512,340),Image.Resampling.NEAREST).convert('RGB'),(col*512,0))
 head.save(D/'source-mask-composite-head-2x.png')
print('Built four source-owned full-frame hair plates; frozen contours read for reconstruction.')
