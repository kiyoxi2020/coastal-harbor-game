#!/usr/bin/env python3
"""Crop GPT component pixels under reviewed semantic regions; never paint anatomy."""
from pathlib import Path
from PIL import Image, ImageDraw
import json, hashlib
ROOT=Path(__file__).resolve().parents[3]
ART=Path(__file__).resolve().parent
BODY=ROOT/'art/design/character-bodies/adult-standard-v1'
OUT=ROOT/'godot2d/assets/characters/adult-standard-v1/head-proof'
DIRECTIONS=['south','west','east','north']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def layer(atlas, index, points, palette=False):
    source=atlas.crop((index*512,0,(index+1)*512,768))
    semantic=Image.new('L',source.size);ImageDraw.Draw(semantic).polygon([tuple(p) for p in points],fill=255)
    owned=Image.new('L',source.size)
    sp=source.load();sem=semantic.load();op=owned.load()
    for y in range(768):
        for x in range(512):
            r,g,b,a=sp[x,y]
            if sem[x,y] and a>=200 and (not palette or (r<200 and g<150 and b<115)):
                op[x,y]=255
    texture=Image.new('RGBA',source.size)
    # Copy entire RGBA source pixel exactly, rather than alpha-blending it a second time.
    texture.paste(source,(0,0),owned)
    return texture, owned

def build():
    config=json.loads((ART/'semantic-masks.json').read_text())
    hair_atlas=Image.open(ART/config['hair_source']).convert('RGBA')
    hat_atlas=Image.open(ART/'hat-worn-v1.png').convert('RGBA') if config['hat_polygons'] else None
    OUT.mkdir(parents=True,exist_ok=True)
    proof=ART/'proof';proof.mkdir(exist_ok=True)
    meta={'template_id':'adult-standard-v1','source_sha256':sha(BODY/'source.png'),'mask_sha256':sha(ART/'semantic-masks.json'),'builder_sha256':sha(Path(__file__)),'registration_sha256':sha(BODY/'registration/registration.json'),'native_renderer_sha256':sha(ART/'render_review.gd'),'native_verifier_sha256':sha(ART/'verify_native_scene.gd'),'review_scene_sha256':sha(ROOT/'godot2d/scenes/reviews/character_head_proof.tscn'),'sources':{'hair':sha(ART/config['hair_source'])},'frames':{},'status':'candidate; see digest-bound review.json; not user accepted'}
    if hat_atlas:meta['sources']['hat']=sha(ART/'hat-worn-v1.png')
    for i,d in enumerate(DIRECTIONS):
        body=Image.open(BODY/'registration'/(d+'.png')).convert('RGBA')
        hair,hair_mask=layer(hair_atlas,i,config['hair_polygons'][d],True)
        hair.save(proof/('hair_'+d+'.png'));hair_mask.save(proof/('hair-mask_'+d+'.png'))
        variants={'bare':[], 'hair':[(hair,hair_mask)]}
        if hat_atlas:
            hat,hat_mask=layer(hat_atlas,i,config['hat_polygons'][d])
            hat.save(proof/('hat_'+d+'.png'));hat_mask.save(proof/('hat-mask_'+d+'.png'))
            # The semantic cap volume includes hair tucked inside the hat, not just
            # visible hat-surface pixels. It follows that direction's brim/ear cutout.
            cap_volume=Image.new('L',body.size)
            ImageDraw.Draw(cap_volume).polygon([tuple(p) for p in config['hat_polygons'][d]],fill=255)
            tucked_hair=hair.copy();tucked_mask=hair_mask.copy()
            tucked_hair.paste((0,0,0,0),(0,0,512,768),cap_volume)
            tucked_mask.paste(0,(0,0,512,768),cap_volume)
            tucked_hair.save(proof/('hair-under-hat_'+d+'.png'))
            variants.update({'hat':[(hat,hat_mask)],'hair_hat':[(tucked_hair,tucked_mask),(hat,hat_mask)]})
        for state,parts in variants.items():
            result=body.copy();coverage=Image.new('L',body.size)
            for texture,owned in parts:
                result.paste(texture,(0,0),owned)
                coverage.paste(255,(0,0),owned)
            # Exposed body/face pixels outside real part ownership are immutable.
            rp=result.load();bp=body.load();cp=coverage.load()
            assert all(rp[x,y]==bp[x,y] for y in range(768) for x in range(512) if not cp[x,y])
            path=OUT/(state+'_'+d+'.png');result.save(path)
            result.save(proof/(state+'_'+d+'.png'))
            meta['frames'][state+'_'+d]={'sha256':sha(path),'non_owned_rgba_unchanged':True,'coverage_pixels':sum(coverage.histogram()[1:])}
    meta['part_hashes']={p.name:sha(p) for p in sorted(proof.glob('*.png')) if p.name.startswith(('hair_', 'hat_', 'hair-mask_', 'hat-mask_', 'hair-under-hat_'))}
    inputs={'verifier':meta['native_verifier_sha256'],'registration':meta['registration_sha256'],'renderer':meta['native_renderer_sha256'],'scene':meta['review_scene_sha256'],'parts':meta['part_hashes'],'source':meta['source_sha256'],'mask':meta['mask_sha256'],'builder':meta['builder_sha256'],'sources':meta['sources'],'frames':meta['frames']}
    meta['artifact_digest']=hashlib.sha256(json.dumps(inputs,sort_keys=True).encode()).hexdigest()
    (ART/'manifest.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
    print('BUILT',len(meta['frames']),'draft states; immutable non-owned body RGBA verified')
if __name__=='__main__':build()
