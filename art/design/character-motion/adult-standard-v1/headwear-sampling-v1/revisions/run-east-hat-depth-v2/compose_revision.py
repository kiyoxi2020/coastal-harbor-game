"""Correct hat depth using existing GPT pixels, exact same-pose anatomy and masks."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops
import json,hashlib,shutil
HERE=Path(__file__).resolve().parent
BASE=HERE.parents[1]/'run-east'
ROOT=HERE.parents[6]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def binary(image):return image.getchannel('A').point(lambda a:255 if a else 0)
def paint(canvas,layer):canvas.paste(layer,(0,0),binary(layer))
def compose(base,rear,front,hair):
 out=base.copy()
 behind=ImageChops.multiply(binary(rear),ImageChops.invert(binary(base)))
 out.paste(rear,(0,0),behind)
 if hair is not None:paint(out,hair)
 paint(out,front);return out
def polygon(size,points):
 result=Image.new('L',size);ImageDraw.Draw(result).polygon([tuple(p) for p in points],fill=255);return result
def masked(image,mask):
 result=Image.new('RGBA',image.size);result.paste(image,(0,0),mask);return result
def main():
 baseline=json.loads((BASE/'sample.json').read_text());registration=json.loads((BASE/'registration.json').read_text())
 for rel,digest in baseline['inputs'].items():
  source=BASE/rel
  assert sha(source)==digest,rel
  target=HERE/rel;target.parent.mkdir(parents=True,exist_ok=True)
  if not target.exists():shutil.copy2(source,target)
 # Reviewed source-space far underside silhouettes. No colors decide depth.
 rear_polygons=[
  [[[316,310],[512,241],[512,512],[316,512]],[[90,369],[207,342],[207,512],[90,512]]],
  [[[327,303],[512,242],[512,512],[327,512]],[[90,369],[205,344],[205,512],[90,512]]],
  [[[359,292],[512,230],[512,512],[359,512]],[[96,367],[218,343],[218,512],[96,512]]],
  [[[350,294],[512,230],[512,512],[350,512]],[[97,368],[210,344],[210,512],[97,512]]],
  [[[393,212],[480,174],[480,768],[393,768]],[[75,309],[154,287],[154,768],[75,768]]]
 ]
 policy={'schema_version':1,'scope':'East run four motion poses and matching idle only','basis':'Manually reviewed GPT hat underside silhouettes; far underside behind same-pose face/hair, crown and near brim in front. No body erasure/translation/resize.','poses':{}}
 sample=json.loads(json.dumps(baseline));sample['revision']={'id':'run-east-hat-depth-v2','baseline_sample':str((BASE/'sample.json').relative_to(ROOT)),'baseline_sha256':sha(BASE/'sample.json'),'reason':'User screenshot: far brim incorrectly painted over forehead.'}
 checks=[]
 for i,f in enumerate(sample['frames']+[sample['idle']]):
  pose=f['pose_id'];old=(baseline['frames']+[baseline['idle']])[i];cfg=registration['idle']['hat'] if i==4 else registration['motion'][i]['hat']
  base=Image.open(HERE/f['states']['bare']['file']).convert('RGBA');full=Image.open(HERE/f['parts']['hat']['registered_file']).convert('RGBA');hair=Image.open(HERE/f['parts']['hair']['registered_file']).convert('RGBA')
  local=Image.open(HERE/f['parts']['hat']['complete_source']).convert('RGBA');rear_local=Image.new('L',local.size)
  for points in rear_polygons[i]:rear_local=ImageChops.lighter(rear_local,polygon(local.size,points))
  rear_mask=Image.new('L',base.size);rear_mask.paste(rear_local,tuple(cfg['offset_px']));rear_mask=ImageChops.darker(rear_mask,binary(full))
  excluded=Image.new('L',base.size)
  if i==4:
   local_exclude=polygon(local.size,[[154,280],[381,200],[389,205],[159,287]])
   excluded.paste(local_exclude,tuple(cfg['offset_px']))
  ownership=ImageChops.subtract(binary(full),excluded);rear_mask=ImageChops.darker(rear_mask,ownership);front_mask=ImageChops.subtract(ownership,rear_mask)
  rear=masked(full,rear_mask);front=masked(full,front_mask)
  cap=Image.new('L',base.size);draw=ImageDraw.Draw(cap);profile={}
  pixels=front_mask.load()
  for x in range(base.width):
   occupied=[y for y in range(base.height) if pixels[x,y]]
   if occupied:profile[x]=max(occupied)
  xs=list(profile);hb=binary(hair).getbbox()
  for x in range(hb[0],hb[2]):draw.line((x,0,x,profile[min(xs,key=lambda v:abs(v-x))]),fill=255)
  tucked_mask=ImageChops.subtract(binary(hair),cap);tucked=masked(hair,tucked_mask)
  outputs={'rear':rear,'front':front};masks={'rear':rear_mask,'front':front_mask,'non_hat_exclusion':excluded,'cap_volume':cap,'tucked_hair':tucked_mask}
  for key,image in outputs.items():image.save(HERE/f'parts/{pose}-hat-{key}.png')
  for key,image in masks.items():image.save(HERE/f'masks/{pose}-depth-{key}.png')
  for state,visible_hair in [('hat',None),('hair_hat',tucked)]:
   out=compose(base,rear,front,visible_hair);path=f'baked/{pose}-{state}.png';out.save(HERE/path)
   edit=ImageChops.lighter(binary(rear),binary(front))
   if visible_hair is not None:edit=ImageChops.lighter(edit,binary(visible_hair))
   editpath=f'masks/{pose}-{state}-depth-edit.png';edit.save(HERE/editpath)
   diff=ImageChops.difference(base,out)
   for channel in diff.split():assert not ImageChops.multiply(channel,ImageChops.invert(edit)).getbbox()
   f['states'][state]={'file':path,'sha256':sha(HERE/path),'edit_mask':editpath}
   checks.append({'pose_id':pose,'state':state,'outside_hat_hair_rgba_unchanged':True,'base_body_never_erased':True})
  f['parts']['hat'].update(rear_file=f'parts/{pose}-hat-rear.png',front_file=f'parts/{pose}-hat-front.png',rear_depth_mask=f'masks/{pose}-depth-rear.png',front_depth_mask=f'masks/{pose}-depth-front.png')
  f['composition']={'layer_order':['hat_far_brim','same_pose_original_body_clothes_hands_tool','tucked_hair_if_selected','hat_crown_and_near_brim'],'body_coverage':'None: original head naturally occludes far brim. Crown/near brim overdraw the cap.'}
  f['cap_volume_mask']=f'masks/{pose}-depth-cap_volume.png';f['hair_under_hat_visible']=f'masks/{pose}-depth-tucked_hair.png';f['occlusion']={'coordinate_space':'target_pose_full_frame','owner_part':'same_pose_head_and_hair','target_part':'hat_far_brim','mask':f'masks/{pose}-depth-rear.png','separate_hair_tucking':f['cap_volume_mask']}
  policy['poses'][pose]={'source_coordinate_space':'Original extracted full hat source crop','source_canvas_px':list(local.size),'source_to_target_offset_px':cfg['offset_px'],'far_brim_polygons':rear_polygons[i],'front_part':'Remaining original GPT hat pixels, excluding non-hat source line in idle only.'}
  assert f['states']['bare']==old['states']['bare'] and f['states']['hair']==old['states']['hair']
 (HERE/'depth-policy.json').write_text(json.dumps(policy,ensure_ascii=False,indent=2)+'\n')
 inputs={}
 for path in sorted(HERE.rglob('*')):
  if path.is_file() and path.name not in ['sample.json','validation.json','review.png','README.md'] and '__pycache__' not in path.parts:inputs[path.relative_to(HERE).as_posix()]=sha(path)
 sample['inputs']=inputs
 (HERE/'sample.json').write_text(json.dumps(sample,ensure_ascii=False,indent=2)+'\n')
 (HERE/'validation.json').write_text(json.dumps({'baseline_sha256':sha(BASE/'sample.json'),'sample_sha256':sha(HERE/'sample.json'),'checks':checks,'user_accepted':False},indent=2)+'\n')
 print('10 hat states rebuilt; 10 bare/hair states and all registration/timing unchanged.')
if __name__=='__main__':main()
