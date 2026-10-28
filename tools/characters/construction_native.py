"""Freeze and verify a bounded strict-construction headwear GPU review.

This validates fixture evidence, not OS input, user approval or production release.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
from datetime import datetime, timezone
from PIL import Image
from build_contract import digest, keys, read_json, require, safe_file, stable
from build import verify
from native_contract import build_contract as migration_inputs

KIND = 'coastal-construction-headwear-native-v1'
STATES = ['bare', 'hair', 'hat', 'hair_hat']
SUITE_KIND = 'coastal-character-construction-review-v1'
FIXTURE = 'godot2d/tests/characters/test_character_construction_native.gd'
REPO = Path(__file__).resolve().parents[2]


def contract_digest(contract):
    return hashlib.sha256(stable({k:v for k,v in contract.items() if k != 'contract_digest'})).hexdigest()


def required_checks(sample_id, states):
    result = ['real_gpu']
    for state in states:
        prefix = sample_id + '-' + state
        result += [prefix + '_' + suffix for suffix in ['selected','idle_matches','canvas_fits',
                   'ten_panel_cycles','tool_starts','live_switch_keeps_clock','all_world_poses',
                   'motion_policy','ends_matching_idle']]
        result += [f'{prefix}_{background}_pose_{i}' for background in ['dark','light'] for i in range(4)]
    return result


def required_pngs(sample_id, states):
    result = ['overview.png']
    for state in states:
        prefix = sample_id + '-' + state
        for background in ['dark','light']:
            result += [f'boards/{prefix}-{background}.png',f'sequence/{prefix}-{background}-idle.png']
            result += [f'sequence/{prefix}-{background}-pose-{i}.png' for i in range(4)]
        result += [f'sequence/{prefix}-world-{i}.png' for i in range(4)]
        result.append(f'sequence/{prefix}-cycle-0000.png')
    return result


def snapshot(repo, suite_path, evidence):
    repo = Path(repo).resolve(); evidence = Path(evidence).absolute()
    _new_evidence_path(evidence)
    suite_path = Path(suite_path).absolute()
    require(suite_path.is_relative_to(repo/'art/characters/reviews'), 'Suite outside review namespace')
    suite = read_json(safe_file(repo, suite_path.relative_to(repo).as_posix()))
    keys(suite, 'kind schema_version resource_root scope sample_id states', 'construction suite')
    require(suite['kind'] == SUITE_KIND and type(suite['schema_version']) is int and suite['schema_version'] == 1
            and suite['resource_root'] == 'art/characters' and suite['scope'] == 'review-only'
            and suite['sample_id'] == 'hoe-west' and set(suite['states']) == set(STATES), 'Unexpected construction suite')
    # Include the actual inherited review dependencies, not only the new textures.
    files = migration_inputs(repo)['files']
    def bind(path):
        path = Path(path)
        name = path.relative_to(repo).as_posix()
        safe_file(repo, name); actual = digest(path)
        require(name not in files or files[name] == actual, 'Conflicting snapshot input')
        files[name] = actual
    bind(suite_path)
    manifest_hashes = {}; baseline = None
    for state in STATES:
        entry = suite['states'][state];keys(entry,'manifest sha256','suite state')
        path = safe_file(repo,entry['manifest'],'art/characters/builds')
        require(digest(path) == entry['sha256'], 'Suite manifest SHA mismatch')
        manifest = verify(repo,path.parent); bind(path); manifest_hashes[state] = digest(path)
        recipe = read_json(safe_file(repo/'art/characters', manifest['recipe'],'recipes'))
        require(recipe.get('head_state') == state and recipe.get('schema_version') == 2, 'Suite recipe state mismatch')
        base = recipe['base_recipe']
        if baseline is None:baseline = base
        require(base == baseline,'Head states have different base recipe')
        for output in manifest['outputs']:bind(path.parent/output['file'])
    base = read_json(safe_file(repo/'art/characters',baseline['file'],'recipes'))
    require([(c['action_id'],c['direction']) for c in base['clips']] == [('hoe','west'),('idle','west')], 'Unbounded native scope')
    clip = base['clips'][0]
    require(len(clip['frames']) == 4 and len(base['clips'][1]['frames']) == 1, 'Unexpected native pose count')
    # Bind every source and current construction engine as well as fixture inheritance.
    for state in STATES:
        manifest = read_json(repo/suite['states'][state]['manifest'])
        for name, expected in manifest['inputs'].items():
            path = repo/'art/characters'/name; require(digest(path)==expected,'Stale input');bind(path)
        for name in manifest['engine']['code']:bind(repo/'tools/characters'/name)
    pending = [repo/FIXTURE]
    visited = set()
    import re
    while pending:
        path = pending.pop()
        if path in visited:continue
        visited.add(path);bind(path)
        if path.suffix in {'.gd','.tscn','.tres'}:
            for target in re.findall(r'["\'](res://[^"\'\n]+)["\']',path.read_text()):
                relative = target[6:]
                if relative and (repo/'godot2d'/relative).is_file():pending.append(repo/'godot2d'/relative)
        uid = Path(str(path)+'.uid')
        if uid.is_file():bind(uid)
    bind(Path(__file__).resolve())
    contract = {'kind':KIND,'schema_version':1,'validator_sha256':digest(__file__),
                'created_utc':datetime.now(timezone.utc).isoformat(), 'files':dict(sorted(files.items())),
                'suite_sha256':digest(suite_path),'sample_id':suite['sample_id'],'states':STATES,
                'duration_ms':[f['duration_ms'] for f in clip['frames']],
                'pose_ids':[f['pose_id'] for f in clip['frames']], 'manifest_sha256':manifest_hashes}
    contract['contract_digest'] = contract_digest(contract)
    evidence.mkdir(parents=True)
    (evidence/'input-contract.json').write_text(json.dumps(contract,indent=2)+'\n')
    return contract


def _new_evidence_path(path):
    require('..' not in path.parts and '.' not in path.parts, 'Evidence path contains dot segments')
    require(path.is_relative_to(Path('/private/tmp')) and path.relative_to('/private/tmp').parts[0].startswith('coastal-'), 'Evidence must be in /private/tmp/coastal-*')
    require(not path.exists(), 'Evidence directory already exists')
    require(not any(p.is_symlink() for p in [path,*path.parents]),'Evidence symlink forbidden')


def _float(row, name):
    encoded = row[name+'_f64le']
    require(isinstance(encoded,str) and len(encoded) == 16,'Missing exact binary64 timing')
    try:value = struct.unpack('<d',bytes.fromhex(encoded))[0]
    except (ValueError,struct.error) as exc:raise ValueError('Invalid binary64 timing') from exc
    require(math.isfinite(value),'Non-finite timing')
    require(type(row[name+'_ms']) in (int,float) and math.isclose(row[name+'_ms'],value,rel_tol=1e-6,abs_tol=1e-3),'Timing summary differs from original binary64')
    return value


def validate_capture(repo, evidence):
    repo = Path(repo).resolve(); evidence = Path(evidence).absolute()
    require(not any(p.is_symlink() for p in [evidence,*evidence.parents]),'Evidence symlink forbidden')
    contract_path = safe_file(evidence,'input-contract.json'); report_path = safe_file(evidence,'report.json')
    contract_sha=digest(contract_path);report_sha=digest(report_path)
    c = read_json(contract_path); report = read_json(report_path)
    require(digest(contract_path)==contract_sha and digest(report_path)==report_sha,'Evidence changed while reading')
    require(c.get('kind') == KIND and type(c.get('schema_version')) is int and c['schema_version']==1,'Invalid native contract')
    require(c.get('validator_sha256')==digest(__file__) and c.get('contract_digest')==contract_digest(c),'Native validator or contract changed')
    require(c.get('states')==STATES and c.get('sample_id')=='hoe-west','Native scope differs')
    for name, expected in c['files'].items():require(digest(safe_file(repo,name))==expected,'Changed native input: '+name)
    require(report.get('input_contract_sha256')==digest(contract_path),'Report binds another contract')
    require(report.get('catalog_sha256')==c['suite_sha256'] and report.get('manifest_sha256')==c['manifest_sha256'],'Report binds another suite/build')
    renderer = report.get('renderer',{})
    require(renderer.get('display_server') not in (None,'','headless') and renderer.get('adapter') and renderer.get('rendering_method'),'Real GPU renderer required')
    checks = report.get('checks',{})
    require(isinstance(checks,dict) and all(type(v) is bool and v for v in checks.values()) and all(checks.get(k) is True for k in required_checks(c['sample_id'],STATES)),'Missing/failed native check')
    clip = report.get('clips',{}).get(c['sample_id'],{})
    require(clip.get('pose_ids')==c['pose_ids'] and clip.get('durations_ms')==c['duration_ms'] and clip.get('states')==STATES,'Report pose/timing mismatch')
    durations = c['duration_ms']
    require(len(durations)==4 and all(type(t) in (int,float) and math.isfinite(t) and t>0 for t in durations),'Invalid durations')
    duration = sum(durations); timing_counts = {}; row_captures=set()
    samples = report.get('samples')
    require(isinstance(samples,list) and samples,'Missing native samples')
    require(all(isinstance(x,dict) and x.get('clip')==c['sample_id'] and x.get('state') in STATES for x in samples),'Unknown timing subject')
    for state in STATES:
        rows = [x for x in samples if x['state']==state]
        require(rows,'Missing timing state')
        last_phase=0.0; last_unwrapped=0.0; last_wall=-1; seen=set(); cycle_images=[];last_capture_wall=-1
        for row in rows:
            phase = _float(row,'phase');unwrapped = _float(row,'unwrapped')
            require(0<=phase<duration and unwrapped>=0,'Invalid timing range')
            require(type(row.get('wall_ms')) is int and row['wall_ms']>last_wall,'Unordered sample time')
            delta=(phase-last_phase)%duration
            require(math.isclose(unwrapped,last_unwrapped+delta,rel_tol=1e-11,abs_tol=1e-7),'Timing modulo accumulation mismatch')
            expected_pose=0; edge=durations[0]
            while expected_pose<3 and phase>=edge:expected_pose+=1;edge+=durations[expected_pose]
            require(type(row.get('pose')) is int and row['pose']==expected_pose,'Timing pose mismatch')
            require(last_capture_wall<0 or row['wall_ms']-last_capture_wall<=400,'Timing capture gap exceeds sampled-sequence scope')
            capture=row.get('capture')
            if capture is not None:
                require(capture==f'sequence/{c["sample_id"]}-{state}-cycle-{len(cycle_images):04d}.png','Invalid timing capture sequence')
                require(capture not in row_captures,'Duplicate timing capture')
                row_captures.add(capture);cycle_images.append(capture);last_capture_wall=row['wall_ms']
            require(last_capture_wall>=0 and row['wall_ms']-last_capture_wall<=400,'Timing capture gap exceeds sampled-sequence scope')
            seen.add(expected_pose);last_phase=phase;last_unwrapped=unwrapped;last_wall=row['wall_ms']
        require(seen=={0,1,2,3} and last_unwrapped>=duration*10,'Less than ten complete panel cycles')
        require(len(cycle_images)>=10,'Insufficient timed cycle images')
        timing_counts[state]=len(rows)
    hashes = report.get('output_hashes'); captures=report.get('captures')
    require(isinstance(hashes,dict) and isinstance(captures,list) and len(captures)==len(set(captures)),'Invalid output inventory')
    actual={p.relative_to(evidence).as_posix() for p in evidence.rglob('*.png')}
    require(actual==set(hashes) and set(required_pngs(c['sample_id'],STATES))<=actual,'PNG output coverage mismatch')
    require(row_captures<=(set(captures)&actual) and row_captures=={name for name in actual if '-cycle-' in name},'Unbound timing PNG capture')
    require(set(captures)<=actual and all(not Path(p).is_absolute() and '..' not in Path(p).parts for p in captures),'Invalid capture paths')
    sizes={}
    for name, expected in hashes.items():
        path=safe_file(evidence,name); require(digest(path)==expected,'PNG SHA mismatch: '+name)
        with Image.open(path) as image:
            require(image.format=='PNG','Non-PNG output');sizes[name]=image.size;image.verify()
    for state in STATES:
        prefix=c['sample_id']+'-'+state
        for background in ['dark','light']:
            size=sizes[f'sequence/{prefix}-{background}-idle.png']
            require(sizes[f'boards/{prefix}-{background}.png']==(size[0]*5,size[1]),'Board does not cover all five views')
            require(all(sizes[f'sequence/{prefix}-{background}-pose-{i}.png']==size for i in range(4)),'Panel capture dimensions mismatch')
        require(all(sizes[f'sequence/{prefix}-world-{i}.png']==(300,320) for i in range(4)),'World capture dimensions mismatch')
    # Recheck the exact bytes that were parsed, not a later version.
    require(digest(contract_path)==contract_sha and digest(report_path)==report_sha,'Evidence changed during validation')
    for name, expected in c['files'].items():require(digest(safe_file(repo,name))==expected,'Input changed during validation')
    return {'kind':KIND+'-receipt','passed':True,'states':STATES,'panel_cycles_per_state':10,
            'timing_counts':timing_counts,'output_count':len(hashes),'input_count':len(c['files']),
            'input_contract_sha256':contract_sha,'report_sha256':report_sha,
            'validator_sha256':digest(__file__),'output_hashes':hashes,
            'scope':'Four fixed states, five stopped views in light/dark, ten panel cycles per state, world four poses/state, fixture live switching and matching idle. No OS input/WM focus, strict contact, export or user acceptance.'}


def write_receipt(repo,evidence,output):
    evidence=Path(evidence).absolute();output=Path(output).absolute()
    require(output.parent==evidence and output.name not in {'report.json','input-contract.json'} and output.suffix=='.json','Receipt must be a fresh evidence JSON')
    require(not output.exists() and not any(p.is_symlink() for p in [output,*output.parents]),'Receipt target exists or is linked')
    receipt=validate_capture(repo,evidence)
    require(digest(safe_file(evidence,'report.json'))==receipt['report_sha256'] and digest(safe_file(evidence,'input-contract.json'))==receipt['input_contract_sha256'],'Evidence changed before receipt')
    with output.open('x') as handle:handle.write(json.dumps(receipt,indent=2)+'\n')
    return receipt


def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
    s=sub.add_parser('snapshot');s.add_argument('--suite',type=Path,required=True);s.add_argument('--evidence',type=Path,required=True)
    v=sub.add_parser('verify');v.add_argument('--evidence',type=Path,required=True);v.add_argument('--receipt',type=Path,required=True)
    a=parser.parse_args()
    try:
        result=snapshot(REPO,a.suite,a.evidence) if a.command=='snapshot' else write_receipt(REPO,a.evidence,a.receipt)
        print(json.dumps({k:result[k] for k in ['kind','passed','input_count','output_count'] if k in result}))
    except (ValueError,KeyError,TypeError,OSError) as exc:parser.exit(1,str(exc)+'\n')

if __name__=='__main__':main()
