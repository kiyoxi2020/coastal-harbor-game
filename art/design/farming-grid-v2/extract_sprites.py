from pathlib import Path
from PIL import Image
import json
# Deterministic extraction only: all artwork comes from the preserved GPT atlas.
art=Path(__file__).resolve().parent
project=art.parents[2]
src=art/'production-atlas-v1.png'
out=project/'godot2d/assets/farming-grid-v2'
out.mkdir(parents=True,exist_ok=True)
im=Image.open(src).convert('RGBA');w,h=im.size
names=['soil_dry','soil_wet','seed','sprout','lettuce_young','lettuce_mature','tomato_young','tomato_mature','flowers_white','flowers_yellow','flowers_pink','grass','pebbles','moss_rock','stone_chips','flower_edge']
meta={'source':'art/design/farming-grid-v2/production-atlas-v1.png','source_size':[w,h],'tool':'built-in GPT imagegen','processing':'Fixed 4x4 extraction, alpha bounding-box trim, nearest resize only. No hand-drawn replacements.','sprites':{}}
for i,name in enumerate(names):
 x,y=i%4,i//4; box=(round(x*w/4),round(y*h/4),round((x+1)*w/4),round((y+1)*h/4));tile=im.crop(box)
 mask=tile.getchannel('A').point(lambda a:255 if a>100 else 0);bbox=mask.getbbox();tile=tile.crop(bbox)
 size=(16,16) if i<2 else ((6,5) if i==2 else ((8,8) if i==3 else ((14,14) if i in [4,5] else ((14,24) if i in [6,7] else (16,14)))))
 tile=tile.resize(size,Image.Resampling.NEAREST);tile.save(out/(name+'.png'))
 meta['sprites'][name]={'source_cell':list(box),'trim':list(bbox),'size':list(size),'root_anchor':[size[0]/2,size[1]],'collision':None}
(out/'metadata.json').write_text(json.dumps(meta,indent=2))
print(im.size, 'saved',len(names),'sprites')
