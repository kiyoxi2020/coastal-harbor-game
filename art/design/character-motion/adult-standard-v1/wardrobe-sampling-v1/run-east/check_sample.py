"""Verify independently extracted slots reconstruct the frozen sampled recipe."""
from pathlib import Path
import hashlib,json,sys
from PIL import Image,ImageChops

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def nonzero(im):return any(im.getdata())
def same(a,b):return all(not nonzero(c) for c in ImageChops.difference(a,b).split())
def validate(d,spec=None):
    s=spec or json.loads((d/'sample.json').read_text());n=0
    assert s['schema_version']==1 and s['template_id']=='adult-standard-v1';n+=1
    assert len(s['frames'])==4 and len({f['pose_id'] for f in s['frames']})==4;n+=1
    assert s['canvas_px']==[512,768] and s['root_anchor_px']==[256,708] and s['display_scale']==138/582;n+=1
    for name,h in s['inputs'].items():
        path=Path(name);assert not path.is_absolute() and '..' not in path.parts;assert digest(d/path)==h;n+=1
    for f in s['frames']+[s['idle']]:
        assert f['file'] in s['inputs'] and f['sha256']==digest(d/f['file']);n+=1
        old=Image.open(d/'references'/f'{f["pose_id"]}-original.png').convert('RGBA');out=Image.open(d/f['file']).convert('RGBA');body=Image.open(d/f['shared_body']).convert('RGBA');rebuild=body.copy()
        assert same(out.getchannel('A'),old.getchannel('A'));n+=1
        changed=Image.open(d/f['masks']['changed-clothing']).convert('L')
        outside=ImageChops.invert(changed)
        assert same(Image.composite(out,old,outside),old);n+=1
        for slot in ['pants','shoes']:
            l=next(x for x in f['layers'] if x['slot']==slot);part=Image.open(d/l['file']).convert('RGBA');mask=Image.open(d/f['masks'][slot]).convert('L');rebuild.paste(part,(0,0),mask)
            assert not nonzero(ImageChops.multiply(body.getchannel('A'),mask));n+=1
        top=[l for l in f['layers'] if l['slot']=='top'];assert len(top)==3;n+=1
        complete=next(l for l in top if l['complete_source_no_hand_holes']);assert complete['source'] in s['inputs'];n+=1
        for l in top:
            part=Image.open(d/l['file']).convert('RGBA');mask=Image.open(d/l['visible_mask']).convert('L');rebuild.paste(part,(0,0),mask)
            src=Image.open(d/l['source']).convert('RGBA')
            assert same(part.convert('RGB'),src.convert('RGB'));n+=1
        rebuild.putalpha(Image.open(d/f['frame_alpha']).convert('L'));assert same(out,rebuild);n+=1
        assert not nonzero(ImageChops.multiply(body.getchannel('A'),Image.open(d/f['masks']['top-visible']).convert('L')));n+=1
    # Negative capability cases: absent raw source, changed pixels and traversal
    # cannot silently become a valid sampled recipe.
    bad=json.loads(json.dumps(s));first=next(iter(bad['inputs']));bad['inputs'][first]='0'*64
    try:validate_inputs(d,bad);raise RuntimeError('changed input accepted')
    except AssertionError:n+=1
    bad=json.loads(json.dumps(s));bad['inputs']['../escape.png']='0'*64
    try:validate_inputs(d,bad);raise RuntimeError('traversal accepted')
    except AssertionError:n+=1
    return n
def validate_inputs(d,s):
    for name,h in s['inputs'].items():
        p=Path(name);assert not p.is_absolute() and '..' not in p.parts;assert digest(d/p)==h
if __name__=='__main__':print('PASS',validate(Path(sys.argv[1]).resolve()),'assertions')
