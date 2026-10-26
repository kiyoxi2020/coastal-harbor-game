"""Color-assisted visible footwear measurements in manually reviewed shoe ROIs.
This is diagnostic only: no formal pixel ownership, anatomy from percentages or art edits.
"""
from pathlib import Path
import json,argparse,shutil
from PIL import Image
ROOT=Path(__file__).resolve().parent
def footwear(im,roi):
 pixels=im.load();x0,y0,x1,y1=roi;points=set()
 for y in range(y0,y1):
  for x in range(x0,x1):
   r,g,b,a=pixels[x,y]
   if a>=128 and 35<r<180 and 15<g<120 and r>g*1.27 and r>b*1.45:points.add((x,y))
 components=[]
 while points:
  start=points.pop();stack=[start];part=[start]
  while stack:
   x,y=stack.pop()
   for other in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
    if other in points:points.remove(other);stack.append(other);part.append(other)
  if len(part)>100:components.append(part)
 components.sort(key=len,reverse=True)
 if len(components)<2:raise ValueError('Cannot identify two visible shoes: inspect ROI')
 boxes=[]
 alpha=im.getchannel('A').point(lambda a:255 if a>=128 else 0)
 for part in components[:2]:
  core=[min(x for x,y in part),min(y for x,y in part),max(x for x,y in part)+1,max(y for x,y in part)+1]
  # Color only locates the shoe. Measure its real opaque lower outline,
  # including the original dark border; never register to the brown fill inset.
  search=[max(0,core[0]-20),core[1]+20,min(im.width,core[2]+20),min(im.height,core[3]+24)]
  local=alpha.crop(tuple(search)).getbbox()
  if local is None:raise ValueError('shoe opaque contour missing')
  boxes.append([local[0]+search[0],local[1]+search[1],local[2]+search[0],local[3]+search[1]])
 return sorted(boxes)
def configure(combo):
 directory=ROOT/combo;spec=json.loads((directory/'manual-observations.json').read_text());direction,garment=combo.split('-');frames=[]
 for phase,duration in [('ready',200),('raise',200),('pour',350),('recovery',250)]:
  s=spec['frames'][phase];im=Image.open(directory/s['source']).convert('RGBA');boxes=footwear(im,s['shoe_roi_px']);foot={}
  for i,b in enumerate(boxes):
   foot['observed_shoe_'+str(i)+'_outer']=[b[0],b[3]-1];foot['observed_shoe_'+str(i)+'_inner']=[b[2]-1,b[3]-1]
  # Fixed source offsets copied from same-direction approved idle geometry, not a body-height fit.
  if direction=='west':root=[max(b[2] for b in boxes)-1-144,max(b[3] for b in boxes)-1-4]
  elif direction=='east':root=[min(b[0] for b in boxes)+144,max(b[3] for b in boxes)-1-4]
  else:root=[round((min(b[0] for b in boxes)+max(b[2] for b in boxes)-1)/2),max(b[3] for b in boxes)-1-4]
  if 'source_root_override_px' in s:
   # Manual source observation excludes adjacent water/occluders; no art pixels moved.
   root=s['source_root_override_px'];foot=s['visible_foot_points_override_px']
  alpha=im.getchannel('A').point(lambda a:255 if a>=128 else 0).getbbox()
  landmarks=s['visible_landmarks_px'];landmarks['head_crown']=[s['head_center_x'],alpha[1]]
  frames.append(dict(phase=phase,duration_ms=duration,source=s['source'],source_box_px=[0,0,1024,1536],source_root_px=root,visible_foot_points_px=foot,visible_grip_points_px=s['visible_grip_points_px'],visible_landmarks_px=landmarks,water_landing_px=s.get('water_landing_px'),observed_shoe_color_bbox_px=boxes))
 cfg=dict(schema_version=1,direction=direction,garment=garment,canvas_px=[1536,1920],root_anchor_px=[768,1600],root_note='Diagnostic observed footwear with fixed same-direction reference offset. Foot contours color-assisted only; manually reviewed actual source shoe ROI. Not approved support trajectory. No character dimension fitting.',frames=frames)
 (directory/'registration-config.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n')
 print(combo,[(f['phase'],f['source_root_px'],f['observed_shoe_color_bbox_px']) for f in frames])
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('combo');configure(parser.parse_args().combo)
