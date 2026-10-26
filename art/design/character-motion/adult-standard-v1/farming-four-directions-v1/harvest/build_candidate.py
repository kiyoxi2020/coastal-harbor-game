"""Whole-frame integer registration of GPT harvest art; never modifies source pixels."""
import argparse,hashlib,json
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parent
PHASES=['ready','reach','pluck','recovery']
DURATIONS=[200,250,250,300]
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def dump(path,data):Path(path).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def local_path(directory,relative):
 p=Path(relative)
 if p.is_absolute() or any(x in ('..','.') for x in p.parts) or '\\' in relative:raise ValueError('unsafe path')
 return directory/p
def validate_candidate(directory,data):
 if data.get('action_id')!='harvest' or data.get('template_id')!='adult-standard-v1' or data.get('direction') not in ('south','west','east','north') or data.get('garment') not in ('A','B'):raise ValueError('identity/capability')
 frames=data.get('frames',[])
 if len(frames)!=4 or [f.get('phase') for f in frames]!=PHASES or len({f['sha256'] for f in frames})!=4:raise ValueError('incomplete real sequence')
 for ref,digest in data['inputs'].items():
  if sha(local_path(directory,ref))!=digest:raise ValueError('source changed: '+ref)
 for frame in frames:
  if not isinstance(frame['duration_ms'],int) or frame['duration_ms']<=0:raise ValueError('timing')
  src=local_path(directory,frame['source']);out=local_path(directory,frame['file'])
  if sha(src)!=frame['source_sha256'] or data['inputs'].get(frame['source'])!=frame['source_sha256'] or sha(out)!=frame['sha256']:raise ValueError('frame/source binding')
  with Image.open(out) as image:
   if list(image.size)!=data['canvas_px']:raise ValueError('real canvas')
 if data.get('display_scale')!=138/1164 or data.get('source_density_scale_vs_idle')!=2:raise ValueError('source density')
 if data.get('modular') or data.get('accepted') or data.get('gameplay_available'):raise ValueError('unearned capability')
 return True
def build(combo):
 directory=ROOT/combo;config=json.loads((directory/'registration-config.json').read_text());direction,garment=combo.split('-')
 (directory/'registered').mkdir(exist_ok=True)
 data={'schema_version':1,'template_id':'adult-standard-v1','motion_set_id':'farming-four-directions-v1','revision_id':'v1','action_id':'harvest','direction':direction,'garment':garment,'status':'complete_four_phase_fixed_outfit_trial_candidate','canvas_px':[1536,1920],'root_anchor_px':[768,1600],'display_scale':138/1164,'source_density_scale_vs_idle':2,'loop':False,'events':[],'accepted':False,'native_checked':False,'geometry_approved':False,'modular':False,'gameplay_available':False,'root_method':config['root_method'],'frames':[],'inputs':{},'registration_tool':{'path':'art/design/character-motion/adult-standard-v1/farming-four-directions-v1/harvest/build_candidate.py','sha256':sha(__file__)},'scope':'Complete fixed-outfit four-phase harvest sequence for isolated trial; not independent garment composition, strict support/grip approval, gameplay or user visual acceptance.'}
 observations=[]
 for i,phase in enumerate(PHASES):
  entry=config['frames'][i];source=directory/entry['source'];image=Image.open(source).convert('RGBA')
  if image.size!=(1024,1536):raise ValueError(f'{combo}/{phase} wrong GPT density {image.size}')
  alpha=image.getchannel('A');corners=[alpha.getpixel(p) for p in [(0,0),(1023,0),(0,1535),(1023,1535)]]
  if max(corners)>1:raise ValueError(f'{combo}/{phase} opaque/noisy corner: {corners}')
  x,y=[int(a-b) for a,b in zip(data['root_anchor_px'],entry['source_root_px'])]
  if x<0 or y<0 or x+image.width>1536 or y+image.height>1920:raise ValueError('complete source outside canvas')
  out=Image.new('RGBA',(1536,1920));out.paste(image,(x,y));name=f'registered/harvest_{direction}_{garment}_{i}.png';out.save(directory/name)
  frame={'pose_id':f'harvest_{direction}_{garment}_{phase}','phase':phase,'duration_ms':DURATIONS[i],'file':name,'sha256':sha(directory/name),'source':entry['source'],'source_sha256':sha(source),'source_box_px':[0,0,1024,1536],'whole_frame_translation_px':[x,y]}
  data['frames'].append(frame)
  observations.append({'pose_id':frame['pose_id'],'source_px':list(image.size),'registered_px':[1536,1920],'canvas_screen_px_1x':[1536*138/1164,1920*138/1164],'source_root_px':entry['source_root_px'],'head_bbox_px':entry.get('head_bbox_px'),'visible_foot_points_source_px':entry.get('visible_foot_points_source_px'),'grip_points_source_px':entry.get('grip_points_source_px'),'hidden_joint_anchors':None,'measurement_uncertainty_source_px':12,'alpha_range':alpha.getextrema(),'corner_alpha':corners,'corner_alpha_quantization_tolerance':1,'note':'Visible manual surface observations only; root registration does not certify support trajectory. Hidden joint centers are unknown.'})
 for folder in ['sources','prompts','references']:
  if (directory/folder).exists():
   for p in sorted((directory/folder).rglob('*')):
    if p.is_file():data['inputs'][str(p.relative_to(directory))]=sha(p)
 data['inputs']['registration-config.json']=sha(directory/'registration-config.json')
 data['artifact_digest']=hashlib.sha256(json.dumps(data,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
 validate_candidate(directory,data);dump(directory/'candidate.json',data);dump(directory/'measurements.json',{'scope':'manual visible landmarks, no strict contact claim','poses':observations})
 print(combo,sha(directory/'candidate.json'))
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--combo',required=True);args=parser.parse_args();build(args.combo)
