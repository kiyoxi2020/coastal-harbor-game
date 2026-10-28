from pathlib import Path
from PIL import Image,ImageDraw,ImageChops
import json,hashlib,importlib.util
import fit_probe as core
P=Path(__file__).resolve().parent;O=core.OLD;H=core.H;ROOT=H.parents[4]
# Frozen default: verify exact artifacts without rewriting masks/images/manifests.
# --rebuild-audit is only for an explicitly authorized pre-freeze regeneration.
import sys,runpy
if '--rebuild-audit' not in sys.argv:
 saved=list(sys.argv);sys.argv=[str(P/'rebuild_frozen.py'),'--check']
 try:runpy.run_path(str(P/'rebuild_frozen.py'),run_name='__main__')
 finally:sys.argv=saved
 digest=lambda q:hashlib.sha256(q.read_bytes()).hexdigest()
 top=json.loads((P/'manifest.json').read_text())
 for rel,expected in top['sha256'].items():assert digest(P/rel)==expected,rel
 for record in top['frames']:
  manifest=P/record['manifest'];assert digest(manifest)==record['sha256']
  value=json.loads(manifest.read_text())
  for rel,expected in value['sha256'].items():assert digest(manifest.parent/rel)==expected,(record['pose_id'],rel)
  assert value['runtime_candidate_allowed_scope']=='hat_component_only'
 print('PASS frozen manifests and 115 artifact bindings; four intact-hair incompatibilities remain explicit.')
 raise SystemExit(0)

sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def js(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def repo(p):return str(p.relative_to(ROOT))
sample=core.S;frames=[];summaries=[]
for index,f in enumerate(sample['frames']+[sample['idle']]):
 pose=f['pose_id'];idle=index==4;D=P/pose;canvas=(512,768) if idle else (1536,1792);src=Image.open(D/'source-full-frame.png').convert('RGBA');own=Image.open(D/'source-ownership.png').convert('L');sn=Image.open(D/'source-near-ownership.png').convert('L');sf=Image.open(D/'source-far-ownership.png').convert('L');reg=Image.open(D/'registered-ownership.png').convert('L');near=Image.open(D/'hat-near.png').convert('RGBA');far=Image.open(D/'hat-far.png').convert('RGBA');plate=Image.open(D/'hat-complete-plate.png').convert('RGBA');body=Image.open(D/'original-body.png').convert('RGBA');hair=Image.open(D/'full-original-hair.png').convert('RGBA');composite=Image.open(D/'composite.png').convert('RGBA');hairhat=Image.open(D/'hair-hat-composite.png').convert('RGBA')
 if idle:
  offset=[0,0];geometry={};boxes={'brow':(145,235,215,270),'eye':(145,265,205,335),'ear':(260,270,335,355)};features={k:core.feature_points(body,b,k) for k,b in boxes.items()};headbox=(120,105,405,features['ear'][1][1]+15)
 else:
  probe=json.loads((D/'registration-probe.json').read_text());offset=probe['candidate_translation_px'];geometry=probe['geometry'];boxes={k:tuple(v['authored_roi_px']) for k,v in probe['features'].items()};features={k:core.feature_points(body,b,k) for k,b in boxes.items()};headbox=(375,100,915,features['ear'][1][1]+15)
 ox,oy=offset;sp=src.load();op=own.load();np=near.load();bp=body.load();hp=hair.load();srcnear=sn.load();counts={};checks={}
 counts['source_owned']=sum(1 for v in own.getdata() if v);counts['near_owned']=sum(1 for v in sn.getdata() if v);counts['far_owned']=sum(1 for v in sf.getdata() if v)
 checks['near_far_ownership_disjoint_complete']=not ImageChops.darker(sn,sf).getbbox() and ImageChops.lighter(sn,sf).tobytes()==own.tobytes()
 sourceplate=Image.new('RGBA',src.size);sourceplate.paste(src,(0,0),own);sourceplate.save(D/'source-plate.png')
 expected=Image.new('RGBA',canvas);expected.paste(sourceplate,(ox,oy));checks['registered_source_rgba_exact_no_scaling']=expected.tobytes()==plate.tobytes()
 expectedmask=Image.new('L',canvas);expectedmask.paste(own,(ox,oy));checks['registration_applied_once']=expectedmask.tobytes()==reg.tobytes()
 checks['original_body_byte_sha_preserved']=sha(D/'original-body.png')==sha(O/f['states']['bare']['file']);checks['full_original_hair_byte_sha_preserved']=sha(D/'full-original-hair.png')==sha(O/f['parts']['hair']['registered_file'])
 a,edit=core.standard.compose(body,near,far);b,edit_hair=core.standard.compose(body,near,far,hair);checks['standard_v5_alpha_composition_exact']=a.tobytes()==composite.tobytes() and b.tobytes()==hairhat.tobytes()
 # Source profile is only a measurement of actual near pixels. It is never
 # extended into a mask, applied to hair, or used to erase the original body.
 profile={x:max([y for y in range(src.height) if srcnear[x,y] and sp[x,y][3]>=200],default=-1) for x in range(src.width)}
 def lip(x):return profile.get(x-ox,-10000)+oy
 cavity=Image.new('L',canvas);contact=Image.new('L',canvas);cp=cavity.load();ct=contact.load();missing=[];arc_missing=[];arc=[]
 hx0,hy0,hx1,hy1=headbox
 for y in range(hy0,hy1):
  row=[]
  for x in range(hx0,hx1):
   if bp[x,y][3]>=200:
    row.append(x)
    if y<=lip(x):
     cp[x,y]=255
     if np[x,y][3]<200:missing.append((x,y))
  if row:
   for x in [min(row),max(row)]:
    if y<=lip(x):arc.append((x,y));arc_missing.extend([(x,y)] if np[x,y][3]<200 else [])
 for x,sy in profile.items():
  if sy<0:continue
  tx,ty=x+ox,sy+oy
  if 0<=tx<canvas[0] and 0<=ty<canvas[1] and bp[tx,ty][3]>=200:ct[tx,ty]=255
 cavity.save(D/'target-coverage.png');contact.save(D/'authored-contact.png')
 miss=Image.new('L',canvas);md=ImageDraw.Draw(miss)
 for xy in missing:md.point(xy,fill=255)
 miss.save(D/'coverage-missing.png')
 upperhair=[];hb=hair.getbbox()
 for y in range(hb[1],hb[3]):
  for x in range(hb[0],hb[2]):
   if hp[x,y][3]>=200 and y<=lip(x) and np[x,y][3]<200:upperhair.append((x,y))
 outside=Image.new('L',canvas);od=ImageDraw.Draw(outside)
 for xy in upperhair:od.point(xy,fill=255)
 outside.save(D/'uncovered-upper-hair.png')
 collisions={k:sum(np[x,y][3]>=200 for x,y in v[0]) for k,v in features.items()}
 outside_changes=0
 for raw,actual,edited in zip(body.getdata(),composite.getdata(),edit.getdata()):
  if not edited and raw!=actual:outside_changes+=1
 checks['outside_hat_support_original_rgba_exact']=outside_changes==0
 checks['original_upper_head_cavity_envelope_covered']=len(missing)==0 and len(arc_missing)==0
 checks['original_eyebrow_eye_ear_opening_protected']=not any(collisions.values())
 # Source ownership of known former skin/face pixels must be zero.
 forbidden=[(200,233),(250,251),(300,268),(345,281),(138,230),(142,205),(144,206)] if idle else []
 checks['generated_skin_face_contamination_excluded']=all(op[x,y]==0 for x,y in forbidden)
 # Every selected original black edge survives ownership unchanged; source boundaries,
 # not recoloring or skin-as-hat, determine which black belongs to this hat.
 previous=Image.open(O/f['parts']['hat']['complete_source']).convert('RGBA')
 black_mismatch=0
 if not idle:
  pp=previous.load()
  for yy in range(src.height):
   for xx in range(src.width):
    rr=pp[xx,yy]
    if rr[3]>=200 and max(rr[:3])<80 and (not op[xx,yy] or sp[xx,yy]!=rr):black_mismatch+=1
 else:
  for xx,yy in json.loads((D/'source-contours.json').read_text())['near_black_lip_inclusive_y_by_x'].items():
   xx=int(xx)
   if max(sp[xx,yy][:3])<80 and not srcnear[xx,yy]:black_mismatch+=1
 checks['owned_black_edge_rgba_not_repainted_or_dropped']=black_mismatch==0
 counts['black_edge_rgba_or_ownership_mismatch']=black_mismatch
 checks['complete_hair_no_crown_or_band_protrusion']=len(upperhair)==0
 full=checks['complete_hair_no_crown_or_band_protrusion'] and checks['original_upper_head_cavity_envelope_covered'] and checks['original_eyebrow_eye_ear_opening_protected']
 hat_body=all(v for k,v in checks.items() if k!='complete_hair_no_crown_or_band_protrusion')
 allowed=bool(hat_body)
 counts.update(cavity_missing=len(missing),upper_arc_missing=len(arc_missing),upper_hair_not_covered_by_actual_near_surface=len(upperhair),protected_collisions=collisions,contact_pixels=sum(1 for v in contact.getdata() if v),outside_hat_support_rgba_changes=outside_changes)
 examples={'cavity_missing_px':missing[::max(1,len(missing)//10)][:10],'upper_arc_missing_px':arc_missing[::max(1,len(arc_missing)//10)][:10],'upper_hair_px':upperhair[::max(1,len(upperhair)//12)][:12]}
 measurement={'pose_id':pose,'source_to_target_integer_translation_px':offset,'runtime_full_frame_placement_px':[0,0],'source_crop_canvas_px':list(src.size),'target_canvas_px':list(canvas),'head_roi_px':headbox,'anatomical_features':{k:{'roi_px':boxes[k],'bbox_px':v[1],'pixels':len(v[0])} for k,v in features.items()},'source_anatomy_correspondence':'Motion source is an isolated complete cap, with no source eyebrow/eye/ear. No fictional paired landmarks or zero feature residuals are claimed. Registration is constrained by the full actual target head/cavity and protected real anatomical features. Idle uses existing wearing-source coordinates without extra movement.','physical_constraints':'Dense actual original upper arc and complete finite upper-head surface above the real near lip; all original eyebrow/eye/ear feature pixels protected; actual near lip must intersect original head. No target body erasure and no cap-volume hair mask.','measured_residuals':counts,'examples':examples,'geometry_search_evidence':'registration-probe.json' if not idle else None,'near_far_review':'Actual underside lobes and their black exterior tips are far; crown/band/bright near brim and continuous lower near lip are near. Masks are mutually exclusive and preserve complete selected RGBA.'}
 js(D/'registration-measurements.json',measurement)
 audit={'pose_id':pose,'checks':checks,'counts':counts,'examples':examples,'full_hair_compatible':full,'hat_body_compatible':bool(hat_body),'runtime_candidate_allowed':allowed,'runtime_candidate_allowed_scope':'hat_component_only; full original hair combination has its independent full_hair_compatible gate','native_verified':False,'user_visual_accepted':False,'original_body_input_sha256':sha(O/f['states']['bare']['file']),'full_original_hair_input_sha256':sha(O/f['parts']['hair']['registered_file']),'standard_composer':repo(core.V5/'build_approved.py'),'standard_composer_sha256':sha(core.V5/'build_approved.py'),'limitations':['No new GPT source, no scaling, no color painting, no original-body erasure.','The finite actual-lip profile is an audit/contact measurement only; original full hair is alpha-composited intact.','Nonzero envelope or hair incompatibility is an explicit rejection, not silently accepted by a source/quantity check.','Native render and user acceptance remain unexecuted for these candidates.']}
 js(D/'audit.json',audit)
 for state,im in [('hat',composite),('hair-hat',hairhat)]:
  board=Image.new('RGB',(canvas[0]*2,canvas[1]));
  for col,color in enumerate([(230,235,239,255),(28,34,44,255)]):
   bg=Image.new('RGBA',canvas,color);bg.alpha_composite(im);board.paste(bg.convert('RGB'),(col*canvas[0],0))
  board.save(D/f'{state}-light-dark-native.png')
 headbox_review=(80,65,450,385) if idle else (300,100,1040,900);scale=3 if idle else 2;cw=headbox_review[2]-headbox_review[0];ch=headbox_review[3]-headbox_review[1]
 board=Image.new('RGB',(cw*2,ch),(225,231,235))
 for col,im in enumerate([composite,hairhat]):
  bg=Image.new('RGBA',canvas,(225,231,235,255));bg.alpha_composite(im);board.paste(bg.crop(headbox_review).convert('RGB'),(col*cw,0))
 board.resize((board.width*scale,board.height*scale),Image.Resampling.NEAREST).save(D/'hat-and-intact-hair-head-enlarged.png')
 files={'source_full_frame':'source-full-frame.png','source_plate':'source-plate.png','source_ownership':'source-ownership.png','source_contours':'source-contours.json','plate':'hat-complete-plate.png','near':'hat-near.png','far':'hat-far.png','ownership':'registered-ownership.png','near_ownership':'near-ownership.png','far_ownership':'far-ownership.png','coverage':'target-coverage.png','coverage_missing':'coverage-missing.png','contact':'authored-contact.png','original_body':'original-body.png','composite':'composite.png','hair_hat_composite':'hair-hat-composite.png','full_original_hair':'full-original-hair.png','registration_measurements':'registration-measurements.json','audit':'audit.json','visual_light_dark':'hat-light-dark-native.png','visual_hair_light_dark':'hair-hat-light-dark-native.png','visual_head_enlarged':'hat-and-intact-hair-head-enlarged.png','uncovered_upper_hair':'uncovered-upper-hair.png'}
 manifest={'pose_id':pose,'status':'hat-component-candidate-ready-for-native-and-user-review' if allowed else 'blocked-hat-body-interface-not-for-runtime','runtime_candidate_allowed':allowed,'runtime_candidate_allowed_scope':'hat_component_only','hat_body_compatible':bool(hat_body),'capabilities':{'hat_over_original_body':bool(hat_body),'hat_over_intact_original_hair':bool(full),'separate_hat_compatible_hair_view_required':not bool(full)},'full_hair_compatible':bool(full),'native_verified':False,'user_visual_accepted':False,'canvas_px':list(canvas),'source_ownership_coordinates':{'space':'source_crop_local','canvas_px':list(src.size),'pose_id':pose},'registered_ownership_coordinates':{'space':'target_pose_full_frame','canvas_px':list(canvas),'pose_id':pose},'source_to_target_integer_translation_px':offset,'runtime_full_frame_placement_px':[0,0],'local_scale':[1,1],'composition':['actual_far_hat','original_body','intact_full_original_hair_if_selected','actual_near_hat'],'files':files,'sha256':{v:sha(D/v) for v in files.values()},'counts':counts,'source':{'file':repo(O/(core.R['idle']['hat']['source'] if idle else core.R['motion_sources']['hat'])),'sha256':sha(O/(core.R['idle']['hat']['source'] if idle else core.R['motion_sources']['hat'])),'crop_px':core.R['idle']['hat']['source_box_px'] if idle else core.R['motion'][index]['atlas_box_px'],'normalization':'none' if idle else 'complete1254square-to1536square-nearest; one768square-cell; no part-local scale'},'original_body_sha256':audit['original_body_input_sha256'],'full_original_hair_sha256':audit['full_original_hair_input_sha256']}
 js(D/'manifest.json',manifest);frames.append({'pose_id':pose,'manifest':f'{pose}/manifest.json','sha256':sha(D/'manifest.json')});summaries.append({'pose_id':pose,'runtime_candidate_allowed':allowed,'runtime_candidate_allowed_scope':'hat_component_only','hat_body_compatible':bool(hat_body),'capabilities':{'hat_over_original_body':bool(hat_body),'hat_over_intact_original_hair':bool(full),'separate_hat_compatible_hair_view_required':not bool(full)},'full_hair_compatible':bool(full),'translation_px':offset,'checks':checks,'counts':counts,'examples':examples})
js(P/'manifest.json',{'schema_version':1,'scope':'five west hoe headwear poses; exact source interface and intact full-hair validation candidates only','runtime_candidate_allowed':all(x['runtime_candidate_allowed'] for x in summaries),'runtime_candidate_allowed_scope':'hat_components_only','full_four_state_sample_allowed_without_separate_hair_views':all(x['full_hair_compatible'] for x in summaries),'missing_hat_compatible_hair_pose_ids':[x['pose_id'] for x in summaries if not x['full_hair_compatible']],'frozen_rebuild_script':'rebuild_frozen.py','native_verified':False,'user_visual_accepted':False,'frames':frames,'summary':summaries})
for x in summaries:print(x['pose_id'],x['runtime_candidate_allowed'],x['full_hair_compatible'],x['counts'],'examples',x['examples'])
