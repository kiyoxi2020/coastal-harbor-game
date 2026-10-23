"""Crop GPT's four props; preserve source resolution and alpha; scene scaling sets world size."""
from pathlib import Path
from PIL import Image
import json
root=Path(__file__).resolve().parent
out=root.parents[2]/'godot2d/assets/restaurant-v1'
out.mkdir(parents=True,exist_ok=True)
im=Image.open(root/'props-original.png').convert('RGBA')
w,h=im.size
meta={'source':'props-original.png','size':im.size,'filter':'nearest','props':{}}
for name,box,target in [('closed',(70,90,590,550),(36,32)),('open',(665,90,1190,550),(36,32)),('menu',(100,615,600,1190),(20,26)),('smoke',(780,650,1120,1220),(18,30))]:
 tile=im.crop(box);bbox=tile.getchannel('A').point(lambda a:255 if a>32 else 0).getbbox();tile=tile.crop(bbox)
 tile.save(out/f'{name}.png')
 meta['props'][name]={'source_box':box,'alpha_bbox':bbox,'output_size':tile.size,'logical_max_size':target,'scale':min(target[0]/tile.width,target[1]/tile.height),'anchor':'center; scene offsets are authoritative'}
(root/'slice-metadata.json').write_text(json.dumps(meta,indent=2))
