"""Whole-frame registration and explicitly reviewed background-only alpha extraction.
No part transforms, recoloring, anatomy drawing, or resampling.
"""
from pathlib import Path
from collections import deque
import hashlib,json
from PIL import Image,ImageFilter,ImageChops
ROOT=Path(__file__).resolve().parent
DIRECTIONS=['south','west','east','north']
OFFSETS={'south':(26,0),'west':(0,0),'east':(0,10),'north':(-26,0)}

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def extract_background(frame):
    # Human review found unrelated alpha noise outside the single connected body.
    # Within this complete unaccessorized silhouette select its opaque connected
    # component, preserving every original pixel plus a two-pixel alpha fringe.
    w,h=frame.size;a=frame.getchannel('A');remaining=a.point(lambda v:255 if v>=128 else 0)
    px=remaining.load();components=[]
    for y in range(h):
        for x in range(w):
            if not px[x,y]:continue
            q=deque([(x,y)]);px[x,y]=0;points=[]
            while q:
                xx,yy=q.popleft();points.append((xx,yy))
                for nx,ny in [(xx-1,yy),(xx+1,yy),(xx,yy-1),(xx,yy+1)]:
                    if 0<=nx<w and 0<=ny<h and px[nx,ny]:px[nx,ny]=0;q.append((nx,ny))
            components.append(points)
    main=max(components,key=len)
    assert len(main)>95000 and all(60<=x<=450 and 100<=y<=735 for x,y in main)
    core=Image.new('L',frame.size)
    for p in main:core.putpixel(p,255)
    mask=core.filter(ImageFilter.MaxFilter(5));out=frame.copy();out.putalpha(ImageChops.multiply(a,mask))
    return out,mask,{'main_opaque_pixels':len(main),'discarded_disconnected_opaque_pixels':sum(map(len,components))-len(main),'retained_alpha_fringe_px':2,'method':'manually reviewed complete body component alpha>=128 + 2px original-alpha fringe; source retained intact'}

def build():
    records=[];idle=Image.open(ROOT/'sources/idle-a-v2.png').convert('RGBA');idle_sheet=Image.new('RGBA',(2048,768))
    for di,d in enumerate(DIRECTIONS):
        entries=[('idle',0,'sources/idle-a-v2.png',di)]
        if d=='west':
            entries += [('walk',i,f'../walk-west-proof-v1/registered/v5/walk_w_{i}.png',None) for i in range(4)]
        else:
            v=1 if d=='south' else 2
            entries += [('walk',i,f'sources/walk-{d}-a-v{v}.png',i) for i in range(4)]
        walk_sheet=Image.new('RGBA',(2048,768))
        for action,i,source,cell in entries:
            if d=='east' and action=='walk':source='sources/walk-east-a-v5.png'
            path=ROOT/source;im=Image.open(path).convert('RGBA')
            original=im if cell is None else im.crop((512*cell,0,512*(cell+1),768))
            meta={};frame=original
            if not (d=='west' and action=='walk'):
                frame,mask,meta=extract_background(frame);mask.save(ROOT/f'masks/source_background_{action}_{d}_{i}.png')
            dx,dy=OFFSETS[d]
            if action=='idle' and d=='east':dy=0
            if action=='walk' and d=='west':dx=dy=0
            if action=='walk' and d=='east':dx,dy=-8,0
            registered=Image.new('RGBA',(512,768));registered.paste(frame,(dx,dy))
            out=ROOT/f'registered/{action}_{d}_{i}.png';registered.save(out)
            records.append({'pose_id':f'{action}_{d}_{i}','source':source,'source_sha256':sha(path),'source_cell':cell,'whole_frame_translation_px':[dx,dy],'scale':1,'output':str(out.relative_to(ROOT)),'sha256':sha(out),'background_extraction':meta})
            if action=='idle':idle_sheet.paste(registered,(di*512,0))
            else:walk_sheet.paste(registered,(i*512,0))
        walk_sheet.save(ROOT/f'registered/walk-{d}-a-sheet.png')
    idle_sheet.save(ROOT/'registered/idle-a-sheet.png')
    (ROOT/'registered/registration.json').write_text(json.dumps({'schema_version':2,'script_sha256':sha(Path(__file__)),'canvas_px':[512,768],'root_anchor_px':[256,708],'placement':'whole frame integer translation only; body silhouettes reviewed before background extraction','frames':records},indent=2)+'\n')
    print('Registered 20 poses; no part scaling or per-part shifts.')
if __name__=='__main__':build()
