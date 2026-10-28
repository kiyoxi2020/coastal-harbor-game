"""Rebuild only hoe-west hats using audited views and the shared v5 compositor."""
from pathlib import Path
import copy
import hashlib
import importlib.util
import json
import shutil
from PIL import Image,ImageChops

P=Path(__file__).resolve().parent
HEAD=P.parents[1]
ROOT=P.parents[6]
SHARED=HEAD/'revisions/run-east-hat-approved-v5/build_approved.py'
spec=importlib.util.spec_from_file_location('shared_headwear_build',SHARED)
shared=importlib.util.module_from_spec(spec);spec.loader.exec_module(shared)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def require_full_hair_compatible(meta):
    if meta.get('full_hair_compatible') is not True:
        raise ValueError('This hat needs a real compatible under-hat hair view; do not carve the original hair.')

def require_hair_compatibility(hat,variant,hat_manifest_sha):
    if variant is None:
        require_full_hair_compatible(hat)
    elif variant.get('runtime_candidate_allowed') is not True or variant.get('compatible_hat_manifest_sha256')!=hat_manifest_sha:
        raise ValueError('Under-hat hair must be audited against this exact hat manifest.')

def build():
    original_path=HEAD/'hoe-west/sample.json';original=json.loads(original_path.read_text())
    before_frames=original['frames']+[original['idle']]
    selected=json.loads((P/'selected-extractions.json').read_text())
    hair_selection=json.loads((P/'selected-hair-extractions.json').read_text()) if (P/'selected-hair-extractions.json').exists() else {}
    resolved={};variants={}
    for frame in before_frames:
        pose=frame['pose_id'];meta,directory=shared.load_extraction(P/selected[pose],pose)
        if meta.get('hat_body_compatible') is not True:raise ValueError('Hat must fit the actual original head first.')
        if pose in hair_selection:variants[pose]=shared.load_extraction(P/hair_selection[pose],pose)
        require_hair_compatibility(meta,variants[pose][0] if pose in variants else None,sha(P/selected[pose]))
        resolved[pose]=(meta,directory)
    out=P/'sample-build';work=P/'sample-build-staging'
    if out.exists() or work.exists():raise ValueError('Refuse to overwrite an existing build or partial staging.')
    work.mkdir();current=copy.deepcopy(original);current['inputs']={};checks=[]
    def copy_original(value):
        if isinstance(value,dict):
            for item in value.values():copy_original(item)
        elif isinstance(value,list):
            for item in value:copy_original(item)
        elif isinstance(value,str) and value in original['inputs']:
            src=original_path.parent/value
            if sha(src)!=original['inputs'][value]:raise ValueError('Original body/hair dependency changed.')
            dst=work/value;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
    for f in current['frames']+[current['idle']]:
        pose=f['pose_id'];meta,directory=resolved[pose];files=meta['files']
        for value in [f['states']['bare'],f['states']['hair'],f['parts']['hair']]:copy_original(value)
        prefix=Path('approved-extractions')/pose
        shutil.copytree(directory,work/prefix,ignore=shutil.ignore_patterns('__pycache__'))
        def role(*names):
            return (prefix/next(files[k] for k in names if k in files)).as_posix()
        def image(*names):return Image.open(work/role(*names)).convert('RGBA')
        body=Image.open(work/f['states']['bare']['file']).convert('RGBA')
        hair=Image.open(work/f['parts']['hair']['registered_file']).convert('RGBA')
        variant_meta=None
        if pose in variants:
            variant_meta,variant_dir=variants[pose];vp=Path('approved-under-hat-hair')/pose
            shutil.copytree(variant_dir,work/vp,ignore=shutil.ignore_patterns('__pycache__'))
            vf=variant_meta['files'];hair_rel=(vp/vf['registered_file']).as_posix()
            hair=Image.open(work/hair_rel).convert('RGBA')
            source_size=list(Image.open(work/vp/vf['source_ownership']).size)
            f['parts']['hair_under_hat']={'registered_file':hair_rel,'source':(vp/vf['source_full_frame']).as_posix(),'source_ownership':(vp/vf['source_ownership']).as_posix(),'source_ownership_coordinates':{'space':'source_full_frame','canvas_px':source_size,'pose_id':pose},'registered_coordinates':{'space':'target_pose_full_frame','canvas_px':list(body.size),'pose_id':pose},'extraction_manifest':(vp/'manifest.json').as_posix(),'placement_mode':'full_frame','offset_px':[0,0],'local_scale':[1,1],'capability':'Visible GPT fringe/side/back view only with the exact audited hat; original full hair-only view unchanged.','compatible_hat_manifest_sha256':variant_meta['compatible_hat_manifest_sha256']}
        near=image('near','hat_near');far=image('far','hat_far');plate=image('plate','hat_complete_plate')
        n=shared.binary(near);b=shared.binary(far);support=ImageChops.lighter(n,b)
        if ImageChops.darker(n,b).getbbox() or ImageChops.difference(support,shared.binary(plate)).getbbox():
            raise ValueError('Near/far must be disjoint and reconstruct the complete registered hat.')
        for folder in ['baked','masks']:(work/folder).mkdir(exist_ok=True)
        for state in ['hat','hair_hat']:
            result,edit=shared.compose(body,near,far,hair if state=='hair_hat' else None)
            if state=='hat':expected=image('composite')
            elif variant_meta is None:expected=image('hair_hat_composite')
            else:expected=Image.open(work/vp/next(vf[k] for k in ['hair_hat_composite','composite'] if k in vf)).convert('RGBA')
            if result.tobytes()!=expected.tobytes():raise ValueError('Independent audited composite differs: '+pose+' '+state)
            outside=ImageChops.invert(edit)
            if any(ImageChops.darker(c,outside).getbbox() for c in ImageChops.difference(body,result).split()):
                raise ValueError('Original RGBA changed outside actual part support.')
            rel=f'baked/{pose}-{state}.png';result.save(work/rel)
            mask=f'masks/{pose}-{state}-edit-region.png';edit.save(work/mask)
            f['states'][state]={'file':rel,'sha256':sha(work/rel),'edit_mask':mask}
            checks.append({'pose_id':pose,'state':state,'independent_composite_exact':True,'outside_parts_rgba_differences':0})
        alpha=hair.getchannel('A');near_alpha=near.getchannel('A')
        visible=ImageChops.multiply(alpha,ImageChops.invert(near_alpha))
        covered=ImageChops.multiply(alpha,near_alpha)
        for suffix,mask in [('hair-under-hat-visible',visible),('hair-occluded-by-hat',covered),('hat-cap-volume',near_alpha)]:
            mask.save(work/f'masks/{pose}-{suffix}.png')
        f['occlusion_mask']=f'masks/{pose}-hair-occluded-by-hat.png'
        f['hair_under_hat_visible']=f'masks/{pose}-hair-under-hat-visible.png'
        f['cap_volume_mask']=f'masks/{pose}-hat-cap-volume.png'
        f['occlusion']={'owner_part':'actual_near_hat_surface','target_surface':'audited_hat_compatible_hair_view' if variant_meta else 'full_original_registered_hair','mask':f['cap_volume_mask'],'coordinate_space':'target_pose_full_frame','kind':'actual_painted_surface_opacity_not_infinite_volume','operation':'Bake audited compatible hair view then real near hat alpha; original full hair-only source retained. Visible/covered hair masks are resulting-opacity diagnostics only; never multiply the source alpha a second time or erase body/hair above a column profile.'}
        own_size=list(Image.open(work/role('source_ownership')).size)
        f['parts']['hat']={'complete_source':role('source_plate','plate','hat_complete_plate'),'registered_file':role('plate','hat_complete_plate'),'near_file':role('near','hat_near'),'far_file':role('far','hat_far'),'source':role('source_full_frame'),'source_ownership':role('source_ownership'),'source_ownership_coordinates':{'space':'source_crop_local','canvas_px':own_size,'pose_id':pose},'coverage':role('coverage','target_coverage'),'coverage_coordinates':{'space':'target_pose_full_frame','canvas_px':list(body.size),'pose_id':pose},'coverage_kind':'audited_actual_original_head_envelope','target_surface':'same_pose_original_head','coverage_operation':'Actual source-owned hat surfaces; original body unchanged','placement_mode':'full_frame','offset_px':[0,0],'local_scale':[1,1],'near_ownership':role('near_ownership'),'far_ownership':role('far_ownership'),'authored_contact':role('contact','authored_contact'),'extraction_manifest':(prefix/'manifest.json').as_posix()}
        f['head_anchor_mapping']['hat']={'operation':'Audited whole-source integer registration from forehead/occiput/full-skull constraints; baked exactly once.','registered_offset_px':meta.get('source_to_target_integer_translation_px',[0,0]),'runtime_placement_px':[0,0],'projection_evidence_file':role('registration_measurements','source_contours')}
        f['composition']={'layer_order':['far_hat','same_pose_original_body_clothes_hands_tool','audited_under_hat_hair_if_selected' if variant_meta else 'full_original_hair_if_selected','near_hat'],'hands_tool_in_front_of_headwear':False,'reason':'Audited real near/far hat geometry per pose; no tool crosses headwear. Original hair retained, no infinite cap subtraction.'}
    shared.assert_preserved(original,current)
    current['recipe']['hat']='straw-navy-contact-repair-v2'
    if variants:current['recipe']['hair_under_hat']='chestnut-short-compressed-hoe-v2'
    current['status']='hoe-contact-repair-candidate-awaiting-native-and-user-review'
    current['acceptance']={'user_visual':False,'native':False,'reason':'New hoe contact/occlusion repair is independent of accepted east-v5.'}
    shutil.copy2(__file__,work/'build-recipe.py');shutil.copy2(SHARED,work/'shared-compose-source.py');shutil.copy2(P/'selected-extractions.json',work/'selected-extractions.json')
    if (P/'selected-hair-extractions.json').exists():shutil.copy2(P/'selected-hair-extractions.json',work/'selected-hair-extractions.json')
    for file in sorted(work.rglob('*')):
        if file.is_file():current['inputs'][file.relative_to(work).as_posix()]=sha(file)
    (work/'sample.json').write_text(json.dumps(current,ensure_ascii=False,indent=2)+'\n')
    (work/'validation.json').write_text(json.dumps({'checks':checks,'preserved_bare_hair_timing':True,'native_verified':False,'sample_sha256':sha(work/'sample.json')},indent=2)+'\n')
    work.rename(out)
    catalog=json.loads((HEAD/'catalog.json').read_text())
    if not (P/'catalog-before.json').exists():shutil.copy2(HEAD/'catalog.json',P/'catalog-before.json')
    for entry in catalog['samples']:
        if entry['id']=='hoe-west':entry.update(sample=(out/'sample.json').relative_to(ROOT).as_posix(),sha256=sha(out/'sample.json'))
    (P/'catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'built':str(out),'preservation_checks':len(checks),'active_catalog_changed':False}))

if __name__=='__main__':build()
