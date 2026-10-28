"""Frozen source-owned idle under-hat visible hair. No image generation or hair trim.
--draft locates candidates in a reviewed anatomical envelope; default reconstructs
only frozen source pixel runs. Crop return [40,50] is not part registration.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
import json,hashlib,sys,shutil,importlib.util
P=Path(__file__).resolve().parent;V=P.parent;SRC=V/'under-hat-hair-sources';HAT=V/'extraction/idle_west_0';D=P/'idle_west_0';D.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def js(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
source=Image.open(SRC/'idle_west_0-v1-full-frame.png').convert('RGBA');shutil.copyfile(SRC/'idle_west_0-v1-full-frame.png',D/'source-full-frame.png');sp=source.load()
polygon=[(136,204),(375,279),(380,299),(369,317),(362,330),(351,341),(344,343),(343,335),(334,345),(325,351),(318,352),(316,346),(307,356),(300,359),(291,357),(291,344),(305,337),(314,329),(319,318),(319,305),(314,294),(305,286),(294,284),(282,289),(274,299),(270,310),(263,320),(258,313),(257,300),(251,302),(250,292),(254,282),(252,270),(247,260),(238,252),(229,245),(224,236),(216,231),(210,229),(203,227),(198,228),(196,243),(200,250),(196,256),(189,251),(181,244),(177,231),(174,231),(172,243),(166,249),(165,261),(160,268),(156,268),(151,259),(146,247),(141,242),(140,233),(137,227),(131,235),(125,232),(127,222),(132,212)]
c=json.loads((D/'source-contours.json').read_text());assert c['source_full_frame_sha256']==sha(SRC/'idle_west_0-v1-full-frame.png');assert c['compatible_hat_manifest_sha256']==sha(HAT/'manifest.json');mask=Image.new('L',source.size);md=ImageDraw.Draw(mask)
for row in c['rows']:
 for lo,hi in row['inclusive_x_runs']:md.line((lo,row['y'],hi,row['y']),fill=255)
mask.save(D/'source-ownership.png');mask.save(D/'registered-ownership.png');plate=Image.new('RGBA',source.size);plate.paste(source,(0,0),mask);plate.save(D/'hair-registered.png')
spec=importlib.util.spec_from_file_location('same_v5_composer',V.parent/'run-east-hat-approved-v5/build_approved.py');std=importlib.util.module_from_spec(spec);spec.loader.exec_module(std)
body=Image.open(HAT/'original-body.png').convert('RGBA');nearhat=Image.open(HAT/'hat-near.png').convert('RGBA');farhat=Image.open(HAT/'hat-far.png').convert('RGBA');comp,_=std.compose(body,nearhat,farhat,plate);comp.save(D/'hair-hat-composite.png')
board=Image.new('RGB',(1740,390),(220,228,234));dr=ImageDraw.Draw(board)
for j,(im,title) in enumerate([(source,'generated source'),(plate,'source-owned hair only'),(comp,'original body + formal hat + hair')]):
 bg=Image.new('RGBA',im.size,(220,228,234,255));bg.alpha_composite(im);crop=bg.crop((115,185,405,370)).resize((580,370),Image.Resampling.NEAREST);board.paste(crop.convert('RGB'),(j*580,20));dr.text((j*580+3,2),title,fill='black')
board.save(D/'source-mask-composite-head-2x.png')
print('idle frozen hair candidate built, zero part registration')
