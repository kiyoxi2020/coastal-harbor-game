"""Single development review launcher; independent of shell working directory."""
from pathlib import Path
import argparse
import json
import math
import subprocess
from build_contract import digest, keys, read_json, require, safe_file
from build import verify

REPO = Path(__file__).resolve().parents[2]
STATES = ['bare', 'hair', 'hat', 'hair_hat']


def validate_fixed_identity(library, base, head):
    require(base.get('schema_version') == 3 and set(base.get('slots', {})) == {'body', 'top', 'pants', 'shoes'}
            and set(head.get('slots', {})) == {'hair', 'hat'}, 'Fixed outfit slots differ')
    template = read_json(safe_file(library, base['template']['file'], 'templates'))
    motion = read_json(safe_file(library, base['motion_set']['file'], 'templates'))
    require(template.get('template_id') == 'adult-standard-v1'
            and motion.get('motion_set_id') == 'review-motion-v1', 'Fixed outfit template/motion differs')
    for recipe, slot, design_id in [(base, 'top', 'top03'), (base, 'pants', 'original-pants'),
            (base, 'shoes', 'original-shoes'), (head, 'hair', 'hair-chestnut-short-v1'),
            (head, 'hat', 'hat-straw-navy-band-v1')]:
        design = read_json(safe_file(library, recipe['slots'][slot]['file'], 'parts'))
        require(design.get('design_id') == design_id and design.get('category') == slot,
                'Fixed outfit design differs: ' + slot)


def validate_runtime(data, clips):
    """Review timing is explicit and bound by the suite hash, never inherited."""
    def positive(value):
        return type(value) in (int, float) and math.isfinite(value) and value > 0
    keys(data, 'schema_version movement default_speed_factor locomotion_transition clips', 'review runtime')
    require(type(data['schema_version']) is int and data['schema_version'] == 1, 'Invalid runtime version')
    keys(data['movement'], 'walk run', 'runtime movement')
    for action in ['walk', 'run']:
        keys(data['movement'][action], 'base_world_speed', 'runtime speed')
        require(positive(data['movement'][action]['base_world_speed']), 'Invalid runtime speed')
    require(positive(data['default_speed_factor']) and 0.5 <= data['default_speed_factor'] <= 1,
            'Invalid runtime speed factor')
    transition = data['locomotion_transition']
    keys(transition, 'kind duration_ms', 'runtime locomotion transition')
    require(transition['kind'] == 'stable-idle-v1' and type(transition['duration_ms']) is int
            and 0 < transition['duration_ms'] <= 1000, 'Invalid stable transition')
    require(isinstance(data['clips'], dict) and set(data['clips']) == {a+'-'+d for a, d in clips},
            'Runtime clips incomplete')
    for (action, direction), clip in clips.items():
        row = data['clips'][action+'-'+direction]
        keys(row, 'playback_rate events', 'runtime clip')
        require(positive(row['playback_rate']), 'Invalid runtime playback rate')
        require(action not in ['walk', 'run'] or row['playback_rate'] == 1,
                'Locomotion rate is driven by actual distance and speed factor')
        events = row['events']
        require(isinstance(events, list) and (action in ['hoe', 'water', 'harvest'] or not events),
                'Runtime locomotion events require an explicit loop contract')
        seen = set()
        previous_time = -1
        for event in events:
            keys(event, 'event_id at_ms pose_id', 'runtime event')
            event_id = event['event_id']
            require(isinstance(event_id, str) and event_id and event_id != 'complete'
                    and event_id not in seen and type(event['at_ms']) is int and event['at_ms'] >= 0,
                    'Invalid runtime event identity/time')
            require(event['at_ms'] >= previous_time, 'Runtime events must be chronological')
            previous_time = event['at_ms']
            seen.add(event_id)
            elapsed = 0
            matched = False
            for frame in clip['frames']:
                if frame['pose_id'] == event['pose_id']:
                    matched = elapsed <= event['at_ms'] < elapsed+frame['duration_ms']
                elapsed += frame['duration_ms']
            require(matched, 'Runtime event outside declared pose')
    return data


def full_action_clips(base, head):
    """Check declared full-package coverage after strict build verification.

    This check is deliberately independent of pose count and art availability:
    source/mask/pixel validation remains the construction contract's job.
    """
    expected = {(action, direction)
                for action in ('idle', 'walk', 'run', 'hoe', 'water', 'harvest')
                for direction in ('south', 'west', 'east', 'north')}
    return _scoped_action_clips(base, head, expected)


def _scoped_action_clips(base, head, expected):
    require(isinstance(base, dict) and isinstance(head, dict), 'Full-action recipe missing')
    require(head.get('head_state') == 'hair_hat', 'Full-action delivery requires fixed hair_hat')


    def indexed(rows, label):
        require(isinstance(rows, list), label + ' missing')
        result = {}
        for row in rows:
            require(isinstance(row, dict), label + ' invalid')
            action, direction = row.get('action_id'), row.get('direction')
            require(isinstance(action, str) and isinstance(direction, str), label + ' invalid')
            key = action, direction
            require(key in expected and key not in result, label + ' unknown or duplicate clip')
            result[key] = row
        require(set(result) == expected, label + ' incomplete')
        return result

    clips = indexed(base.get('clips'), 'Full-action capability')
    indexed(base.get('required_capabilities'), 'Full-action capability requirements')
    heads = indexed(head.get('clips'), 'Full-action head')
    for key, clip in clips.items():
        frames, head_frames = clip.get('frames'), heads[key].get('frames')
        require(isinstance(frames, list) and frames and isinstance(head_frames, list),
                'Full-action head/base frames missing')
        require(all(isinstance(frame, dict) and isinstance(frame.get('pose_id'), str)
                    for frame in frames + head_frames), 'Full-action head/base pose invalid')
        require([frame['pose_id'] for frame in frames] == [frame['pose_id'] for frame in head_frames],
                'Full-action head pose coverage/order differs')
        if 'output_padding_px' in heads[key]:
            from build_contract import whole_frame_padding
            clips[key] = whole_frame_padding(clip, heads[key]['output_padding_px'])
    return clips


def construction_preflight(repo, suite_path):
    repo=Path(repo).resolve(); suite_path=Path(suite_path).absolute()
    require(suite_path.is_relative_to(repo/'art/characters/reviews'), 'Suite outside reviews')
    suite=read_json(safe_file(repo,suite_path.relative_to(repo).as_posix(),'art/characters/reviews'))
    if isinstance(suite, dict) and type(suite.get('schema_version')) is int and suite['schema_version'] == 2:
        keys(suite, 'kind schema_version resource_root scope head_state manifest samples canonical_idle runtime',
             'full-action review suite')
        require(suite['kind'] == 'coastal-character-construction-review-v1'
                and suite['resource_root'] == 'art/characters' and suite['scope'] == 'review-only'
                and suite['head_state'] == 'hair_hat', 'Invalid full-action review scope')
        binding = suite['manifest']
        keys(binding, 'manifest sha256', 'full-action manifest')
        path = safe_file(repo, binding['manifest'], 'art/characters/builds')
        require(path.name == 'manifest.json' and digest(path) == binding['sha256'],
                'Review manifest SHA mismatch')
        manifest = verify(repo, path.parent)
        library = repo/'art/characters'
        head = read_json(safe_file(library, manifest['recipe'], 'recipes'))
        require(head.get('schema_version') == 2, 'Full-action head recipe must use schema2')
        base = read_json(safe_file(library, head['base_recipe']['file'], 'recipes'))
        clips = full_action_clips(base, head)
        validate_fixed_identity(library, base, head)
        validate_runtime(suite['runtime'], clips)
        samples = suite['samples']
        require(isinstance(samples, list), 'Full-action samples missing')
        seen = set()
        for sample in samples:
            keys(sample, 'id action_id direction', 'full-action sample')
            action, direction = sample['action_id'], sample['direction']
            require(isinstance(action, str) and isinstance(direction, str), 'Invalid full-action sample')
            key = action, direction
            require(action != 'idle' and key in clips and key not in seen
                    and sample['id'] == action + '-' + direction, 'Invalid full-action sample')
            seen.add(key)
        require(seen == {key for key in clips if key[0] != 'idle'}, 'Full-action samples incomplete')
        idle = suite['canonical_idle']
        require(isinstance(idle, dict) and set(idle) == {'south', 'west', 'east', 'north'},
                'Full-action canonical idle incomplete')
        for direction, poses in idle.items():
            require(poses == [frame['pose_id'] for frame in clips['idle', direction]['frames']],
                    'Full-action canonical idle differs')
        return suite
    keys(suite,'kind schema_version resource_root scope sample_id states','construction review suite')
    require(suite['kind']=='coastal-character-construction-review-v1' and type(suite['schema_version']) is int and suite['schema_version']==1
            and suite['resource_root']=='art/characters' and suite['scope']=='review-only'
            and suite['sample_id']=='hoe-west' and isinstance(suite['states'],dict) and set(suite['states'])==set(STATES),'Invalid construction review scope')
    base=None
    for state in STATES:
        ref=suite['states'][state];keys(ref,'manifest sha256','review state')
        path=safe_file(repo,ref['manifest'],'art/characters/builds')
        require(path.name=='manifest.json' and digest(path)==ref['sha256'],'Review manifest SHA mismatch')
        manifest=verify(repo,path.parent)
        recipe=read_json(safe_file(repo/'art/characters',manifest['recipe'],'recipes'))
        require(recipe.get('schema_version')==2 and recipe.get('head_state')==state,'Review state recipe mismatch')
        if base is None:base=recipe['base_recipe']
        require(recipe['base_recipe']==base,'Review states must share one base recipe')
    return suite


def candidate_preflight(repo, suite_path):
    """An internal subset is explicitly bounded and never a full delivery."""
    repo = Path(repo).resolve(); suite_path = Path(suite_path).absolute()
    require(suite_path.is_relative_to(repo/'art/characters/reviews'), 'Candidate outside reviews')
    suite = read_json(safe_file(repo, suite_path.relative_to(repo).as_posix(), 'art/characters/reviews'))
    keys(suite, 'kind schema_version resource_root scope head_state manifest capabilities samples canonical_idle runtime', 'candidate suite')
    require(suite['kind']=='coastal-character-construction-candidate-v1'
            and type(suite['schema_version']) is int and suite['schema_version']==1
            and suite['resource_root']=='art/characters' and suite['scope']=='internal-review-only'
            and suite['head_state']=='hair_hat', 'Invalid internal candidate scope')
    require(isinstance(suite['capabilities'], list) and 0<len(suite['capabilities'])<=24, 'Candidate capabilities missing')
    expected = set()
    for cap in suite['capabilities']:
        keys(cap, 'action_id direction', 'candidate capability')
        require(isinstance(cap['action_id'],str) and isinstance(cap['direction'],str)
                and cap['action_id'] in ['idle','walk','run','hoe','water','harvest']
                and cap['direction'] in ['south','west','east','north'], 'Invalid candidate capability')
        key = cap['action_id'],cap['direction']
        require(key not in expected, 'Duplicate candidate capability'); expected.add(key)
    keys(suite['manifest'], 'manifest sha256', 'candidate manifest')
    path = safe_file(repo,suite['manifest']['manifest'],'art/characters/builds')
    require(path.name=='manifest.json' and digest(path)==suite['manifest']['sha256'], 'Candidate manifest SHA mismatch')
    manifest = verify(repo,path.parent); library = repo/'art/characters'
    head = read_json(safe_file(library,manifest['recipe'],'recipes'))
    base = read_json(safe_file(library,head['base_recipe']['file'],'recipes'))
    validate_fixed_identity(library,base,head)
    clips = _scoped_action_clips(base,head,expected)
    directions = {direction for _,direction in clips}
    require(all(('idle',direction) in clips for direction in directions), 'Candidate canonical idle missing')
    idle = suite['canonical_idle']
    require(isinstance(idle,dict) and set(idle)==directions, 'Candidate canonical idle scope differs')
    for direction in directions:
        require(idle[direction]==[f['pose_id'] for f in clips['idle',direction]['frames']], 'Candidate canonical idle differs')
    require(isinstance(suite['samples'],list), 'Candidate samples missing')
    seen = set()
    for sample in suite['samples']:
        keys(sample,'id action_id direction','candidate sample')
        require(isinstance(sample['action_id'],str) and isinstance(sample['direction'],str), 'Invalid candidate sample')
        key = sample['action_id'],sample['direction']
        require(key in clips and key[0]!='idle' and key not in seen
                and sample['id']==key[0]+'-'+key[1], 'Invalid candidate sample')
        seen.add(key)
    require(seen=={key for key in clips if key[0]!='idle'}, 'Candidate samples incomplete')
    validate_runtime(suite['runtime'],clips)
    return suite


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('suite',choices=['locomotion','farming','wardrobe','headwear','static-candidates','headwear-construction','all-actions-construction'],nargs='?',default='headwear')
    parser.add_argument('--dry-run',action='store_true')
    args=parser.parse_args();lib=REPO/'art/characters'
    path=lib/'reviews'/args.suite/'review.json'
    try:
        if args.suite in ['headwear-construction','all-actions-construction']:
            checked=construction_preflight(REPO,path)
            if args.suite=='all-actions-construction':
                require(checked['schema_version']==2, 'All-actions launcher requires full-package scope')
            scene='res://dev/characters/character_headwear_trial.tscn' if args.suite=='all-actions-construction' else 'res://dev/characters/character_headwear_hoe_review.tscn'
            config={'scene':scene,'args':['--construction-suite='+str(path)]}
        else:config=read_json(path)
        if 'html' in config:cmd=['open',str(lib/config['html'])]
        else:
            cmd=['/Applications/Godot.app/Contents/MacOS/Godot','--path',str(REPO/'godot2d'),'--log-file','/private/tmp/coastal-character-'+args.suite+'-review.log',config['scene'],'--']+[s.replace('{library}',str(lib)) for s in config.get('args',[])]
        if args.dry_run:print(json.dumps(cmd,ensure_ascii=False))
        else:raise SystemExit(subprocess.call(cmd,cwd=REPO))
    except (ValueError,KeyError,TypeError,OSError) as exc:parser.exit(1,str(exc)+'\n')

if __name__=='__main__':main()
