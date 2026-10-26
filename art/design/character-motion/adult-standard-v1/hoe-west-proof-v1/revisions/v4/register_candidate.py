"""Preserve raw GPT art; whole-frame integer registration and observed measurements."""
from pathlib import Path
import hashlib,json,math
from PIL import Image
ROOT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(name,value):(ROOT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def translate(points,dx,dy):return{k:None if v is None else[v[0]+dx,v[1]+dy] for k,v in points.items()}
def build():
 cfg=json.loads((ROOT/'registration-config.json').read_text());records=[];poses=[];measurements=[]
 for i,f in enumerate(cfg['frames']):
  source=ROOT/f['source'];im=Image.open(source).convert('RGBA')
  if list(im.size)!=cfg['source_canvas_px']:raise ValueError('Source canvas changed; no rescale allowed')
  dx,dy=[cfg['root_anchor_px'][j]-f['source_root_px'][j] for j in [0,1]]
  if not all(type(v)is int and v>=0 for v in [dx,dy]) or dx+im.width>cfg['canvas_px'][0] or dy+im.height>cfg['canvas_px'][1]:raise ValueError('Entire source including low-alpha pixels must fit')
  out=Image.new('RGBA',tuple(cfg['canvas_px']));out.paste(im,(dx,dy))
  pose=f'hoe_west_key_{i}';target=ROOT/f'registered/{pose}.png';out.save(target)
  records.append(dict(pose_id=pose,phase=f['phase'],file=target.relative_to(ROOT).as_posix(),duration_ms=f['duration_ms'],source=f['source'],source_sha256=sha(source),sha256=sha(target),source_box_px=[0,0,im.width,im.height],whole_frame_translation_px=[dx,dy]))
  poses.append(dict(pose_id=pose,phase=f['phase'],source=f['source'],source_sha256=sha(source),source_root_px=f['source_root_px'],whole_frame_translation_px=[dx,dy],landmarks_source_px=f['landmarks_px'],landmarks_registered_px=translate(f['landmarks_px'],dx,dy),foot_points_source_px=f['foot_points_px'],foot_points_registered_px=translate(f['foot_points_px'],dx,dy),tool_points_source_px=f['tool_points_px'],tool_points_registered_px=translate(f['tool_points_px'],dx,dy),foot_contacts='Observed grounded shoes; precise support trajectory not frozen',anatomical_sides='near/far view-side observations; left/right anatomical mapping not frozen',hidden_regions='Clothed hip/knee/ankle joints unknown/null, not inferred from total height',default_layers='Complete GPT raster only; no modular layers, ownership/coverage masks or clothing compatibility claimed'))
  hb=f['head_bbox_px'];head=[hb[2]-hb[0],hb[3]-hb[1]];lm=f['landmarks_px'];tool=f['tool_points_px'];collar=tool['collar'];butt=tool['butt'];length=math.dist(collar,butt);vec=[butt[j]-collar[j] for j in [0,1]];grips={}
  for name in ['near_grip','far_grip']:
   point=tool[name];fraction=sum((point[j]-collar[j])*vec[j] for j in [0,1])/length**2;projection=[collar[j]+fraction*vec[j] for j in [0,1]]
   grips[name]=dict(axis_fraction=fraction,distance_from_observed_axis_px=math.dist(point,projection))
  measurements.append(dict(pose_id=pose,phase=f['phase'],source=f['source'],source_sha256=sha(source),source_canvas_px=list(im.size),head_bbox_px=hb,head_size_px=head,head_difference_vs_approved_water_percent=[(head[j]/cfg['reference_head_size_px'][j]-1)*100 for j in [0,1]],projected_y_segments_px=dict(crown_to_chin=lm['chin'][1]-lm['head_crown'][1],chin_to_shirt_hem=lm['shirt_hem'][1]-lm['chin'][1],shirt_hem_to_observed_root=f['source_root_px'][1]-lm['shirt_hem'][1],crown_to_observed_root=f['source_root_px'][1]-lm['head_crown'][1]),shaft_length_px=length,shaft_angle_deg=math.degrees(math.atan2(vec[1],vec[0])),grips=grips,blade_lowest_source_px=tool['blade_lowest'],blade_lowest_registered_px=[tool['blade_lowest'][0]+dx,tool['blade_lowest'][1]+dy],foot_points_source_px=f['foot_points_px'],foot_points_registered_px=translate(f['foot_points_px'],dx,dy)))
 dump('poses.json',dict(schema_version=1,coordinate_space='actual source/registered pixels; never resized source',manual_uncertainty_source_px=8,poses=poses))
 lengths=[m['shaft_length_px'] for m in measurements]
 foot_spread={name:dict(x_span_source_px=max(m['foot_points_registered_px'][name][0] for m in measurements)-min(m['foot_points_registered_px'][name][0] for m in measurements),y_span_source_px=max(m['foot_points_registered_px'][name][1] for m in measurements)-min(m['foot_points_registered_px'][name][1] for m in measurements)) for name in measurements[0]['foot_points_registered_px']}
 dump('measurements.json',dict(schema_version=1,method='Manual outline/visible surface and tool endpoint observations ±8sourcepx per point. Head bbox uses observed crown/nose/back/chin envelope excluding neck; derived floats are arithmetic, not subpixel precision. Tilt/hem projection is not an anatomical limb-length proof.',reference=dict(source='references/approved-water-ready.png',sha256=sha(ROOT/'references/approved-water-ready.png'),canvas_px=[1024,1536],head_size_px=[473,488],head_bbox_px=[294,247,767,735]),source_density_scale_vs_idle=2,display_scale=cfg['display_scale'],canvas_px=cfg['canvas_px'],root_anchor_px=cfg['root_anchor_px'],native_canvas_extent_at_1x=[v*cfg['display_scale'] for v in cfg['canvas_px']],frames=measurements,shaft_max_min_spread_percent=(max(lengths)/min(lengths)-1)*100,registered_foot_outline_spread=foot_spread,warnings=['Recovery shaft remains longer after two source attempts; no local shortening.','Near heel equal by registration definition is not a passed contact trajectory.','Hip/knee/ankle anatomy is hidden and not guessed.','Projected torso/leg segments vary with pose/hem and remain available for visual review; no total-height fit.'],acceptance=dict(head_density_gate=True,rigid_tool=False,precise_grip=False,precise_support=False,full_dynamic_motion=False,hidden_body_or_wardrobe=False,native=False,user_accepted=False)))
 inputs={p.relative_to(ROOT).as_posix():sha(p) for folder in ['sources','prompts','references'] for p in sorted((ROOT/folder).glob('*')) if p.is_file()}
 for name in ['registration-config.json','poses.json','measurements.json','provenance.json','register_candidate.py','test_candidate.py','method.md']:
  inputs[name]=sha(ROOT/name)
 data={k:cfg[k] for k in ['schema_version','template_id','motion_set_id','revision_id','action_id','direction','status','canvas_px','root_anchor_px','display_scale','source_density_scale_vs_idle','accepted','native_checked','modular','gameplay_available','loop','root_method']}
 data.update(frames=records,inputs=inputs,events=[],review_repeat=True,move_policy='diagnostic_only_no_world_or_gameplay',scope='Four distinct complete GPT key poses for native/user review. Head density restored; no rigid-tool/contact/wardrobe/user acceptance or release claim.')
 data['artifact_digest']=hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':')).encode()).hexdigest()
 dump('candidate.json',data);dump('source-manifest.json',dict(generator='built-in image_gen',exact_model_id='not returned',inputs=inputs,frames=records))
 print(json.dumps(dict(candidate_sha256=sha(ROOT/'candidate.json'),artifact_digest=data['artifact_digest'],canvas_px=data['canvas_px'],root_anchor_px=data['root_anchor_px'],durations_ms=[f['duration_ms'] for f in records],shaft_max_min_spread_percent=(max(lengths)/min(lengths)-1)*100),ensure_ascii=False))
if __name__=='__main__':build()
