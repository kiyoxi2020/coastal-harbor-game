"""Freeze actual full-package native inputs; no art acceptance is inferred.

Observers share the real character player. Each run binds a complete strict
package and its runtime/observer closure before collecting any pixels.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

from build_contract import digest, read_json, require, safe_file, stable
from construction_native import _new_evidence_path, full_capture_plan
from review import construction_preflight

KIND='coastal-all-actions-native-input-v1'
OBSERVERS={
    'poses':'capture_registered_candidate.gd',
    'world':'capture_registered_actions_world.gd',
    'timing':'capture_registered_farm_timing.gd',
    'transitions':'capture_registered_transitions.gd',
    'spatial':'capture_registered_spatial.gd',
    'locomotion-timing':'capture_registered_locomotion_timing.gd',
}
REPO=Path(__file__).resolve().parents[2]


def contract_digest(contract):
    return hashlib.sha256(stable({k:v for k,v in contract.items() if k!='contract_digest'})).hexdigest()


def _input_contract(repo,suite_path,observer):
    repo=Path(repo).resolve();suite_path=Path(suite_path).absolute()
    require(observer in OBSERVERS,'Unknown full-package observer')
    suite=construction_preflight(repo,suite_path)
    require(suite.get('schema_version')==2,'Full native snapshot requires full package')
    manifest_path=safe_file(repo,suite['manifest']['manifest'],'art/characters/builds')
    manifest=read_json(manifest_path);library=repo/'art/characters'
    head=read_json(safe_file(library,manifest['recipe'],'recipes'))
    base=read_json(safe_file(library,head['base_recipe']['file'],'recipes'))
    plan=full_capture_plan(base,head);files={}
    def bind(path,expected=None):
        path=Path(path);relative=path.relative_to(repo).as_posix()
        safe_file(repo,relative);actual=digest(path)
        require(expected is None or actual==expected,'Native input changed: '+relative)
        require(relative not in files or files[relative]==actual,'Conflicting native input')
        files[relative]=actual
    bind(suite_path);bind(manifest_path,suite['manifest']['sha256'])
    for relative,expected in manifest['inputs'].items():bind(library/relative,expected)
    for relative,expected in manifest['engine']['code'].items():bind(repo/'tools/characters'/relative,expected)
    for output in manifest['outputs']:bind(manifest_path.parent/output['file'],output['sha256'])
    for name in ['all_actions_capture.py','all_actions_native.py','construction_native.py','native_contract.py','review.py']:
        bind(repo/'tools/characters'/name)
    scene='character_headwear_trial.tscn' if observer in {'poses','spatial'} else 'character_motion_lane.tscn'
    capture_scene='res://dev/characters/'+scene
    observer_path='godot2d/tests/characters/'+OBSERVERS[observer]
    pending=[repo/observer_path,repo/'godot2d/dev/characters'/scene,repo/'godot2d/project.godot'];visited=set()
    while pending:
        path=pending.pop()
        if path in visited:continue
        visited.add(path);bind(path)
        if path.suffix in {'.gd','.tscn','.tres','.godot','.cfg'}:
            for resource in re.findall(r'''["'](res://[^"'\n]+)["']''',path.read_text()):
                relative=resource[6:]
                if not relative or relative in {'.','..'}:continue
                require('..' not in Path(relative).parts,'Runtime resource path escapes project')
                target=repo/'godot2d'/relative
                if target.is_file():pending.append(target)
        uid=Path(str(path)+'.uid')
        if uid.is_file():pending.append(uid)
    for relative,expected in files.items():require(digest(safe_file(repo,relative))==expected,'Native input changed during freeze')
    contract={'kind':KIND,'schema_version':1,'scope':'Full registered package native observation inputs only; not contact, art, user approval or production release.',
        'suite':suite_path.relative_to(repo).as_posix(),'observer':observer,'observer_script':observer_path,
        'capture_scene':capture_scene,'manifest':suite['manifest'],'artifact_digest':manifest['artifact_digest'],
        'runtime':suite['runtime'],'plan':plan,'transitions':plan['transitions'] if observer=='transitions' else [],
        'files':dict(sorted(files.items()))}
    if observer=='world':contract['capture_every_rendered_frame']=True
    contract['contract_digest']=contract_digest(contract)
    return contract


def snapshot(repo,suite_path,evidence,observer):
    evidence=Path(evidence).absolute()
    _new_evidence_path(evidence)
    contract=_input_contract(repo,suite_path,observer)
    evidence.mkdir(parents=True)
    (evidence/'input-contract.json').write_text(json.dumps(contract,ensure_ascii=False,indent=2)+'\n')
    return contract


def verify_inputs(repo,evidence):
    repo=Path(repo).resolve();evidence=Path(evidence).absolute()
    contract=read_json(safe_file(evidence,'input-contract.json'))
    require(isinstance(contract,dict),'Invalid full native input contract object')
    require(contract.get('kind')==KIND and type(contract.get('schema_version')) is int and contract['schema_version']==1,'Invalid full native input contract')
    require(contract.get('contract_digest')==contract_digest(contract),'Native input contract changed')
    require(contract.get('observer') in OBSERVERS and contract.get('observer_script')=='godot2d/tests/characters/'+OBSERVERS[contract['observer']],'Native observer changed')
    require(isinstance(contract.get('files'),dict) and contract['files'],'Missing native input closure')
    for relative,expected in contract['files'].items():
        require(digest(safe_file(repo,relative))==expected,'Native input changed: '+relative)
    rebuilt=_input_contract(repo,safe_file(repo,contract['suite'],'art/characters/reviews'),contract['observer'])
    require(contract==rebuilt,'Native input contract closure or plan changed')
    return {'scope':'input-closure-only','passed':True,'files_verified':len(contract['files']),'artifact_digest':contract['artifact_digest']}


def main():
    parser=argparse.ArgumentParser();sub=parser.add_subparsers(dest='command',required=True)
    freeze=sub.add_parser('snapshot');freeze.add_argument('--suite',type=Path,required=True);freeze.add_argument('--evidence',type=Path,required=True);freeze.add_argument('--observer',choices=OBSERVERS,required=True)
    check=sub.add_parser('verify-inputs');check.add_argument('--evidence',type=Path,required=True)
    args=parser.parse_args()
    try:
        if args.command=='snapshot':
            result=snapshot(REPO,args.suite,args.evidence,args.observer)
            print(json.dumps({'passed':True,'observer':args.observer,'files':len(result['files']),'clips':len(result['plan']['clips']),'artifact_digest':result['artifact_digest']}))
        else:print(json.dumps(verify_inputs(REPO,args.evidence)))
    except (ValueError,KeyError,TypeError,OSError) as error:parser.exit(1,str(error)+'\n')


if __name__=='__main__':main()
