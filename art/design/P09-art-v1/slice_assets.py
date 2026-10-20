"""Slice GPT atlas artwork without painting or resampling it."""
from pathlib import Path
import json
from PIL import Image
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
OUT=ROOT/'godot2d/assets/ui/crafting-v1'
OUT.mkdir(parents=True,exist_ok=True)
metadata={'generator':'built-in GPT image_gen','filter':'nearest','items':{},'ui':{}}
im=Image.open(HERE/'items-original.png').convert('RGBA')
w,h=im.size
for name,(x,y) in {'marine_fertilizer':(0,0),'clam_salad':(1,0),'snail_stew':(0,1),'kitchen_badge':(1,1)}.items():
 rect=(x*w//2,y*h//2,(x+1)*w//2,(y+1)*h//2)
 if name=='snail_stew':rect=(0,h//2,690,h)
 if name=='kitchen_badge':rect=(690,h//2,w,h)
 tile=im.crop(rect)
 # Ignore nearly invisible alpha fringes only for the bounding-box calculation.
 bbox=tile.getchannel('A').point(lambda a:255 if a>32 else 0).getbbox()
 assert bbox
 sprite=tile.crop(bbox)
 # Center in a square transparent canvas so all consumers share its visual anchor.
 side=max(sprite.size)+32
 canvas=Image.new('RGBA',(side,side))
 canvas.paste(sprite,((side-sprite.width)//2,(side-sprite.height)//2))
 canvas.save(OUT/f'{name}.png')
 metadata['items'][name]={'source':list(rect),'trim':list(bbox),'size':list(canvas.size),'anchor':'center','world_collision':'unchanged; inventory/UI asset'}
im=Image.open(HERE/'kitchen-kit-clean-attempt.png').convert('RGBA')
rects={'background':(32,28,1508,644),'recipe_normal':(43,677,514,811),'recipe_selected':(538,676,1000,811),'confirm':(1028,676,1498,811),'utility':(42,838,515,976),'quantity':(538,838,999,976),'disabled':(1028,838,1497,976)}
for name,rect in rects.items():
 im.crop(rect).save(OUT/f'{name}.png')
 metadata['ui'][name]={'source':list(rect),'size':[rect[2]-rect[0],rect[3]-rect[1]]}
(HERE/'slices.json').write_text(json.dumps(metadata,indent=2))
print('sliced',len(metadata['items'])+len(metadata['ui']),'assets')
