"""Derive temporary authoring contracts from tracked main-game runtime pixels.

Only the integration manifest, its PNGs and SpriteFrames are repository inputs.
The schema3 template, source bundle and recipe below are independent test data;
they make no claim to recover the local V4/V5 production authoring graph.
"""
import copy
import json
from pathlib import Path
import shutil

from build_contract import digest, safe_file

REPO = Path(__file__).resolve().parents[3]
PACKAGE = Path('godot2d/assets/characters/integrations/adult-v4-tank-visible-r001')
BUILD = Path('art/characters/builds/runtime-fixture-r001')
FRAMES = Path('godot2d/resources/player_body_v4_frames.tres')


def runtime_manifest():
    return json.loads((REPO/PACKAGE/'manifest.json').read_text())


def runtime_png(frame):
    path = frame['texture']
    if not path.startswith('res://assets/characters/integrations/adult-v4-tank-visible-r001/frames/'):
        raise ValueError('Unexpected main runtime fixture texture')
    return safe_file(REPO/'godot2d', path.removeprefix('res://'),
                     'assets/characters/integrations/adult-v4-tank-visible-r001/frames')


def animation_inputs(manifest):
    """The actual clip order, poses, timing and output identities for unit APIs."""
    clips, outputs = [], []
    for clip in manifest['clips']:
        frames = []
        for frame in clip['frames']:
            frames.append({'pose_id': frame['pose_id'], 'duration_ms': frame['duration_ms']})
            outputs.append({'file': f"frames/{clip['action']}/{clip['direction']}/{frame['pose_id']}.png",
                            'sha256': frame['sha256'], 'rgba_sha256': frame['rgba_sha256'],
                            'size': copy.deepcopy(manifest['geometry']['canvas_px'])})
        clips.append({'action_id': clip['action'], 'direction': clip['direction'],
                      'canvas_px': copy.deepcopy(manifest['geometry']['canvas_px']),
                      'root_anchor_px': copy.deepcopy(manifest['geometry']['root_anchor_px']),
                      'display_scale': 1.0, 'variant': 'visible', 'frames': frames})
    return {'clips': clips}, {'outputs': outputs}


def write_fixture(repo):
    """Write a strict recipe with full-frame sources, using only runtime PNGs."""
    repo = Path(repo)
    lib = repo/'art/characters'
    manifest = runtime_manifest()
    recipe, _ = animation_inputs(manifest)

    def reference(name): return {'file': name, 'sha256': digest(lib/name)}
    def write(name, value):
        path = lib/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))
        return reference(name)
    def image(name, source):
        path = lib/name
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, path)
        return reference(name)

    sources, textures = {}, {}
    for clip in manifest['clips']:
        for frame in clip['frames']:
            pose = frame['pose_id']
            original = runtime_png(frame)
            if digest(original) != frame['sha256']:
                raise ValueError('Main runtime oracle PNG SHA mismatch')
            sources[pose] = image(f'sources/runtime-fixture/originals/{pose}.png', original)
            textures[pose] = image(f'templates/runtime-fixture/motions/runtime/body-views/{pose}.png', original)
    bundle = write('sources/runtime-fixture/source.json', {
        'source_id': 'runtime-fixture', 'assets': [
            {'new_path': 'art/characters/'+ref['file'], 'new_sha256': ref['sha256']}
            for ref in sources.values()]})
    actions = {}
    for clip in recipe['clips']:
        action, direction = clip['action_id'], clip['direction']
        originals = []
        for frame in clip['frames']:
            pose = frame['pose_id']
            originals.append({**frame, **textures[pose]})
            frame.update(layers=[{
                'id': 'body', 'slot': 'body', 'pose_id': pose, 'texture': textures[pose],
                'source': sources[pose], 'source_bundle': bundle,
                'ownership': None, 'coverage': None, 'occlusion': None,
                'interface_scope': 'same-pose-reference', 'placement_mode': 'full_frame',
                'offset_px': [0, 0], 'local_scale': [1, 1]}],
                layer_order=['body'], registration=None, composition='ownership-replace')
        geometry = {key: copy.deepcopy(clip[key]) for key in ['canvas_px', 'root_anchor_px', 'display_scale']}
        clip['poses'] = write(f'templates/runtime-fixture/motions/runtime/actions/{action}/r001/{direction}/poses.json', {
            'template_id': 'runtime-fixture', 'action_id': action, 'direction': direction,
            'variants': {'visible': {**geometry, 'frames': originals}}})
        actions.setdefault(action, {})[direction] = clip['poses']['file']
    motion_actions = {}
    for action, directions in actions.items():
        action_ref = write(f'templates/runtime-fixture/motions/runtime/actions/{action}/r001/action.json', {
            'action_id': action, 'revision': 'r001', 'loop': action in {'idle', 'walk', 'run'},
            'directions': directions})
        motion_actions[action] = action_ref['file']
        for clip in recipe['clips']:
            if clip['action_id'] == action: clip['action'] = action_ref
    motion = write('templates/runtime-fixture/motions/runtime/motion-set.json', {
        'template_id': 'runtime-fixture', 'motion_set_id': 'runtime', 'actions': motion_actions})
    template = write('templates/runtime-fixture/template.json', {
        'template_id': 'runtime-fixture', 'active_revision': 'r001', 'motion_set': motion['file']})
    recipe.update(kind='coastal-character-construction-v1', schema_version=3,
                  resource_root='art/characters', character_model_id=manifest['character_model_id'],
                  recipe_id='runtime-fixture', revision='r001', template=template, motion_set=motion,
                  slots={'body': None}, adaptations={}, authoring_inputs=list(sources.values()),
                  required_capabilities=[{'action_id': c['action_id'], 'direction': c['direction']}
                                         for c in recipe['clips']])
    path = lib/'recipes/runtime-fixture/r001.json'
    write('recipes/runtime-fixture/r001.json', recipe)
    return {'repo': repo, 'lib': lib, 'recipe': recipe, 'path': path,
            'output': repo/BUILD, 'runtime': manifest}
