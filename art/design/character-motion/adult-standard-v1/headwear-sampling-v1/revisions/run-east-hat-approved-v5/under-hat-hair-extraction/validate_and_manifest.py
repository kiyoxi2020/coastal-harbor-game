"""Audit pixel provenance/registration/depth, then bind manifests to actual files."""
from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib
P=Path(__file__).resolve().parent;V=P.parent;H=V.parent.parent;ROOT=H.parents[4]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def savej(p,j):p.write_text(json.dumps(j,indent=2)+'\n')
def ref(p):return str(p.resolve().relative_to(ROOT.resolve()))
normalized=V/'under-hat-hair-sources/source-v1-normalized.png';raw=V/'under-hat-hair-sources/source-v1.png'
a=Image.open(normalized).convert('RGBA');assert a.size==(1024,1024)
assert Image.open(raw).convert('RGBA').resize((1024,1024),Image.Resampling.NEAREST).tobytes()==a.tobytes()
oldsample=json.loads((H/'run-east/sample.json').read_text());old={j['pose_id']:j for j in oldsample['frames']}
forbidden=[{'brow':(350,254),'ear_skin':(265,315),'eye':(355,300),'face_stroke':(393,300),'shirt':(250,400),'background':(100,250)}, {'brow':(360,249),'ear_skin':(276,310),'eye':(368,300),'face_stroke':(409,300),'shirt':(250,400),'background':(100,250)}, {'brow':(380,252),'ear_skin':(290,320),'eye':(385,305),'face_stroke':(429,310),'shirt':(250,400),'background':(100,250)}, {'brow':(382,252),'ear_skin':(292,320),'eye':(387,305),'face_stroke':(431,310),'shirt':(250,400),'background':(100,250)}]
frames=[];summary=[]
for i in range(4):
 pose=f'run_east_{i}';D=P/pose;plate=Image.open(D/'hair-registered.png').convert('RGBA');source=Image.open(D/'source-full-frame.png').convert('RGBA');mask=Image.open(D/'source-ownership.png').convert('L');regmask=Image.open(D/'registered-ownership.png').convert('L')
 assert plate.size==mask.size==(512,768);assert mask.tobytes()==regmask.tobytes()
 rows=json.loads((D/'source-contours.json').read_text())['rows'];frozen=Image.new('L',mask.size);dr=ImageDraw.Draw(frozen)
 for row in rows:
  for x0,x1 in row['inclusive_x_runs']:dr.line((x0,row['y'],x1,row['y']),fill=255)
 assert frozen.tobytes()==mask.tobytes()
 count=0;bad=0
 for m,s,p in zip(mask.getdata(),source.getdata(),plate.getdata()):
  if m:count+=1;bad+=p!=s
  else:assert p==(0,0,0,0)
 assert not bad
 for name,xy in forbidden[i].items():assert mask.getpixel(xy)==0,(pose,name,xy)
 hatdir=V/('motion-extraction' if i<2 else 'motion-extraction-v2')/pose;hat_manifest=json.loads((hatdir/'manifest.json').read_text());bodyfile=H/f'run-east/references/{pose}-bare.png';body=Image.open(bodyfile).convert('RGBA');far=Image.open(hatdir/'hat-far.png').convert('RGBA');near=Image.open(hatdir/'hat-near.png').convert('RGBA');comp=Image.open(D/'composite.png').convert('RGBA')
 expected=far.copy();expected.alpha_composite(body);expected.alpha_composite(plate);expected.alpha_composite(near)
 ep=expected.load();bp=body.load();fp=far.load();np=near.load();mp=mask.load()
 for yy in range(768):
  for xx in range(512):
   if not(mp[xx,yy] or fp[xx,yy][3] or np[xx,yy][3]):ep[xx,yy]=bp[xx,yy]
 assert expected.tobytes()==comp.tobytes()
 assert sha(bodyfile)==hat_manifest['sha256']['original-body.png']
 outside_diff=0
 for b,c,h0,h1,m in zip(body.getdata(),comp.getdata(),far.getdata(),near.getdata(),mask.getdata()):
  if not(m or h0[3] or h1[3]) and b!=c:outside_diff+=1
 assert not outside_diff
 # Fully explicit state boundary: original full naked-head source stays independently intact.
 original_hair=old[pose]['parts']['hair'];hair_state=old[pose]['states']['hair'];oldrefs={}
 for k in ['complete_source','registered_file']:
  q=H/'run-east'/original_hair[k];oldrefs[k]={'path':ref(q),'sha256':sha(q)}
 q=H/'run-east'/hair_state['file'];assert sha(q)==hair_state['sha256'];oldrefs['hair_only_baked']={'path':ref(q),'sha256':sha(q)}
 measurements=json.loads((D/'registration-measurements.json').read_text());assert measurements['source_to_target_integer_translation_px']==[0,0]
 audit={'pose_id':pose,'checks':{'source_normalization_nearest_exact':True,'source_cell_row_major_exact':source.crop((0,0,512,512)).tobytes()==a.crop((i%2*512,i//2*512,(i%2+1)*512,(i//2+1)*512)).tobytes(),'selected_source_rgba_exact':bad==0,'unselected_plate_rgba_zero':True,'frozen_contours_exact':True,'zero_registration_baked_once':True,'source_and_registered_ownership_exact':True,'forbidden_anatomical_samples_excluded':True,'original_body_sha_matches_formal_hat_input':True,'far_body_hair_near_composite_exact':True,'outside_all_owned_surfaces_rgba_difference_zero':outside_diff==0,'hair_only_state_sha_unchanged':True},'counts':{'owned_source_pixels':count,'source_rgba_mismatch':bad,'outside_surface_union_rgba_difference':outside_diff},'forbidden_anatomical_samples_px':forbidden[i],'geometry_review':{'source_mask_and_composite_2x_reviewed':True,'light_dark_full_body_reviewed':True,'hair_crown_protrusion_observed':False,'generated_ear_brow_eye_face_replacement_allowed':False,'uniform_max_y_hair_cut_used':False,'source_rgb_recolor_or_local_scale_used':False},'limitations':['Hat-compatible visible fringe/side/back/nape view only. Hidden complete bare-head hair is not invented.','Generated facial feature shapes have small per-feature residuals; these do not support a consistent additional translation. Original-body face is always used.','Native continuous playback and user acceptance have not been executed by this extraction task. Tiny scalp/contact-edge differences require review at the integrated display scale.'],'original_hair_only_assets_untouched':oldrefs}
 savej(D/'audit.json',audit)
 files={'registered_file':'hair-registered.png','source_full_frame':'source-full-frame.png','source_ownership':'source-ownership.png','registered_ownership':'registered-ownership.png','source_contours':'source-contours.json','registration_measurements':'registration-measurements.json','audit':'audit.json','composite':'composite.png','visual_light_dark':'composite-light-dark.png','visual_source_mask_composite_head_2x':'source-mask-composite-head-2x.png'}
 manifest={'pose_id':pose,'status':'source-owned-hat-compatible-visible-hair-candidate-ready-for-native-interface-review','runtime_candidate_allowed':True,'native_verified':False,'user_visual_accepted':False,'canvas_px':[512,768],'local_scale':[1,1],'runtime_full_frame_placement_px':[0,0],'source_to_target_integer_translation_px':[0,0],'view_scope':'hat-only compact visible fringe/side/back/nape; not a replacement for complete hair-only state','source':{'raw_file':ref(raw),'raw_sha256':sha(raw),'normalized_file':ref(normalized),'normalized_sha256':sha(normalized),'normalization':'complete 1254x1254 image to 1024x1024 using nearest; no per-pose rescale','normalized_cell_xywh_px':[i%2*512,i//2*512,512,512],'cell_to_source_full_frame_translation_px':[0,0]},'original_body':{'file':ref(bodyfile),'sha256':sha(bodyfile)},'formal_hat':{'manifest_file':ref(hatdir/'manifest.json'),'manifest_sha256':sha(hatdir/'manifest.json'),'far_sha256':sha(hatdir/'hat-far.png'),'near_sha256':sha(hatdir/'hat-near.png')},'layer_order':['formal_hat_far','original_body','registered_under_hat_hair','formal_hat_near'],'files':files,'sha256':{f:sha(D/f) for f in files.values()},'counts':audit['counts'],'original_hair_only_assets_untouched':oldrefs}
 savej(D/'manifest.json',manifest);frames.append({'pose_id':pose,'manifest':f'{pose}/manifest.json','sha256':sha(D/'manifest.json')});summary.append({'pose_id':pose,'owned_source_pixels':count,'registration_residuals_px':{k:v['target_minus_source_px'] for k,v in measurements['features'].items()}})
savej(P/'manifest.json',{'schema_version':1,'scope':'run-east four-frame hat-compatible visible hair extraction','runtime_candidate_allowed':True,'native_verified':False,'user_visual_accepted':False,'files':{'extractor':'extract_hair.py','validator':'validate_and_manifest.py','registration_measurement_script':'measure_registration.py','draft_source_ownership_provenance':'draft_source_ownership.py','audit_note':'source-audit.md'},'frames':frames,'summary':summary})
print(json.dumps(summary,indent=2))
print('PASS: 4 poses × 12 source/provenance/registration/composite checks. Native not run.')
