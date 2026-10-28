"""Actual-asset regression for the reported ear opening, not a visual-approval gate."""
from pathlib import Path
import argparse, hashlib, json
from PIL import Image, ImageChops
P=Path(__file__).resolve().parent
OLD=P.parent/'hoe-west-hat-v2/sample-build'
ISSUE=P.parent/'hoe-west-hat-v2/feedback/2026-10-28-key2-ear-gap/issue.json'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def check(sample):
    sample=sample.resolve()
    old=json.loads((OLD/'sample.json').read_text());new=json.loads(sample.read_text());base=sample.parent
    checks={};points=[tuple(w['xy']) for w in json.loads(ISSUE.read_text())['witness_pixels']]
    before=old['frames'][2];frame=new['frames'][2]
    images={s:Image.open(base/frame['states'][s]['file']).convert('RGBA') for s in ['bare','hair','hair_hat']}
    checks['hair_only_covers_all_reported_points']=all(images['hair'].getpixel(xy)!=images['bare'].getpixel(xy) for xy in points)
    full_hair=Image.open(base/frame['parts']['hair']['registered_file']).convert('RGBA')
    original_overlay=Image.alpha_composite(images['bare'],full_hair)
    checks['hair_hat_restores_original_posterior_hair_at_all_reported_points']=all(images['hair_hat'].getpixel(xy)==original_overlay.getpixel(xy) for xy in points)
    for a,b in zip(old['frames']+[old['idle']],new['frames']+[new['idle']]):
        checks[a['pose_id']+'_timing_preserved']=a.get('duration_ms')==b.get('duration_ms')
        for state in ['bare','hair','hat','hair_hat']:
            if a['pose_id']=='hoe_west_key_2' and state=='hair_hat':continue
            checks[a['pose_id']+'_'+state+'_unchanged']=sha(OLD/a['states'][state]['file'])==sha(base/b['states'][state]['file'])
    if base!=OLD:
        repair=json.loads((base/'ear-repair/manifest.json').read_text())
        original=Image.open(base/frame['parts']['hair']['registered_file']).convert('RGBA')
        oldhair=Image.open(OLD/before['parts']['hair_under_hat']['registered_file']).convert('RGBA')
        hair=Image.open(base/frame['parts']['hair_under_hat']['registered_file']).convert('RGBA')
        selection=Image.open(base/'ear-repair/posterior-view-selection.png').convert('L')
        checks['replacement_is_exact_source_selection_no_paint_or_alpha_blending']=hair.tobytes()==Image.composite(original,oldhair,selection).tobytes()
        checks['full_frame_no_translation_or_scaling']=repair['runtime_placement_px']==[0,0] and repair['local_scale']==[1,1]
        checks['all_declared_inputs_match']=all(sha(base/rel)==digest for rel,digest in new['inputs'].items())
        near=Image.open(base/frame['parts']['hat']['near_file']).convert('RGBA');far=Image.open(base/frame['parts']['hat']['far_file']).convert('RGBA')
        rendered=Image.alpha_composite(Image.alpha_composite(Image.alpha_composite(far,images['bare']),hair),near)
        support=ImageChops.lighter(ImageChops.lighter(near.getchannel('A'),far.getchannel('A')),hair.getchannel('A')).point(lambda a:255 if a else 0)
        expected=images['bare'].copy();expected.paste(rendered,(0,0),support)
        checks['actual_bake_matches_independent_layer_composition']=expected.tobytes()==images['hair_hat'].tobytes()
    return {'sample':str(sample),'checks':checks,'passed':all(checks.values()),'scope':'Six reported ear points plus source/preservation checks; native visual review is required separately.'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--sample',type=Path,default=P/'sample-build/sample.json');p.add_argument('--output',type=Path);a=p.parse_args()
    result=check(a.sample);out=json.dumps(result,indent=2)+'\n'
    if a.output:a.output.write_text(out)
    print(out);raise SystemExit(0 if result['passed'] else 1)
