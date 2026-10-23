#!/usr/bin/env python3
"""Apply only the user's requested frontal brow and eyelid revision from GPT pixels."""
from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib
HERE=Path(__file__).resolve().parent
BODY=HERE.parents[1]
ROOT=HERE.parents[5]
HEAD=ROOT/'art/design/character-head-proof-v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def build():
    source=Image.open(BODY/'source.png').convert('RGBA')
    generated=Image.open(HERE/'eyelid-only-edit.png').convert('RGBA')
    assert source.size==generated.size==(2048,768)
    # Deliberate user-authorized feature revision, not a patch to hide a bad split.
    regions={'left_brow':[[148,237],[204,237],[204,260],[148,260]],'right_brow':[[253,237],[310,237],[310,260],[253,260]],'left_eyelid_tip':[[146,293],[153,293],[153,304],[150,307],[146,306]],'right_eyelid_tip':[[305,293],[313,293],[313,301],[310,305],[305,304]]}
    mask=Image.new('L',source.size);draw=ImageDraw.Draw(mask)
    for points in regions.values():draw.polygon([tuple(p) for p in points],fill=255)
    revised=source.copy();revised.paste(generated,(0,0),mask)
    revised.putalpha(source.getchannel('A')) # face color only; all original alpha retained.
    a,b,m=source.load(),revised.load(),mask.load()
    assert all(a[x,y]==b[x,y] for y in range(768) for x in range(2048) if not m[x,y])
    assert source.crop((512,0,2048,768)).tobytes()==revised.crop((512,0,2048,768)).tobytes()
    for box in [(158,272,201,323),(259,272,303,323),(208,328,248,351)]:assert source.crop(box).tobytes()==revised.crop(box).tobytes()
    revised.save(HERE/'source.png');mask.save(HERE/'authorized-edit-mask.png');front=revised.crop((0,0,512,768));front.save(HERE/'south.png')
    proof=HERE/'proof';proof.mkdir(exist_ok=True)
    parent_frames=json.loads((HEAD/'manifest.json').read_text())['frames']
    for state in ['bare','hair','hat','hair_hat']:
        result=front.copy()
        if state in ['hair','hair_hat']:
            hair=Image.open(HEAD/'proof'/('hair_south.png')).convert('RGBA');owned=Image.open(HEAD/'proof/hair-mask_south.png')
            if state=='hair_hat':
                config=json.loads((HEAD/'semantic-masks.json').read_text());cap=Image.new('L',front.size);ImageDraw.Draw(cap).polygon([tuple(p) for p in config['hat_polygons']['south']],fill=255);hair=hair.copy();owned=owned.copy();hair.paste((0,0,0,0),(0,0,512,768),cap);owned.paste(0,(0,0,512,768),cap)
            result.paste(hair,(0,0),owned)
        if state in ['hat','hair_hat']:
            result.paste(Image.open(HEAD/'proof/hat_south.png'),(0,0),Image.open(HEAD/'proof/hat-mask_south.png'))
        result.save(proof/(state+'_south.png'))
        for d in ['west','east','north']:
            data=(HEAD/'proof'/(state+'_'+d+'.png')).read_bytes();(proof/(state+'_'+d+'.png')).write_bytes(data)
            assert sha(proof/(state+'_'+d+'.png'))==parent_frames[state+'_'+d]['sha256']
    metrics={}
    for name,box in {'left':[147,298,152,304],'right':[308,298,312,302]}.items():
        def dark(im):return sum(1 for p in im.crop(tuple(box)).getdata() if max(p[:3])<80)
        metrics[name]={'sample_box':box,'old_dark_pixels':dark(source),'new_dark_pixels':dark(revised)}
        assert metrics[name]['new_dark_pixels']<metrics[name]['old_dark_pixels']
    frame_hashes={p.name:sha(p) for p in sorted(proof.glob('*.png'))}
    inputs={'baseline_source_sha256':sha(BODY/'source.png'),'gpt_source_sha256':sha(HERE/'eyelid-only-edit.png'),'mask_sha256':sha(HERE/'authorized-edit-mask.png'),'builder_sha256':sha(Path(__file__)),'source_sha256':sha(HERE/'source.png'),'parent_head_manifest_sha256':sha(HEAD/'manifest.json'),'frame_hashes':frame_hashes,'regions':regions}
    manifest={**inputs,'artifact_digest':hashlib.sha256(json.dumps(inputs,sort_keys=True).encode()).hexdigest(),'revision_id':'front-eyelids-brows-v2','status':'candidate; native review pending; not user accepted','validation':{'outside_authorized_features_rgba_unchanged':True,'all_source_alpha_unchanged':True,'other_three_directions_byte_identical':True,'eye_interiors_and_nose_mouth_unchanged':True,'outer_eyelid_tip_dark_pixels':metrics}}
    (HERE/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print('FRONT_REVISION_EXACT_NON_EDITED_PIXELS_OK',metrics)
if __name__=='__main__':build()
