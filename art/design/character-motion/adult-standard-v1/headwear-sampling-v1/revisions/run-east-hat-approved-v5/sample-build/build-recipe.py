"""Bake only genuine registered GPT hat layers over preserved original poses."""
from pathlib import Path
import copy
import hashlib
import json
import shutil

from PIL import Image, ImageChops

HERE=Path(__file__).resolve().parent
HEAD=HERE.parents[1]
ROOT=HERE.parents[6]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def binary(image):
    return image.getchannel('A').point(lambda a:255 if a else 0)

def compose(body,near,far,hair=None):
    if any(im.size!=body.size for im in [near,far]+([hair] if hair is not None else [])):
        raise ValueError('Registered layers must share full-frame coordinates.')
    edit=ImageChops.lighter(binary(near),binary(far))
    rendered=Image.alpha_composite(far,body)
    if hair is not None:
        rendered=Image.alpha_composite(rendered,hair)
        edit=ImageChops.lighter(edit,binary(hair))
    rendered=Image.alpha_composite(rendered,near)
    # Preserve original hidden RGB and soft alpha wherever no part is present.
    out=body.copy();out.paste(rendered,(0,0),edit)
    return out,edit

def assert_preserved(original,current):
    left=original['frames']+[original['idle']]
    right=current['frames']+[current['idle']]
    if len(left)!=len(right):raise ValueError('Pose count changed.')
    for before,after in zip(left,right):
        for key in ['pose_id','duration_ms']:
            if before.get(key)!=after.get(key):raise ValueError('Original pose or timing changed.')
        for state in ['bare','hair']:
            if before['states'][state]['sha256']!=after['states'][state]['sha256']:
                raise ValueError('Previously accepted bare/hair texture changed.')

def load_extraction(path,expected_pose):
    path=Path(path);meta=json.loads(path.read_text());directory=path.parent
    for name,digest in meta['sha256'].items():
        if sha(directory/name)!=digest:raise ValueError('Extraction changed: '+str(directory/name))
    if meta.get('pose_id')!=expected_pose:raise ValueError('Extraction belongs to a different pose.')
    # Frozen idle audit predates the explicit runtime flag: whitelist its exact
    # reviewed manifest, not arbitrary idle files or missing candidate fields.
    frozen_idle=(expected_pose=='idle_east_0' and path.resolve()==(HERE/'idle-extraction/manifest.json').resolve()
                 and sha(path)=='bf6506ed4553c312be660b0d4b02b3a23c0d6a274b715747fdbdd688696de082')
    if meta.get('runtime_candidate_allowed') is not True and not frozen_idle:
        raise ValueError('Pose source is not an explicitly allowed runtime candidate.')
    if meta.get('runtime_full_frame_placement_px',meta.get('placement_px'))!=[0,0]:
        raise ValueError('Registration must already be baked once into full frame.')
    return meta,directory

def build():
    selection=json.loads((HERE/'selected-extractions.json').read_text())
    hair_selection=json.loads((HERE/'selected-hair-extractions.json').read_text())
    old_path=HEAD/'run-east/sample.json';old=json.loads(old_path.read_text())
    poses=old['frames']+[old['idle']]
    # Resolve every accepted extraction before making any new runtime artifact.
    resolved={f['pose_id']:load_extraction(HERE/selection[f['pose_id']],f['pose_id']) for f in poses}
    tucked={pose:load_extraction(HERE/path,pose) for pose,path in hair_selection.items()}
    if set(tucked)!={f['pose_id'] for f in old['frames']}:
        raise ValueError('Every run pose requires its real GPT under-hat hair view.')
    out=HERE/'sample-build'
    if out.exists():raise ValueError('Refuse to overwrite an existing sample build.')
    work=HERE/'sample-build-staging';work.mkdir(exist_ok=False)
    current=copy.deepcopy(old);current['inputs']={};checks=[]
    def copy_old_references(value):
        if isinstance(value,dict):
            for entry in value.values():copy_old_references(entry)
        elif isinstance(value,list):
            for entry in value:copy_old_references(entry)
        elif isinstance(value,str) and value in old['inputs']:
            src=old_path.parent/value
            if sha(src)!=old['inputs'][value]:raise ValueError('Original bare/hair input changed.')
            dst=work/value;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
    for before,f in zip(poses,current['frames']+[current['idle']]):
        pose=f['pose_id'];meta,directory=resolved[pose];files=meta['files']
        for record in [f['states']['bare'],f['states']['hair'],f['parts']['hair']]:copy_old_references(record)
        prefix=Path('approved-extractions')/pose
        shutil.copytree(directory,work/prefix,ignore=shutil.ignore_patterns('__pycache__'))
        def role(*names):
            for name in names:
                if name in files:return (prefix/files[name]).as_posix()
            raise ValueError('Missing extraction role '+str(names))
        def image(*names):return Image.open(work/role(*names)).convert('RGBA')
        body=Image.open(work/f['states']['bare']['file']).convert('RGBA')
        hair=Image.open(work/f['parts']['hair']['registered_file']).convert('RGBA')
        hair_for_hat=hair
        if pose in tucked:
            hair_meta,hair_dir=tucked[pose]
            hair_prefix=Path('approved-under-hat-hair')/pose
            shutil.copytree(hair_dir,work/hair_prefix,ignore=shutil.ignore_patterns('__pycache__'))
            hair_files=hair_meta['files']
            hair_rel=(hair_prefix/hair_files['registered_file']).as_posix()
            hair_for_hat=Image.open(work/hair_rel).convert('RGBA')
            f['parts']['hair_under_hat']={'registered_file':hair_rel,'extraction_manifest':(hair_prefix/'manifest.json').as_posix(),'source':(hair_prefix/hair_files['source_full_frame']).as_posix(),'source_ownership':(hair_prefix/hair_files['source_ownership']).as_posix(),'placement_mode':'full_frame','offset_px':[0,0],'local_scale':[1,1],'capability':'Visible under-hat fringe/side/back view only; original complete bare-head hair retained for hair-only state.','source_to_target_integer_translation_px':hair_meta.get('source_to_target_integer_translation_px',[0,0])}
        near=image('hat_near','near');far=image('hat_far','far');plate=image('hat_complete_plate','plate')
        if ImageChops.darker(binary(near),binary(far)).getbbox():raise ValueError('Near/far hat overlap.')
        union=ImageChops.lighter(binary(near),binary(far))
        if ImageChops.difference(union,binary(plate)).getbbox():raise ValueError('Near/far hat incomplete.')
        for sub in ['baked','masks']:(work/sub).mkdir(exist_ok=True)
        for state in ['hat','hair_hat']:
            result,edit=compose(body,near,far,hair_for_hat if state=='hair_hat' else None)
            if state=='hat' and result.tobytes()!=image('composite').tobytes():
                raise ValueError('Independent extraction composite does not reconstruct.')
            outside=ImageChops.invert(edit)
            diff=ImageChops.difference(body,result)
            if any(ImageChops.darker(channel,outside).getbbox() for channel in diff.split()):
                raise ValueError('Original body changed outside authored parts.')
            rel=f'baked/{pose}-{state}.png';result.save(work/rel)
            mask=f'masks/{pose}-{state}-edit-region.png';edit.save(work/mask)
            f['states'][state]={'file':rel,'sha256':sha(work/rel),'edit_mask':mask}
            checks.append({'pose_id':pose,'state':state,'outside_authored_parts_rgba_differences':0,'source_anatomy_adopted':False})
        near_mask=binary(near);hair_mask=binary(hair_for_hat)
        visible=ImageChops.subtract(hair_mask,near_mask);hidden=ImageChops.darker(hair_mask,near_mask)
        for suffix,mask in [('hair-under-hat-visible',visible),('hair-occluded-by-hat',hidden),('hat-cap-volume',near_mask)]:
            mask.save(work/f'masks/{pose}-{suffix}.png')
        f['occlusion_mask']=f'masks/{pose}-hair-occluded-by-hat.png'
        f['hair_under_hat_visible']=f'masks/{pose}-hair-under-hat-visible.png'
        f['cap_volume_mask']=f'masks/{pose}-hat-cap-volume.png'
        f['occlusion']={'owner_part':'actual_near_hat_surface','target_surface':'registered_under_hat_hair_view' if pose in tucked else 'registered_hair_layer_only','mask':f['cap_volume_mask'],'coordinate_space':'target_pose_full_frame','kind':'painted_surface_occlusion_not_infinite_cavity','operation':'Use dedicated GPT under-hat view for run; full original short-hair source retained separately. Actual near hat surface occludes overlapping hair; visible bangs/sideburns retained. No max-column profile, body erase, or unpainted cavity trim.'}
        f['parts']['hat']={'complete_source':role('source_plate','hat_complete_plate'),'registered_file':role('hat_complete_plate','plate'),'near_file':role('hat_near','near'),'far_file':role('hat_far','far'),'source_ownership':role('source_ownership'),'source_ownership_coordinates':{'space':'source_crop_local','canvas_px':[512,768],'pose_id':pose},'coverage':role('target_coverage','coverage'),'coverage_coordinates':{'space':'target_pose_full_frame','canvas_px':[512,768],'pose_id':pose},'coverage_kind':'actual_same_pose_original_skull_envelope','target_surface':'same_pose_original_head','coverage_operation':'Actual authored hat surface only; original body source unchanged','placement_mode':'full_frame','offset_px':[0,0],'local_scale':[1,1],'source':role('source_full_frame'),'near_ownership':role('near_ownership'),'far_ownership':role('far_ownership'),'authored_contact':role('authored_contact','contact'),'extraction_manifest':(prefix/'manifest.json').as_posix()}
        f['head_anchor_mapping']['hat']={'operation':'Actual source view registered once by multi-point pose evidence; runtime full-frame zero placement, no part-local resize.','registered_offset_px':meta.get('source_to_target_integer_translation_px',[0,0]),'projection_evidence_file':role('registration_measurements','source_contours'),'source_to_target_residual_px':meta.get('registration_residual_px',[]),'runtime_placement_px':[0,0]}
        f['composition']={'layer_order':['far_hat','same_pose_original_body_clothes_hands_tool','full_same_pose_short_hair_if_selected','near_hat'],'hands_tool_in_front_of_headwear':False,'reason':'Actual near/far source geometry audited for this pose; hands are below headwear. No body alteration.'}
    current['status']='approved-hat-reference-derived-candidate-awaiting-native-and-user-review'
    current['recipe']['hat']='straw-navy-approved-v5'
    current['recipe']['hair_under_hat']='chestnut-short-tucked-approved-hat-v5'
    current['acceptance']={'user_visual':False,'native':False,'static_reference_user_visual':True,'reference_binding':'visual-acceptance-reference.json'}
    shutil.copy2(HERE/'visual-acceptance-reference.json',work/'visual-acceptance-reference.json')
    shutil.copy2(HERE/'selected-extractions.json',work/'selected-extractions.json')
    shutil.copy2(HERE/'selected-hair-extractions.json',work/'selected-hair-extractions.json')
    shutil.copy2(__file__,work/'build-recipe.py')
    assert_preserved(old,current)
    for file in sorted(work.rglob('*')):
        if file.is_file():current['inputs'][file.relative_to(work).as_posix()]=sha(file)
    (work/'sample.json').write_text(json.dumps(current,ensure_ascii=False,indent=2)+'\n')
    (work/'validation.json').write_text(json.dumps({'checks':checks,'preserved_bare_hair_timing':True,'source_anatomy_adopted':False,'native_verified':False,'sample_sha256':sha(work/'sample.json')},indent=2)+'\n')
    work.rename(out)
    catalog=json.loads((HEAD/'catalog.json').read_text())
    if not (HERE/'catalog-before.json').exists():shutil.copy2(HEAD/'catalog.json',HERE/'catalog-before.json')
    for entry in catalog['samples']:
        if entry['id']=='run-east':entry.update(sample=(out/'sample.json').relative_to(ROOT).as_posix(),sha256=sha(out/'sample.json'))
    (HERE/'catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'built':str(out),'preservation_checks':len(checks),'active_catalog_changed':False}))

if __name__=='__main__':build()
