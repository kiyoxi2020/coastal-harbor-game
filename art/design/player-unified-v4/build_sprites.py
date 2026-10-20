"""Extract GPT frames without redrawing them. Sources/prompts remain alongside this script.
A single scale per action/direction preserves authored pose movement. Root translations
register stationary feet; movement retains the generated bob/airborne stride.
"""
from pathlib import Path
from PIL import Image
import json, statistics, shutil
ROOT=Path(__file__).resolve().parents[3]
ART=Path(__file__).resolve().parent
OUT=ROOT/'godot2d/assets/player-unified-v4'
OUT.mkdir(parents=True,exist_ok=True)
DIRECTIONS=['south','west','east','north']
CANVAS=384; ANCHOR=(192,336)

def components(mask,w,h):
 unseen=set(mask); result=[]
 while unseen:
  start=unseen.pop(); stack=[start]; points=[start]
  while stack:
   p=stack.pop();x=p%w;y=p//w
   for q in (p-1 if x else -1,p+1 if x<w-1 else -1,p-w if y else -1,p+w if y<h-1 else -1):
    if q in unseen: unseen.remove(q);stack.append(q);points.append(q)
  result.append(points)
 return result

def bounds(points,w):
 return (min(p%w for p in points),min(p//w for p in points),max(p%w for p in points)+1,max(p//w for p in points)+1)

def red(c):
 r,g,b,a=c;return a>100 and r>110 and r>g*1.8 and r>b*1.5

def hair(c):
 r,g,b,a=c;return a>100 and 20<r<170 and r*.48<g<r*.90 and b<g*.95

def boot(c):
 r,g,b,a=c;return a>100 and r>170 and 95<g<235 and b<105 and r>g*1.07

sources=json.loads((ART/'sources.json').read_text())
raw={};metadata={'canvas':[CANVAS,CANVAS],'anchor':list(ANCHOR),'world_scale':0.15,'directions':DIRECTIONS,'frames':{},'groups':{},'tool':'built-in GPT imagegen'}
for action,source in sources.items():
 source_path=Path(source)
 if not source_path.is_absolute():source_path=ART/source_path
 preserved=ART/f'{action}-original.png'
 if source_path.resolve()!=preserved.resolve():shutil.copy2(source_path,preserved)
 im=Image.open(preserved).convert('RGBA');cw=im.width//6
 for col in range(6):
  tile=im.crop((col*cw,0,(col+1)*cw,im.height));w,h=tile.size;pixels=list(tile.get_flattened_data())
  groups=components([i for i,c in enumerate(pixels) if c[3]>100],w,h)
  bodies=[g for g in groups if sum(red(pixels[p]) for p in g)>150]
  bodies.sort(key=lambda g: statistics.mean(p//w for p in g if red(pixels[p])))
  if len(bodies)!=4:raise ValueError(f'{action} col{col}: expected four bodies, got {len(bodies)}')
  boxes=[bounds(g,w) for g in bodies];assigned=[[] for _ in range(4)]
  body_ids={id(g) for g in bodies}
  for g in groups:
   if id(g) in body_ids:continue
   box=bounds(g,w);center=((box[0]+box[2])/2,(box[1]+box[3])/2)
   distances=[max(b[0]-center[0],0,center[0]-b[2])**2+max(b[1]-center[1],0,center[1]-b[3])**2 for b in boxes]
   index=min(range(4),key=lambda i:distances[i])
   if distances[index]<45**2:assigned[index].extend(g)
  for row,body in enumerate(bodies):
   direction=DIRECTIONS[row]
   hs=components([p for p in body if hair(pixels[p])],w,h)
   head=max(hs,key=len);hb=bounds(head,w)
   # Only yellow pixels below the head can be boots, avoiding skin highlights.
   bs=[p for p in body if p//w>hb[3]+20 and boot(pixels[p])]
   if not bs:raise ValueError(f'No boots: {action} {direction} {col}')
   bb=bounds(bs,w);all_points=body+assigned[row];box=bounds(all_points,w)
   isolated=Image.new('RGBA',(w,h));ip=isolated.load()
   for p in all_points:
    r,g,b,a=pixels[p];ip[p%w,p//w]=(r,g,b,255 if a>247 else a)
   raw[action,direction,col]={'image':isolated,'body':body,'head':hb,'boots':bb,'box':box,'column':col,'source':f'art/design/player-unified-v4/{action}-original.png','source_size':list(im.size)}
for action in sources:
 for direction in DIRECTIONS:
  items=[raw[action,direction,i] for i in range(6)]
  ref=statistics.median(raw['walk',direction,i]['head'][2]-raw['walk',direction,i]['head'][0] for i in range(6))
  current=statistics.median(d['head'][2]-d['head'][0] for d in items)
  scale=ref/current # one factor for all six frames, never frame-to-frame pumping
  floor=max(d['boots'][3] for d in items)
  metadata['groups'][action+'_'+direction]={'source_head_width':current,'reference_head_width':ref,'normalization':scale,'source_floor':floor}
  for i,d in enumerate(items):
   moving=action in ['walk','run']
   anchor_x=(d['head'][0]+d['head'][2])/2 if moving else (d['boots'][0]+d['boots'][2])/2
   anchor_y=floor if moving else d['boots'][3]
   box=d['box'];part=d['image'].crop(box)
   part=part.resize((round(part.width*scale),round(part.height*scale)),Image.Resampling.NEAREST)
   point=(round(ANCHOR[0]+(box[0]-anchor_x)*scale),round(ANCHOR[1]+(box[1]-anchor_y)*scale))
   if point[0]<0 or point[1]<0 or point[0]+part.width>CANVAS or point[1]+part.height>CANVAS:raise ValueError(f'Frame clips canvas: {action} {direction} {i}, {point}, {part.size}')
   canvas=Image.new('RGBA',(CANVAS,CANVAS));canvas.alpha_composite(part,point)
   name=f'{action}_{direction}_{i}';canvas.save(OUT/f'{name}.png')
   metadata['frames'][name]={'source':d['source'],'source_column':i,'source_bounds':list(box),'head_bounds':list(d['head']),'boot_bounds':list(d['boots']),'source_anchor':[anchor_x,anchor_y],'normalization':scale,'canvas_anchor':list(ANCHOR)}
(OUT/'metadata.json').write_text(json.dumps(metadata,indent=2))
# Static Inspector-editable SpriteFrames, using original direction names for door compatibility.
res=['[gd_resource type="SpriteFrames" load_steps=121 format=3]']
for index,name in enumerate(metadata['frames']):res.append(f'[ext_resource type="Texture2D" path="res://assets/player-unified-v4/{name}.png" id="f{index}"]')
ids={name:index for index,name in enumerate(metadata['frames'])};animations=[]
for action in sources:
 for direction in DIRECTIONS:
  name=direction if action=='walk' else action+'_'+direction
  textures=', '.join('{"duration":1.0,"texture":ExtResource("f%d")}'%ids[f'{action}_{direction}_{i}'] for i in range(6))
  animations.append('{"frames":['+textures+'],"loop":'+('true' if action in ['walk','run'] else 'false')+',"name":&"'+name+'","speed":'+str(12.0 if action=='run' else 9.0 if action=='walk' else 9.0)+'}')
res+=['[resource]','animations = ['+',\n'.join(animations)+']'];(ROOT/'godot2d/resources/player_unified_frames.tres').write_text('\n\n'.join(res)+'\n')
print('Saved',len(metadata['frames']),'registered frames and',len(animations),'animations')
