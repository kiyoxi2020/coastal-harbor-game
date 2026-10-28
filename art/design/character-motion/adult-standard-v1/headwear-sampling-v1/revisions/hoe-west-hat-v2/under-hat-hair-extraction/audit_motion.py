"""Audit source-owned west hoe compact hair against each exact frozen hat."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops,ImageFilter
import json,hashlib,importlib.util,sys,statistics
P=Path(__file__).resolve().parent;V=P.parent;SRC=V/'under-hat-hair-sources';ROOT=V.parents[6]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def js(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
spec=importlib.util.spec_from_file_location('frozen_geometry_feature_helpers',V/'extraction/fit_probe.py');geometry=importlib.util.module_from_spec(spec);spec.loader.exec_module(geometry)
spec=importlib.util.spec_from_file_location('actual_standard_v5_composer',V.parent/'run-east-hat-approved-v5/build_approved.py');std=importlib.util.module_from_spec(spec);spec.loader.exec_module(std)
forbidden_windows={0:{'brow':(280,472),'ear_arc':(430,655),'ear_skin':(452,608),'eye':(275,560),'face_line':(176,490),'neck_shadow':(468,680),'shirt':(485,710),'hat_crown':(400,200),'hat_band':(480,420),'gray':(700,700)},2:{'primary_brow':(260,530),'extra_generated_brow':(280,500),'gap_forehead_skin':(282,510),'ear_arc':(416,714),'ear_skin':(436,666),'eye':(259,620),'face_line':(149,550),'neck_shadow':(445,738),'shirt':(470,760),'hat_crown':(400,240),'hat_band':(480,480),'gray':(700,700)},3:{'brow':(280,468),'ear_arc':(445,648),'ear_skin':(450,600),'eye':(279,550),'face_line':(180,490),'neck_shadow':(456,663),'shirt':(477,710),'hat_crown':(400,200),'hat_band':(480,420),'gray':(700,700)}}

def audit(i,write=False):
 pose=f'hoe_west_key_{i}';D=P/pose;H=V/f'extraction/{pose}';hat_sha=sha(H/'manifest.json');hat=json.loads((H/'manifest.json').read_text());source=Image.open(D/'source-full-frame.png').convert('RGBA');mask=Image.open(D/'source-ownership.png').convert('L');registered=Image.open(D/'registered-ownership.png').convert('L');hair=Image.open(D/'hair-registered.png').convert('RGBA');body=Image.open(H/'original-body.png').convert('RGBA');near=Image.open(H/'hat-near.png').convert('RGBA');far=Image.open(H/'hat-far.png').convert('RGBA');actual=Image.open(D/'hair-hat-composite.png').convert('RGBA');base=Image.open(H/'composite.png').convert('RGBA');sp=source.load();mp=mask.load();hp=hair.load();np=near.load()
 rawfile=SRC/f'{pose}-v1.png';raw=Image.open(rawfile).convert('RGBA');window=Image.open(SRC/f'{pose}-v1-window.png').convert('RGBA');assert raw.resize((880,880),Image.Resampling.NEAREST).tobytes()==window.tobytes();returned=Image.new('RGBA',(1536,1792));returned.paste(window,(240,80));assert returned.tobytes()==source.tobytes()
 checks={'entire_raw_nearest_window_and_return_exact':True,'source_and_registered_masks_zero_full_frame_registration':source.size==mask.size==hair.size==registered.size==(1536,1792) and mask.tobytes()==registered.tobytes()};c=json.loads((D/'source-contours.json').read_text());rebuilt=Image.new('L',source.size);dr=ImageDraw.Draw(rebuilt)
 for row in c['rows']:
  for lo,hi in row['inclusive_x_runs']:dr.line((lo,row['y'],hi,row['y']),fill=255)
 checks['frozen_semantic_contours_exact']=rebuilt.tobytes()==mask.tobytes()
 owned=bad=clear_bad=0
 for m,s,p in zip(mask.getdata(),source.getdata(),hair.getdata()):
  if m:owned+=1;bad+=p!=s
  else:clear_bad+=p!=(0,0,0,0)
 checks['selected_source_rgba_exact_unselected_rgba_zero']=bad==clear_bad==0
 original_features=json.loads((H/'registration-measurements.json').read_text())['anatomical_features']
 def features(im,is_source):
  out={}
  for kind in ['eye','brow']:
   box=tuple(original_features[kind]['roi_px']);pts,bb=geometry.feature_points(im,box,kind)
   if kind=='eye':
    top=min(y for x,y in pts);xs=[x for x,y in pts if y==top];point=[bb[0],bb[1]]
   else:
    broad_bbox=list(bb);gray=set();px=im.load()
    for yy in range(box[1],box[3]):
     for xx in range(box[0],box[2]):
      rr,gg,bl,aa=px[xx,yy]
      if aa>=200 and 60<rr<190 and 45<gg<140 and bl>35 and rr<1.68*gg:gray.add((xx,yy))
    components=[]
    while gray:
     q=[gray.pop()];component=[]
     while q:
      z=q.pop();component.append(z)
      for dx,dy in [(0,1),(0,-1),(1,0),(-1,0)]:
       t=(z[0]+dx,z[1]+dy)
       if t in gray:gray.remove(t);q.append(t)
     components.append(component)
    pts=[point for component in components if len(component)>=60 for point in component]
    if not pts:pts=max(components,key=len)
    bb=[min(x for x,y in pts),min(y for x,y in pts),max(x for x,y in pts)+1,max(y for x,y in pts)+1];point=[(bb[0]+bb[2]-1)/2,(bb[1]+bb[3]-1)/2]

   out[kind]={'point_px':point,'component_bbox_px':bb,'roi_px':box,'pixels':len(pts),'method':'Upper-left actual eye component bbox, not the shape-sensitive darkest top-row span center.' if kind=='eye' else 'Actual gray-brown eyebrow segments in authored skin ROI; use their union across color gaps, exclude tiny fringe-colored fragments. Broad-predicate bbox is retained separately.'}
   if kind=='eye':out[kind]['dark_top_span_center_diagnostic_only_px']=[(min(xs)+max(xs))/2,top]
   else:out[kind]['broad_brown_predicate_bbox_diagnostic_only_px']=broad_bbox
  eb=original_features['ear']['bbox_px'];box=(eb[0]+6,eb[3]-18,eb[0]+round((eb[2]-eb[0])*.5),eb[3]+4);px=im.load();pts=[]
  for y in range(box[1],box[3]):
   for x in range(box[0],box[2]):
    if px[x,y][3]>=200 and max(px[x,y][:3])<80 and (not is_source or not mp[x,y]):pts.append((x,y))
  bottom=max(y for x,y in pts);xs=[x for x,y in pts if y==bottom];out['ear_lower_arc']={'point_px':[(min(xs)+max(xs))/2,bottom],'roi_px':box,'pixels':len(pts),'method':'Actual lower visible ear arc inside authored ROI; selected hair pixels excluded from source measurement.'}
  return out
 sf=features(source,True);tf=features(body,False);measured={k:{'source':sf[k],'original_body':tf[k],'target_minus_source_px':[tf[k]['point_px'][j]-sf[k]['point_px'][j] for j in range(2)],'residual_after_zero_registration_px':[tf[k]['point_px'][j]-sf[k]['point_px'][j] for j in range(2)]} for k in sf}
 # Zero is retained unless the source provides consistent whole-view displacement;
 # generated partial brow/ear shape differences are not a reason to move the hair.
 checks['zero_registration_original_anatomy_reviewed']=max(abs(x) for x in measured['eye']['target_minus_source_px'])<=3 and max(abs(x) for x in measured['brow']['target_minus_source_px'])<=5 and max(abs(x) for x in measured['ear_lower_arc']['target_minus_source_px'])<=3
 forbidden={k:(x+240,y+80) for k,(x,y) in forbidden_windows[i].items()};selected_forbidden={k:mp[x,y] for k,(x,y) in forbidden.items() if mp[x,y]};checks['generated_body_ear_brow_face_hat_clothes_background_excluded']=not selected_forbidden
 near_black=sum(bool(mp[x,y]) for y in range(80+310,80+760) for x in range(240+110,240+640) if np[x,y][3]>=200 and max(sp[x,y][:3])<70);checks['actual_near_hat_black_lip_not_in_hair']=near_black==0
 expected,edit=std.compose(body,near,far,hair);checks['exact_formal_far_original_body_new_hair_near_composition']=expected.tobytes()==actual.tobytes()
 outside_hair=outside_all=0
 for before,original,current,m,e in zip(base.getdata(),body.getdata(),actual.getdata(),mask.getdata(),edit.getdata()):
  if not m and before!=current:outside_hair+=1
  if not e and original!=current:outside_all+=1
 checks['outside_hair_and_all_surface_support_rgba_exact']=outside_hair==outside_all==0
 profile={x:max([y for y in range(near.height) if np[x,y][3]>=200],default=-1) for x in range(near.width)};protrusions=[(x,y) for y in range(80+310,80+760) for x in range(240+110,240+640) if mp[x,y] and y<=profile[x] and np[x,y][3]<200];checks['entire_crown_band_no_hair_protrusion']=not protrusions
 hat_support=ImageChops.lighter(near.getchannel('A'),far.getchannel('A')).point(lambda v:255 if v>=200 else 0);adjacent=hat_support.filter(ImageFilter.MaxFilter(3)).load();touch=sum(bool(mp[x,y] and adjacent[x,y]) for y in range(80+310,80+760) for x in range(240+110,240+640));checks['real_visible_fringe_side_back_roots_meet_formal_hat']=touch>50
 checks['exact_hat_binding_and_original_hair_only_retained']=hat['runtime_candidate_allowed'] is True and hat['hat_body_compatible'] is True and sha(H/'full-original-hair.png')==hat['full_original_hair_sha256'] and sha(H/'original-body.png')==hat['original_body_sha256']
 allowed=all(checks.values());counts={'owned_source_pixels':owned,'source_rgba_mismatch':bad,'unselected_nonzero_rgba':clear_bad,'forbidden_source_samples_selected':len(selected_forbidden),'source_hat_black_selected':near_black,'outside_new_hair_support_rgba_differences':outside_hair,'outside_all_part_support_rgba_differences':outside_all,'crown_or_band_protrusions':len(protrusions),'actual_hat_adjacent_root_pixels':touch}
 measurement={'pose_id':pose,'window_return_px':[240,80],'window_return_is_part_registration':False,'source_to_target_integer_translation_px':[0,0],'runtime_full_frame_placement_px':[0,0],'features':measured,'decision':'Keep zero whole-view registration. Actual original eye/brow/visible lower ear arc were compared; local generated feature/occlusion residuals are recorded, not adopted as a new face or used to justify arbitrary offsets. All source facial pixels remain outside hair ownership.','source_ownership_space':'1536x1792 returned source full frame;880-square window already returned to[240,80] exactly once.'}
 if write:
  js(D/'registration-measurements.json',measurement);js(D/'audit.json',{'pose_id':pose,'checks':checks,'counts':counts,'forbidden_source_samples_px':forbidden,'selected_forbidden_samples':selected_forbidden,'protrusion_examples_px':protrusions[:30],'compatible_hat_manifest_sha256':hat_sha,'runtime_candidate_allowed':allowed,'native_verified':False,'user_visual_accepted':False,'scope':'Only compact drawn fringe/side/back/nape visible with this exact frozen hat. Complete hidden naked-head hair is not claimed.','key2_extra_brow_review':'A second source eyebrow stroke on actual generated forehead skin was explicitly excluded; the original-body single eyebrow stays intact.' if i==2 else None,'original_hair_only_sha256':sha(H/'full-original-hair.png')})
  board=Image.new('RGB',(3072,1792))
  for col,color in enumerate([(230,235,239,255),(28,34,44,255)]):
   bg=Image.new('RGBA',(1536,1792),color);bg.alpha_composite(actual);board.paste(bg.convert('RGB'),(col*1536,0))
  board.save(D/'hair-hat-light-dark-native.png')
  bg=Image.new('RGBA',(1536,1792),(220,228,234,255));bg.alpha_composite(actual);crop=bg.crop((300,100,1070,940));crop.resize((1540,1680),Image.Resampling.NEAREST).save(D/'formal-hat-new-hair-head-2x.png')
  landmark=Image.new('RGB',(1600,850),(220,228,234));draw=ImageDraw.Draw(landmark)
  for col,im in enumerate([body,source]):
   bg=Image.new('RGBA',(1536,1792),(220,228,234,255));bg.alpha_composite(im);landmark.paste(bg.crop((300,100,1100,950)).convert('RGB'),(col*800,0))
  for name,rec in measured.items():
   for col,key in enumerate(['original_body','source']):
    x,y=rec[key]['point_px'];x=x-300+col*800;y-=100;draw.ellipse((x-3,y-3,x+3,y+3),outline='red');draw.text((x+5,y-10),name,fill='blue')
  landmark.save(D/'registration-original-source.png')
  files={'registered_file':'hair-registered.png','source_full_frame':'source-full-frame.png','source_ownership':'source-ownership.png','registered_ownership':'registered-ownership.png','source_contours':'source-contours.json','registration_measurements':'registration-measurements.json','hair_hat_composite':'hair-hat-composite.png','audit':'audit.json','visual_source_mask_composite':'source-mask-composite-head.png','visual_head_2x':'formal-hat-new-hair-head-2x.png','visual_light_dark':'hair-hat-light-dark-native.png','visual_registration':'registration-original-source.png'}
  manifest={'pose_id':pose,'status':'exact-frozen-hat-compatible-visible-hair-candidate' if allowed else 'rejected-source-interface-needs-rework','runtime_candidate_allowed':allowed,'source_to_target_integer_translation_px':[0,0],'runtime_full_frame_placement_px':[0,0],'canvas_px':[1536,1792],'local_scale':[1,1],'compatible_hat_manifest_sha256':hat_sha,'compatible_hat_manifest_file':str((H/'manifest.json').relative_to(ROOT)),'compatible_hat_body_sha256':sha(H/'original-body.png'),'compatible_hat_near_sha256':sha(H/'hat-near.png'),'compatible_hat_far_sha256':sha(H/'hat-far.png'),'native_verified':False,'user_visual_accepted':False,'source':{'raw_file':str(rawfile.relative_to(ROOT)),'raw_sha256':sha(rawfile),'raw_px':[1254,1254],'normalized_window_px':[880,880],'window_return_xy_px':[240,80],'window_return_is_part_registration':False,'full_frame_sha256':sha(D/'source-full-frame.png')},'source_ownership_coordinates':{'space':'returned_source_full_frame','canvas_px':[1536,1792],'pose_id':pose},'registered_ownership_coordinates':{'space':'target_pose_full_frame','canvas_px':[1536,1792],'pose_id':pose},'view_scope':'Only compact visible fringe/side/back/nape with this exact hat; original complete hair-only state is unchanged.','files':files,'sha256':{rel:sha(D/rel) for rel in files.values()},'counts':counts};js(D/'manifest.json',manifest)
 else:
  manifest=json.loads((D/'manifest.json').read_text());assert manifest['compatible_hat_manifest_sha256']==hat_sha and manifest['runtime_candidate_allowed']==allowed and manifest['source']['raw_sha256']==sha(rawfile)
  for rel,digest in manifest['sha256'].items():assert sha(D/rel)==digest,(pose,rel)
 assert sha(H/'manifest.json')==hat_sha,'compatible hat changed during audit'
 print(json.dumps({'pose_id':pose,'runtime_candidate_allowed':allowed,'checks':checks,'counts':counts,'feature_residuals':{k:v['target_minus_source_px'] for k,v in measured.items()},'selected_forbidden':selected_forbidden,'protrusion_examples':protrusions[:12],'compatible_hat_manifest_sha256':hat_sha},indent=2))
 return allowed
if __name__=='__main__':
 ids=[int(x) for x in sys.argv[1:] if not x.startswith('--')];ok=True
 for i in ids:ok=audit(i,'--write-audit' in sys.argv) and ok
 raise SystemExit(0 if ok else 1)
