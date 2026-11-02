"""Strict body-only full-action review consumer and native input snapshot.

Reuses the frozen construction/packing verifiers and the existing runtime.
Successful checks establish input integrity, never contact or art acceptance.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

from PIL import Image

import build
import pack_sources
from build_contract import digest, keys, read_json, require, safe_file, stable
from review import validate_runtime

KIND = 'coastal-body-character-review-v1'
INPUT_KIND = 'coastal-all-actions-native-input-v1'
ACTIONS = ('idle', 'walk', 'run', 'hoe', 'water', 'harvest')
DIRECTIONS = ('south', 'west', 'east', 'north')
EXPECTED = {(a, d) for a in ACTIONS for d in DIRECTIONS}
OBSERVERS = {
    'poses': 'capture_registered_candidate.gd',
    'world': 'capture_registered_actions_world.gd',
    'timing': 'capture_registered_farm_timing.gd',
    'transitions': 'capture_registered_transitions.gd',
    'spatial': 'capture_registered_spatial.gd',
    'locomotion-timing': 'capture_registered_locomotion_timing.gd',
}
REPO = Path(__file__).resolve().parents[2]


def _absolute(path, base=None):
    path = Path(path).expanduser()
    if not path.is_absolute(): path = (base or Path.cwd()) / path
    require('..' not in path.parts and '.' not in path.parts, 'Path contains dot segments')
    require(not any(p.is_symlink() for p in [path, *path.parents]), 'Path symlink forbidden')
    return path


def body_clips(recipe):
    """Validate this consumer's body-only capability boundary after strict verify."""
    require(isinstance(recipe, dict) and type(recipe.get('schema_version')) is int
            and recipe['schema_version'] == 3 and recipe.get('slots') == {'body': None}
            and recipe.get('adaptations') == {}, 'Body review requires schema3 body-only recipe')
    clips = {}
    for clip in recipe.get('clips', []):
        require(isinstance(clip, dict), 'Invalid body clip')
        key = clip.get('action_id'), clip.get('direction')
        require(key in EXPECTED and key not in clips, 'Unknown or duplicate body capability')
        clips[key] = clip
        require(isinstance(clip.get('frames'), list) and clip['frames'], 'Missing body frames')
        for frame in clip['frames']:
            layers = frame.get('layers')
            require(isinstance(layers, list) and len(layers) == 1 and isinstance(layers[0], dict),
                    'Body review supports a single body layer')
            layer = layers[0]
            require(layer.get('id') == layer.get('slot') == 'body'
                    and frame.get('layer_order') == ['body'] and frame.get('registration') is None
                    and all(layer.get(k) is None for k in ('ownership', 'coverage', 'occlusion')),
                    'Body review requires canonical body and null masks')
    require(set(clips) == EXPECTED, 'Body review requires complete 24-capability coverage')
    caps = recipe.get('required_capabilities')
    require(isinstance(caps, list) and len(caps) == len(EXPECTED), 'Incomplete body capabilities')
    claimed = set()
    for cap in caps:
        keys(cap, 'action_id direction', 'body capability')
        key = cap['action_id'], cap['direction']
        require(key in EXPECTED and key not in claimed, 'Duplicate or unknown body capability')
        claimed.add(key)
    require(claimed == EXPECTED, 'Incomplete body capabilities')
    return clips


def _rgba(path):
    with Image.open(path) as image:
        require(image.format == 'PNG' and image.mode == 'RGBA', 'Actual RGBA PNG required: ' + str(path))
        image.load()
        return image.copy()


def preflight(repo, suite_path):
    """Return suite, verified manifest/recipe, tuple-indexed clips and source packs.

    manifest_path is an absolute Path. Suite references stay library-relative;
    snapshot translates only its native manifest binding to repository-relative.
    """
    repo = _absolute(repo); library = repo / 'art/characters'
    suite_path = _absolute(suite_path, repo)
    require(suite_path.is_relative_to(library/'reviews'), 'Suite outside reviews')
    suite = read_json(safe_file(repo, suite_path.relative_to(repo).as_posix(), 'art/characters/reviews'))
    keys(suite, 'kind schema_version resource_root scope manifest packed_sources runtime', 'body review suite')
    require(suite['kind'] == KIND and type(suite['schema_version']) is int and suite['schema_version'] == 1
            and suite['resource_root'] == 'art/characters' and suite['scope'] == 'review-only', 'Invalid body review scope')

    def binding(ref, namespace=None):
        keys(ref, 'file sha256', 'body review reference')
        path = safe_file(library, ref['file'], namespace)
        require(path.name == 'manifest.json' and digest(path) == ref['sha256'], 'Review manifest path or SHA mismatch')
        return path

    manifest_path = binding(suite['manifest'], 'builds')
    require(manifest_path.parent.parent == library/'builds', 'Build manifest outside canonical root')
    initial = read_json(manifest_path)
    require(isinstance(initial, dict) and isinstance(initial.get('inputs'), dict), 'Invalid strict manifest inputs')
    for name in initial['inputs']: safe_file(library, name)
    manifest = build.verify(repo, manifest_path.parent)
    recipe = read_json(safe_file(library, manifest['recipe'], 'recipes'))
    clips = body_clips(recipe)
    validate_runtime(suite['runtime'], clips)
    inputs = manifest['inputs']

    def bound(ref):
        keys(ref, 'file sha256', 'body dependency')
        path = safe_file(library, ref['file'])
        require(inputs.get(ref['file']) == ref['sha256'] == digest(path),
                'Packed source closure not directly bound: ' + ref['file'])
        return path

    refs = suite['packed_sources']
    require(isinstance(refs, list) and 0 < len(refs) <= 32, 'Missing or excessive packed sources')
    packed = []; seen = set(); indexed = {}
    for ref in refs:
        path = binding(ref)
        require(ref['file'].startswith(('sources/', 'parts/')) and ref['file'] not in seen,
                'Invalid or duplicate packed source')
        seen.add(ref['file']); bound(ref)
        pm = pack_sources.verify(repo, path.parent)
        for name, sha in pm['inputs'].items(): bound({'file': name, 'sha256': sha})
        for output in pm['outputs']:
            relative = (path.parent / output['file']).relative_to(library).as_posix()
            bound({'file': relative, 'sha256': output['sha256']})
        layout = read_json(path.parent/'layout.json')
        atlases = {}
        for row in layout['clips']:
            representations = {'body'}
            if row['action'] in ('hoe', 'water', 'harvest'):
                representations.add(row['action'] + '-visible')
            if row['representation'] not in representations: continue
            for frame in row['frames']:
                atlas_name = frame['atlas']
                if atlas_name not in atlases: atlases[atlas_name] = _rgba(safe_file(path.parent, atlas_name, 'atlases'))
                item = {'binding': ref, 'manifest': pm, 'directory': path.parent,
                        'layout': layout, 'clip': row, 'frame': frame, 'atlas': atlases[atlas_name]}
                indexed.setdefault((row['action'], row['direction'], frame['pose_id']), []).append(item)
        packed.append({'binding': ref, 'manifest': pm, 'directory': path.parent, 'layout': layout})

    used = set(); cache = {}
    def image(ref):
        path = bound(ref)
        if ref['file'] not in cache: cache[ref['file']] = _rgba(path)
        return cache[ref['file']]
    for (action, direction), clip in clips.items():
        poses = read_json(bound(clip['poses']))['variants'][clip['variant']]['frames']
        for frame, original in zip(clip['frames'], poses):
            body = frame['layers'][0]
            canonical = {k: original[k] for k in ('file', 'sha256')}
            require(body['texture'] == canonical, 'Body texture must bind actual canonical reference')
            texture = image(body['texture']); source = image(body['source'])
            matches = []
            for item in indexed.get((action, direction, frame['pose_id']), []):
                lf = item['frame']; layout = item['layout']; atlas = item['atlas']
                if (lf['duration_ms'] != frame['duration_ms'] or layout['cell_px'] != clip['canvas_px']
                        or layout['root_px'] != clip['root_anchor_px'] or layout['display_scale'] != clip['display_scale']):
                    continue
                x, y, w, h = lf['region_px']
                registered = atlas.crop((x, y, x+w, y+h))
                if (source.size == atlas.size and source.tobytes() == atlas.tobytes()
                        and texture.size == registered.size and texture.tobytes() == registered.tobytes()):
                    matches.append(item)
            require(len(matches) == 1, 'Body source atlas must match exactly one packed action/pose/geometry')
            used.add(matches[0]['binding']['file'])
    require(used == seen, 'Unused decorative packed source binding')
    for output in manifest['outputs']: _rgba(safe_file(manifest_path.parent, output['file'], 'frames'))
    return {'suite': suite, 'manifest': manifest, 'manifest_path': manifest_path, 'recipe': recipe,
            'clips': clips, 'packed_sources': packed, 'full_package': True}


def capture_plan(clips):
    """Use the existing native observer plan schema without inventing head layers."""
    pending = {}; pngs = ['overview.png']; transitions = set()
    for (action, direction), clip in clips.items():
        key = action+'-'+direction
        pending[key] = {'action_id': action, 'direction': direction,
            'pose_ids': [f['pose_id'] for f in clip['frames']],
            'duration_ms': [f['duration_ms'] for f in clip['frames']],
            **{k: clip[k] for k in ('canvas_px', 'root_anchor_px', 'display_scale')},
            'minimum_repetitions': 0 if action == 'idle' else 10, 'world_motion': action in ('walk', 'run')}
        for i in range(len(clip['frames'])):
            pngs.extend(f'stills/{key}-{b}-{i}.png' for b in ('dark', 'light'))
            pngs.append(f'world/{key}-pose-{i}.png')
    for direction in DIRECTIONS:
        for source in ('idle', 'walk', 'run'):
            for target in ('idle', 'walk', 'run'):
                if source != target: transitions.add(f'{source}-{direction}-to-{target}-{direction}')
            for target in ('hoe', 'water', 'harvest'): transitions.add(f'{source}-{direction}-to-{target}-{direction}')
        for action in ('hoe', 'water', 'harvest'): transitions.add(f'{action}-{direction}-to-idle-{direction}')
        for target in DIRECTIONS:
            if target != direction:
                for action in ('walk', 'run'): transitions.add(f'{action}-{direction}-to-{action}-{target}')
    return {'kind': 'coastal-all-actions-capture-plan-v1', 'scope': 'capture-plan-only', 'head_state': 'body',
        'clips': pending, 'required_pngs': sorted(pngs), 'transitions': sorted(transitions),
        'requires_contact_measurements': True, 'requires_actual_engine_delta': True,
        'requires_binary64_clock_records': True, 'requires_world_screen_transforms': True,
        'time_scenarios': {k: ['low-frame-rate', 'focus-pause', 'playback-rate', 'replay-once']
                           for k, c in pending.items() if c['action_id'] != 'idle'}}


def contract_digest(contract):
    return hashlib.sha256(stable({k: v for k, v in contract.items() if k != 'contract_digest'})).hexdigest()


def _input_contract(repo, suite_path, observer):
    repo = _absolute(repo); suite_path = _absolute(suite_path, repo)
    require(observer in OBSERVERS, 'Unknown body observer')
    checked = preflight(repo, suite_path); suite = checked['suite']; manifest = checked['manifest']
    library = repo/'art/characters'; manifest_path = checked['manifest_path']; files = {}
    def bind(path, expected=None):
        relative = path.relative_to(repo).as_posix(); path = safe_file(repo, relative); actual = digest(path)
        require(expected is None or actual == expected, 'Native input changed: ' + relative)
        require(relative not in files or files[relative] == actual, 'Conflicting native input')
        files[relative] = actual
    bind(suite_path); bind(manifest_path, suite['manifest']['sha256'])
    for name, sha in manifest['inputs'].items(): bind(library/name, sha)
    for output in manifest['outputs']: bind(manifest_path.parent/output['file'], output['sha256'])
    engines = [manifest['engine'], *[p['manifest']['engine'] for p in checked['packed_sources']]]
    for engine in engines:
        for name, sha in engine['code'].items(): bind(repo/'tools/characters'/name, sha)
    for name in ('body_review.py', 'review.py', 'all_actions_capture.py', 'all_actions_evidence.py', 'all_actions_native.py', 'construction_native.py', 'native_contract.py'):
        bind(repo/'tools/characters'/name)
    scene = 'character_headwear_trial.tscn' if observer in ('poses', 'spatial') else 'character_motion_lane.tscn'
    script = 'godot2d/tests/characters/'+OBSERVERS[observer]
    pending = [repo/script, repo/'godot2d/dev/characters'/scene, repo/'godot2d/project.godot']; visited = set()
    while pending:
        path = pending.pop()
        if path in visited: continue
        visited.add(path); bind(path)
        if path.suffix in {'.gd', '.tscn', '.tres', '.godot', '.cfg'}:
            for resource in re.findall(r'''["'](res://[^"'\n]+)["']''', path.read_text()):
                relative = resource[6:]
                if not relative or relative in ('.', '..'): continue
                require('..' not in Path(relative).parts, 'Runtime resource path escapes project')
                target = repo/'godot2d'/relative
                if target.is_file(): pending.append(target)
        uid = Path(str(path)+'.uid')
        if uid.is_file(): pending.append(uid)
    for relative, expected in files.items(): require(digest(safe_file(repo, relative)) == expected, 'Native input changed during freeze')
    plan = capture_plan(checked['clips'])
    contract = {'kind': INPUT_KIND, 'schema_version': 1, 'suite_kind': KIND, 'full_package': True,
        'scope': 'Complete body capability inputs only; not art, contact, user approval or release.',
        'suite': suite_path.relative_to(repo).as_posix(), 'observer': observer, 'observer_script': script,
        'capture_scene': 'res://dev/characters/'+scene,
        'manifest': {'manifest': manifest_path.relative_to(repo).as_posix(), 'sha256': suite['manifest']['sha256']},
        'artifact_digest': manifest['artifact_digest'], 'runtime': suite['runtime'], 'plan': plan,
        'transitions': plan['transitions'] if observer == 'transitions' else [], 'files': dict(sorted(files.items()))}
    if observer == 'world': contract['capture_every_rendered_frame'] = True
    contract['contract_digest'] = contract_digest(contract)
    return contract


def snapshot(repo, suite_path, evidence, observer='world'):
    from construction_native import _new_evidence_path
    evidence = _absolute(evidence); _new_evidence_path(evidence)
    contract = _input_contract(repo, suite_path, observer)
    evidence.mkdir(parents=True)
    (evidence/'input-contract.json').write_text(json.dumps(contract, ensure_ascii=False, indent=2)+'\n')
    return contract


def verify_inputs(repo, evidence):
    repo = _absolute(repo); evidence = _absolute(evidence)
    contract = read_json(safe_file(evidence, 'input-contract.json'))
    require(isinstance(contract, dict) and contract.get('kind') == INPUT_KIND
            and type(contract.get('schema_version')) is int and contract['schema_version'] == 1
            and contract.get('suite_kind') == KIND, 'Invalid body native input contract')
    require(contract.get('contract_digest') == contract_digest(contract), 'Native input contract changed')
    require(isinstance(contract.get('files'), dict) and contract['files'], 'Missing native input closure')
    for name, sha in contract['files'].items(): require(digest(safe_file(repo, name)) == sha, 'Native input changed: ' + name)
    rebuilt = _input_contract(repo, safe_file(repo, contract['suite'], 'art/characters/reviews'), contract.get('observer'))
    require(contract == rebuilt, 'Native input contract closure or plan changed')
    return {'scope': 'input-closure-only', 'passed': True, 'files_verified': len(contract['files']),
            'artifact_digest': contract['artifact_digest']}


def main():
    parser = argparse.ArgumentParser(description=__doc__); sub = parser.add_subparsers(dest='command', required=True)
    check = sub.add_parser('preflight'); check.add_argument('--suite', type=Path, required=True)
    freeze = sub.add_parser('snapshot'); freeze.add_argument('--suite', type=Path, required=True)
    freeze.add_argument('--evidence', type=Path, required=True); freeze.add_argument('--observer', choices=OBSERVERS, default='world')
    verify = sub.add_parser('verify-inputs'); verify.add_argument('--evidence', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == 'preflight':
            result = preflight(REPO, args.suite)
            output = {'passed': True, 'clips': len(result['clips']), 'frames': len(result['manifest']['outputs']), 'full_package': True}
        elif args.command == 'snapshot':
            result = snapshot(REPO, args.suite, args.evidence, args.observer)
            output = {'passed': True, 'clips': len(result['plan']['clips']), 'files': len(result['files']), 'contract_digest': result['contract_digest']}
        else: output = verify_inputs(REPO, args.evidence)
        print(json.dumps(output))
    except (ValueError, KeyError, TypeError, OSError) as exc: parser.exit(1, str(exc)+'\n')


if __name__ == '__main__': main()
