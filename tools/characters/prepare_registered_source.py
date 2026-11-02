#!/usr/bin/env python3
"""Derive review-only garment sources using an existing, verified body registration.

This is source preprocessing, not character construction or release validation.
A binary ownership mask selects unchanged sampled RGBA, including hidden RGB.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import io
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import tempfile

from PIL import Image, __version__ as PILLOW_VERSION

PLAN_KIND = 'coastal-registered-source-preparation-plan-v1'
MANIFEST_KIND = 'coastal-registered-source-preparation-v1'
REPO = Path(__file__).absolute().parents[2]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def keys(value, names, label):
    require(isinstance(value, dict) and set(value) == set(names.split()), 'Invalid keys: ' + label)


def identifier(value):
    require(isinstance(value, str) and re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]*', value), 'Invalid identifier')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def stable(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def document_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode()


def checked_absolute(value, base=None):
    path = Path(value)
    require('..' not in path.parts, 'Parent traversal forbidden')
    if not path.is_absolute():
        path = (Path.cwd() if base is None else base) / path
    path = Path(os.path.abspath(path))
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current /= part
        require(not current.is_symlink(), 'Symlink forbidden: ' + str(current))
    return path


def relative_file(root, name):
    require(isinstance(name, str) and name and '\\' not in name, 'Invalid relative file')
    relative = PurePosixPath(name)
    require(not relative.is_absolute() and all(x not in ('', '.', '..') for x in name.split('/')),
            'Invalid relative file')
    path = checked_absolute(root.joinpath(*relative.parts))
    require(path.is_relative_to(root) and path.is_file(), 'Missing or outside input: ' + name)
    return path


def load_json(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, 'Duplicate JSON key: ' + key)
            result[key] = value
        return result
    try:
        require(path.stat().st_size <= 16 * 1024 * 1024, 'JSON too large')
        return json.loads(path.read_text(encoding='utf8'), object_pairs_hook=unique,
                          parse_constant=lambda value: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError('Cannot read JSON: ' + str(path)) from exc


def integers(value, length, minimum=0):
    return isinstance(value, list) and len(value) == length and all(type(x) is int and x >= minimum for x in value)


def fraction(value, label):
    require(integers(value, 2, 1) and max(value) <= 1000000, 'Invalid ' + label)
    result = Fraction(*value)
    require([result.numerator, result.denominator] == value, 'Nonreduced ' + label)
    return result


def rational(value):
    value = Fraction(value)
    return [value.numerator, value.denominator]


def image(path, mode):
    try:
        with Image.open(path) as opened:
            require(opened.format == 'PNG' and opened.mode == mode, 'Expected PNG ' + mode + ': ' + str(path))
            require(0 < min(opened.size) and max(opened.size) <= 8192
                    and opened.width * opened.height <= 32 * 1024 * 1024, 'Image extent too large')
            opened.load()
            return opened.copy()
    except (OSError, Image.DecompressionBombError) as exc:
        raise ValueError('Cannot decode PNG: ' + str(path)) from exc


def box_crop(opened, box):
    require(integers(box, 4) and min(box[2:]) > 0
            and box[0] + box[2] <= opened.width and box[1] + box[3] <= opened.height, 'Invalid source box')
    return opened.crop((box[0], box[1], box[0] + box[2], box[1] + box[3]))


def mapped(opened, canvas, target_root, source_root, scale):
    inverse = 1 / scale
    return opened.transform(tuple(canvas), Image.Transform.AFFINE,
        (float(inverse), 0, float(source_root[0] - target_root[0] * inverse),
         0, float(inverse), float(source_root[1] - target_root[1] * inverse)),
        resample=Image.Resampling.NEAREST, fillcolor=(0, 0, 0, 0) if opened.mode == 'RGBA' else 0)


def engine():
    script = checked_absolute(Path(__file__).absolute())
    return {'pillow': PILLOW_VERSION,
            'code': {'tools/characters/prepare_registered_source.py': sha(script.read_bytes())}}


def output_path(repo, output, source_id):
    path = checked_absolute(output, repo)
    source = repo / 'art/characters/sources' / source_id
    temporary_parts = path.relative_to('/private/tmp').parts if path.is_relative_to('/private/tmp') else ()
    temporary = bool(temporary_parts) and temporary_parts[0].startswith('coastal-')
    if path.is_relative_to(repo / 'art/characters'):
        require(path == source, 'Source output identity mismatch')
    require(path == source or temporary, 'Output must be new sources/<source_id> or /private/tmp/coastal-*')
    return path


def prepare(repo, plan_path):
    repo = checked_absolute(repo)
    library = checked_absolute(repo / 'art/characters')
    plan_path = checked_absolute(plan_path, repo)
    require(plan_path.is_relative_to(library / 'sources') and plan_path.is_file(), 'Plan must be inside sources')
    plan_relative = plan_path.relative_to(library).as_posix()
    plan = load_json(plan_path)
    keys(plan, 'kind schema_version resource_root source_id registration_plan frames authoring_inputs', 'preparation plan')
    require(plan['kind'] == PLAN_KIND and type(plan['schema_version']) is int and plan['schema_version'] == 1
            and plan['resource_root'] == 'art/characters', 'Unsupported preparation plan')
    identifier(plan['source_id'])
    inputs = {plan_relative: sha(plan_path.read_bytes())}

    def bind(ref):
        keys(ref, 'file sha256', 'reference')
        require(isinstance(ref['sha256'], str) and re.fullmatch(r'[0-9a-f]{64}', ref['sha256']), 'Invalid SHA256')
        path = relative_file(library, ref['file'])
        require(ref['file'].split('/')[0] in {'sources', 'templates', 'parts', 'builds'}, 'Invalid input namespace')
        actual = sha(path.read_bytes())
        require(actual == ref['sha256'], 'Input SHA mismatch: ' + ref['file'])
        inputs[ref['file']] = actual
        return path

    def authoring(refs):
        require(isinstance(refs, list) and len(refs) <= 4096, 'Invalid authoring inputs')
        for ref in refs:
            bind(ref)

    registration = load_json(bind(plan['registration_plan']))
    keys(registration, 'kind schema_version resource_root source_id revision cell_px root_px rows frames', 'body registration plan')
    require(registration['kind'] == 'coastal-character-source-atlas-plan-v1'
            and type(registration['schema_version']) is int and registration['schema_version'] == 1
            and registration['resource_root'] == 'art/characters', 'Invalid body registration plan')
    identifier(registration['source_id']); identifier(registration['revision'])
    require(plan['registration_plan']['file'] == f"sources/{registration['source_id']}/packing/{registration['revision']}.json",
            'Body registration plan identity mismatch')
    canvas, target_root = registration['cell_px'], registration['root_px']
    require(integers(canvas, 2, 1) and max(canvas) <= 2048, 'Invalid canonical canvas')
    require(integers(target_root, 2) and all(target_root[i] < canvas[i] for i in (0, 1)), 'Invalid canonical root')
    require(registration['rows'] == ['north', 'west', 'south', 'east'], 'Invalid registration rows')
    require(isinstance(registration['frames'], list) and 0 < len(registration['frames']) <= 4096, 'Invalid body frames')
    authoring(plan['authoring_inputs'])
    require(isinstance(plan['frames'], list) and 0 < len(plan['frames']) <= 256, 'Missing or excessive frames')
    seen, layouts, outputs = set(), [], {}
    for frame in plan['frames']:
        keys(frame, 'pose_id source ownership box_px density_ratio canonical_poses variant', 'preparation frame')
        pose = frame['pose_id']; identifier(pose); identifier(frame['variant'])
        require(pose not in seen, 'Duplicate pose'); seen.add(pose)
        matches = [item for item in registration['frames'] if isinstance(item, dict)
                   and item.get('representation') == 'body' and item.get('pose_id') == pose]
        require(len(matches) == 1, 'Missing or duplicate body pose registration')
        body = matches[0]
        keys(body, 'representation action direction frame_index pose_id duration_ms source source_root_px scale authoring_inputs', 'body frame')
        identifier(body['action'])
        require(body['direction'] in registration['rows'], 'Invalid body direction')
        require(type(body['frame_index']) is int and body['frame_index'] >= 0
                and type(body['duration_ms']) is int and 0 < body['duration_ms'] <= 60000, 'Invalid body clock')
        raw = body['source']
        keys(raw, 'file sha256 size_px box_px', 'raw body source')
        raw_image = image(bind({k: raw[k] for k in ('file', 'sha256')}), 'RGBA')
        require(integers(raw['size_px'], 2, 1) and raw['size_px'] == list(raw_image.size), 'Raw body size mismatch')
        body_crop = box_crop(raw_image, raw['box_px'])
        require(body_crop.getchannel('A').getbbox() is not None, 'Empty raw body source')
        source_root = body['source_root_px']
        require(integers(source_root, 2) and all(source_root[i] < body_crop.size[i] for i in (0, 1)), 'Invalid body source root')
        scale = fraction(body['scale'], 'body scale')
        require(Fraction(1, 64) <= scale <= 16, 'Body scale out of range')
        authoring(body['authoring_inputs'])
        poses_path = bind(frame['canonical_poses'])
        poses = load_json(poses_path)
        relative_parts = PurePosixPath(frame['canonical_poses']['file']).parts
        require(len(relative_parts) >= 9 and relative_parts[0] == 'templates'
                and relative_parts[2] == 'motions' and relative_parts[4] == 'actions'
                and relative_parts[5] == body['action'] and relative_parts[-2] == body['direction']
                and relative_parts[-1] == 'poses.json', 'Canonical motion pose path mismatch')
        require(isinstance(poses, dict) and (poses.get('template_id'), poses.get('action_id'), poses.get('direction'))
                == (relative_parts[1], body['action'], body['direction']), 'Canonical pose identity mismatch')
        require(isinstance(poses.get('variants'), dict) and frame['variant'] in poses['variants'], 'Missing canonical variant')
        variant = poses['variants'][frame['variant']]
        require(isinstance(variant, dict) and variant.get('canvas_px') == canvas
                and variant.get('root_anchor_px') == target_root, 'Canonical variant geometry mismatch')
        display = variant.get('display_scale')
        require(type(display) in (int, float) and math.isfinite(display) and display > 0, 'Invalid display scale')
        require(isinstance(variant.get('frames'), list) and 0 < len(variant['frames']) <= 256, 'Invalid canonical frames')
        canonical_matches = [item for item in variant['frames'] if isinstance(item, dict) and item.get('pose_id') == pose]
        require(len(canonical_matches) == 1, 'Missing or duplicate canonical pose')
        canonical = canonical_matches[0]
        require(canonical.get('duration_ms') == body['duration_ms'], 'Canonical clock mismatch')
        canonical_image = image(bind({k: canonical.get(k) for k in ('file', 'sha256')}), 'RGBA')
        require(list(canonical_image.size) == canvas and mapped(body_crop, canvas, target_root, source_root, scale).tobytes()
                == canonical_image.tobytes(), 'Raw body mapping does not match canonical RGBA')
        material = image(bind(frame['source']), 'RGBA')
        owner = image(bind(frame['ownership']), 'L')
        require(owner.size == material.size and set(owner.tobytes()) <= {0, 255}, 'Ownership must be same-size binary L')
        material = box_crop(material, frame['box_px'])
        owner = box_crop(owner, frame['box_px'])
        density = fraction(frame['density_ratio'], 'density ratio')
        require(all(Fraction(material.size[i]) == body_crop.size[i] * density for i in (0, 1)), 'Density/aspect mismatch')
        root = [Fraction(value) * density for value in source_root]
        effective_scale = scale / density
        support = owner.getbbox()
        require(support is not None, 'Empty ownership')
        for axis in (0, 1):
            require(target_root[axis] + (support[axis] - root[axis]) * effective_scale >= 0
                    and target_root[axis] + (support[axis + 2] - root[axis]) * effective_scale <= canvas[axis],
                    'Registration crops declared ownership support')
        material = mapped(material, canvas, target_root, root, effective_scale)
        owner = mapped(owner, canvas, target_root, root, effective_scale)
        texture = Image.composite(material, Image.new('RGBA', tuple(canvas)), owner)
        require(owner.getbbox() is not None and texture.getchannel('A').getbbox() is not None, 'Empty transformed garment')
        for folder, opened in [('materials', material), ('ownership', owner), ('textures', texture)]:
            outputs[f'{folder}/{pose}.png'] = opened
        layouts.append({'pose_id': pose, 'action': body['action'], 'direction': body['direction'],
            'frame_index': body['frame_index'], 'duration_ms': body['duration_ms'],
            'source': frame['source'], 'ownership': frame['ownership'], 'box_px': frame['box_px'],
            'canonical_poses': frame['canonical_poses'], 'variant': frame['variant'],
            'canonical_frame': {k: canonical[k] for k in ('file', 'sha256')},
            'body_source': raw, 'body_source_root_px': source_root, 'body_scale': body['scale'],
            'density_ratio': frame['density_ratio'], 'material_root_px': [rational(value) for value in root],
            'effective_scale': rational(effective_scale), 'inverse_scale': rational(1 / effective_scale),
            'canvas_px': canvas, 'root_anchor_px': target_root, 'display_scale': display,
            'resampling': 'nearest', 'material_fill_rgba': [0, 0, 0, 0], 'ownership_fill': 0})
    return {'repo': repo, 'plan': plan, 'plan_ref': {'file': plan_relative, 'sha256': inputs[plan_relative]},
            'inputs': dict(sorted(inputs.items())), 'frames': layouts, 'images': outputs}


def expected(prepared):
    blobs, records, assets = {}, [], []
    for name, opened in sorted(prepared['images'].items()):
        buffer = io.BytesIO(); opened.save(buffer, format='PNG'); data = buffer.getvalue()
        blobs[name] = data
        records.append({'file': name, 'sha256': sha(data), 'size_px': list(opened.size),
                        'mode': opened.mode, 'rgba_sha256': sha(opened.convert('RGBA').tobytes())})
        folder = name.split('/')[0]
        assets.append({'new_path': f"art/characters/sources/{prepared['plan']['source_id']}/{name}",
                       'new_sha256': sha(data), 'role': 'prepared-derived-' + folder})
    source = {'source_id': prepared['plan']['source_id'], 'status': 'prepared-derived-review-only',
        'accepted': False, 'runtime_eligible': False, 'complete_hidden_source': False,
        'preparation_plan': prepared['plan_ref'], 'registration_plan': prepared['plan']['registration_plan'],
        'raw_parents': [{'source': f['source'], 'ownership': f['ownership'], 'box_px': f['box_px']}
                        for f in prepared['plan']['frames']], 'inputs': prepared['inputs'], 'assets': assets}
    blobs['source.json'] = document_bytes(source)
    records.append({'file': 'source.json', 'sha256': sha(blobs['source.json'])})
    identity = engine()
    token = sha(stable({'plan': prepared['plan_ref'], 'inputs': prepared['inputs'], 'engine': identity,
                       'frames': prepared['frames'], 'outputs': records}))
    manifest = {'kind': MANIFEST_KIND, 'schema_version': 1, 'status': 'review-only', 'release_eligible': False,
                'plan': prepared['plan_ref'], 'inputs': prepared['inputs'], 'engine': identity,
                'artifact_digest': token, 'frames': prepared['frames'], 'outputs': records}
    return manifest, blobs


def build(repo, plan_path, output):
    prepared = prepare(repo, plan_path)
    output = output_path(prepared['repo'], output, prepared['plan']['source_id'])
    require(not output.exists(), 'Output already exists; use a new directory')
    manifest, blobs = expected(prepared)
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='.registered-source-stage-', dir=output.parent))
    try:
        for name, data in blobs.items():
            path = stage / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(data)
        (stage / 'manifest.json').write_bytes(document_bytes(manifest))
        require(expected(prepare(repo, plan_path))[0] == manifest, 'Inputs changed during preparation')
        checked_absolute(output)
        require(not output.exists(), 'Output already exists')
        # mkdir is exclusive, so a concurrent existing output cannot be overwritten.
        output.mkdir()
        try:
            for child in stage.iterdir():
                os.rename(child, output / child.name)
        except BaseException:
            shutil.rmtree(output)
            raise
    finally:
        shutil.rmtree(stage)
    return manifest


def verify(repo, output):
    repo = checked_absolute(repo)
    directory = checked_absolute(output, repo)
    manifest = load_json(relative_file(directory, 'manifest.json'))
    require(isinstance(manifest, dict) and isinstance(manifest.get('plan'), dict), 'Invalid manifest')
    keys(manifest['plan'], 'file sha256', 'manifest plan')
    library = checked_absolute(repo / 'art/characters')
    plan_path = relative_file(library, manifest['plan']['file'])
    prepared = prepare(repo, plan_path)
    require(output_path(repo, directory, prepared['plan']['source_id']) == directory, 'Output identity mismatch')
    wanted, blobs = expected(prepared)
    require(manifest == wanted, 'Manifest differs from recomputed original sources/engine')
    actual_files, actual_dirs = set(), set()
    for root, directories, files in os.walk(directory, followlinks=False):
        root = Path(root)
        for name in directories + files:
            path = checked_absolute(root / name)
            relative = path.relative_to(directory).as_posix()
            if path.is_dir():
                actual_dirs.add(relative)
            else:
                require(path.is_file(), 'Unexpected nonregular output')
                actual_files.add(relative)
    require(actual_files == set(blobs) | {'manifest.json'} and actual_dirs == {'materials', 'ownership', 'textures'},
            'Extra or missing output files/directories')
    for name, data in blobs.items():
        require(relative_file(directory, name).read_bytes() == data, 'Output differs from raw-derived pixels: ' + name)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    build_parser = sub.add_parser('build'); build_parser.add_argument('plan'); build_parser.add_argument('--output', required=True)
    verify_parser = sub.add_parser('verify'); verify_parser.add_argument('directory')
    args = parser.parse_args()
    try:
        manifest = build(REPO, args.plan, args.output) if args.command == 'build' else verify(REPO, args.directory)
    except (ValueError, OSError) as exc:
        parser.exit(1, f'ERROR: {exc}\n')
    print(json.dumps({'status': 'ok', 'kind': manifest['kind'], 'frames': len(manifest['frames']),
                      'artifact_digest': manifest['artifact_digest']}))


if __name__ == '__main__':
    main()
