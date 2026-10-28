from pathlib import Path
import json,hashlib,sys
from PIL import Image,ImageDraw
d=Path(sys.argv[1]).resolve();s=json.loads((d/'sample.json').read_text());frames=[s['idle']]+s['frames']
rows=[(1,(225,225,213)),(1,(28,30,35)),(2,(225,225,213)),(2,(28,30,35))]
board=Image.new('RGB',(5*270,1250),(75,75,75));draw=ImageDraw.Draw(board);y=0
for scale,bg in rows:
    h=round(768*s['display_scale'])*scale;w=round(512*s['display_scale'])*scale
    draw.text((5,y+2),f'game display {scale}x / RGB{bg}',fill='white');y+=20
    for i,f in enumerate(frames):
        cell=Image.new('RGB',(270,h+24),bg);im=Image.open(d/f['file']).convert('RGBA').resize((w,h),Image.Resampling.NEAREST);cell.paste(im,((270-w)//2,20),im);ImageDraw.Draw(cell).text((5,2),f['pose_id'],fill=(115,115,115));board.paste(cell,(270*i,y))
    y+=h+24
board.crop((0,0,1350,y)).save(d/'evidence/display-1x-2x-light-dark.png')
parts=Image.new('RGB',(6*256,5*400),(215,215,205));draw=ImageDraw.Draw(parts)
for j,f in enumerate(frames):
    files=[f['shared_body']]+[l['file'] for l in f['layers']]
    for i,path in enumerate(files):
        im=Image.open(d/path).convert('RGBA').resize((256,384),Image.Resampling.NEAREST);parts.paste(im,(i*256,j*400+16),im);draw.text((i*256+2,j*400+2),Path(path).stem,fill='black')
parts.save(d/'evidence/independent-slot-board.png')
# Final snapshot includes every actual input, generated source, tool and mask.
s['inputs']={str(p.relative_to(d)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(d.rglob('*')) if p.is_file() and p.name not in ['sample.json','README.md','implementation-report.md'] and '__pycache__' not in str(p)}
(d/'sample.json').write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n')
print(hashlib.sha256((d/'sample.json').read_bytes()).hexdigest())
