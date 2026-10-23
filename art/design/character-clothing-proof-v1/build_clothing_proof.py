#!/usr/bin/env python3
"""GPT garment pixels + semantic ownership, no anatomy painting or part transforms."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter,ImageChops
from itertools import product
import json,hashlib
ROOT=Path(__file__).resolve().parents[3];ART=Path(__file__).resolve().parent
BODY=ROOT/'art/design/character-bodies/adult-standard-v1';HEAD=ROOT/'art/design/character-head-proof-v1'
DIRECTIONS=['south','west','east','north']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def poly(size,polygons):
    result=Image.new('L',size);draw=ImageDraw.Draw(result)
    for points in polygons:draw.polygon([tuple(p) for p in points],fill=255)
    return result
def build():
    config=json.loads((ART/'semantic-masks.json').read_text());selection=json.loads((BODY/'selection.json').read_text());path=BODY/selection['active_revision']['source'];assert sha(path)==selection['active_revision']['source_sha256']
    master=Image.open(path).convert('RGBA');proof=ART/'proof';parts=ART/'parts';proof.mkdir(exist_ok=True);parts.mkdir(exist_ok=True)
    sources={k:Image.open(ART/(k+'-worn.png')).convert('RGBA') for k in ['top','pants','shoes']};assert all(s.size==(2048,768) for s in sources.values())
    frames={};interfaces={}
    head_config=json.loads((HEAD/'semantic-masks.json').read_text())
    for i,d in enumerate(DIRECTIONS):
        body=master.crop((i*512,0,(i+1)*512,768));hands=poly(body.size,config['protected_hands'][d]);neck_region=poly(body.size,[config['protected_neck'][d]])
        neck_skin=Image.new('L',body.size);bp=body.load();ns=neck_skin.load();nr=neck_region.load()
        for y in range(355,407):
            for x in range(512):
                r,g,b,a=bp[x,y]
                if nr[x,y] and r>150 and r>g+40 and g>b+10:ns[x,y]=255
        neck_near=neck_skin.filter(ImageFilter.MaxFilter(5));neck=neck_skin.copy();nn=neck_near.load();nk=neck.load()
        for y in range(355,407):
            for x in range(512):
                if nr[x,y] and nn[x,y] and max(bp[x,y][:3])<90:nk[x,y]=255
        layers={}
        for kind,atlas in sources.items():
            image=atlas.crop((i*512,0,(i+1)*512,768));semantic=poly(body.size,config[kind][d]);owned=semantic.copy()
            if kind=='top':
                # Palette only assists this reviewed clothing outline; never searches body/face.
                core=Image.new('L',body.size);cp=core.load();ip=image.load()
                for y in range(360,545):
                    for x in range(512):
                        r,g,b,a=ip[x,y]
                        if a>=200 and b>r*1.12 and b>g*1.025:cp[x,y]=255
                nearby=core.filter(ImageFilter.MaxFilter(9));old=body.load();sp=semantic.load();np=nearby.load();op=owned.load()
                for y in range(768):
                    for x in range(512):
                        if not sp[x,y]:continue
                        r,g,b,a=ip[x,y];br,bg,bb,ba=old[x,y]
                        old_fabric=br>165 and bg>145 and br-bb>12 and ba>=200
                        op[x,y]=255 if cp[x,y] or (np[x,y] and max(r,g,b)<105) or old_fabric else 0
            if kind in ['top','pants']:
                owned=ImageChops.subtract(owned,hands)
                if kind=='top':owned=ImageChops.subtract(owned,neck)
                if kind=='pants':
                    op=owned.load();bp=body.load()
                    for y in range(519,546):
                        for x in range(512):
                            r,g,b,a=bp[x,y]
                            if r>180 and g>150 and r-b>12:op[x,y]=0
            if kind=='top':owned.paste(0,(0,0,512,360)) # complete head belongs to approved body
            # Exposed ankle/foot skin is not a shoe or trouser surface. Keeping it in
            # these layers would paint bare skin over the other selected garment.
            if kind in ['pants','shoes']:
                op=owned.load();ip=image.load()
                for y in range(519 if kind=='pants' else 620,768):
                    for x in range(512):
                        r,g,b,a=ip[x,y]
                        if r>185 and r>g+25 and g>b+12:op[x,y]=0
            # Outside outlines remain transparent even if generation has a very faint glow.
            clean=image.copy();alpha=clean.getchannel('A').point(lambda a:0 if a<200 else a);clean.putalpha(alpha)
            texture=Image.new('RGBA',body.size);texture.paste(clean,(0,0),owned)
            texture.save(parts/(kind+'_'+d+'.png'));owned.save(parts/(kind+'-owner_'+d+'.png'));layers[kind]=(texture,owned)
        for switches in product([0,1],repeat=3):
            selected=[kind for kind,on in zip(['top','pants','shoes'],switches) if on]
            state='_'.join(selected) or 'baseline';result=body.copy();coverage=Image.new('L',body.size)
            for kind in ['pants','top','shoes']:
                if kind in selected:
                    texture,owned=layers[kind];result.paste(texture,(0,0),owned);coverage=ImageChops.lighter(coverage,owned)
            rp=result.load();bp=body.load();cov=coverage.load();assert all(rp[x,y]==bp[x,y] for y in range(768) for x in range(512) if not cov[x,y])
            assert result.crop((0,0,512,360)).tobytes()==body.crop((0,0,512,360)).tobytes(),(d,state,'head changed')
            # Entire exposed hand region stays byte-identical to the approved mother template.
            assert not ImageChops.multiply(ImageChops.difference(result,body).convert('RGB').convert('L'),hands).getbbox()
            p=proof/(state+'_'+d+'.png');result.save(p);frames[p.stem]={'sha256':sha(p),'non_owned_rgba_unchanged':True,'hands_unchanged':True,'head_unchanged':True}
            if len(selected)==3:
                for head_state in ['hair','hair_hat']:
                    dressed=result.copy();hair=Image.open(HEAD/'proof'/('hair_'+d+'.png'));hair_owner=Image.open(HEAD/'proof'/('hair-mask_'+d+'.png'))
                    if head_state=='hair_hat':
                        cap=poly(body.size,[head_config['hat_polygons'][d]]);hair=hair.copy();hair_owner=hair_owner.copy();hair.paste((0,0,0,0),(0,0,512,768),cap);hair_owner.paste(0,(0,0,512,768),cap)
                    dressed.paste(hair,(0,0),hair_owner)
                    if head_state=='hair_hat':dressed.paste(Image.open(HEAD/'proof'/('hat_'+d+'.png')),(0,0),Image.open(HEAD/'proof'/('hat-mask_'+d+'.png')))
                    p=proof/('full_'+head_state+'_'+d+'.png');dressed.save(p);frames[p.stem]={'sha256':sha(p),'composition':'full clothes + same approved head layers'}
        interfaces[d]={'body_root':json.loads((BODY/'registration/registration.json').read_text())['frames'][d]['root_anchor'],'part_canvas':[512,768],'part_transforms':'identity; no resize/translation','owned_boxes':{k:list(mask.getbbox()) for k,(_,mask) in layers.items()}}
    inputs={'template_id':'adult-standard-v1','active_revision':selection['active_revision']['id'],'source_sha256':sha(path),'selection_sha256':sha(BODY/'selection.json'),'mask_sha256':sha(ART/'semantic-masks.json'),'builder_sha256':sha(Path(__file__)),'renderer_sha256':sha(ART/'render_review.gd'),'head_manifest_sha256':sha(HEAD/'manifest.json'),'sources':{k:sha(ART/(k+'-worn.png')) for k in sources},'parts':{p.name:sha(p) for p in sorted(parts.glob('*.png'))},'frames':frames,'interfaces':interfaces}
    manifest={**inputs,'artifact_digest':hashlib.sha256(json.dumps(inputs,sort_keys=True).encode()).hexdigest(),'status':'first clothing set candidate; no general naked body or cross-body compatibility; review.json records visual results'}
    (ART/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');print('CLOTHING_PROOF_BUILT',len(frames),'frames, geometry/head/hand invariants checked')
if __name__=='__main__':build()
