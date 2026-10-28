from pathlib import Path
from PIL import Image,ImageDraw,ImageChops
import json,hashlib,shutil
P=Path(__file__).resolve().parent;V5=P.parent;H=V5.parents[1];SIZE=(512,768)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def blank():return Image.new('L',SIZE)
def poly(pts):
 m=blank();ImageDraw.Draw(m).polygon([tuple(v) for v in pts],fill=255);return m
count=lambda m:sum(m.histogram()[1:])
frames=[]
for i in range(4):
 q=P/f'run_east_{i}';c=json.loads((q/'contours.json').read_text());window=Image.open(q/'source-window.png').convert('RGBA');src=Image.new('RGBA',SIZE);src.paste(window,(0,0));src.save(q/'source-full-frame.png');base=Image.open(H/f'run-east/references/run_east_{i}-bare.png').convert('RGBA');shutil.copyfile(H/f'run-east/references/run_east_{i}-bare.png',q/'original-body.png')
 tr=c['near_edge'];fr=c['far_right_x'];nearsem=poly([(90,40),(fr-1,40)]+list(reversed(tr))+[(tr[0][0],350),(90,350)]);leftsem=poly(c['left_semantic']);rightsem=poly([(fr,40),(505,40),(505,c['far_right_max_y']),(fr,c['far_right_max_y'])])
 semantic=ImageChops.lighter(ImageChops.lighter(nearsem,leftsem),rightsem);outer=blank();d=ImageDraw.Draw(outer)
 for y,x0,x1 in c['outer_spans']:d.line((x0,y,x1,y),fill=255)
 own=ImageChops.darker(semantic,outer)
 for xy in c.get('background_exclusions',[]):own.putpixel(tuple(xy),0)
 far=ImageChops.darker(own,ImageChops.lighter(poly(c['far_left_depth']),poly(c['far_right_depth'])));near=ImageChops.subtract(own,far)
 plate=Image.new('RGBA',SIZE);plate.paste(src,(0,0),own);rear=Image.new('RGBA',SIZE);rear.paste(src,(0,0),far);front=Image.new('RGBA',SIZE);front.paste(src,(0,0),near)
 source_own=own.copy()
 for name,im in [('source-plate',plate),('source-near',front),('source-far',rear),('source-near-ownership',near),('source-far-ownership',far),('source-ownership',source_own)]:im.save(q/(name+'.png'))
 dx,dy=c['placement_px']
 def registered(im):
  out=Image.new(im.mode,SIZE);out.paste(im,(dx,dy));return out
 original_count=count(own);plate,rear,front,own,far,near=[registered(im) for im in [plate,rear,front,own,far,near]]
 assert count(own)==original_count,'registered hat clipped by target canvas'
 out=base.copy();out.paste(Image.alpha_composite(rear,base),(0,0),far);out.paste(front,(0,0),near)
 # Actual reviewed near surface lower contour determines this authored opening.
 # This is an audit reference only: never paints pixels or removes hair/body.
 profile={}
 for x in range(512):
  ys=[y for y in range(768) if near.getpixel((x,y))]
  if ys:profile[x]=max(ys)
 contact=blank();dc=ImageDraw.Draw(contact);bo=base.getchannel('A').point(lambda a:255 if a>=200 else 0);cover=blank();bp=bo.load();cp=cover.load()
 for x in range(100,480):
  ymax=profile.get(x,[291,286,291,291][i]-100)
  for y in range(100,ymax+1):
   if bp[x,y]:cp[x,y]=255
  if x in profile and bp[x,min(ymax+1,767)]:dc.point((x,ymax),fill=255)
 (q/'authored-opening-profile.json').write_text(json.dumps({'coordinate_space':'target_full_frame','source_to_target_integer_translation':[dx,dy],'basis':'Lower border of actual manually reviewed near hat surface, including continuation above original forehead beyond generated source face. Does not alter hat/body/hair.','samples_px':[[x,y] for x,y in profile.items()]},indent=2)+'\n')
 missing=ImageChops.subtract(cover,near)
 for n,im in [('hat-complete-plate',plate),('hat-near',front),('hat-far',rear),('composite',out),('registered-ownership',own),('near-ownership',near),('far-ownership',far),('target-coverage',cover),('authored-contact',contact),('coverage-missing',missing)]:im.save(q/(n+'.png'))
 for n,im in [('hat',plate),('composite',out)]:
  bg=Image.new('RGBA',SIZE,'#d2dce4');bg.alpha_composite(im);bg.crop((90,60,505,405)).resize((830,690),Image.Resampling.NEAREST).convert('RGB').save(q/(n+'-head-2x.png'))
  board=Image.new('RGB',(1024,768))
  for col,colr in enumerate(['#e0e7eb','#26364b']):
   bg=Image.new('RGBA',SIZE,colr);bg.alpha_composite(im);board.paste(bg.convert('RGB'),(col*512,0))
  board.save(q/(n+'-light-dark.png'))
 points=[[x,y] for y in range(768) for x in range(512) if missing.getpixel((x,y))]
 report={'pose_id':f'run_east_{i}','placement_px':[dx,dy],'counts':{'owned':count(own),'near':count(near),'far':count(far),'coverage_missing':count(missing)},'coverage_missing_first':points[:20],'source_image_sha256':sha(q/'source-window.png'),'original_body_sha256':sha(q/'original-body.png'),'source_face_probes':c['source_face_probes'],'source_face_probe_owned':[xy for xy in c['source_face_probes'] if source_own.getpixel(tuple(xy))]}
 (q/'audit.json').write_text(json.dumps(report,indent=2)+'\n');frames.append(report)
(P/'preliminary-audit.json').write_text(json.dumps(frames,indent=2)+'\n');print(json.dumps(frames,indent=2))
