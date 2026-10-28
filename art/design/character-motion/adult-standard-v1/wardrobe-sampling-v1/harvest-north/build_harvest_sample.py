"""Same-pose GPT garment extraction; no painting, warping or local placement.

Visible ownership, complete source ownership and occlusion are separate files.
All new RGB is copied from referenced GPT output at the identical pixel position.
"""
from PIL import Image, ImageDraw, ImageChops, ImageOps
from pathlib import Path
import hashlib, json, argparse, shutil
from audit_source_semantics import audit as audit_semantics

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
REPO=next(p for p in HERE.parents if (p/'godot2d/project.godot').exists())

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def binary(m):
    if any(n and i not in (0,255) for i,n in enumerate(m.histogram())):raise ValueError('nonbinary ownership')
    return m
def count(m):return m.histogram()[255]
def mask_polygons(size,polygons):
    m=Image.new('L',size);d=ImageDraw.Draw(m)
    for p in polygons:d.polygon([tuple(v) for v in p],fill=255)
    return m
def register(src,canvas,offset):
    x,y=offset
    if not all(isinstance(v,int) for v in offset) or min(x,y)<0 or x+src.width>canvas[0] or y+src.height>canvas[1]:raise ValueError('whole-frame bounds')
    out=Image.new('RGBA',tuple(canvas));out.paste(src,(x,y));return out
def check_exact(old,out,changed):
    if old.getchannel('A').tobytes()!=out.getchannel('A').tobytes():raise ValueError('alpha changed')
    diff=ImageChops.difference(old,out).convert('RGB')
    if ImageChops.multiply(diff,ImageOps.invert(changed).convert('RGB')).getbbox():raise ValueError('non-clothing RGBA changed')
    return {'non_clothing_rgba_changed_pixels':0,'original_alpha_identical':True}
def compose_visible(old,raws,masks):
    old=old.convert('RGBA');out=old.copy();union=Image.new('L',old.size)
    for slot,m in masks.items():
        binary(m)
        if m.size!=old.size or raws[slot].size!=old.size:raise ValueError('same-frame size required')
        if count(ImageChops.multiply(union,m)):raise ValueError('slot ownership overlap')
        raw=raws[slot].convert('RGBA')
        if count(ImageChops.multiply(m,raw.getchannel('A').point(lambda a:255 if a==0 else 0))):raise ValueError('missing GPT surface under visible cloth')
        raw.putalpha(old.getchannel('A'));out=Image.composite(raw,out,m);union=ImageChops.lighter(union,m)
    check_exact(old,out,union);return out
def validate_structure(s):
    if s.get('schema_version')!=1 or s.get('status')!='sampled-not-exhaustive':raise ValueError('sample schema/status')
    if set(s.get('recipe',{}).get('slots',{}))!={'top','pants','shoes'}:raise ValueError('three slots required')
    fs=s.get('frames',[])
    if len(fs)!=4 or len({f.get('pose_id') for f in fs})!=4 or len({f.get('phase') for f in fs})!=4:raise ValueError('four distinct poses/phases required')
    for f in fs+[s.get('idle',{})]:
        if not f.get('file') or len(f.get('sha256',''))!=64:raise ValueError('file/hash required')
    if any(not isinstance(f.get('duration_ms'),int) or f['duration_ms']<=0 for f in fs):raise ValueError('duration')

def intersect(*ms):
    out=ms[0]
    for m in ms[1:]:out=ImageChops.multiply(out,m)
    return out
def material(old,slot):
    r,g,b,a=old.convert('RGBA').split()
    if slot=='top':
        return intersect(ImageChops.subtract(b,r).point(lambda v:255 if v>6 else 0),ImageChops.subtract(b,g).point(lambda v:255 if v>0 else 0),a.point(lambda v:255 if v>=220 else 0))
    if slot=='pants':
        return intersect(ImageChops.subtract(g,b).point(lambda v:255 if v>6 else 0),ImageChops.subtract(g,r).point(lambda v:255 if v<9 else 0),ImageChops.subtract(r,g).point(lambda v:255 if v<23 else 0),g.point(lambda v:255 if v>35 else 0),r.point(lambda v:255 if v<180 else 0),a.point(lambda v:255 if v>=220 else 0))
    return intersect(ImageChops.subtract(r,g).point(lambda v:255 if v>24 else 0),ImageChops.subtract(g,b).point(lambda v:255 if v>4 else 0),r.point(lambda v:255 if v<180 else 0),a.point(lambda v:255 if v>=220 else 0))

SPECS={
 'hoe-west':{'slots':{'top':'top03','pants':'original-pants','shoes':'original-shoes'},'changed':['top']},
 'water-south':{'slots':{'top':'original-blue-long-sleeve','pants':'pants02','shoes':'shoes04'},'changed':['pants','shoes']},
 'harvest-north':{'slots':{'top':'original-blue-long-sleeve','pants':'pants02','shoes':'original-shoes'},'changed':['pants']}}

def visible_masks(old,annotation):
    masks={}
    for slot in ['top','pants','shoes']:
        m=intersect(mask_polygons(old.size,annotation[slot]),material(old,slot))
        for p in annotation.get(slot+'_protected_polygons',[]):m=ImageChops.subtract(m,mask_polygons(old.size,[p]))
        for p in annotation.get('protected_foreground_polygons',[]):m=ImageChops.subtract(m,mask_polygons(old.size,[p]))
        if not count(m):raise ValueError('empty manually owned '+slot)
        masks[slot]=m
    return masks

def source_region(cp,slot,annotation,name):
    """Only explicitly observed hidden target surfaces are copied from GPT.
    Completing a torso can redraw an irrelevant sleeve or hem. Those pixels
    are deliberately not imported: complete source ownership is independent
    of GPT alpha, colors or its unvalidated outer silhouette.
    """
    polygons=annotation.get('hidden_surface_polygons',{}).get(slot,[])
    return intersect(mask_polygons(cp.size,polygons),cp.getchannel('A').point(lambda v:255 if v>=220 else 0))

def make_pose(d,name,phase,parent_frame=None):
    spec=SPECS[name];ann=read(d/'ownership.json')['frames'][phase]
    old=Image.open(d/f'references/original-{phase}.png').convert('RGBA')
    raw_path=d/f'sources/{phase}-full-attempt1.png'
    if phase=='idle':
        raw_path=d/'sources/idle-full-attempt2.png'
    raw=Image.open(raw_path).convert('RGBA')
    normalization=None
    if phase=='idle' and raw.size==(1024,1536):
        raw=raw.resize((512,768),Image.Resampling.NEAREST)
        normalization={'operation':'whole-frame nearest uniform density conversion','source_canvas_px':[1024,1536],'output_canvas_px':[512,768],'scale':0.5,'offset_px':[0,0],'reference_only_upsample':'references/idle-registration-reference2x.png','new_pixels_authored_by':'built-in GPT imagegen; no upsampled original is used as new garment texture'}
    if raw.size!=old.size:raise ValueError('GPT complete frame dimensions')
    masks=visible_masks(old,ann)
    surface_repairs=[]
    for i,repair in enumerate(ann.get('source_surface_repairs',[])):
        patch=Image.open(d/repair['source']).convert('RGBA');projection=None
        if patch.size!=old.size:
            if phase=='idle' and patch.size==(1024,1536) and old.size==(512,768):
                patch=patch.resize(old.size,Image.Resampling.NEAREST);projection={'whole_frame_scale':0.5,'resampling':'nearest','offset_px':[0,0]}
            else:raise ValueError('repair source is not same-coordinate whole frame')
        slot=repair['slot'];mask=intersect(mask_polygons(old.size,repair['polygons']),masks[slot])
        if count(intersect(mask,patch.getchannel('A').point(lambda a:255 if a==0 else 0))):raise ValueError('repair lacks same-coordinate GPT garment surface')
        mp=d/f'masks/{phase}-source-surface-repair-{i}.png';mask.save(mp)
        raw=Image.composite(patch,raw,mask)
        surface_repairs.append(dict(repair,mask=str(mp.relative_to(d)),density_projection=projection))
    raw_normal=d/f'sources/{phase}-selected-density.png';raw.save(raw_normal)
    cp_path=d/f'sources/{phase}-anchored-completion-attempt2.png'
    if not cp_path.exists():cp_path=d/f'sources/{phase}-anchored-completion-attempt1.png'
    cp=Image.open(cp_path).convert('RGBA') if cp_path.exists() else raw
    if cp.size!=old.size:
        if phase=='idle' and cp.size==(1024,1536):cp=cp.resize(old.size,Image.Resampling.NEAREST)
        else:raise ValueError('completion source dimensions')
    masks=visible_masks(old,ann)
    sources={s:(raw if s in spec['changed'] else old) for s in masks}
    rendered=compose_visible(old,sources,masks)
    changed=Image.new('L',old.size);allcloth=Image.new('L',old.size)
    layers=[];detail={};pd=d/f'parts/{phase}';pd.mkdir(parents=True,exist_ok=True)
    shared=old.copy()
    for slot in ann['slot_order']:
        m=masks[slot];allcloth=ImageChops.lighter(allcloth,m)
        if slot in spec['changed']:changed=ImageChops.lighter(changed,m)
        source_mask=source_region(cp,slot,ann,name)
        # Keep raw completion intact; visible and hidden surface provenance is
        # split explicitly. No hand-shaped cuts are made into this full source.
        complete=Image.new('RGBA',old.size);complete.paste(cp,(0,0),source_mask)
        visible_source=sources[slot].copy();visible_source.putalpha(old.getchannel('A'))
        complete=Image.composite(visible_source,complete,m)
        source_mask=ImageChops.lighter(source_mask,m)
        complete_alpha=intersect(complete.getchannel('A'),source_mask)
        complete.putalpha(complete_alpha)
        complete_path=pd/f'{slot}-complete-source.png';complete.save(complete_path)
        own_path=d/f'masks/{phase}-{slot}-source-ownership.png';source_mask.save(own_path)
        coverage_path=d/f'masks/{phase}-{slot}-visible-coverage.png';m.save(coverage_path)
        occlusion=ImageChops.subtract(source_mask,m);occ_path=d/f'masks/{phase}-{slot}-occlusion.png';occlusion.save(occ_path)
        visible=Image.new('RGBA',old.size);visible=Image.composite(complete,visible,m);vp=pd/f'{slot}-visible.png';visible.save(vp)
        shared=Image.composite(Image.new('RGBA',old.size),shared,m)
        layers.append({'id':slot,'design_id':spec['slots'][slot],'file':str(complete_path.relative_to(d)),'visible_file':str(vp.relative_to(d)),'source_ownership':str(own_path.relative_to(d)),'coverage_mask':str(coverage_path.relative_to(d)),'occlusion_mask':str(occ_path.relative_to(d)),'placement_mode':'full_frame','offset_px':[0,0],'local_scale':[1,1],'source_references':([str(raw_path.relative_to(d)) if slot in spec['changed'] else f'references/original-{phase}.png']+([str(cp_path.relative_to(d))] if cp_path.exists() and count(occlusion) else [])),'selected_density_source':str(raw_normal.relative_to(d)) if slot in spec['changed'] else f'references/original-{phase}.png','source_surface_repairs':[x for x in surface_repairs if x['slot']==slot],'visible_pixels':count(m),'retained_hidden_source_pixels':count(occlusion)})
        detail[slot]={'visible_pixels':count(m),'hidden_pixels_retained':count(occlusion),'visible_rgb_source':'GPT full adaptation' if slot in spec['changed'] else 'original same-pose approved parent','complete_source_rgb':('GPT anchored hidden donor + exact visible source' if count(occlusion) else ('GPT visible garment surface only' if slot in spec['changed'] else 'original same-pose approved garment surface only')),'target_surface':slot+' garment; same-cut profile only'}
    shared_path=pd/'shared_same_pose_foreground_and_contour.png';shared.save(shared_path)
    layers.insert(0,{'id':'shared_same_pose_foreground_and_contour','file':str(shared_path.relative_to(d)),'placement_mode':'full_frame','offset_px':[0,0],'scope':'Exact original face/skin/hands/tool/vegetables/water, original cut contour and alpha edge. Not a hidden nude body.'})
    # Reassemble actual independent slot files by binary pixel ownership. This
    # avoids multiplying the original soft alpha twice.
    rebuilt=shared.copy()
    for slot in ann['slot_order']:
        layer=Image.open(pd/f'{slot}-visible.png').convert('RGBA');rebuilt=Image.composite(layer,rebuilt,masks[slot])
    if rebuilt.tobytes()!=rendered.tobytes():raise ValueError('slot reconstruction mismatch')
    ck=check_exact(old,rendered,changed)
    changed.save(d/f'masks/{phase}-changed-clothing.png')
    if phase=='idle':canvas=[512,768];offset=[0,0];pose_id='idle_'+name.rsplit('-',1)[1]+'_0';duration=200
    else:
        parent=read(d/'references/parent-candidate.json.txt');canvas=parent['canvas_px'];offset=parent_frame['whole_frame_translation_px'];pose_id=parent_frame['pose_id'];duration=parent_frame['duration_ms']
    baked=register(rendered,canvas,offset);fp=d/f'baked/{pose_id}.png';baked.save(fp)
    original_registered=register(old,canvas,offset);registered_mask=Image.new('L',tuple(canvas));registered_mask.paste(changed,tuple(offset));check_exact(original_registered,baked,registered_mask)
    return {'pose_id':pose_id,'phase':phase,'duration_ms':duration,'file':str(fp.relative_to(d)),'sha256':sha(fp),'source_references':[f'references/original-{phase}.png',str(raw_path.relative_to(d)),str(cp_path.relative_to(d)) if cp_path.exists() else str(raw_path.relative_to(d))],'whole_frame_translation_px':offset,'source_box_px':[0,0,old.width,old.height],'layers':layers,'changed_clothing_mask':f'masks/{phase}-changed-clothing.png','selected_density_base_source':str(raw_path.relative_to(d)),'source_surface_repairs':surface_repairs,'density_normalization':normalization},dict(ck,slot_reconstruction_rgba_exact=True,slots=detail,registered_non_clothing_rgba_changed_pixels=0)

def build(name):
    if name not in SPECS:raise ValueError('unsupported sample')
    d=BASE/name;parent=read(d/'references/parent-candidate.json.txt');spec=SPECS[name]
    frames=[];checks={}
    for f in parent['frames']:
        out,ck=make_pose(d,name,f['phase'],f);frames.append(out);checks[f['phase']]=ck
    idle,ck=make_pose(d,name,'idle');checks['idle']=ck
    idle.update({'canvas_px':[512,768],'root_anchor_px':[256,708],'display_scale':138/582,'source_density_scale_vs_idle':1})
    # Snapshot the actual builder into each independently frozen sample. Later
    # helper work for another sample cannot invalidate an already frozen one.
    shutil.copyfile(Path(__file__),d/'references/build_samples.py.txt')
    task=read(d/'task-scope.json')
    sample={'schema_version':1,'template_id':'adult-standard-v1','action_id':name.split('-')[0],'direction':name.rsplit('-',1)[1],'status':'sampled-not-exhaustive','recipe':{'id':name+'-sample-v1','slots':spec['slots'],'changed_slots':spec['changed'],'variant':'same-cut-surface-adaptation-v1'},'canvas_px':parent['canvas_px'],'root_anchor_px':parent['root_anchor_px'],'display_scale':parent['display_scale'],'source_density_scale_vs_idle':2,'frames':frames,'idle':idle,'loop':False,'review_repeat':True,'scope':'Original approved blue long-sleeve top and shoes retained; only pants02 is newly sampled here. Only this recipe and direction, four original poses plus matching idle. Independent same-cut garment surface slots with shared_same_pose_foreground_and_contour. No arbitrary cuts, hidden nude body, other combinations, directions or production capability.','source_parent':{'project_path':task['parent_candidate'],'copied_reference':'references/parent-candidate.json.txt','sha256':sha(d/'references/parent-candidate.json.txt')},'accepted':False,'native_checked':False,'inputs':{}}
    validate_structure(sample)
    write(d/'checks.json',{'schema_version':1,'status':'structural-pixel-checks-only','poses':checks,'manual_source_review_required':True,'source_semantics':audit_semantics(d),'manual_selected_surface_review_completed':True,'native_checked':False})
    # Only referenced inputs, local paths; no repository or cache walk.
    paths=[d/'ownership.json',d/'task-scope.json',d/'checks.json',d/'audit_source_semantics.py',d/'test_harvest_sample.py',d/'evidence/source-semantics-before.json',d/'evidence/repair-attempt-audit.json',d/'evidence/rejected-red-source-geometry.json']
    for sub in ['references','sources','prompts','parts','masks','baked']:
        paths.extend(p for p in (d/sub).rglob('*') if p.is_file())
    sample['inputs']={str(p.relative_to(d)):sha(p) for p in sorted(set(paths))}
    sample['artifact_digest']=hashlib.sha256(json.dumps(sample,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    write(d/'sample.json',sample)
    return sample

def validate(name):
    d=BASE/name;s=read(d/'sample.json');validate_structure(s)
    digest=s.pop('artifact_digest')
    if hashlib.sha256(json.dumps(s,sort_keys=True,separators=(',',':')).encode()).hexdigest()!=digest:raise ValueError('artifact digest')
    for rel,h in s['inputs'].items():
        if Path(rel).is_absolute() or '..' in Path(rel).parts:raise ValueError('nonlocal input')
        if sha(d/rel)!=h:raise ValueError('stale input '+rel)
    parent=read(d/'references/parent-candidate.json.txt')
    for key in ['canvas_px','root_anchor_px','display_scale','source_density_scale_vs_idle']:
        if s[key]!=parent[key]:raise ValueError('parent geometry changed')
    for frame,pf in zip(s['frames'],parent['frames']):
        for k in ['pose_id','phase','duration_ms','whole_frame_translation_px','source_box_px']:
            if frame[k]!=pf[k]:raise ValueError('parent pose/registration/timing changed '+k)
        if sha(d/frame['file'])!=frame['sha256']:raise ValueError('frame hash')
    for f in s['frames']+[s['idle']]:
        phase=f['phase'];old=Image.open(d/f'references/original-{phase}.png').convert('RGBA');changed=Image.open(d/f['changed_clothing_mask']).convert('L');all_masks={slot:Image.open(d/f'masks/{phase}-{slot}-visible-coverage.png').convert('L') for slot in ['top','pants','shoes']}
        base=Image.open(d/f['selected_density_base_source']).convert('RGBA')
        if base.size!=old.size:
            if phase=='idle' and base.size==(1024,1536):base=base.resize(old.size,Image.Resampling.NEAREST)
            else:raise ValueError('base source density')
        for repair in f.get('source_surface_repairs',[]):
            patch=Image.open(d/repair['source']).convert('RGBA')
            if patch.size!=old.size:
                if phase=='idle' and patch.size==(1024,1536):patch=patch.resize(old.size,Image.Resampling.NEAREST)
                else:raise ValueError('patch density')
            mask=Image.open(d/repair['mask']).convert('L')
            expected_mask=intersect(mask_polygons(old.size,repair['polygons']),all_masks[repair['slot']])
            if mask.tobytes()!=expected_mask.tobytes():raise ValueError('repair source ownership changed')
            base=Image.composite(patch,base,mask)
        if base.tobytes()!=Image.open(d/f'sources/{phase}-selected-density.png').convert('RGBA').tobytes():raise ValueError('selected source not exactly same-coordinate GPT selection')
        current_union=Image.new('L',old.size)
        for slot,m in all_masks.items():
            binary(m)
            if count(ImageChops.multiply(current_union,m)):raise ValueError('visible slot overlap')
            current_union=ImageChops.lighter(current_union,m)
            full=Image.open(d/f'parts/{phase}/{slot}-complete-source.png').convert('RGBA')
            source=Image.open(d/f'sources/{phase}-selected-density.png').convert('RGBA') if slot in SPECS[name]['changed'] else old
            diff=ImageChops.difference(full.convert('RGB'),source.convert('RGB'))
            if ImageChops.multiply(diff,m.convert('RGB')).getbbox():raise ValueError('visible RGB not copied from declared same-coordinate source')
            if count(intersect(m,full.getchannel('A').point(lambda a:255 if a==0 else 0))):raise ValueError('complete source has a visible hole')
        rebuilt=Image.open(d/f'parts/{phase}/shared_same_pose_foreground_and_contour.png').convert('RGBA')
        for slot in ['shoes','pants','top']:
            rebuilt=Image.composite(Image.open(d/f'parts/{phase}/{slot}-visible.png').convert('RGBA'),rebuilt,all_masks[slot])
        check_exact(old,rebuilt,changed)
        target=Image.open(d/f['file']).convert('RGBA');expected=register(rebuilt,[512,768] if phase=='idle' else s['canvas_px'],f['whole_frame_translation_px'])
        if target.tobytes()!=expected.tobytes():raise ValueError('baked slot RGBA mismatch')
    semantic=audit_semantics(d)
    if not semantic['passed']:raise ValueError('new skin owned by garment: '+json.dumps(semantic))
    return {'source_semantics':semantic,'sample':name,'sample_sha256':sha(d/'sample.json'),'input_hashes_current':True,'four_pose_and_matching_idle':True,'non_clothing_rgba_changed_pixels':0,'alpha_identical':True,'slot_bake_rgba_exact':True}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('command',choices=['build','validate']);ap.add_argument('sample',choices=list(SPECS));args=ap.parse_args()
    if args.command=='build':build(args.sample)
    print(json.dumps(validate(args.sample),ensure_ascii=False))
