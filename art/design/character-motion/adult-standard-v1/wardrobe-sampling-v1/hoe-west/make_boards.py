"""Nearest-scale diagnostic boards only; never an art pixel source."""
from PIL import Image,ImageDraw
from pathlib import Path
import json,sys
base=Path(__file__).resolve().parent.parent
for name in sys.argv[1:]:
 d=base/name;s=json.loads((d/'sample.json').read_text());fs=[s['idle']]+s['frames']
 sheet=Image.new('RGBA',(2000,1520));draw=ImageDraw.Draw(sheet)
 for bg,y0 in [((242,240,231,255),0),((42,46,50,255),760)]:
  draw.rectangle((0,y0,2000,y0+759),fill=bg)
  color='black' if y0==0 else 'white'
  for i,f in enumerate(fs):
   phase=f['phase'];new=Image.open(d/f['file']).convert('RGBA');old=Image.open(d/f'references/original-{phase}.png').convert('RGBA')
   scale=s['idle']['display_scale'] if phase=='idle' else s['display_scale']
   if phase!='idle':
    canvas=Image.new('RGBA',tuple(s['canvas_px']));canvas.paste(old,tuple(f['whole_frame_translation_px']));old=canvas
   draw.text((i*400+5,y0+5),f'{phase}: original1x | sample1x; sample2x below',fill=color)
   for j,im in enumerate([old,new]):
    sz=tuple(round(v*scale) for v in im.size);sheet.alpha_composite(im.resize(sz,Image.Resampling.NEAREST),(i*400+5+j*195,y0+30))
   sz=tuple(round(v*scale*2) for v in new.size);sheet.alpha_composite(new.resize(sz,Image.Resampling.NEAREST),(i*400+5,y0+290))
 sheet.save(d/'evidence/comparison-1x-2x.png')
 parts=Image.new('RGBA',(1750,1680),(70,74,78,255));pd=ImageDraw.Draw(parts)
 for i,f in enumerate(fs):
  phase=f['phase']
  for row,slot in enumerate(['top','pants','shoes','shared_same_pose_foreground_and_contour']):
   file=d/f'parts/{phase}/{slot}-complete-source.png' if row<3 else d/f'parts/{phase}/{slot}.png'
   im=Image.open(file).convert('RGBA');sz=tuple(round(v*(0.5 if phase=='idle' else .25)) for v in im.size);parts.alpha_composite(im.resize(sz,Image.Resampling.NEAREST),(i*350+10,row*420+25));pd.text((i*350+10,row*420+5),f'{phase}/{slot}',fill='white')
 parts.save(d/'evidence/independent-slot-sources.png')
 print(name,'boards ready')
