"""Generate diagnostic masks from reviewed geometry; no final artwork is painted."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageChops, ImageFilter
import json, hashlib, math
P=Path(__file__).resolve().parent
H=P.parents[2]
B=H/'run-east'
SIZE=(512,768)
CURVE=[(145,276),(180,266),(232,250),(296,230),(340,216),(376,208)]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def count(m): return sum(m.histogram()[1:])
def blank(): return Image.new('L',SIZE)
def intersect(a,b): return ImageChops.darker(a,b)
def union(a,b): return ImageChops.lighter(a,b)
def diff(a,b): return ImageChops.subtract(a,b)
def poly(pts):
 m=blank();ImageDraw.Draw(m).polygon(pts,fill=255);return m
r=json.loads((B/'registration.json').read_text())['idle']['hat']
assert r['offset_px']==[0,0] and r['source_box_px']==[1024,0,1536,768]
raw=Image.open(B/r['source']).convert('RGBA').crop(tuple(r['source_box_px']))
base=Image.open(B/'references/idle_east_0-bare.png').convert('RGBA')
old=Image.open(B/'parts/idle_east_0-hat-registered.png').convert('RGBA')
opaque=lambda a:a.getchannel('A').point(lambda n:255 if n>=200 else 0)
ro=opaque(raw);bo=opaque(base);old_mask=opaque(old)
# This dense source contour was proposed with color-assisted inspection ONLY,
# inspected against raw 4x/6x contact boards, and is persisted as coordinate data.
# Runtime formal ownership uses this frozen geometry, never source RGB classes.
trace_path=P/'reviewed-inner-brim-boundary.json'
assert trace_path.exists(), 'Frozen reviewed contour required; do not infer ownership from source colors.'
trace=json.loads(trace_path.read_text())['points']
# Independent geometry regions: near rim/crown, far-right brim, visible far-left brim.
near_poly=[(50,50),(389,50)]+list(reversed([tuple(v) for v in trace]))+[(145,330),(50,330)]
near=poly(near_poly)
right=poly([(390,50),(485,50),(485,260),(390,260)])
left=poly([(50,260),(137,278),(145,284),(145,287),(153,292),(157,300),(161,304),(161,314),(150,321),(50,330)])
semantic=union(union(near,right),left)
own=intersect(semantic,ro)
# Disjoint face exclusion. Interior source opening includes all old skin sliver and
# the generated face's vertical inner line. T-junction below left end is excluded.
source_face=diff(poly([(145,285)]+[tuple(v) for v in trace[1:]]+[(390,240),(375,270),(375,360),(190,360),(145,315)]),semantic)
source_forbidden=intersect(diff(old_mask,own),ro)
source_forbidden=union(source_forbidden,intersect(source_face,ro))
# Contact samples use approved curve, not source boundaries.
samples=[]
for i in range(len(CURVE)-1):
 a,b=CURVE[i:i+2]
 for x in range(a[0],b[0]+(1 if i==len(CURVE)-2 else 0)):
  y=round(a[1]+(b[1]-a[1])*(x-a[0])/(b[0]-a[0]));samples.append([x,y])
contact=blank();opening=blank();scalp=blank();cp=contact.load();op=opening.load();sp=scalp.load();bp=bo.load()
y_by_x=dict(samples)
for x,y in samples:
 for yy in [y-1,y]:cp[x,yy]=255
 for yy in range(y+1,y+5):
  if bp[x,yy]:op[x,yy]=255
for x in range(100,410):
 limit=y_by_x.get(x,CURVE[0][1] if x<CURVE[0][0] else CURVE[-1][1])
 for y in range(105,limit+1):
  if bp[x,y]:sp[x,y]=255
outer_head=intersect(scalp,diff(bo,bo.filter(ImageFilter.MinFilter(3))))
assert scalp.getpixel((344,152))==255
max_edit=blank();d=ImageDraw.Draw(max_edit);d.line(CURVE,fill=255,width=25,joint='curve')
for x,y in [CURVE[0],CURVE[-1]]:d.ellipse((x-16,y-16,x+16,y+16),fill=255)
# Actual source exterior, not mask-created opening edge, is frozen. 5px inward
# retains the true black external outline and immediate real hat surface.
raw_outer=diff(ro,ro.filter(ImageFilter.MinFilter(11)))
freeze_outline=intersect(own,raw_outer)
allowed=diff(max_edit,freeze_outline)
visible_head=blank();vp=visible_head.load()
for x,y in samples:
 for yy in range(y+1,min(y+25,SIZE[1])):
  if bp[x,yy] and max_edit.getpixel((x,yy)):vp[x,yy]=255
frozen=union(diff(own,max_edit),freeze_outline)
missing_cover=diff(scalp,own);missing_contact=diff(contact,own)
# Additional candidate-only deficits cannot expand the editable band silently.
outside_edit=diff(union(missing_cover,missing_contact),allowed)
# Genuine near-brim pixels where approved opening must show original head.
intrusion=intersect(intersect(opening,own),near)
intrusion_full=intersect(intersect(visible_head,own),near)
recoverable=diff(own,old_mask)
old_non_hat=intersect(old_mask,source_forbidden)
outputs={'required_cover':scalp,'required_outer_head':outer_head,'required_contact':contact,'required_opening':opening,'visible_head_in_edit_band':visible_head,'allowed_edit':allowed,'max_edit_band':max_edit,'frozen_hat':frozen,'frozen_outer_outline':freeze_outline,'old_source_forbidden':source_forbidden,'old_source_ownership':own,'old_near_hat':intersect(own,near),'old_far_right_hat':intersect(own,right),'old_far_left_hat':intersect(own,left),'missing_cover':missing_cover,'missing_contact':missing_contact,'missing_outside_edit':outside_edit,'old_inner_lip_intrusion':intrusion,'old_inner_lip_intrusion_full':intrusion_full,'recoverable_source_pixels':recoverable,'old_non_hat_contamination':old_non_hat}
for k,m in outputs.items():m.save(P/(k+'.png'))
inputs={str(p.relative_to(H)):sha(p) for p in [B/'registration.json',B/r['source'],B/'references/idle_east_0-bare.png',B/'parts/idle_east_0-hat-registered.png']}
contract={'schema_version':1,'status':'frozen-source-mask-audit-not-art-acceptance','pose_id':'idle_east_0','canvas_px':list(SIZE),'source_to_target':{'source_image':str((B/r['source']).relative_to(H)),'source_crop_px':r['source_box_px'],'crop_to_target_translation_px':[0,0],'scale':[1,1],'note':'Source crop and target full-frame share coordinates; no post-generation head registration.'},'inputs_sha256':inputs,'contact_curve_px':CURVE,'contact_semantics':'Each ordered (x,y) sample requires actual hat at (x,y-1),(x,y). Original body/hair must be visible at next four rows where required_opening mask is set. Legal exterior brim overhang air is not tested as contact.','contact_ordered_samples_px':samples,'mask_semantics':{'required_cover':'Original opaque upper-head surface inside approved cap opening; target-specific, no body erasure.','required_outer_head':'Actual original alpha>=200 outer arc included in required_cover.','required_contact':'Two source-pixel hat-side rows along fixed contact curve.','required_opening':'Four body-side rows after contact; target original opaque head only; excludes legitimate overhang air.','visible_head_in_edit_band':'All target-body pixels below approved contact in editable band, for near-surface exclusion; far brim may exist behind the original body.','allowed_edit':'25px contact band plus radius16 endpoint neighborhoods, minus frozen true external outline. No expansion authorized.','frozen_hat':'Genuine old hat outside max band and all confirmed true external outline.','old_source_ownership':'Manually reviewed geometry intersected with actual source alpha>=200; source pixels only, includes actual black brim border.','old_source_forbidden':'Source face/skin/face-outline region including every old extracted pixel outside genuine hat ownership.','old_inner_lip_intrusion':'Genuine existing near-lip pixels in the four adjacent body-side rows; NOT missing art/contamination.','old_inner_lip_intrusion_full':'All genuine old near-lip pixels below fixed curve inside edit band; full authored replacement/removal extent. A new GPT inner black lip is needed, not geometric clipping.','recoverable_source_pixels':'Actual source hat excluded by previous extraction; can recover exactly at same coordinates.','missing_outside_edit':'Stop gate: required missing pixels outside approved editable region.'},'masks':{k:{'file':k+'.png','sha256':sha(P/(k+'.png')),'coordinates':'target_full_frame_px; identical to source_east_crop_px','mode':'L','count':count(m)} for k,m in outputs.items()},'source_region_geometry':{'near_crown_polygon_px':near_poly,'far_right_polygon_px':[(390,50),(485,50),(485,260),(390,260)],'far_left_polygon_px':[(50,260),(137,278),(145,284),(145,287),(153,292),(157,300),(161,304),(161,314),(150,321),(50,330)],'alpha_support_threshold':200,'manual_review':'Complete ownership and forbidden layers reviewed at3x; source face/brim intersections reviewed at6x. Source face inner line excluded; real exterior black contour retained.'},'source_trace':{'file':trace_path.name,'sha256':sha(trace_path),'right_face_line_exclusion':'Below near lip, x<=389 is source face opening; right far-brim ownership starts x390.','left_hidden_junction':'Source head-line T junction to right of retained far-brim boundary excluded; no hole painted into original target body.'},'audit':{'contact_samples':len(samples),'missing_cover_pixels':count(missing_cover),'missing_contact_pixels':count(missing_contact),'missing_outside_edit_pixels':count(outside_edit),'genuine_old_inner_lip_intrusion_pixels':count(intrusion),'genuine_old_inner_lip_intrusion_full_pixels':count(intrusion_full),'intrusion_full_outside_edit':count(diff(intrusion_full,allowed)),'old_non_hat_pixels':count(old_non_hat),'recoverable_same_coordinate_hat_pixels':count(recoverable),'frozen_overlap_allowed_edit':count(intersect(frozen,allowed)),'v3_failure_probe_target_px':[344,152],'old_genuine_hat_at_probe':bool(own.getpixel((344,152))),'intrusion_outside_allowed_edit':count(diff(intrusion,allowed)),'missing_contact_positions_px':[[x,y] for y in range(SIZE[1]) for x in range(SIZE[0]) if missing_contact.getpixel((x,y))],'old_extracted_missing_cover':count(diff(scalp,old_mask))},'not_final_art':True,'user_visual_accepted':False}
(P/'idle-contract.json').write_text(json.dumps(contract,ensure_ascii=False,indent=2)+'\n')
# Diagnostic guides use colors only for explanation, never final game pixels.
board=Image.new('RGB',(1536,768),'#ccd6dc')
for idx,(name,im) in enumerate([('Original target + approved contact',base),('Raw source ownership / exclusions',raw),('Missing / intrusion / frozen',old)]):
 bg=Image.new('RGBA',SIZE,'#ccd6dc');bg.alpha_composite(im)
 if idx==0:
  tint=Image.new('RGBA',SIZE,(55,140,230,0));tint.putalpha(scalp.point(lambda v:65 if v else 0));bg.alpha_composite(tint)
 elif idx==1:
  tint=Image.new('RGBA',SIZE,(238,45,108,0));tint.putalpha(source_forbidden.point(lambda v:185 if v else 0));bg.alpha_composite(tint)
 else:
  for m,col in [(frozen,(40,165,100)),(intrusion,(230,55,150)),(missing_contact,(255,30,15))]:
   tint=Image.new('RGBA',SIZE,(*col,0));tint.putalpha(m.point(lambda v:185 if v else 0));bg.alpha_composite(tint)
 dd=ImageDraw.Draw(bg);dd.line(CURVE,fill=(0,210,255,255),width=2)
 for x,y in CURVE:dd.ellipse((x-2,y-2,x+2,y+2),fill='yellow')
 dd.text((10,10),name,fill='black');board.paste(bg.convert('RGB'),(idx*512,0))
board.save(P/'idle-diagnostic-guide.png')
# Tight actual-size diagnostic crops for human review.
for name,m in [('ownership',own),('forbidden',source_forbidden)]:
 im=Image.new('RGBA',SIZE);im.paste(raw,(0,0),m);bg=Image.new('RGBA',SIZE,'#cbd4dc');bg.alpha_composite(im)
 bg.crop((65,65,480,330)).resize((1245,795),Image.Resampling.NEAREST).convert('RGB').save(P/f'review-{name}-3x.png')
print(json.dumps(contract['audit'],indent=2))
