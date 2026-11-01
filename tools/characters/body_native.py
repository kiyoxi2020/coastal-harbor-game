"""Freeze strict body-only source-pose raster captures; never physical contacts."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from build import verify
from build_contract import digest, read_json, require, safe_file, stable
from contact_evidence import BoundContactEvidence

REPO=Path(__file__).resolve().parents[2]
OBSERVER_INPUTS=(
    'godot2d/tests/characters/capture_body_raster.gd',
    'godot2d/tests/characters/body_raster_fixture.gd',
    'godot2d/dev/characters/character_walk_trial.gd',
    'godot2d/dev/characters/character_motion_lane.tscn',
    'godot2d/project.godot',
    'tools/characters/body_native.py',
    'tools/characters/contact_evidence.py',
    'tools/characters/native_raster.py',
)


def contract_digest(data):
    return hashlib.sha256(stable({k:v for k,v in data.items() if k!='contract_digest'})).hexdigest()


def input_contract(repo, directory, points):
    repo=Path(repo).resolve();library=repo/'art/characters'
    directory=Path(directory).absolute();points=Path(points).absolute()
    manifest=verify(repo,directory);mp=directory/'manifest.json'
    recipe=read_json(safe_file(library,manifest['recipe'],'recipes'))
    require(recipe.get('schema_version')==3 and recipe.get('slots')=={'body':None},
            'Source-pose capture requires a strict schema3 body-only recipe')
    require(points.is_relative_to(repo),'Material points must be a versioned repository input')
    tool=BoundContactEvidence(repo,mp,digest(mp),manifest['artifact_digest'],points,digest(points))
    require(tool.static_points(),'Source-pose capture requires explicit material points')
    files={}
    def bind(path, expected=None):
        relative=Path(path).absolute().relative_to(repo).as_posix()
        path=safe_file(repo,relative)
        actual=digest(path);require(expected is None or expected==actual,'Capture input changed: '+relative)
        require(relative not in files or files[relative]==actual,'Conflicting capture input')
        files[relative]=actual
    bind(mp);bind(points)
    for path,expected in manifest['inputs'].items():bind(library/path,expected)
    for output in manifest['outputs']:bind(directory/output['file'],output['sha256'])
    for name,expected in manifest['engine']['code'].items():bind(repo/'tools/characters'/name,expected)
    pending=[repo/name for name in OBSERVER_INPUTS];seen=set()
    while pending:
        path=pending.pop()
        if path in seen:continue
        seen.add(path);bind(path)
        if path.suffix in {'.gd','.tscn','.tres','.godot','.cfg'}:
            for resource in re.findall(r'''["'](res://[^"'\n]+)["']''',path.read_text()):
                relative=resource[6:]
                if relative in {'','.','..'}:continue
                require('..' not in Path(relative).parts,'Runtime resource escapes project')
                target=repo/'godot2d'/relative
                if target.is_file():pending.append(target)
    outputs={o['file']:o for o in manifest['outputs']};plan=[]
    for clip in recipe['clips']:
        for frame in clip['frames']:
            name=f"frames/{clip['action_id']}/{clip['direction']}/{frame['pose_id']}.png"
            out=outputs[name]
            plan.append({'action':clip['action_id'],'direction':clip['direction'],'pose_id':frame['pose_id'],
                'file':(directory/name).relative_to(repo).as_posix(),'sha256':out['sha256'],
                'rgba_sha256':out['rgba_sha256'],'canvas_px':clip['canvas_px'],
                'root_anchor_px':clip['root_anchor_px'],'display_scale':clip['display_scale']})
    for path,expected in files.items():require(digest(safe_file(repo,path))==expected,'Input changed during freeze')
    tool.verify_unchanged()
    result={'kind':'coastal-body-source-native-input-v1','schema_version':1,'observer':'source-poses',
        'scope':'Static posed material raster correspondence only; not actual motion, support/slide or ground contact.',
        'manifest':{'manifest':mp.relative_to(repo).as_posix(),'sha256':digest(mp)},
        'artifact_digest':manifest['artifact_digest'],
        'source_points':{'file':points.relative_to(repo).as_posix(),'sha256':digest(points)},
        'capture_scene':'res://dev/characters/character_motion_lane.tscn',
        'camera_zoom':4.0,'plan':plan,'files':dict(sorted(files.items()))}
    result['contract_digest']=contract_digest(result)
    return result


def snapshot(repo,directory,points,evidence):
    evidence=Path(evidence).absolute()
    require(evidence.is_relative_to('/private/tmp')
            and evidence.relative_to('/private/tmp').parts[0].startswith('coastal-'),
            'Native evidence must be inside /private/tmp/coastal-*')
    require(not any(p.is_symlink() for p in [evidence,*evidence.parents]),'Native evidence symlink forbidden')
    require(not evidence.exists(),'Native evidence must be fresh')
    contract=input_contract(repo,directory,points)
    evidence.mkdir(parents=True)
    (evidence/'input-contract.json').write_text(json.dumps(contract,ensure_ascii=False,indent=2)+'\n')
    return contract


def verify_inputs(repo,evidence):
    repo=Path(repo).resolve();cp=safe_file(Path(evidence).absolute(),'input-contract.json')
    contract=read_json(cp)
    require(contract.get('contract_digest')==contract_digest(contract),'Native contract digest differs')
    manifest=safe_file(repo,contract['manifest']['manifest'],'art/characters/builds')
    points=safe_file(repo,contract['source_points']['file'])
    rebuilt=input_contract(repo,manifest.parent,points)
    require(contract==rebuilt,'Native input closure or pose plan changed')
    return {'passed':True,'scope':'source-pose-inputs-only','poses':len(contract['plan']),'files':len(contract['files'])}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    commands=parser.add_subparsers(dest='command',required=True)
    p=commands.add_parser('snapshot');p.add_argument('--build',type=Path,required=True)
    p.add_argument('--points',type=Path,required=True);p.add_argument('--evidence',type=Path,required=True)
    p=commands.add_parser('verify-inputs');p.add_argument('--evidence',type=Path,required=True)
    args=parser.parse_args()
    try:
        result=snapshot(REPO,args.build,args.points,args.evidence) if args.command=='snapshot' else verify_inputs(REPO,args.evidence)
        print(json.dumps({'passed':True,'poses':len(result['plan'])} if 'plan' in result else result))
    except (ValueError,KeyError,TypeError,OSError) as error:parser.exit(1,str(error)+'\n')


if __name__=='__main__':main()
