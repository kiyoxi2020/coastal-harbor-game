"""Crop GPT originals into UI textures; no repainting or replacement artwork."""
from pathlib import Path
from PIL import Image
import json
ROOT=Path(__file__).resolve().parent
OUT=ROOT.parents[2]/'godot2d/assets/ui/trade-v5'
OUT.mkdir(parents=True,exist_ok=True)
regions={
    'slot':(96,74,468,448),
    'selected':(578,74,960,448),
    'hover':(1068,74,1442,448),
    'tab':(66,544,506,690),
    'active':(550,542,986,692),
    'confirm':(1030,542,1472,694),
    'square':(174,770,358,940),
    'input':(530,784,1008,934),
    'coin':(1180,782,1330,934),
}
source=Image.open(ROOT/'controls-original.png')
for name,box in regions.items():
    source.crop(box).save(OUT/(name+'.png'))
background=Image.open(ROOT/'background-original.png')
background.save(OUT/'background.png')
metadata={'generator':'built-in GPT imagegen','processing':'RGBA crop only; original pixels preserved, no redraw, no resize',
          'background_frame_rect':[112,48,1306,912],
          'controls':{key:{'source':'controls-original.png','rect_xyxy':list(box)} for key,box in regions.items()},
          'filter':'nearest','design':'v4 layout, texture replacement v5'}
(ROOT/'slices.json').write_text(json.dumps(metadata,indent=2)+'\n')
