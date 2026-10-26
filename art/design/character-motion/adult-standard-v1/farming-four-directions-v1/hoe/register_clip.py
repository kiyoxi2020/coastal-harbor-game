"""Single existing character contract: complete-raster farming candidate registration."""
from pathlib import Path
import hashlib,json,sys,math
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parent
PHASES=['ready','lift','contact','recovery']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def translated(points,dx,dy):return{k:None if v is None else[v[0]+dx,v[1]+dy]for k,v in points.items()}
def validate_data(root,c,verify_digest=True):
 def require(v,message):
  if not v:raise ValueError(message)
 require(c['schema_version']==1 and c['template_id']=='adult-standard-v1' and c['action_id']=='hoe','invalid character/action contract')
 require(c['direction']in['west','east','north','south']and c['garment']in['A','B'],'unknown direction/garment')
 require(c['canvas_px']==[1536,1792]and c['root_anchor_px']==[768,1544],'changed common registered geometry')
 require(c['source_density_scale_vs_idle']==2 and abs(c['display_scale']-138/1164)<1e-12,'wrong source density')
 require([f['phase']for f in c['frames']]==PHASES,'missing/out-of-order phase')
 require(len({f['pose_id']for f in c['frames']})==4,'duplicate pose ids')
 rgba=[]
 for f in c['frames']:
  require(type(f['duration_ms'])is int and f['duration_ms']>0,'invalid time')
  require(f['source']in c['inputs'],'source is not a bound dependency')
  require(sha(root/f['source'])==f['source_sha256']==c['inputs'][f['source']],'source hash mismatch')
  require(sha(root/f['file'])==f['sha256'],'registered hash mismatch')
  im=Image.open(root/f['source']).convert('RGBA');out=Image.open(root/f['file']).convert('RGBA')
  require(im.size==(1024,1536)and out.size==(1536,1792),'density/resolution changed; upsampling forbidden')
  dx,dy=f['whole_frame_translation_px'];require(all(type(v)is int and v>=0 for v in[dx,dy])and dx+1024<=1536 and dy+1536<=1792,'invalid registration')
  expected=Image.new('RGBA',out.size);expected.paste(im,(dx,dy));require(expected.tobytes()==out.tobytes(),'source RGBA changed')
  a=im.getchannel('A');require(a.getextrema()[0]==0 and a.histogram()[0]>1000,'opaque background')
  rgba.append(hashlib.sha256(im.tobytes()).hexdigest())
 require(len(set(rgba))==4,'duplicate raster pose content')
 for path,value in c['inputs'].items():require(sha(root/path)==value,'stale input '+path)
 if verify_digest:
  v=c.copy();saved=v.pop('artifact_digest');require(digest(v)==saved,'artifact digest mismatch')
 return True
def validate(path):
 path=Path(path);return validate_data(path.parent,json.loads(path.read_text()))
def build(root):
 root=Path(root);cfg=json.loads((root/'registration-config.json').read_text());records=[];poses=[];measurements=[]
 for i,f in enumerate(cfg['frames']):
  im=Image.open(root/f['source']).convert('RGBA')
  if im.size!=(1024,1536):raise ValueError('Only true1024x1536 cell sources; no upsampling')
  dx,dy=[cfg['root_anchor_px'][j]-f['source_root_px'][j]for j in[0,1]]
  if any(type(v)is not int or v<0 for v in[dx,dy])or dx+1024>1536 or dy+1536>1792:raise ValueError('Entire source must fit')
  pose='hoe_'+cfg['direction']+'_key_'+str(i);file='registered/'+pose+'.png';out=Image.new('RGBA',(1536,1792));out.paste(im,(dx,dy));out.save(root/file)
  records.append(dict(pose_id=pose,phase=f['phase'],file=file,source=f['source'],sha256=sha(root/file),source_sha256=sha(root/f['source']),duration_ms=f['duration_ms'],source_box_px=[0,0,1024,1536],whole_frame_translation_px=[dx,dy]))
  pose_record=dict(pose_id=pose,phase=f['phase'],source=f['source'],source_root_px=f['source_root_px'],whole_frame_translation_px=[dx,dy],uncertainty_source_px=cfg.get('manual_uncertainty_source_px',12),anatomical_sides='Visible near/far or screen-left/right surfaces; anatomical joints hidden by clothes remain null.')
  for group in['landmarks','foot_points','tool_points']:
   pts=f.get(group+'_px',{});pose_record[group+'_source_px']=pts;pose_record[group+'_registered_px']=translated(pts,dx,dy)
  poses.append(pose_record)
  head=f.get('head_bbox_px');tool=f.get('tool_points_px',{});a=im.getchannel('A');measurement=dict(pose_id=pose,phase=f['phase'],source=f['source'],source_sha256=sha(root/f['source']),head_bbox_px=head,head_size_px=None if head is None else[head[2]-head[0],head[3]-head[1]],root_to_crown_projected_px=None if head is None else f['source_root_px'][1]-head[1],shaft_projected_length_px=None if tool.get('collar')is None or tool.get('butt')is None else math.dist(tool['collar'],tool['butt']),alpha_range=list(a.getextrema()),alpha_bbox_px=a.getbbox(),corner_alpha=[a.getpixel(p)for p in[(0,0),(1023,0),(0,1535),(1023,1535)]],observation=f.get('observation',''))
  measurements.append(measurement)
 dump(root/'poses.json',dict(schema_version=1,coordinate_space='true source and registered pixels',poses=poses,scope='Complete clothing rasters, no masks, hidden anatomy or modular parts.'))
 dump(root/'measurements.json',dict(schema_version=1,method='Manually observed visible outlines/feet/hands/tool; unknown/occluded joints null. No total-height proportional joint guesses. Root is stable authoring registration, not certified support trajectory.',manual_uncertainty_source_px=cfg.get('manual_uncertainty_source_px',12),display_scale=138/1164,frames=measurements,precise_grip_checked=False,precise_support_checked=False,modular=False))
 inputs={p.relative_to(root).as_posix():sha(p)for folder in['sources','prompts','references']for p in sorted((root/folder).glob('*'))if p.is_file()}
 for n in['registration-config.json','provenance.json','poses.json','measurements.json']:inputs[n]=sha(root/n)
 c=dict(schema_version=1,template_id='adult-standard-v1',motion_set_id='farming-four-directions-v1',revision_id='v1',action_id='hoe',direction=cfg['direction'],garment=cfg['garment'],status='complete_four_pose_fixed_outfit_review_candidate',canvas_px=[1536,1792],root_anchor_px=[768,1544],display_scale=138/1164,source_density_scale_vs_idle=2,frames=records,inputs=inputs,events=[],loop=False,review_repeat=True,accepted=False,native_checked=False,modular=False,gameplay_available=False,move_policy='isolated_trial_only_locked_during_action',scope='Four distinct full GPT poses for fixed A/B outfit trial; not independent garment/body compatibility or production release.',registration_tool_sha256=sha(Path(__file__)))
 c['artifact_digest']=digest(c);dump(root/'candidate.json',c);validate(root/'candidate.json')
 board=Image.new('RGB',(400*4,460*2));draw=ImageDraw.Draw(board)
 for row,bg in enumerate([(232,229,216),(36,45,57)]):
  draw.rectangle((0,row*460,1600,(row+1)*460),fill=bg)
  for i,f in enumerate(records):
   out=Image.open(root/f['file']).convert('RGBA').resize((364,425),Image.Resampling.NEAREST);board.paste(out,(i*400+18,row*460+25),out);draw.text((i*400+18,row*460+6),cfg['direction']+' '+cfg['garment']+' '+f['phase'],fill=(15,15,15)if row==0 else(245,245,245))
 board.save(root/'evidence/four-poses-2x.png')
 print(json.dumps(dict(path=str(root/'candidate.json'),sha256=sha(root/'candidate.json'),artifact_digest=c['artifact_digest'],duration_ms=sum(f['duration_ms']for f in records))))
 return c
if __name__=='__main__':
 if sys.argv[1]=='--validate':validate(sys.argv[2]);print('validated')
 else:build(Path(sys.argv[1]))
