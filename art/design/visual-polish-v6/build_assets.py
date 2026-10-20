from pathlib import Path
from PIL import Image
import json
ROOT=Path(__file__).resolve().parent
OUT=ROOT.parents[2]/'godot2d/assets/visual-polish-v6'
OUT.mkdir(parents=True,exist_ok=True)
a=Image.open(ROOT/'atlas-original.png').convert('RGBA')
names=['clam','snail','kelp','grass','flowers_white','flowers_yellow','flowers_pink','flower_edge']
meta={'source_size':list(a.size),'processing':'crop alpha bounds then nearest fit; no repainting','sprites':{}}
for i,name in enumerate(names):
    c,r=i%4,i//4
    cell=(round(c*a.width/4),(0 if r==0 else round(a.height*.62)),round((c+1)*a.width/4),(round(a.height*.58) if r==0 else a.height))
    tile=a.crop(cell)
    bounds=tile.getchannel('A').point(lambda v:255 if v>=64 else 0).getbbox()
    crop=tile.crop(bounds)
    size=(64,64) if i<3 else (16,14)
    pad=3 if i<3 else 1
    ratio=min((size[0]-pad*2)/crop.width,(size[1]-pad*2)/crop.height)
    target=(max(1,round(crop.width*ratio)),max(1,round(crop.height*ratio)))
    crop=crop.resize(target,Image.Resampling.NEAREST)
    result=Image.new('RGBA',size)
    at=((size[0]-target[0])//2,size[1]-pad-target[1])
    result.paste(crop,at)
    result.save(OUT/(name+'.png'))
    meta['sprites'][name]={'cell':cell,'trim':bounds,'size':size,'fit_size':target,'offset':at,'world_size':[12,11] if i<3 else [16,14],'world_anchor':[6,9] if i<3 else [8,14]}
(ROOT/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
