"""Register whole GPT-redrawn figures. One common uniform scale; no limb warping."""
from pathlib import Path
from PIL import Image
import json
ROOT=Path(__file__).resolve().parents[3];ART=Path(__file__).resolve().parent;OUT=ROOT/'godot2d/assets/npc-modular-v2'
OUT.mkdir(parents=True,exist_ok=True)
DIRS=['south','west','east','north'];SIZE=(768,768);ANCHOR=(384,672)
SOURCE={'resident_a':'resident-a-master-edit.png','resident_b':'resident-b-master-edit.png'}
SCALE=1.0 # Source already has the original master's 2x detail density; never stretch limbs.
meta={'master':'player-proportion-master.png','canvas':SIZE,'anchor':ANCHOR,'world_scale':0.075,'uniform_scale':SCALE,'registration':'whole-figure translation only; no per-part or nonuniform transform','frames':{}}
for profile,filename in SOURCE.items():
 im=Image.open(ART/filename).convert('RGBA');w,h=im.size;meta['frames'][profile]={}
 for index,d in enumerate(DIRS):
  box=(index*w//4,0,(index+1)*w//4,h);tile=im.crop(box)
  b=tile.getchannel('A').point(lambda a:255 if a>64 else 0).getbbox()
  # Use the actual sole span, so hat/hair mass never biases the root.
  foot=tile.crop((0,b[3]-30,tile.width,b[3])).getchannel('A').point(lambda a:255 if a>64 else 0).getbbox()
  foot_x=(foot[0]+foot[2])/2
  scaled=tile.resize((round(tile.width*SCALE),round(tile.height*SCALE)),Image.Resampling.NEAREST)
  pos=(round(ANCHOR[0]-foot_x*SCALE),round(ANCHOR[1]-b[3]*SCALE))
  frame=Image.new('RGBA',SIZE);frame.alpha_composite(scaled,pos)
  frame.save(OUT/(profile+'_'+d+'.png'))
  meta['frames'][profile][d]={'source':filename,'source_box':box,'alpha_bbox':b,'source_sole_x':foot_x,'position':pos,'scale':SCALE,'output_bbox':frame.getchannel('A').point(lambda a:255 if a>64 else 0).getbbox()}
(ART/'metadata.json').write_text(json.dumps(meta,indent=2))
review=Image.new('RGBA',(768*3,768*4))
for row,d in enumerate(DIRS):
 for col,profile in enumerate(['player','resident_a','resident_b']):
  if profile=='player':
   frame=Image.open(ROOT/'godot2d/assets/player-unified-v4'/('walk_'+d+'_0.png')).convert('RGBA').resize(SIZE,Image.Resampling.NEAREST)
  else:frame=Image.open(OUT/(profile+'_'+d+'.png'))
  review.alpha_composite(frame,(col*768,row*768))
review.save(ART/'standing-review-full.png')
# Explicit review-only 50% image; game assets remain high resolution.
review.resize((1152,1536),Image.Resampling.NEAREST).save(ART/'standing-review.png')
print('Registered 8 frames; one uniform scale for all directions and outfits.')
