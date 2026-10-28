"""Read-only frozen validation by default; --write-audit materializes review evidence once."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops,ImageFilter
import json,hashlib,importlib.util,sys,statistics
P=Path(__file__).resolve().parent;V=P.parent;SRC=V/'under-hat-hair-sources';H=V/'extraction/idle_west_0';D=P/'idle_west_0';ROOT=V.parents[6]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def js(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
write='--write-audit' in sys.argv
hat_sha=sha(H/'manifest.json');hat=json.loads((H/'manifest.json').read_text());source=Image.open(D/'source-full-frame.png').convert('RGBA');mask=Image.open(D/'source-ownership.png').convert('L');registered=Image.open(D/'registered-ownership.png').convert('L');hair=Image.open(D/'hair-registered.png').convert('RGBA');body=Image.open(H/'original-body.png').convert('RGBA');near=Image.open(H/'hat-near.png').convert('RGBA');far=Image.open(H/'hat-far.png').convert('RGBA');actual=Image.open(D/'hair-hat-composite.png').convert('RGBA');base=Image.open(H/'composite.png').convert('RGBA');sp=source.load();mp=mask.load();np=near.load();fp=far.load();hp=hair.load()
raw=Image.open(SRC/'idle_west_0-v1.png').convert('RGBA');window=Image.open(SRC/'idle_west_0-v1-window.png').convert('RGBA');assert raw.resize((420,420),Image.Resampling.NEAREST).tobytes()==window.tobytes();returned=Image.new('RGBA',(512,768));returned.paste(window,(40,50));assert returned.tobytes()==source.tobytes()
checks={};checks['entire_raw_to_window_nearest_and_return_exact']=True;checks['source_registered_masks_and_full_frame_placement_zero']=source.size==hair.size==mask.size==registered.size==(512,768) and mask.tobytes()==registered.tobytes()
contours=json.loads((D/'source-contours.json').read_text());rebuilt=Image.new('L',mask.size);dr=ImageDraw.Draw(rebuilt)
for row in contours['rows']:
 for lo,hi in row['inclusive_x_runs']:dr.line((lo,row['y'],hi,row['y']),fill=255)
checks['frozen_semantic_contours_exact']=rebuilt.tobytes()==mask.tobytes()
owned=0;rgba_bad=0;clear_bad=0
for m,s,p in zip(mask.getdata(),source.getdata(),hair.getdata()):
 if m:owned+=1;rgba_bad+=p!=s
 else:clear_bad+=p!=(0,0,0,0)
checks['selected_original_source_rgba_exact_and_unselected_zero']=not rgba_bad and not clear_bad
# Actual eyebrow tip, eye-top and lower visible ear arc are independently measured.
def measure(im):
 p=im.load();eye=[(x,y) for y in range(265,325) for x in range(180,225) if p[x,y][3]>=200 and max(p[x,y][:3])<65];top=min(y for x,y in eye);xs=[x for x,y in eye if y==top];e=[(min(xs)+max(xs))/2,top]
 brow=[(x,y) for y in range(237,250) for x in range(198,226) if 60<p[x,y][0]<180 and 40<p[x,y][1]<130 and p[x,y][2]>35 and p[x,y][0]<1.65*p[x,y][1]];right=max(x for x,y in brow);ys=[y for x,y in brow if x==right];b=[right,statistics.median(ys)]
 xs=[x for x in range(274,299) if p[x,342][3]>=200 and max(p[x,342][:3])<65];ear=[(min(xs)+max(xs))/2,342]
 return {'eye_top':e,'visible_brow_right_tip':b,'lower_ear_arc':ear}
a=measure(source);b=measure(body);features={k:{'source_point_px':a[k],'original_body_point_px':b[k],'target_minus_source_px':[b[k][j]-a[k][j] for j in range(2)],'residual_after_zero_registration_px':[b[k][j]-a[k][j] for j in range(2)]} for k in a}
measurement={'pose_id':'idle_west_0','source_window_return_px':[40,50],'source_window_return_is_part_registration':False,'source_to_target_integer_translation_px':[0,0],'runtime_full_frame_placement_px':[0,0],'features':features,'decision':'Eye top y is unchanged; the top-span center differs by one pixel and lower ear arc differs by a subpixel feature-shape measurement. The partly occluded eyebrow tip has a small different residual. No shared nonzero whole-view translation is supported; keep zero. Generated face/ear/brow are not adopted.','source_ownership_space':'512x768 returned source full frame; window [40,50] already included exactly once.'}
checks['zero_registration_supported_by_independent_original_features']=features['eye_top']['target_minus_source_px'][1]==0 and abs(features['eye_top']['target_minus_source_px'][0])<=1 and abs(features['lower_ear_arc']['target_minus_source_px'][0])<=1 and features['lower_ear_arc']['target_minus_source_px'][1]==0
forbidden={'generated_brow':(215,243),'generated_ear_arc':(285,340),'generated_ear_skin':(294,314),'generated_eye':(200,295),'generated_forehead_face_line':(161,289),'generated_neck_shadow':(292,348),'generated_nape_face_contour':(299,350),'generated_skin_behind_ear':(306,336),'hat_crown':(290,130),'hat_band':(315,226),'hat_near_black_lip':(250,241),'shirt':(280,420),'gray_background':(100,300)}
checks['generated_body_hat_and_background_samples_excluded']=all(mp[xy[0],xy[1]]==0 for xy in forbidden.values())
source_hat_black=sum(bool(mp[x,y]) for y in range(190,363) for x in range(120,383) if np[x,y][3]>=200 and max(sp[x,y][:3])<65)
checks['formal_hat_black_lip_not_claimed_as_hair']=source_hat_black==0
spec=importlib.util.spec_from_file_location('exact_frozen_v5_composer',V.parent/'run-east-hat-approved-v5/build_approved.py');std=importlib.util.module_from_spec(spec);spec.loader.exec_module(std);expected,edit=std.compose(body,near,far,hair)
checks['formal_far_original_body_new_hair_near_exact']=expected.tobytes()==actual.tobytes()
outside_hair=0;outside_union=0
for before,original,current,m,all_edit in zip(base.getdata(),body.getdata(),actual.getdata(),mask.getdata(),edit.getdata()):
 if not m and before!=current:outside_hair+=1
 if not all_edit and original!=current:outside_union+=1
checks['outside_new_hair_and_all_part_support_rgba_exact']=outside_hair==outside_union==0
profile={x:max([y for y in range(near.height) if np[x,y][3]>=200],default=-1) for x in range(near.width)}
protrusions=[(x,y) for y in range(190,363) for x in range(120,383) if mp[x,y] and y<=profile[x] and np[x,y][3]<200]
checks['entire_crown_and_band_no_uncovered_hair']=not protrusions
hat_support=ImageChops.lighter(near.getchannel('A'),far.getchannel('A')).point(lambda v:255 if v>=200 else 0);adjacent=hat_support.filter(ImageFilter.MaxFilter(3));ap=adjacent.load();touch=sum(bool(mp[x,y] and ap[x,y]) for y in range(190,363) for x in range(120,383))
checks['real_fringe_and_side_back_roots_contact_formal_hat']=touch>20
checks['exact_compatible_hat_binding_and_original_hair_only_untouched']=hat['runtime_candidate_allowed'] is True and hat['hat_body_compatible'] is True and sha(H/'full-original-hair.png')==hat['full_original_hair_sha256'] and sha(H/'original-body.png')==hat['original_body_sha256']
allowed=all(checks.values());counts={'owned_source_pixels':owned,'source_rgba_mismatch':rgba_bad,'unselected_nonzero_rgba':clear_bad,'forbidden_source_samples_selected':sum(mp[xy[0],xy[1]]>0 for xy in forbidden.values()),'source_hat_black_selected':source_hat_black,'outside_new_hair_support_rgba_differences':outside_hair,'outside_all_part_support_rgba_differences':outside_union,'crown_or_band_protrusions':len(protrusions),'actual_hat_adjacent_root_pixels':touch}
if write:
 js(D/'registration-measurements.json',measurement)
 audit={'pose_id':'idle_west_0','checks':checks,'counts':counts,'forbidden_source_samples_px':forbidden,'protrusion_examples_px':protrusions[:20],'compatible_hat_manifest_sha256':hat_sha,'runtime_candidate_allowed':allowed,'native_verified':False,'user_visual_accepted':False,'scope':'Only drawn compact visible fringe/side/back/nape with this exact hat. Hidden complete bare-head hair is not claimed.','visual_review':'Source, extracted plate, original-body/formal-hat composite reviewed at2x; source eyebrow/ear arc/neck shadow excluded by actual anatomical contours.','original_hair_only_sha256':sha(H/'full-original-hair.png')};js(D/'audit.json',audit)
 board=Image.new('RGB',(1024,768))
 for col,color in enumerate([(230,235,239,255),(28,34,44,255)]):
  bg=Image.new('RGBA',(512,768),color);bg.alpha_composite(actual);board.paste(bg.convert('RGB'),(col*512,0))
 board.save(D/'hair-hat-light-dark-native.png')
 landmarks=Image.new('RGB',(1024,400),(220,228,234));draw=ImageDraw.Draw(landmarks)
 for col,im in enumerate([body,source]):
  bg=Image.new('RGBA',(512,768),(220,228,234,255));bg.alpha_composite(im);landmarks.paste(bg.crop((0,0,512,400)).convert('RGB'),(col*512,0))
 for name,rec in features.items():
  for col,key in enumerate(['original_body_point_px','source_point_px']):
   x,y=rec[key];x+=col*512;draw.ellipse((x-2,y-2,x+2,y+2),outline='red');draw.text((x+4,y-8),name,fill='blue')
 landmarks.save(D/'registration-original-source.png')
 files={'registered_file':'hair-registered.png','source_full_frame':'source-full-frame.png','source_ownership':'source-ownership.png','registered_ownership':'registered-ownership.png','source_contours':'source-contours.json','registration_measurements':'registration-measurements.json','hair_hat_composite':'hair-hat-composite.png','audit':'audit.json','visual_head_2x':'source-mask-composite-head-2x.png','visual_light_dark':'hair-hat-light-dark-native.png','visual_registration':'registration-original-source.png'}
 manifest={'pose_id':'idle_west_0','status':'exact-hat-compatible-visible-hair-candidate' if allowed else 'rejected-source-interface-needs-rework','runtime_candidate_allowed':allowed,'runtime_full_frame_placement_px':[0,0],'source_to_target_integer_translation_px':[0,0],'canvas_px':[512,768],'local_scale':[1,1],'compatible_hat_manifest_sha256':hat_sha,'compatible_hat_manifest_file':str(H.relative_to(ROOT)/'manifest.json'),'compatible_hat_body_sha256':sha(H/'original-body.png'),'compatible_hat_near_sha256':sha(H/'hat-near.png'),'compatible_hat_far_sha256':sha(H/'hat-far.png'),'native_verified':False,'user_visual_accepted':False,'source':{'raw_file':str((SRC/'idle_west_0-v1.png').relative_to(ROOT)),'raw_sha256':sha(SRC/'idle_west_0-v1.png'),'raw_px':[1254,1254],'normalized_window_px':[420,420],'window_return_xy_px':[40,50],'window_return_is_part_registration':False,'full_frame_sha256':sha(D/'source-full-frame.png')},'source_ownership_coordinates':{'space':'returned_source_full_frame','canvas_px':[512,768],'pose_id':'idle_west_0'},'registered_ownership_coordinates':{'space':'target_pose_full_frame','canvas_px':[512,768],'pose_id':'idle_west_0'},'view_scope':'Only visible compressed fringe/side/back/nape with the exact frozen hat; original complete hair-only state retained unchanged.','files':files,'sha256':{rel:sha(D/rel) for rel in files.values()},'counts':counts};js(D/'manifest.json',manifest)
else:
 m=json.loads((D/'manifest.json').read_text());assert m['compatible_hat_manifest_sha256']==hat_sha and m['runtime_candidate_allowed']==allowed and m['source']['raw_sha256']==sha(SRC/'idle_west_0-v1.png') and m['source']['full_frame_sha256']==sha(D/'source-full-frame.png')
 for rel,digest in m['sha256'].items():assert sha(D/rel)==digest,rel
assert sha(H/'manifest.json')==hat_sha,'frozen compatible hat changed during audit'
print(json.dumps({'pose_id':'idle_west_0','runtime_candidate_allowed':allowed,'checks':checks,'counts':counts,'feature_residuals':{k:v['target_minus_source_px'] for k,v in features.items()},'compatible_hat_manifest_sha256':hat_sha},indent=2))
raise SystemExit(0 if allowed else 1)
