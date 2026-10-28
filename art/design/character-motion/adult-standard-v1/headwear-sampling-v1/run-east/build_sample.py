#!/usr/bin/env python3
"""Deterministic GPT part extraction and registered full-frame baking. No painted pixels."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageChops
import json,hashlib,shutil
P=Path(__file__).resolve().parent
ROOT=P.parents[5]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def mask_poly(size,points):
 m=Image.new('L',size);ImageDraw.Draw(m).polygon([tuple(v) for v in points],fill=255);return m
def extract(src,points,palette,exclusions=(),paths=(),body_dark=()):
 sem=mask_poly(src.size,points)
 for poly in exclusions:ImageDraw.Draw(sem).polygon([tuple(v) for v in poly],fill=0)
 for path in paths:ImageDraw.Draw(sem).line([tuple(v) for v in path['points']],fill=0,width=path['width_px'],joint='curve')
 own=Image.new('L',src.size); ss=src.load();oo=own.load();pp=sem.load()
 for y in range(src.height):
  for x in range(src.width):
   r,g,b,a=ss[x,y]
   if pp[x,y] and a>=200 and (not palette or (r<200 and g<150 and b<115)):
    is_body_line=max(r,g,b)<80 and any(v[0]<=x<v[2] and v[1]<=y<v[3] for v in body_dark)
    if not is_body_line:oo[x,y]=255
 part=Image.new('RGBA',src.size);part.paste(src,(0,0),own);return part,own,sem
def build():
 c=json.loads((P/'registration.json').read_text());parent_path=ROOT/c['parent_sample']; parent=json.loads(parent_path.read_text())
 sample={k:parent[k] for k in ['schema_version','template_id','action_id','direction','canvas_px','root_anchor_px','display_scale']};sample.update(parent_sample=c['parent_sample'],parent_sha256=sha(parent_path),frames=[],inputs={},status='sampled-candidate-awaiting-user-visual-acceptance',recipe={'hair':'chestnut-short-v2','hat':'straw-navy-v1'},acceptance={'user_visual':False,'native':False})
 report={'schema_version':1,'non_head_preservation':'Exact RGBA outside union of actual hair/hat ownership; no generated anatomy used.','checks':[],'native_verified':False,'user_accepted':False}
 normalized={}
 for slot in ['hair','hat']:
  src=Image.open(P/c['motion_sources'][slot]).convert('RGBA');size=c['atlas_px'];norm=src.resize(tuple(size),Image.Resampling.NEAREST); norm.save(P/f'sources/{slot}-motion-density-normalized.png');normalized[slot]=norm
 for idx,pf in enumerate(parent['frames']+[parent['idle']]):
  pose=pf['pose_id'];idle=idx==len(parent['frames']); geom=pf if idle else parent; canvas=geom['canvas_px'];base=Image.open(P/f'references/{pose}-bare.png').convert('RGBA'); assert base.size==tuple(canvas)
  parent_bare=parent_path.parent/pf['file']
  assert sha(parent_bare)==pf['sha256'] and sha(P/f'references/{pose}-bare.png')==pf['sha256'],f'{pose} parent bare mismatch'
  shutil.copyfile(P/f'references/{pose}-bare.png',P/f'baked/{pose}-bare.png')
  f={'pose_id':pose,'duration_ms':pf.get('duration_ms',200),'states':{'bare':{'file':f'baked/{pose}-bare.png','sha256':sha(P/f'baked/{pose}-bare.png')}},'parts':{},'head_anchor_mapping':{},'composition':{'layer_order':['same_pose_original_body_clothes_hands_tool','hair','hat'],'hands_tool_in_front_of_headwear':False,'reason':'Inspected native pose: all hands and tool lie spatially below headwear; no crossing.'}}
  if idle:
   for k in ['canvas_px','root_anchor_px','display_scale']:f[k]=pf[k]
  registered={}; masks={};semantics={}
  for slot in ['hair','hat']:
   cfg=c['idle'][slot] if idle else c['motion'][idx][slot]
   if idle:
    src=Image.open(P/cfg['source']).convert('RGBA').crop(tuple(cfg['source_box_px']))
   else:
    if cfg.get('source') and cfg['source']!=c['motion_sources'][slot]:
     src0=Image.open(P/cfg['source']).convert('RGBA');targetsize=tuple(cfg.get('normalization_px',c['atlas_px']));src0=src0.resize(targetsize,Image.Resampling.NEAREST);src0.save(P/('sources/'+Path(cfg['source']).stem+'-density-normalized.png'));src=src0.crop(tuple(cfg.get('source_box_px',c['motion'][idx]['atlas_box_px'])))
    else:src=normalized[slot].crop(tuple(c['motion'][idx]['atlas_box_px']))
   part,own,sem=extract(src,cfg['polygon'],slot=='hair' and not cfg.get('component_only',False),cfg.get('body_exclusion_polygons',[]),cfg.get('body_exclusion_paths',[]),cfg.get('source_body_dark_exclusion_boxes_px',[]));part.save(P/f'parts/{pose}-{slot}-complete-source.png');own.save(P/f'masks/{pose}-{slot}-source-ownership.png');sem.save(P/f'masks/{pose}-{slot}-semantic-region.png')
   offset=cfg['offset_px']; out=Image.new('RGBA',tuple(canvas));out.paste(part,tuple(offset));mask=Image.new('L',tuple(canvas));mask.paste(own,tuple(offset));assert sum(own.histogram()[1:])==sum(mask.histogram()[1:]), f'{pose}/{slot} source part clipped by registered canvas'
   out.save(P/f'parts/{pose}-{slot}-registered.png')
   visible=out.getchannel('A').point(lambda a:255 if a else 0);visible.save(P/f'masks/{pose}-{slot}-coverage.png')
   registered[slot]=out;masks[slot]=visible
   semantic_full=Image.new('L',tuple(canvas));semantic_full.paste(sem,tuple(offset));semantics[slot]=semantic_full
   f['parts'][slot]={'complete_source':f'parts/{pose}-{slot}-complete-source.png','registered_file':f'parts/{pose}-{slot}-registered.png','source_ownership':f'masks/{pose}-{slot}-source-ownership.png','source_ownership_coordinates':{'space':'source_crop_local','canvas_px':list(src.size),'pose_id':pose},'coverage':f'masks/{pose}-{slot}-coverage.png','coverage_coordinates':{'space':'target_pose_full_frame','canvas_px':canvas,'pose_id':pose},'coverage_kind':'visible_alpha_overdraw','target_surface':'same_pose_baked_head_projection' if slot=='hair' else 'same_pose_baked_head_or_registered_hair','coverage_operation':'source-painted alpha overdraw only; no target-body erase mask','placement_mode':'full_frame','offset_px':[0,0],'local_scale':[1,1],'source':cfg.get('source',c['motion_sources'][slot]),'semantic_region':f'masks/{pose}-{slot}-semantic-region.png'}
   f['head_anchor_mapping'][slot]={'operation':'integer head-anchor translation after uniform full-atlas density normalization; no local part resize','registered_offset_px':offset,**{k:v for k,v in cfg.items() if k in ['source_anchor_px','target_anchor_px','projection_evidence']}}
  # A hat is the real foreground surface over the intact hair view. Full source retained.
  cap=Image.new('L',base.size);cd=ImageDraw.Draw(cap);hat_mask=masks['hat'];hair_box=masks['hair'].getbbox()
  # The physical cap volume follows the actual lowest painted brim in every
  # occupied column. Interpolate missing columns so stray tufts cannot poke
  # through transparent gaps at the cap edge; this touches only the hair layer.
  hat_pixels=hat_mask.load();profile={}
  for x in range(base.width):
   ys=[y for y in range(base.height) if hat_pixels[x,y]]
   if ys:profile[x]=max(ys)
  assert profile and hair_box
  occupied=sorted(profile)
  for x in range(hair_box[0],hair_box[2]):
   nearest=min(occupied,key=lambda v:abs(v-x))
   cd.line((x,0,x,profile[nearest]),fill=255)
  cap.save(P/f'masks/{pose}-hat-cap-volume.png')
  tucked=ImageChops.subtract(masks['hair'],cap);tucked.save(P/f'masks/{pose}-hair-under-hat-visible.png')
  occ=ImageChops.subtract(masks['hair'],tucked);occ.save(P/f'masks/{pose}-hair-occluded-by-hat.png');f['occlusion_mask']=f'masks/{pose}-hair-occluded-by-hat.png';f['cap_volume_mask']=f'masks/{pose}-hat-cap-volume.png';f['hair_under_hat_visible']=f'masks/{pose}-hair-under-hat-visible.png';f['occlusion']={'owner_part':'hat_cap','target_surface':'registered_hair_layer_only','mask':f['cap_volume_mask'],'coordinate_space':'target_pose_full_frame','operation':'tuck upper hair under the painted cap/brim profile; base body untouched'}
  for state,slots in [('hair',['hair']),('hat',['hat']),('hair_hat',['hair','hat'])]:
   result=base.copy();edit=Image.new('L',base.size)
   for slot in slots:
    active=tucked if state=='hair_hat' and slot=='hair' else masks[slot]
    result.paste(registered[slot],(0,0),active);edit=ImageChops.lighter(edit,active)
   path=f'baked/{pose}-{state}.png'; result.save(P/path);editpath=f'masks/{pose}-{state}-edit-region.png';edit.save(P/editpath)
   bp=base.load();rp=result.load();ep=edit.load();changed=0;outside=0
   for y in range(base.height):
    for x in range(base.width):
     if bp[x,y]!=rp[x,y]:changed+=1;outside+=not bool(ep[x,y])
   assert outside==0
   f['states'][state]={'file':path,'sha256':sha(P/path),'edit_mask':editpath}
   report['checks'].append({'pose_id':pose,'state':state,'canvas_px':canvas,'changed_pixels':changed,'non_edit_rgba_differences':outside,'reconstruction_exact':True,'edit_mask':editpath,'edit_bbox_px':edit.getbbox()})
  assert sha(P/f'baked/{pose}-bare.png')==pf['sha256']
  if idle:sample['idle']=f
  else:sample['frames'].append(f)
 for p in sorted(P.rglob('*')):
  if p.is_file() and p.name not in ['sample.json','validation.json','review.png','README.md'] and '__pycache__' not in str(p) and 'failed-drafts' not in str(p) and p.name!='large-head-review.png':sample['inputs'][str(p.relative_to(P))]=sha(p)
 sample['external_inputs']={str(parent_path.relative_to(ROOT)):sha(parent_path)}
 for pf in parent['frames']+[parent['idle']]:
  source=parent_path.parent/pf['file'];sample['external_inputs'][str(source.relative_to(ROOT))]=sha(source)
 (P/'sample.json').write_text(json.dumps(sample,ensure_ascii=False,indent=2)+'\n');report['sample_sha256']=sha(P/'sample.json');(P/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 # Offline review image at actual 1x game source-to-display scale, magnified uniformly 2x for human scan.
 sheet=Image.new('RGB',(1000,650),'#59667b');draw=ImageDraw.Draw(sheet)
 for row,f in enumerate(sample['frames']+[sample['idle']]):
  geom=f if row==4 else sample
  for col,state in enumerate(['bare','hair','hat','hair_hat']):
   im=Image.open(P/f['states'][state]['file']).convert('RGBA');s=geom['display_scale']*1.9;im=im.resize((round(im.width*s),round(im.height*s)),Image.Resampling.NEAREST);box=im.getbbox();im=im.crop(box) if box else im;im.thumbnail((230,110),Image.Resampling.NEAREST);sheet.paste(im,(col*250+30,row*130+17),im);draw.text((col*250+4,row*130+3),f['pose_id']+' '+state,fill='white')
 sheet.save(P/'review.png');print(P.name,'15 non-edit RGBA preservation and exact bare hash checks passed')
if __name__=='__main__':build()
