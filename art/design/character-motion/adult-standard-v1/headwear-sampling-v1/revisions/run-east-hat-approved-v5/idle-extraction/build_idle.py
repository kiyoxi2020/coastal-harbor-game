"""Extract approved source pixels using frozen reviewed contours. No painted art."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops,ImageFilter
import json,hashlib,shutil
P=Path(__file__).resolve().parent;H=P.parents[2];V4=H/'revisions/run-east-hat-interface-v4/builtin-mask-edit';SIZE=(512,768)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def blank():return Image.new('L',SIZE)
def mask_poly(pts):
 m=blank();ImageDraw.Draw(m).polygon(pts,fill=255);return m
raw=Image.open(V4/'wearing-source-v2.png').convert('RGBA');window=Image.open(V4/'wearing-source-v2-window-512.png').convert('RGBA');base=Image.open(H/'run-east/references/idle_east_0-bare.png').convert('RGBA')
assert raw.size==(1254,1254) and window.size==(512,512)
assert ImageChops.difference(raw.resize((512,512),Image.Resampling.NEAREST),window).getbbox() is None
shutil.copyfile(V4/'wearing-source-v2.png',P/'approved-source-original.png');shutil.copyfile(V4/'wearing-source-v2-window-512.png',P/'approved-source-window-512.png');shutil.copyfile(H/'run-east/references/idle_east_0-bare.png',P/'original-body.png')
src=Image.new('RGBA',SIZE);src.paste(window,(0,0));src.save(P/'approved-source-full-frame.png')
contours=json.loads((P/'reviewed-contours.json').read_text());near_trace=contours['source_near_inner_edge_px']
near_sem=mask_poly([(60,60),(377,60)]+list(reversed([tuple(v) for v in near_trace]))+[(145,330),(60,330)])
left_sem=mask_poly(contours['source_far_left_semantic_px']);right_sem=mask_poly(contours['source_far_right_semantic_px'])
semantic=ImageChops.lighter(ImageChops.lighter(near_sem,left_sem),right_sem)
outer=blank();d=ImageDraw.Draw(outer)
for y,x0,x1 in contours['source_outer_row_spans_px']:d.line((x0,y,x1,y),fill=255)
own=ImageChops.darker(semantic,outer)
for xy in contours['source_background_exclusion_pixels_px']:own.putpixel(tuple(xy),0)
# Physically observed underside is behind the head; no arbitrary target cutline.
far_left=mask_poly(contours['far_left_depth_polygon_px']);far_right=mask_poly(contours['far_right_depth_polygon_px'])
far=ImageChops.darker(own,ImageChops.lighter(far_left,far_right));near=ImageChops.subtract(own,far)
plate=Image.new('RGBA',SIZE);plate.paste(src,(0,0),own)
rear=Image.new('RGBA',SIZE);rear.paste(src,(0,0),far);front=Image.new('RGBA',SIZE);front.paste(src,(0,0),near)
# Preserve original hidden RGB outside actual hat support; use real alpha-over
# at rear-brim/head intersections, including the original head's soft edge.
out=base.copy();under=Image.alpha_composite(rear,base);out.paste(under,(0,0),far);out.paste(front,(0,0),near)
for n,im in [('hat-complete-plate',plate),('hat-far',rear),('hat-near',front),('original-body-with-approved-hat',out)]:im.save(P/(n+'.png'))
# New contact based on actual authored edge. It is not the historical v4 curve.
contact=blank();cd=ImageDraw.Draw(contact)
for x,y in near_trace:
 if 155<=x<=369:cd.point((x,y),fill=255)
bo=base.getchannel('A').point(lambda a:255 if a>=200 else 0)
cover=blank();cp=cover.load();bp=bo.load();ys=dict(near_trace)
for x in range(100,410):
 yy=ys.get(x,near_trace[0][1] if x<near_trace[0][0] else near_trace[-1][1])
 for y in range(105,yy+1):
  if bp[x,y]:cp[x,y]=255
cover_missing=ImageChops.subtract(cover,near)
# Non-hat face/background ownership is geometric, not a color rule at build.
face_forbidden=ImageChops.subtract(mask_poly([(145,282)]+[tuple(v) for v in near_trace[1:]]+[(378,260),(375,370),(180,370),(145,315)]),own)
for n,m in [('source-ownership',own),('source-hat-semantic',semantic),('source-outer-silhouette',outer),('near-ownership',near),('far-ownership',far),('source-face-forbidden',face_forbidden),('new-contact-authored-edge',contact),('new-target-scalp-coverage',cover),('coverage-missing',cover_missing)]:m.save(P/(n+'.png'))
# Dark/light diagnostics are explanations, not new artwork.
for name,im in [('hat',plate),('composite',out)]:
 board=Image.new('RGB',(1024,768));
 for i,bgcol in enumerate(['#dde5e9','#27364a']):
  bg=Image.new('RGBA',SIZE,bgcol);bg.alpha_composite(im);board.paste(bg.convert('RGB'),(i*512,0))
 board.save(P/f'{name}-light-dark.png')
 for z in [1,3]:
  bg=Image.new('RGBA',SIZE,'#cbd7df');bg.alpha_composite(im);bg.crop((65,65,485,380)).resize((420*z,315*z),Image.Resampling.NEAREST).convert('RGB').save(P/f'{name}-head-{z}x.png')
count=lambda m:sum(m.histogram()[1:])
diff=ImageChops.difference(base,out);outside=0
for y in range(768):
 for x in range(512):
  if not own.getpixel((x,y)) and base.getpixel((x,y))!=out.getpixel((x,y)):outside+=1
report={'status':'extraction-awaiting-visual-audit','pose_id':'idle_east_0','new_visual_authority':'User accepted wearing-source-v2 static effect; historical v4 232-column curve is not the v5 interface.','source_sha256':sha(P/'approved-source-original.png'),'normalized_source_sha256':sha(P/'approved-source-window-512.png'),'original_body_sha256':sha(P/'original-body.png'),'source_coordinates':{'original_size':[1254,1254],'whole_window_normalization':[512,512],'destination_full_frame':[512,768],'placement_px':[0,0],'local_scale':[1,1],'source_mode':'opaque RGB; ownership excludes background and source anatomy geometrically; selected original RGB and alpha255 preserved'},'layer_order':['real_far_brim','exact_original_body','crown_and_real_near_brim'],'checks':{'source_owned_pixels':count(own),'near_pixels':count(near),'far_pixels':count(far),'near_far_overlap':count(ImageChops.darker(near,far)),'source_face_owned':count(ImageChops.darker(own,face_forbidden)),'required_scalp_uncovered':count(cover_missing),'outside_hat_support_rgba_differences':outside,'body_file_unchanged':sha(P/'original-body.png')==sha(H/'run-east/references/idle_east_0-bare.png'),'hat_rgb_changed':False,'body_erased':False},'motion_reuse':'Not granted. Source is an idle view; every run pose needs multi-point projection and silhouette/occlusion checks.','artifacts':{f.name:sha(f) for f in P.iterdir() if f.is_file() and f.suffix in ['.png','.json'] and f.name!='audit.json'}}
(P/'audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report['checks'],indent=2))
