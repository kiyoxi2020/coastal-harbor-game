"""Hat-compatible source-owned west hoe visible hair; default frozen reconstruction."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
import json,hashlib,sys,shutil,importlib.util
P=Path(__file__).resolve().parent;V=P.parent;SRC=V/'under-hat-hair-sources'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def js(p,v):p.write_text(json.dumps(v,indent=2)+'\n')

def build(i,draft=False):
 pose=f'hoe_west_key_{i}';D=P/pose;D.mkdir(exist_ok=True);H=V/f'extraction/{pose}';srcfile=SRC/f'{pose}-v1-full-frame.png';source=Image.open(srcfile).convert('RGBA');window=Image.open(SRC/f'{pose}-v1-window.png').convert('RGBA');frozen=json.loads((D/'source-contours.json').read_text());assert frozen['source_full_frame_sha256']==sha(srcfile) and frozen['compatible_hat_manifest_sha256']==sha(H/'manifest.json');shutil.copyfile(srcfile,D/'source-full-frame.png');wp=window.load();formalnear=Image.open(H/'hat-near.png').convert('RGBA');np=formalnear.load()
 c=json.loads((D/'source-contours.json').read_text());assert c['source_full_frame_sha256']==sha(srcfile) and c['compatible_hat_manifest_sha256']==sha(H/'manifest.json');mask=Image.new('L',source.size);dr=ImageDraw.Draw(mask)
 for row in c['rows']:
  for lo,hi in row['inclusive_x_runs']:dr.line((lo,row['y'],hi,row['y']),fill=255)
 mask.save(D/'source-ownership.png');mask.save(D/'registered-ownership.png');plate=Image.new('RGBA',source.size);plate.paste(source,(0,0),mask);plate.save(D/'hair-registered.png')
 spec=importlib.util.spec_from_file_location('same_v5_composer_motion',V.parent/'run-east-hat-approved-v5/build_approved.py');std=importlib.util.module_from_spec(spec);spec.loader.exec_module(std);body=Image.open(H/'original-body.png').convert('RGBA');far=Image.open(H/'hat-far.png').convert('RGBA');comp,_=std.compose(body,formalnear,far,plate);comp.save(D/'hair-hat-composite.png')
 board=Image.new('RGB',(2520,590),(220,228,234));d=ImageDraw.Draw(board)
 for col,(im,name) in enumerate([(source,'generated source'),(plate,'true source-owned visible hair'),(comp,'formal hat + original body + new hair')]):
  bg=Image.new('RGBA',im.size,(220,228,234,255));bg.alpha_composite(im);crop=bg.crop((340,380 if i==2 else 330,970,840 if i==2 else 800));crop.thumbnail((840,560),Image.Resampling.NEAREST);board.paste(crop.convert('RGB'),(col*840,25));d.text((col*840+3,4),pose+' '+name,fill='black')
 board.save(D/'source-mask-composite-head.png');print(pose,'frozen source view reconstructed at zero part registration')
if __name__=='__main__':
 args=[int(x) for x in sys.argv[1:] if not x.startswith('--')]
 for i in args:build(i,'--draft' in sys.argv)
