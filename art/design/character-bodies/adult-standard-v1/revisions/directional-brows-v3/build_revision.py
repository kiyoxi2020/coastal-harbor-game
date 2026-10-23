#!/usr/bin/env python3
"""Localized GPT-authored side brows, retaining every other approved master pixel."""
from pathlib import Path
from PIL import Image, ImageDraw
import hashlib,json
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[5]
PARENT=HERE.parent/'front-eyelids-brows-v2'
HEAD=ROOT/'art/design/character-head-proof-v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def build():
    source=Image.open(PARENT/'source.png').convert('RGBA');edited=Image.open(HERE/'gpt-side-brows.png').convert('RGBA');assert source.size==edited.size==(2048,768)
    regions={'west_brow':[[688,231],[742,231],[742,258],[688,258]],'east_brow':[[1314,229],[1372,229],[1372,255],[1314,255]]}
    mask=Image.new('L',source.size);draw=ImageDraw.Draw(mask)
    for points in regions.values():draw.polygon([tuple(p) for p in points],fill=255)
    revised=source.copy();revised.paste(edited,(0,0),mask);revised.putalpha(source.getchannel('A'))
    sp=source.load();rp=revised.load();mp=mask.load()
    assert all(sp[x,y]==rp[x,y] for y in range(768) for x in range(2048) if not mp[x,y])
    for box in [(0,0,512,768),(1536,0,2048,768)]:assert source.crop(box).tobytes()==revised.crop(box).tobytes()
    revised.save(HERE/'source.png');mask.save(HERE/'authorized-edit-mask.png')
    proof=HERE/'proof';proof.mkdir(exist_ok=True);config=json.loads((HEAD/'semantic-masks.json').read_text())
    for i,d in enumerate(['south','west','east','north']):
        body=revised.crop((i*512,0,(i+1)*512,768));body.save(HERE/(d+'.png'))
        for state in ['bare','hair','hat','hair_hat']:
            result=body.copy()
            if state in ['hair','hair_hat']:
                hair=Image.open(HEAD/'proof'/('hair_'+d+'.png'));owned=Image.open(HEAD/'proof'/('hair-mask_'+d+'.png'))
                if state=='hair_hat':
                    cap=Image.new('L',body.size);ImageDraw.Draw(cap).polygon([tuple(p) for p in config['hat_polygons'][d]],fill=255);hair=hair.copy();owned=owned.copy();hair.paste((0,0,0,0),(0,0,512,768),cap);owned.paste(0,(0,0,512,768),cap)
                result.paste(hair,(0,0),owned)
            if state in ['hat','hair_hat']:result.paste(Image.open(HEAD/'proof'/('hat_'+d+'.png')),(0,0),Image.open(HEAD/'proof'/('hat-mask_'+d+'.png')))
            result.save(proof/(state+'_'+d+'.png'))
            if d in ['south','north']:assert result.tobytes()==Image.open(PARENT/'proof'/(state+'_'+d+'.png')).tobytes()
    metrics={}
    for name,box in [('west',[688,231,742,258]),('east',[1314,229,1372,255])]:
        def brow_pixels(im):
            crop=im.crop(tuple(box));return sum(1 for y in range(crop.height) for x in range(crop.width) if 40<crop.getpixel((x,y))[0]<170 and 15<crop.getpixel((x,y))[1]<110)
        metrics[name]={'old_brown_pixels':brow_pixels(source),'new_brown_pixels':brow_pixels(revised)}
        assert metrics[name]['new_brown_pixels']>metrics[name]['old_brown_pixels']
    inputs={'parent_source_sha256':sha(PARENT/'source.png'),'gpt_source_sha256':sha(HERE/'gpt-side-brows.png'),'source_sha256':sha(HERE/'source.png'),'mask_sha256':sha(HERE/'authorized-edit-mask.png'),'builder_sha256':sha(Path(__file__)),'head_component_manifest_sha256':sha(HEAD/'manifest.json'),'frames':{p.name:sha(p) for p in sorted(proof.glob('*.png'))},'regions':regions}
    manifest={**inputs,'artifact_digest':hashlib.sha256(json.dumps(inputs,sort_keys=True).encode()).hexdigest(),'status':'candidate; review.json records native checks and user status','validation':{'non_edited_rgba_unchanged':True,'source_alpha_unchanged':True,'front_and_back_and_8_corresponding_frames_unchanged':True,'brow_pixels':metrics}}
    (HERE/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');print('DIRECTIONAL_BROWS_LOCALIZED_16_FRAMES_OK',metrics)
if __name__=='__main__':build()
