"""Rectangle-slice GPT art; keep source pixels and record all 9-slice margins."""
from pathlib import Path
from PIL import Image
import json
HERE=Path(__file__).resolve().parent
OUT=HERE.parents[2]/'godot2d/assets/ui/kitchen-v2'
OUT.mkdir(parents=True,exist_ok=True)
metadata={}
# Actual generated dimensions differ from prompt. Rectangles use inspected source pixels.
rects={'background':('background-original.png',(49,20,1626,911)),
 'card':('controls-original.png',(37,48,403,405)),
 'card_selected':('controls-original.png',(444,48,814,406)),
 'card_hover':('controls-original.png',(854,48,1221,406)),
 'utility':('controls-original.png',(34,546,405,680)),
 'active':('controls-original.png',(444,546,812,680)),
 'disabled':('controls-original.png',(856,546,1220,680)),
 'input':('controls-original.png',(34,932,404,1062)),
 'scroll_track':('controls-original.png',(601,824,653,935)),
 'scroll_thumb':('controls-original.png',(599,941,656,1052)),
 'ingredient':('controls-original.png',(855,824,1220,1172)),
 'pot':('expandable-kitchen-concept.png',(122,64,197,126)),
 'empty':('controls-original.png',(0,0,1,1))}
for name,(source,rect) in rects.items():
 im=Image.open(HERE/source).convert('RGBA').crop(rect)
 if name=='pot':
  # Alpha-cut the original GPT pot; preserve RGB, discard only connected paper
  # and the unrelated tiny corner fragment outside the pot silhouette.
  from collections import deque
  pixels=im.load();w,h=im.size;queue=deque();seen=set()
  for x in range(w):queue.extend([(x,0),(x,h-1)])
  for y in range(h):queue.extend([(0,y),(w-1,y)])
  while queue:
   x,y=queue.popleft()
   if (x,y) in seen or x<0 or x>=w or y<0 or y>=h:continue
   seen.add((x,y));rr,gg,bb,aa=pixels[x,y]
   if not (rr>165 and gg>160 and bb>125 and max(rr,gg,bb)-min(rr,gg,bb)<65):continue
   pixels[x,y]=(rr,gg,bb,0)
   queue.extend([(x-1,y),(x+1,y),(x,y-1),(x,y+1)])
  unvisited={(x,y) for y in range(h) for x in range(w) if pixels[x,y][3]>0}
  components=[]
  while unvisited:
   start=unvisited.pop();group={start};queue=deque([start])
   while queue:
    x,y=queue.popleft()
    for point in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
     if point in unvisited:unvisited.remove(point);group.add(point);queue.append(point)
   components.append(group)
  keep=max(components,key=len)
  for y in range(h):
   for x in range(w):
    if (x,y) not in keep:
     rr,gg,bb,aa=pixels[x,y];pixels[x,y]=(rr,gg,bb,0)
 im.save(OUT/(name+'.png'))
 # Cards preserve thin square corners. Button borders stay smaller than half height.
 margins=[12,12,12,12] if name.startswith('card') or name=='ingredient' else [12,10,12,10]
 if name in ['background','pot','empty']:margins=[0,0,0,0]
 metadata[name]={'source':source,'rect':rect,'size':im.size,'texture_margins':margins,'resampled':False}
(HERE/'slices.json').write_text(json.dumps(metadata,indent=2))
# Scene-owned reusable texture styles. Texture pixels remain at source resolution.
for name,entry in metadata.items():
 if name in ['background','pot','empty']:continue
 l,t,rr,b=entry['texture_margins']
 (OUT/(name+'.tres')).write_text(f'''[gd_resource type="StyleBoxTexture" load_steps=2 format=3]
[ext_resource type="Texture2D" path="res://assets/ui/kitchen-v2/{name}.png" id="texture"]
[resource]
texture = ExtResource("texture")
texture_margin_left = {l}.0
texture_margin_top = {t}.0
texture_margin_right = {rr}.0
texture_margin_bottom = {b}.0
content_margin_left = 10.0
content_margin_top = 4.0
content_margin_right = 10.0
content_margin_bottom = 4.0
''')
Image.open(HERE/'controls-original.png').crop((0,0,1,1)).save(OUT/'empty.png')
p=OUT/'input.tres'
p.write_text(p.read_text().replace('content_margin_left = 10.0','content_margin_left = 18.0').replace('content_margin_right = 10.0','content_margin_right = 18.0'))
print('assets',len(metadata),OUT)

p=OUT/'search.tres'
s=(OUT/'input.tres').read_text().replace('content_margin_left = 18.0','content_margin_left = 28.0').replace('content_margin_right = 18.0','content_margin_right = 20.0').replace('content_margin_top = 4.0','content_margin_top = 8.0').replace('content_margin_bottom = 4.0','content_margin_bottom = 8.0')
p.write_text(s)
