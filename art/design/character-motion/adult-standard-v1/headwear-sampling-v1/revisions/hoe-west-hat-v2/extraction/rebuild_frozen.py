"""Validate/rebuild only frozen masks, integer registration and standard composition.
Default is read-only --check. --write explicitly reconstructs derived files in this
extraction directory; no registration search, color classifier or hair cutter runs.
"""
from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib,importlib.util,sys
P=Path(__file__).resolve().parent;H=P.parents[2];ROOT=H.parents[4];OLD=H/'hoe-west'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
spec=importlib.util.spec_from_file_location('frozen_standard_composer',H/'revisions/run-east-hat-approved-v5/build_approved.py');std=importlib.util.module_from_spec(spec);spec.loader.exec_module(std)
sample=json.loads((OLD/'sample.json').read_text());poses={f['pose_id']:f for f in sample['frames']+[sample['idle']]}
def mask(size,rows):
 out=Image.new('L',size);d=ImageDraw.Draw(out)
 for row in rows:
  for lo,hi in row['inclusive_x_runs']:d.line((lo,row['y'],hi,row['y']),fill=255)
 return out
for pose,f in poses.items():
 D=P/pose;m=json.loads((D/'manifest.json').read_text());c=json.loads((D/'source-contours.json').read_text());files=m['files'];rawpath=ROOT/m['source']['file'];assert sha(rawpath)==m['source']['sha256'];raw=Image.open(rawpath).convert('RGBA')
 if pose!='idle_west_0':raw=raw.resize((1536,1536),Image.Resampling.NEAREST)
 src=raw.crop(tuple(m['source']['crop_px']));assert src.tobytes()==Image.open(D/files['source_full_frame']).convert('RGBA').tobytes()
 assert sha(OLD/f['states']['bare']['file'])==m['original_body_sha256'];assert sha(OLD/f['parts']['hair']['registered_file'])==m['full_original_hair_sha256']
 own=mask(src.size,c['source_ownership']);nearown=mask(src.size,c['near_ownership']);farown=mask(src.size,c['far_ownership']);ox,oy=m['source_to_target_integer_translation_px'];canvas=tuple(m['canvas_px'])
 def plate(msk):
  srcplate=Image.new('RGBA',src.size);srcplate.paste(src,(0,0),msk);registered=Image.new('RGBA',canvas);registered.paste(srcplate,(ox,oy));return srcplate,registered
 sourceplate,full=plate(own);_,near=plate(nearown);_,far=plate(farown);body=Image.open(OLD/f['states']['bare']['file']).convert('RGBA');hair=Image.open(OLD/f['parts']['hair']['registered_file']).convert('RGBA');comp,_=std.compose(body,near,far);both,_=std.compose(body,near,far,hair)
 images={files['source_ownership']:own,'source-near-ownership.png':nearown,'source-far-ownership.png':farown,files['source_plate']:sourceplate,files['plate']:full,files['near']:near,files['far']:far,files['composite']:comp,files['hair_hat_composite']:both}
 for role,srcmask in [('ownership',own),('near_ownership',nearown),('far_ownership',farown)]:
  q=Image.new('L',canvas);q.paste(srcmask,(ox,oy));images[files[role]]=q
 for rel,image in images.items():
  actual=Image.open(D/rel).convert(image.mode);assert image.size==actual.size and image.tobytes()==actual.tobytes(),(pose,rel,'frozen reconstruction mismatch')
  if '--write' in sys.argv:image.save(D/rel)
 print(pose,'PASS frozen source RGBA / mask coordinates / one integer registration / standard composer')
