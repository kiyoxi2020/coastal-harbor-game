from pathlib import Path
from PIL import Image
import json
ROOT=Path(__file__).resolve().parent
SOURCE=ROOT.parent/'visual-polish-v6'
OUT=ROOT.parents[2]/'godot2d/assets/flowers-v7'
a=Image.open(SOURCE/'atlas-original.png').convert('RGBA')
meta=json.loads((SOURCE/'metadata.json').read_text())
result={'source':'../visual-polish-v6/atlas-original.png','method':'crop original GPT pixels; nearest normalization, never upscale v6 16px output','variants':{}}
for width in (32,48):
    target=(width,width*14//16)
    entries={}
    for name in ['flowers_white','flowers_yellow','flowers_pink','flower_edge']:
        prior=meta['sprites'][name]
        crop=a.crop(prior['cell']).crop(prior['trim'])
        pad=width//16
        ratio=min((target[0]-pad*2)/crop.width,(target[1]-pad*2)/crop.height)
        size=(round(crop.width*ratio),round(crop.height*ratio))
        crop=crop.resize(size,Image.Resampling.NEAREST)
        image=Image.new('RGBA',target)
        at=((target[0]-size[0])//2,target[1]-pad-size[1])
        image.paste(crop,at)
        dest=OUT/str(width);dest.mkdir(parents=True,exist_ok=True)
        image.save(dest/(name+'.png'))
        entries[name]={'source_cell':prior['cell'],'trim':prior['trim'],'size':target,'offset':at,'scale':16/width,'sprite_offset':[0,-target[1]/2],'world_size':[16,14]}
    result['variants'][str(width)]=entries
(ROOT/'metadata.json').write_text(json.dumps(result,indent=2)+'\n')
