"""Author a union of registered recipes; all pixels remain the strict builder's job.

Parents are immutable verified builds. This creates versioned definitions and
namespace-qualified view catalogs, without editing sources, masks or textures.
Run build.py build/verify on the returned recipe before using the result.
"""
import argparse
import copy
import json
from pathlib import Path

import build
from build_contract import digest, identifier, read_json, require, safe_file


def assemble(repo, parents, recipe_id, revision):
    repo=Path(repo); library=repo/'art/characters'
    identifier(recipe_id); identifier(revision)
    records=[]; capabilities={}; profile=None
    # Validate every parent and every duplicate before writing any authoring file.
    for index, directory in enumerate(parents):
        directory=Path(directory).resolve()
        manifest=build.verify(repo,directory)
        head=read_json(safe_file(library,manifest['recipe'],'recipes'))
        require(head.get('schema_version')==2 and head.get('head_state')=='hair_hat'
                and 'adaptations' in head,'Assembly needs registered hair_hat parents')
        base=read_json(safe_file(library,head['base_recipe']['file'],'recipes'))
        require(base.get('schema_version')==3,'Assembly needs schema3 parents')
        current=(base['template'],base['motion_set'],base['character_model_id'],
                 {slot:read_json(library/ref['file'])['design_id'] for slot,ref in base['slots'].items() if slot!='body'},
                 {slot:read_json(library/ref['file'])['design_id'] for slot,ref in head['slots'].items()})
        if profile is None:profile=current
        require(profile==current,'Parent template/motion/part identities differ')
        require(len(base['clips'])==len(head['clips']),'Parent clip mismatch')
        keep=[]
        for clip,hclip in zip(base['clips'],head['clips']):
            key=(clip['action_id'],clip['direction'])
            require(key==(hclip['action_id'],hclip['direction']),'Parent clip order differs')
            if key in capabilities:
                require(key[0]=='idle','Duplicate nonidle capability')
                previous=capabilities[key]
                old=previous['clip']
                signature=lambda c:{k:c[k] for k in ['action_id','direction','action','poses','variant','canvas_px','root_anchor_px','display_scale']}
                require(signature(old)==signature(clip),'Conflicting canonical idle geometry/template')
                require([(f['pose_id'],f['duration_ms'],next(l['texture']['sha256'] for l in f['layers'] if l['slot']=='body')) for f in old['frames']]
                        ==[(f['pose_id'],f['duration_ms'],next(l['texture']['sha256'] for l in f['layers'] if l['slot']=='body')) for f in clip['frames']],
                        'Conflicting canonical idle pose/body')
                old_outputs={o['file']:o for o in previous['manifest']['outputs']}
                new_outputs={o['file']:o for o in manifest['outputs']}
                for frame in clip['frames']:
                    path=f"frames/idle/{clip['direction']}/{frame['pose_id']}.png"
                    require(old_outputs[path]['rgba_sha256']==new_outputs[path]['rgba_sha256']
                            and old_outputs[path]['size']==new_outputs[path]['size'],'Conflicting canonical idle pixels')
                # The base itself must match too; headwear may hide a body error.
                from build_contract import validate
                old_base=validate(repo,library/previous['base_ref']['file'])
                new_base=validate(repo,library/head['base_recipe']['file'])
                from build import render
                old_frames=dict(render(old_base));new_frames=dict(render(new_base))
                for frame in clip['frames']:
                    path=f"frames/idle/{clip['direction']}/{frame['pose_id']}.png"
                    require(old_frames[path].tobytes()==new_frames[path].tobytes(),'Conflicting canonical idle base pixels')
            else:
                capabilities[key]={'clip':clip,'directory':directory,'manifest':manifest,'base_ref':head['base_recipe']}
                keep.append(key)
        records.append((index,directory,manifest,head,base,keep))
    require(records,'No parent builds')
    base_id=recipe_id+'-body'
    destination=library/f'recipes/{recipe_id}/{revision}.json'
    require(not destination.exists() and not (library/f'recipes/{base_id}/{revision}.json').exists(),'Assembly revision already exists')
    staged={}; authoring=[]
    def write(relative,data):
        require(not (library/relative).exists(),'Assembly output already exists: '+relative)
        encoded=(json.dumps(data,indent=2)+'\n').encode();staged[relative]=encoded
        import hashlib
        return {'file':relative,'sha256':hashlib.sha256(encoded).hexdigest()}
    def add(ref):
        if ref not in authoring:authoring.append(ref)
    base=copy.deepcopy(records[0][4]);head=copy.deepcopy(records[0][3])
    base.update(recipe_id=base_id,revision=revision,clips=[],required_capabilities=[],authoring_inputs=[])
    head.update(recipe_id=recipe_id,revision=revision,clips=[],authoring_inputs=[])
    catalogs={}
    for slot in ['top','pants','shoes','hair','hat']:
        owner=head if slot in ['hair','hat'] else base
        original=read_json(library/owner['slots'][slot]['file'])
        design=copy.deepcopy(original);design.update(revision=recipe_id+'-'+revision,
            scope='Explicit union of verified parent registrations; review-only. No new source, pose or approval capability.')
        design.pop('status',None)
        owner['slots'][slot]=write(f"parts/{design['design_id']}/revisions/{design['revision']}/design.json",design)
        first=read_json(library/owner['adaptations'][slot]['file'])
        catalog=copy.deepcopy(first);catalog.update(design_revision=design['revision'],views=[],mappings=[])
        catalogs[slot]=catalog
    for index,directory,manifest,parent_head,parent_base,keep in records:
        prefix=f'p{index}-'
        for parent in [parent_base,parent_head]:
            # Historical parent recipes are provenance snapshots, not live
            # nested construction contracts. Preserve the exact source text
            # under an explicitly different type so consumers do not traverse
            # an unused parent's recipe dependency graph as runtime inputs.
            parent_ref=manifest['recipe'] if parent is parent_head else parent_head['base_recipe']['file']
            snapshot={'kind':'coastal-recipe-authoring-snapshot-v1',
                      'original_file':parent_ref,'original_sha256':digest(library/parent_ref),
                      'original_json':(library/parent_ref).read_text()}
            add(write(f"sources/registered-recipe-assembly-v1/metadata/{recipe_id}-{revision}-p{index}-{parent['recipe_id']}.json",snapshot))
            for ref in parent['authoring_inputs']:add(ref)
            for ref in list(parent['adaptations'].values())+[ref for ref in parent['slots'].values() if ref is not None]:add(ref)
            for slot,ref in parent['adaptations'].items():
                catalog=read_json(library/ref['file'])
                for view in catalog['views']:
                    row=copy.deepcopy(view);row['view_id']=prefix+row['view_id'];catalogs[slot]['views'].append(row)
                for mapping in catalog['mappings']:
                    row=copy.deepcopy(mapping);row['view_id']=prefix+row['view_id'];row['mapping_id']=prefix+row['mapping_id'];catalogs[slot]['mappings'].append(row)
        for original,horiginal in zip(parent_base['clips'],parent_head['clips']):
            key=(original['action_id'],original['direction'])
            if key not in keep:continue
            for target,clip in [(base,original),(head,horiginal)]:
                clip=copy.deepcopy(clip)
                for frame in clip['frames']:
                    for layer in frame['layers']:
                        if 'view_binding' in layer:
                            layer['view_binding']={k:prefix+v for k,v in layer['view_binding'].items()}
                target['clips'].append(clip)
            base['required_capabilities'].append({'action_id':key[0],'direction':key[1]})
    for slot,catalog in catalogs.items():
        owner=head if slot in ['hair','hat'] else base
        relative=f"parts/{catalog['design_id']}/adaptations/{catalog['template_id']}/{catalog['motion_set_id']}/{recipe_id}-{revision}/views.json"
        owner['adaptations'][slot]=write(relative,catalog)
    proof={'kind':'coastal-registered-recipe-assembly-provenance-v1','scope':'metadata-only; strict build and native acceptance remain separate',
           'parents':[{'manifest':directory.relative_to(repo).as_posix()+'/manifest.json','manifest_sha256':digest(directory/'manifest.json'),
                       'artifact_digest':manifest['artifact_digest'],'recipe':manifest['recipe']} for _,directory,manifest,_,_,_ in records]}
    add(write(f'sources/registered-recipe-assembly-v1/metadata/{recipe_id}-{revision}-provenance.json',proof))
    base['authoring_inputs']=copy.deepcopy(authoring)
    head['base_recipe']=write(f'recipes/{base_id}/{revision}.json',base)
    head['authoring_inputs']=copy.deepcopy(authoring)
    write(f'recipes/{recipe_id}/{revision}.json',head)
    for relative,encoded in staged.items():
        path=library/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(encoded)
    return destination


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('recipe_id');parser.add_argument('revision');parser.add_argument('parents',nargs='+',type=Path)
    args=parser.parse_args()
    print(assemble(Path(__file__).resolve().parents[2],args.parents,args.recipe_id,args.revision))
