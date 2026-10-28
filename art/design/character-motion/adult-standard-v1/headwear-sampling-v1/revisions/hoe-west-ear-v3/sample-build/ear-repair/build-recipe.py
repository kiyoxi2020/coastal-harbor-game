"""Reuse a same-pose GPT posterior hair view without moving or painting pixels."""
from pathlib import Path
import copy, hashlib, importlib.util, json, shutil
from PIL import Image, ImageChops, ImageDraw
P=Path(__file__).resolve().parent
HEAD=P.parents[1];ROOT=P.parents[6];OLD=P.parent/'hoe-west-hat-v2/sample-build'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def js(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')

def build():
    old=json.loads((OLD/'sample.json').read_text())
    for rel,digest in old['inputs'].items():
        if sha(OLD/rel)!=digest:raise ValueError('Frozen baseline changed: '+rel)
    out=P/'sample-build'
    if out.exists():raise ValueError('Do not overwrite a delivered candidate.')
    shutil.copytree(OLD,out);s=copy.deepcopy(old);f=s['frames'][2];d=out/'ear-repair';d.mkdir()
    original=Image.open(out/f['parts']['hair']['registered_file']).convert('RGBA')
    compact=Image.open(out/f['parts']['hair_under_hat']['registered_file']).convert('RGBA')
    # Authored interface: top buried under the real brim; the left seam runs
    # through the ear opening. Select the complete posterior view, including
    # its natural alpha edge. This is source selection, never a body erase.
    polygon=[(645,600),(950,680),(1020,900),(620,900),(620,820),(660,790),(700,740),(700,670)]
    selection=Image.new('L',original.size);ImageDraw.Draw(selection).polygon(polygon,fill=255)
    selection.save(d/'posterior-view-selection.png')
    hair=Image.composite(original,compact,selection);hair.save(d/'hair-registered.png')
    original_mask=ImageChops.darker(selection,original.getchannel('A').point(lambda a:255 if a else 0))
    compact_mask=ImageChops.darker(ImageChops.invert(selection),compact.getchannel('A').point(lambda a:255 if a else 0))
    original_mask.save(d/'original-posterior-ownership.png');compact_mask.save(d/'compact-front-ownership.png')
    body=Image.open(out/f['states']['bare']['file']).convert('RGBA');near=Image.open(out/f['parts']['hat']['near_file']).convert('RGBA');far=Image.open(out/f['parts']['hat']['far_file']).convert('RGBA')
    rendered=Image.alpha_composite(Image.alpha_composite(Image.alpha_composite(far,body),hair),near)
    support=ImageChops.lighter(ImageChops.lighter(near.getchannel('A'),far.getchannel('A')),hair.getchannel('A')).point(lambda a:255 if a else 0)
    result=body.copy();result.paste(rendered,(0,0),support);result.save(d/'hair-hat-composite.png');support.save(d/'edit-support.png')
    alpha=hair.getchannel('A');na=near.getchannel('A')
    ImageChops.multiply(alpha,ImageChops.invert(na)).save(d/'visible-hair.png');ImageChops.multiply(alpha,na).save(d/'occluded-hair.png')
    manifest={'pose_id':f['pose_id'],'runtime_candidate_allowed':True,'status':'same-pose-posterior-view-reuse-candidate','native_verified':False,'user_visual_accepted':False,'runtime_placement_px':[0,0],'local_scale':[1,1],'canvas_px':list(body.size),'selection_polygon_px':polygon,'source_selection':'Exact binary replacement of compact posterior view by complete same-pose original posterior hair; no alpha blending, no body edits, no translation or scaling. Top boundary is under real near brim, left boundary in the ear opening.','sources':[{'registered_file':f['parts']['hair']['registered_file'],'sha256':sha(out/f['parts']['hair']['registered_file']),'original_source':f['parts']['hair']['source'],'source_sha256':sha(out/f['parts']['hair']['source']),'ownership':'original-posterior-ownership.png'},{'registered_file':f['parts']['hair_under_hat']['registered_file'],'sha256':sha(out/f['parts']['hair_under_hat']['registered_file']),'original_manifest':f['parts']['hair_under_hat']['extraction_manifest'],'ownership':'compact-front-ownership.png'}],'compatible_hat_manifest_sha256':f['parts']['hair_under_hat']['compatible_hat_manifest_sha256'],'baseline_sample_sha256':sha(OLD/'sample.json'),'files':{q.name:sha(q) for q in sorted(d.iterdir()) if q.is_file()}}
    js(d/'manifest.json',manifest)
    oldpart=f['parts']['hair_under_hat']
    f['parts']['hair_under_hat']={'registered_file':'ear-repair/hair-registered.png','extraction_manifest':'ear-repair/manifest.json','source_views':manifest['sources'],'placement_mode':'full_frame','offset_px':[0,0],'local_scale':[1,1],'compatible_hat_manifest_sha256':oldpart['compatible_hat_manifest_sha256'],'capability':'Compact front plus original same-pose posterior hair; exact source selection, no new anatomy.'}
    f['states']['hair_hat']={'file':'ear-repair/hair-hat-composite.png','sha256':sha(d/'hair-hat-composite.png'),'edit_mask':'ear-repair/edit-support.png'}
    f['hair_under_hat_visible']='ear-repair/visible-hair.png';f['occlusion_mask']='ear-repair/occluded-hair.png'
    f['composition']['reason']='Same frozen hat and body; compact forelock plus original same-pose posterior view, exact source pixels at zero placement.'
    s['recipe']['hair_under_hat']='chestnut-short-hoe-key2-posterior-v3';s['status']='ear-gap-repair-awaiting-user-review';s['acceptance']={'user_visual':False,'native':False,'reason':'New key2 posterior hair view; independent evidence required.'}
    shutil.copy2(__file__,d/'build-recipe.py');s['inputs']={q.relative_to(out).as_posix():sha(q) for q in sorted(out.rglob('*')) if q.is_file() and q.name not in ['sample.json','validation.json']}
    js(out/'sample.json',s);js(out/'validation.json',{'scope':'key2 hair_hat only','sample_sha256':sha(out/'sample.json'),'native_verified':False})
    cat=json.loads((HEAD/'catalog.json').read_text());js(P/'catalog-before.json',cat)
    for entry in cat['samples']:
        if entry['id']=='hoe-west':entry.update(sample=(out/'sample.json').relative_to(ROOT).as_posix(),sha256=sha(out/'sample.json'))
    js(P/'catalog.json',cat)
    print('Built candidate without changing active catalog:',out)
if __name__=='__main__':build()
