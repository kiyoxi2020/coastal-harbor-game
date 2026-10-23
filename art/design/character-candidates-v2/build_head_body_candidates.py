#!/usr/bin/env python3
"""Preserve mother pixels; extract GPT head parts within reviewed cranial ownership only."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter,ImageChops
import hashlib,json,argparse
from collections import deque
ROOT=Path(__file__).resolve().parents[3];ART=Path(__file__).resolve().parent;BODY=ROOT/'art/design/character-bodies/adult-standard-v1';DIRS=['south','west','east','north']
# Full visible face including brows, eyes, nose, cheeks and ears. New short styles keep these exposed.
FACE={
 'south':[[112,262],[139,262],[149,234],[309,234],[320,262],[345,263],[361,281],[360,310],[342,329],[327,327],[307,351],[272,369],[184,369],[151,350],[134,327],[114,328],[99,312],[99,281]],
 'west':[[153,234],[237,234],[255,263],[281,276],[308,275],[325,287],[326,316],[315,337],[292,344],[279,353],[239,369],[197,367],[168,349],[147,334],[147,309],[158,292],[155,260]],
 'east':[[275,234],[359,234],[357,260],[354,292],[365,309],[365,334],[344,349],[315,367],[273,369],[233,353],[220,344],[197,337],[186,316],[187,287],[204,275],[231,276],[257,263]],
 'north':[[170,270],[191,269],[211,286],[210,312],[194,327],[174,317],[158,293]]}
NORTH_SECOND_EAR=[[353,269],[375,270],[388,293],[372,317],[352,327],[335,312],[335,286]]
# Source-reviewed bandanna knot/tails: real cloth may cover the neck here.
BANDANNA_TAIL={'west':[[352,269],[385,275],[410,291],[433,329],[420,337],[389,322],[391,359],[379,361],[354,337],[347,310]],'north':[[259,279],[302,279],[312,305],[332,350],[328,368],[303,351],[282,325],[265,352],[232,368],[232,345],[249,310]]}
BANDANNA_TAIL['east']=[[512-x,y] for x,y in BANDANNA_TAIL['west']]
NECK=json.loads((ROOT/'art/design/character-clothing-proof-v1/semantic-masks.json').read_text())['protected_neck']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def mask_polygon(size,points):
 im=Image.new('L',size);ImageDraw.Draw(im).polygon([tuple(p) for p in points],fill=255);return im
def cranial_connected(owner):
 # After semantic face exclusion, retain source islands connected to actual crown.
 # Detached shoulder/jaw lines cannot be hair. This never invents or paints pixels.
 out=Image.new('L',owner.size);a=owner.load();o=out.load();seen=set()
 for y in range(387):
  for x in range(512):
   if not a[x,y] or (x,y) in seen:continue
   q=deque([(x,y)]);seen.add((x,y));group=[];crown=False
   while q:
    px,py=q.popleft();group.append((px,py));crown=crown or py<220
    for nx,ny in [(px-1,py),(px+1,py),(px,py-1),(px,py+1)]:
     if 0<=nx<512 and 0<=ny<387 and (nx,ny) not in seen and a[nx,ny]:seen.add((nx,ny));q.append((nx,ny))
   if crown:
    for px,py in group:o[px,py]=255
 return out

def build_job(job,master,template_sha):
 folder=Path(job['directory']);source=folder/'source.png'
 if not source.exists():return None
 atlas=Image.open(source).convert('RGBA')
 if atlas.size!=(2048,768):return {'id':job['id'],'status':'incomplete','reason':f'Unexpected source size {atlas.size}; do not independently resize anatomy'}
 cat=job['category'];kind_id=job['id'];previews={};components={};hashes={};metrics={}
 for sub in ['previews','components','owners']:(folder/sub).mkdir(exist_ok=True)
 for i,d in enumerate(DIRS):
  generated=atlas.crop((i*512,0,(i+1)*512,768));body=master.crop((i*512,0,(i+1)*512,768))
  if cat=='body':
   # Each new full body is an independent whole template candidate; no adult-part fitting.
   component=generated;preview=generated;owned=generated.getchannel('A').point(lambda a:255 if a>=200 else 0)
   bbox=owned.getbbox();assert bbox is not None
   bottom=bbox[3]-1;floor_mask=owned.crop((0,max(0,bottom-5),512,bottom+1));contact=floor_mask.getbbox()
   metrics[d]={'source_box':[i*512,0,(i+1)*512,768],'canvas':[512,768],'whole_frame_transform':'identity','visible_bounds':list(bbox),'root_anchor':[round((contact[0]+contact[2])/2),bottom],'landmarks':'pending explicit body-family review/registration; do not infer old adult joints','hidden_body_complete':False}
  else:
   # Semantic head volume, excluding entire visible face/ears and neck; only palette/difference assistance inside it.
   volume=Image.new('L',body.size);ImageDraw.Draw(volume).rectangle((0,0,511,386 if cat=='hair' else 352),fill=255)
   protected=mask_polygon(body.size,FACE[d])
   if d=='north':protected=ImageChops.lighter(protected,mask_polygon(body.size,NORTH_SECOND_EAR))
   protected=protected.filter(ImageFilter.MaxFilter(9))
   protected=ImageChops.lighter(protected,mask_polygon(body.size,NECK[d]))
   # Short-style anatomical envelope: no source jaw/shoulder can belong to a cap.
   ceiling=275 if d=='south' else (355 if cat=='hair' else 320 if d=='north' else 300)
   ImageDraw.Draw(volume).rectangle((0,ceiling+1,511,767),fill=0)
   if d=='west':ImageDraw.Draw(protected).rectangle((0,234,180,386),fill=255)
   if d=='east':ImageDraw.Draw(protected).rectangle((332,234,511,386),fill=255)
   tail=mask_polygon(body.size,BANDANNA_TAIL[d]) if kind_id=='hat08' and d in BANDANNA_TAIL else Image.new('L',body.size)
   volume=ImageChops.lighter(volume,tail)
   protected=ImageChops.subtract(protected,tail)
   volume=ImageChops.subtract(volume,protected)
   core=Image.new('L',body.size);ip=generated.load();bp=body.load();vp=volume.load();cp=core.load();tp=tail.load()
   limit=387 if cat=='hair' or kind_id=='hat08' else 353
   for y in range(0,limit):
    for x in range(512):
     if not vp[x,y]:continue
     r,g,b,a=ip[x,y];br,bg,bb,ba=bp[x,y]
     skin=(r>215 and g>125 and r>g+25 and g>b+12)
     changed=abs(r-br)+abs(g-bg)+abs(b-bb)>30 or abs(a-ba)>80
     if a>=200 and not skin and changed and (cat=='hair' or max(r,g,b)>=24) and (not tp[x,y] or b>r+8):cp[x,y]=255
   near=core.filter(ImageFilter.MaxFilter(7));np=near.load();owned=core.copy();op=owned.load()
   for y in range(0,limit):
    for x in range(512):
     if vp[x,y] and np[x,y] and ip[x,y][3]>=200 and max(ip[x,y][:3])<90:op[x,y]=255
   owned=cranial_connected(owned)
   assert sum(owned.histogram()[1:])>800,(kind_id,d,'empty/noncredible head component')
   component=Image.new('RGBA',body.size);component.paste(generated,(0,0),owned)
   preview=body.copy();preview.paste(component,(0,0),owned)
   assert not ImageChops.multiply(ImageChops.difference(preview,body).convert('RGB').convert('L'),protected).getbbox()
   pp=preview.load();op=owned.load();assert all(pp[x,y]==bp[x,y] for y in range(768) for x in range(512) if not op[x,y])
   metrics[d]={'owned_pixels':sum(owned.histogram()[1:]),'non_owned_rgba_unchanged':True,'entire_visible_face_ears_unchanged':True,'neck_ownership':'unchanged except reviewed hat08 cloth-tail polygon' if kind_id=='hat08' else 'unchanged','canvas':[512,768],'part_transform':'identity','source_box':[i*512,0,(i+1)*512,768]}
  for sub,im,target in [('components',component,components),('previews',preview,previews)]:
   p=folder/sub/(d+'.png');im.save(p);rel=p.relative_to(ROOT).as_posix();target[d]=rel;hashes[rel]=sha(p)
  p=folder/'owners'/(d+'.png');owned.save(p);hashes[p.relative_to(ROOT).as_posix()]=sha(p)
 template_id='adult-standard-v1' if cat!='body' else kind_id+'-candidate-v1'
 for p in [source,folder/'prompt.txt',Path(__file__)]:hashes[p.relative_to(ROOT).as_posix()]=sha(p)
 own_source=source.relative_to(ROOT).as_posix();prompt=(folder/'prompt.txt').relative_to(ROOT).as_posix()
 entry={'id':kind_id,'design_id':kind_id,'label':job['label'],'template_id':template_id,'template_hash':sha(source) if cat=='body' else template_sha,'status':'candidate','source':own_source,'prompt':prompt,'previews':previews,'components':components,'hashes':hashes,'compatibility':{'body_ids':[kind_id] if cat=='body' else ['body01'],'pose':'standing_0'},'extraction':{'method':'independent whole-body master' if cat=='body' else 'reviewed cranial volume minus whole-face/ear/neck ownership; local palette+source difference assistance; never global dark components','script':Path(__file__).relative_to(ROOT).as_posix(),'metrics':metrics},'review_scope':'candidate visual review required; new body not approved naked rig or existing adult-clothing compatible'}
 (folder/'item.json').write_text(json.dumps(entry,ensure_ascii=False,indent=2)+'\n');return entry

def main():
 p=argparse.ArgumentParser();p.add_argument('--id');p.add_argument('--all',action='store_true');args=p.parse_args();selection=json.loads((BODY/'selection.json').read_text());source=BODY/selection['active_revision']['source'];template_sha=sha(source);assert template_sha==selection['active_revision']['source_sha256'];master=Image.open(source).convert('RGBA');jobs=json.loads((ART/'jobs.json').read_text());built=[]
 for j in jobs:
  if j['category'] not in ['hair','hat','body'] or (args.id and j['id']!=args.id):continue
  result=build_job(j,master,template_sha)
  if result:built.append(result);print(j['id'],result['status'])
 (ART/'head-body-built.json').write_text(json.dumps(built,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
