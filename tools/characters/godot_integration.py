"""Deliver a verified strict build to Godot without granting production release."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil

from build import verify as verify_build
from build_contract import digest, read_json, require, safe_file

REPO = Path(__file__).resolve().parents[2]
ACTIONS = ('idle', 'walk', 'run', 'hoe', 'water', 'harvest')
DIRECTIONS = ('north', 'west', 'south', 'east')
KIND = 'coastal-godot-character-integration-v1'
IMPORT_PARAMS = {
    'compress/mode': 0, 'compress/high_quality': False, 'compress/lossy_quality': 0.7,
    'compress/uastc_level': 0, 'compress/rdo_quality_loss': 0.0, 'compress/hdr_compression': 1,
    'compress/normal_map': 0, 'compress/channel_pack': 0,
    'mipmaps/generate': False, 'mipmaps/limit': -1, 'roughness/mode': 0, 'roughness/src_normal': '',
    'process/channel_remap/red': 0, 'process/channel_remap/green': 1,
    'process/channel_remap/blue': 2, 'process/channel_remap/alpha': 3,
    'process/fix_alpha_border': False, 'process/premult_alpha': False,
    'process/normal_map_invert_y': False, 'process/hdr_as_srgb': False,
    'process/hdr_clamp_exposure': False, 'process/size_limit': 0, 'detect_3d/compress_to': 1,
}


def import_sections(texture):
    # Godot's texture importer names its cached resource using MD5 of res://path.
    cached = 'res://.godot/imported/' + texture.rsplit('/', 1)[1] + '-' + hashlib.md5(texture.encode()).hexdigest() + '.ctex'
    return {'remap': {'importer': 'texture', 'type': 'CompressedTexture2D', 'path': cached},
            'deps': {'source_file': texture, 'dest_files': [cached]}, 'params': IMPORT_PARAMS}


def import_config(texture):
    return '\n\n'.join('[' + section + ']\n\n' + '\n'.join(
        key + '=' + json.dumps(value) for key, value in values.items())
        for section, values in import_sections(texture).items()) + '\n'


def verify_import(path, texture):
    require(path.is_file() and not path.is_symlink(), 'Import record missing or symlink')
    text = path.read_text()
    for section, expected_values in import_sections(texture).items():
        match = re.search(r'(?ms)^\[' + section + r'\]\s*\n(.*?)(?=^\[|\Z)', text)
        require(match is not None, 'Import section missing: ' + section)
        found = {}
        for line in match[1].splitlines():
            if '=' not in line: continue
            key, value = line.split('=', 1)
            if key in expected_values or section == 'params':
                require(key not in found, 'Import duplicate parameter')
                found[key] = json.loads(value)
        require(json.dumps(found, sort_keys=True) == json.dumps(expected_values, sort_keys=True),
                'Import pixel processing or source binding mismatch: ' + section)


def managed_path(repo, path, prefix):
    repo = Path(repo).resolve()
    path = Path(path)
    if not path.is_absolute(): path = repo / path
    require('..' not in path.parts, 'Path traversal forbidden')
    require(path.is_relative_to(repo / prefix), 'Unmanaged integration path')
    for item in (path, *path.parents):
        require(not item.is_symlink(), 'Integration symlink forbidden')
    return path


def animation_data(recipe, outputs, texture_root):
    clips = recipe['clips']
    required = {(a, d) for a in ACTIONS for d in DIRECTIONS}
    require(len(clips) == len(required) and
            {(c['action_id'], c['direction']) for c in clips} == required,
            'Full player requires exactly 24 unique action/direction capabilities')
    output_by_name = {entry['file']: entry for entry in outputs}
    require(len(output_by_name) == len(outputs), 'Duplicate build output')
    geometry = (clips[0]['canvas_px'], clips[0]['root_anchor_px'], clips[0]['display_scale'])
    used, result = set(), []
    for clip in clips:
        require(clip['variant'] == 'visible', 'Game requires visible variant including farming tools')
        require((clip['canvas_px'], clip['root_anchor_px'], clip['display_scale']) == geometry,
                'Inconsistent clip geometry')
        frames = []
        require(bool(clip['frames']), 'Empty action frames')
        for frame in clip['frames']:
            duration = frame['duration_ms']
            require(type(duration) is int and duration > 0, 'Invalid frame duration')
            pose = frame['pose_id']
            name = f"frames/{clip['action_id']}/{clip['direction']}/{pose}.png"
            require(name in output_by_name and name not in used, 'Missing or duplicate build output')
            output = output_by_name[name]
            require(output['size'] == clip['canvas_px'], 'Output geometry mismatch')
            used.add(name)
            frames.append({'texture': texture_root + '/' + name, 'pose_id': pose,
                           'duration_ms': duration, 'sha256': output['sha256'],
                           'rgba_sha256': output['rgba_sha256']})
        result.append({'name': clip['action_id'] + '_' + clip['direction'],
                       'action': clip['action_id'], 'direction': clip['direction'],
                       'loop': clip['action_id'] in {'idle', 'walk', 'run'}, 'frames': frames})
    require(used == set(output_by_name), 'Unexpected build outputs')
    return result


def sprite_frames(clips):
    textures = [f['texture'] for c in clips for f in c['frames']]
    lines = [f'[gd_resource type="SpriteFrames" load_steps={len(textures) + 1} format=3]', '']
    for index, texture in enumerate(textures, 1):
        lines.append(f'[ext_resource type="Texture2D" path="{texture}" id="{index}"]')
    lines += ['', '[resource]', 'animations = [']
    index = 1
    animations = []
    for clip in clips:
        frames = []
        for frame in clip['frames']:
            frames.append('{"duration": %s.0, "texture": ExtResource("%s")}' % (frame['duration_ms'], index))
            index += 1
        animations.append('{\n"frames": [' + ',\n'.join(frames) + '],\n"loop": ' +
                          str(clip['loop']).lower() + ',\n"name": &"' + clip['name'] +
                          '",\n"speed": 1000.0\n}')
    lines += [',\n'.join(animations), ']']
    return '\n'.join(lines) + '\n'


def expected(repo, build_dir, package_dir, frames_file):
    repo = Path(repo).resolve()
    build_dir = managed_path(repo, build_dir, 'art/characters/builds')
    package_dir = managed_path(repo, package_dir, 'godot2d/assets/characters/integrations')
    require(package_dir.parent == repo / 'godot2d/assets/characters/integrations', 'Expected direct integration package')
    frames_file = managed_path(repo, frames_file, 'godot2d/resources')
    require(frames_file.suffix == '.tres', 'Expected SpriteFrames .tres')
    source = verify_build(repo, build_dir)
    recipe = read_json(safe_file(repo / 'art/characters', source['recipe'], 'recipes'))
    texture_root = 'res://' + package_dir.relative_to(repo / 'godot2d').as_posix()
    clips = animation_data(recipe, source['outputs'], texture_root)
    for source_clip, clip in zip(recipe['clips'], clips):
        action = read_json(safe_file(repo / 'art/characters', source_clip['action']['file']))
        require(action['loop'] == clip['loop'], 'Unsupported action loop contract')
    resource = sprite_frames(clips)
    first = recipe['clips'][0]
    manifest = {
        'kind': KIND, 'schema_version': 1, 'status': 'local-development-integration',
        'production_release': False, 'character_model_id': recipe['character_model_id'],
        'source_build': {'file': (build_dir / 'manifest.json').relative_to(repo).as_posix(),
                         'sha256': digest(build_dir / 'manifest.json'),
                         'artifact_digest': source['artifact_digest']},
        'recipe': {'file': 'art/characters/' + source['recipe'],
                   'sha256': digest(repo / 'art/characters' / source['recipe'])},
        'package': package_dir.relative_to(repo).as_posix(),
        'sprite_frames': {'file': frames_file.relative_to(repo).as_posix(),
                          'sha256': hashlib.sha256(resource.encode()).hexdigest()},
        'geometry': {'canvas_px': first['canvas_px'], 'root_anchor_px': first['root_anchor_px'],
                     'world_scale': 0.25},
        'clips': clips,
        'generator': {'file': 'tools/characters/godot_integration.py', 'sha256': digest(Path(__file__))},
    }
    return manifest, resource, source


def create(repo, build_dir, package_dir, frames_file):
    repo = Path(repo).resolve()
    package_dir = managed_path(repo, package_dir, 'godot2d/assets/characters/integrations')
    frames_file = managed_path(repo, frames_file, 'godot2d/resources')
    require(not package_dir.exists() and not frames_file.exists(), 'Integration output already exists')
    manifest, resource, source = expected(repo, build_dir, package_dir, frames_file)
    build_dir = repo / Path(manifest['source_build']['file']).parent
    package_dir.mkdir(parents=True)
    resource_created = False
    try:
        for output in source['outputs']:
            src = safe_file(build_dir, output['file'], 'frames')
            require(digest(src) == output['sha256'], 'Source output SHA changed during delivery')
            dest = package_dir / output['file']
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dest)
            require(digest(dest) == output['sha256'], 'Delivered output SHA mismatch')
            texture = 'res://' + dest.relative_to(repo / 'godot2d').as_posix()
            Path(str(dest) + '.import').write_text(import_config(texture))
        frames_file.parent.mkdir(parents=True, exist_ok=True)
        with frames_file.open('x') as stream:
            resource_created = True
            stream.write(resource)
        (package_dir / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    except BaseException:
        shutil.rmtree(package_dir)
        if resource_created: frames_file.unlink()
        raise
    return manifest


def verify(repo, manifest_path):
    repo = Path(repo).resolve()
    manifest_path = managed_path(repo, manifest_path, 'godot2d/assets/characters/integrations')
    manifest = read_json(manifest_path)
    package_dir = manifest_path.parent
    frames_file = managed_path(repo, manifest['sprite_frames']['file'], 'godot2d/resources')
    build_dir = managed_path(repo, Path(manifest['source_build']['file']).parent, 'art/characters/builds')
    binding, resource, source = expected(repo, build_dir, package_dir, frames_file)
    require(manifest == binding, 'Integration manifest binding mismatch')
    require(frames_file.read_text() == resource, 'SpriteFrames binding mismatch')
    names = {'manifest.json'}
    for output in source['outputs']:
        path = safe_file(package_dir, output['file'], 'frames')
        require(digest(path) == output['sha256'], 'Runtime PNG SHA mismatch')
        texture = 'res://' + path.relative_to(repo / 'godot2d').as_posix()
        verify_import(Path(str(path) + '.import'), texture)
        names.add(output['file'])
        names.add(output['file'] + '.import')
    actual = set()
    for path in package_dir.rglob('*'):
        require(not path.is_symlink(), 'Integration symlink forbidden')
        if path.is_file():
            relative = path.relative_to(package_dir).as_posix()
            actual.add(relative)
    require(actual == names, 'Unexpected integration files')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    create_parser = commands.add_parser('create')
    create_parser.add_argument('build_dir', type=Path)
    create_parser.add_argument('--package', type=Path, required=True)
    create_parser.add_argument('--frames', type=Path, required=True)
    verify_parser = commands.add_parser('verify')
    verify_parser.add_argument('manifest', type=Path)
    args = parser.parse_args()
    try:
        result = (create(REPO, args.build_dir, args.package, args.frames) if args.command == 'create'
                  else verify(REPO, args.manifest))
        print(json.dumps({'passed': True, 'status': result['status'], 'clips': len(result['clips']),
                          'frames': sum(len(c['frames']) for c in result['clips']), 'production_release': False}))
    except (ValueError, KeyError, TypeError, OSError) as exc:
        parser.exit(1, str(exc) + '\n')


if __name__ == '__main__': main()
