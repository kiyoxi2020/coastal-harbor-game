"""Preflight for finite schema3 body + prepared top authoring reviews.

Raw reconstruction is delegated to the existing strict and source preparation
verifiers. This consumer adds explicit source-to-pose and review-scope binding.
"""
from pathlib import Path
import math

import build
import prepare_registered_source as prep

KIND = 'coastal-registered-character-review-v1'


def runtime_valid(value):
    prep.keys(value, 'world_scale walk_world_speed speed_factor', 'registered runtime')
    for name in value:
        prep.require(type(value[name]) in (int, float) and math.isfinite(value[name]), 'Invalid runtime number')
    prep.require(0 < value['world_scale'] <= 1 and 0 < value['walk_world_speed'] <= 1000
                 and .5 <= value['speed_factor'] <= 1, 'Runtime number out of range')


def locomotion_clips(recipe):
    prep.require(isinstance(recipe, dict) and type(recipe.get('schema_version')) is int
                 and recipe['schema_version'] == 3 and recipe.get('slots', {}).keys() == {'body', 'top'},
                 'Registered review requires schema3 body + top')
    prep.require(recipe['slots']['body'] is None and isinstance(recipe.get('clips'), list)
                 and 0 < len(recipe['clips']) <= 8, 'Invalid registered review clips')
    clips = {}
    for clip in recipe['clips']:
        prep.require(isinstance(clip, dict) and clip.get('action_id') in ('idle', 'walk')
                     and clip.get('direction') in ('north', 'west', 'south', 'east'),
                     'Unsupported registered action/direction; only idle/walk supported')
        key = clip['action_id'], clip['direction']
        prep.require(key not in clips, 'Duplicate registered clip')
        clips[key] = clip
    prep.require(any(action == 'walk' for action, _ in clips), 'Registered walk capability missing')
    directions = {direction for _, direction in clips}
    prep.require(set(clips) == {(action, direction) for action in ('idle', 'walk') for direction in directions},
                 'Every registered walk direction needs matching idle')
    required = recipe.get('required_capabilities')
    prep.require(isinstance(required, list) and len(required) == len(clips), 'Missing registered capabilities')
    claimed = set()
    for cap in required:
        prep.keys(cap, 'action_id direction', 'registered capability')
        prep.require(isinstance(cap['action_id'], str) and isinstance(cap['direction'], str), 'Invalid capability')
        key = cap['action_id'], cap['direction']
        prep.require(key in clips and key not in claimed, 'Unknown or duplicate capability')
        claimed.add(key)
    geometry = None
    for clip in clips.values():
        current = {key: clip.get(key) for key in ('canvas_px', 'root_anchor_px', 'display_scale')}
        if geometry is None: geometry = current
        prep.require(current == geometry, 'Registered trial requires consistent whole-frame geometry')
        prep.require(isinstance(clip.get('frames'), list) and clip['frames'], 'Missing registered frames')
        for frame in clip['frames']:
            prep.require(isinstance(frame, dict) and frame.get('composition') == 'alpha-over'
                         and frame.get('registration') is None, 'Registered review supports prepared alpha-over frames')
            layers = frame.get('layers')
            prep.require(isinstance(layers, list) and len(layers) == 2
                         and all(isinstance(layer, dict) for layer in layers), 'Invalid registered frame layers')
            bodies = [layer for layer in layers if layer.get('slot') == 'body']
            tops = [layer for layer in layers if layer.get('slot') == 'top']
            prep.require(len(bodies) == len(tops) == 1
                         and frame.get('layer_order') == [bodies[0].get('id'), tops[0].get('id')],
                         'Registered frame layer order must be body then top')
            prep.require(all(layer.get(field) is None for layer in layers for field in ('coverage', 'occlusion')),
                         'Registered frame scope requires null coverage/occlusion')
    return clips


def preflight(repo, suite_path):
    repo = prep.checked_absolute(repo)
    library = prep.checked_absolute(repo / 'art/characters')
    suite_path = prep.checked_absolute(suite_path, repo)
    prep.require(suite_path.is_relative_to(library / 'reviews') and suite_path.is_file(), 'Suite outside reviews')
    suite = prep.load_json(suite_path)
    prep.keys(suite, 'kind schema_version resource_root scope manifest prepared_sources runtime', 'registered review suite')
    prep.require(suite['kind'] == KIND and type(suite['schema_version']) is int and suite['schema_version'] == 1
                 and suite['resource_root'] == 'art/characters' and suite['scope'] == 'review-only', 'Invalid registered review scope')
    runtime_valid(suite['runtime'])

    def binding(ref, prefix):
        prep.keys(ref, 'file sha256', 'review reference')
        path = prep.relative_file(library, ref['file'])
        prep.require(ref['file'].startswith(prefix + '/') and path.name == 'manifest.json'
                     and isinstance(ref['sha256'], str) and prep.sha(path.read_bytes()) == ref['sha256'],
                     'Review manifest path or SHA mismatch')
        return path

    manifest_path = binding(suite['manifest'], 'builds')
    prep.require(manifest_path.parent.parent == library / 'builds', 'Build manifest must be at canonical root')
    # Check all lexical paths before the older verifier can resolve ancestors.
    initial = prep.load_json(manifest_path)
    prep.require(isinstance(initial, dict) and isinstance(initial.get('inputs'), dict), 'Invalid strict manifest inputs')
    for name in initial['inputs']:
        prep.relative_file(library, name)
    manifest = build.verify(repo, manifest_path.parent)
    recipe = prep.load_json(prep.relative_file(library, manifest['recipe']))
    clips = locomotion_clips(recipe)
    inputs = manifest['inputs']

    def bound(ref):
        prep.keys(ref, 'file sha256', 'bound registered reference')
        path = prep.relative_file(library, ref['file'])
        prep.require(inputs.get(ref['file']) == ref['sha256'] == prep.sha(path.read_bytes()),
                     'Preparation input closure not directly bound: ' + ref['file'])
        return path

    refs = suite['prepared_sources']
    prep.require(isinstance(refs, list) and 0 < len(refs) <= 32, 'Missing or excessive prepared sources')
    prepared = {}; seen = set()
    for ref in refs:
        path = binding(ref, 'sources')
        prep.require(ref['file'] not in seen, 'Duplicate prepared source')
        seen.add(ref['file']); bound(ref)
        source_manifest = prep.verify(repo, path.parent)
        prep.require(isinstance(source_manifest['inputs'], dict), 'Invalid preparation inputs')
        for name, digest in source_manifest['inputs'].items(): bound({'file': name, 'sha256': digest})
        source_json = next(row for row in source_manifest['outputs'] if row['file'] == 'source.json')
        bundle = {'file': path.parent.relative_to(library).as_posix() + '/source.json', 'sha256': source_json['sha256']}
        bound(bundle)
        outputs = {row['file']: row for row in source_manifest['outputs']}
        for frame in source_manifest['frames']:
            key = (ref['file'], frame['pose_id'])
            prep.require(key not in prepared, 'Duplicate prepared pose')
            prefix = path.parent.relative_to(library).as_posix() + '/'
            prepared[key] = {'frame': frame, 'bundle': bundle,
                'refs': {folder: {'file': prefix + folder + '/' + frame['pose_id'] + '.png',
                                  'sha256': outputs[folder + '/' + frame['pose_id'] + '.png']['sha256']}
                         for folder in ('materials', 'ownership', 'textures')}}
    def same_pose_annotation(selector, clip, frame, canonical):
        prep.keys(selector, 'document record', 'registered pose annotation selector')
        prep.require(isinstance(selector['record'], str), 'Invalid pose annotation selector')
        data = prep.load_json(bound(selector['document']))
        prep.require(isinstance(data, dict) and data.get('kind') == 'coastal-pose-annotations-v1'
                     and isinstance(data.get('records'), list), 'Invalid pose annotation document')
        matches = [row for row in data['records'] if isinstance(row, dict)
                   and row.get('record_id') == selector['record']]
        prep.require(len(matches) == 1, 'Missing or duplicate source pose annotation')
        row = matches[0]
        prep.require(row.get('poses') == clip['poses'] and row.get('variant') == clip['variant']
                     and row.get('pose_id') == frame['pose_id'] and row.get('reference_frame') == canonical,
                     'Prepared source annotation must match actual canonical pose')
        for field in ('canvas_px', 'root_anchor_px', 'display_scale'):
            prep.require(row.get(field) == clip[field], 'Prepared source annotation geometry mismatch')

    adaptation = prep.load_json(bound(recipe['adaptations']['top']))
    views = {row['view_id']: row for row in adaptation['views']}
    mappings = {row['mapping_id']: row for row in adaptation['mappings']}
    used_sources = set()
    for clip in clips.values():
        poses = prep.load_json(bound(clip['poses']))
        canonical = poses['variants'][clip['variant']]['frames']
        for frame, original in zip(clip['frames'], canonical):
            bodies = [layer for layer in frame['layers'] if layer['slot'] == 'body']
            tops = [layer for layer in frame['layers'] if layer['slot'] == 'top']
            prep.require(len(bodies) == 1 and len(tops) == 1
                         and bodies[0]['texture'] == {key: original[key] for key in ('file', 'sha256')},
                         'Review body layer must bind the actual canonical body reference')
            layer = tops[0]; view = views[layer['view_binding']['view_id']]; mapping = mappings[layer['view_binding']['mapping_id']]
            prep.keys(view['extraction'], 'kind density_normalization', 'registered prepared extraction')
            prep.require(view['extraction']['kind'] == 'binary-rgba-extract-v1'
                         and view['extraction']['density_normalization'] is None,
                         'Registered view scope requires prepared binary extraction without density normalization')
            prep.require(mapping['coverage'] is None and mapping['occlusion'] is None,
                         'Registered mapping scope requires null coverage/occlusion')
            canonical_ref = {field: original[field] for field in ('file', 'sha256')}
            same_pose_annotation(view['source_pose'], clip, frame, canonical_ref)
            same_pose_annotation(mapping['target_pose'], clip, frame, canonical_ref)
            matches = [(key, item) for key, item in prepared.items()
                       if key[1] == frame['pose_id'] and item['refs']['materials'] == view['source']
                       and item['bundle'] == view['source_bundle'] and item['refs']['ownership'] == view['source_ownership']['mask']]
            prep.require(len(matches) == 1, 'Nonbody view must bind exactly one same-pose prepared source')
            (key, item), = matches
            prep.require(item['frame']['action'] == clip['action_id'] and item['frame']['direction'] == clip['direction']
                         and item['frame']['canonical_poses'] == clip['poses'] and item['frame']['variant'] == clip['variant'],
                         'Prepared source pose/template/action mismatch')
            for field in ('canvas_px', 'root_anchor_px', 'display_scale'):
                prep.require(item['frame'][field] == clip[field], 'Prepared source geometry mismatch')
            for ref in item['refs'].values(): bound(ref)
            bound(item['bundle'])
            # Strict construction requires parts/ textures. They must be exact
            # same-pose prepared samples even if PNG encoding differs.
            copied = prep.image(bound(mapping['texture']), 'RGBA')
            source_texture = prep.image(bound(item['refs']['textures']), 'RGBA')
            prep.require(copied.size == source_texture.size and copied.tobytes() == source_texture.tobytes(),
                         'Mapping texture differs from same-pose prepared output')
            used_sources.add(key[0])
    prep.require(used_sources == seen, 'Unused decorative prepared source binding')
    return suite
