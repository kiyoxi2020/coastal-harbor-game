"""Rebuild source-owned hat-compressed hair from reviewed frozen row contours.
The production rebuild reads frozen source-contours.json and never classifies colors.
Initial color-assisted anatomical drafting provenance is retained separately. All RGB and selected alpha are source.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
import json,hashlib,sys,math
P=Path(__file__).resolve().parent;V=P.parent;H=V.parent.parent;SRC=V/'under-hat-hair-sources/source-v1-normalized.png'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def savej(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
a=Image.open(SRC).convert('RGBA')
for i in range(4):
 pose=f'run_east_{i}';D=P/pose;D.mkdir(exist_ok=True)
 cell=a.crop((i%2*512,i//2*512,(i%2+1)*512,(i//2+1)*512));full=Image.new('RGBA',(512,768));full.paste(cell,(0,0));full.save(D/'source-full-frame.png')
 data=json.loads((D/'source-contours.json').read_text());mask=Image.new('L',full.size);d=ImageDraw.Draw(mask)
 for row in data['rows']:
  for x0,x1 in row['inclusive_x_runs']:d.line((x0,row['y'],x1,row['y']),fill=255)
 mask.save(D/'source-ownership.png');mask.save(D/'registered-ownership.png')
 plate=Image.new('RGBA',full.size);plate.paste(full,(0,0),mask);plate.save(D/'hair-registered.png')
 # Registration is zero, source and target already share pose-frame coordinates.
 body=Image.open(H/f'run-east/references/{pose}-bare.png').convert('RGBA')
 hat_dir=V/('motion-extraction' if i<2 else 'motion-extraction-v2')/pose
 far=Image.open(hat_dir/'hat-far.png').convert('RGBA');near_hat=Image.open(hat_dir/'hat-near.png').convert('RGBA')
 comp=far.copy();comp.alpha_composite(body);comp.alpha_composite(plate);comp.alpha_composite(near_hat)
 # Preserve original transparent RGB as well as visible RGBA outside all owned surfaces.
 cp=comp.load();bp=body.load();fp=far.load();np=near_hat.load();mp=mask.load()
 for yy in range(768):
  for xx in range(512):
   if not(mp[xx,yy] or fp[xx,yy][3] or np[xx,yy][3]):cp[xx,yy]=bp[xx,yy]
 comp.save(D/'composite.png')
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
