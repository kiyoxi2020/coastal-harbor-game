"""Prepare whole source frames as atlases; never compose character parts.

Outputs are review-only authoring inputs, not construction recipes or releases.
The existing build.py remains the sole character construction entry point.
"""
import argparse
from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import PIL
from PIL import Image
from build_contract import digest, identifier, keys, read_json, require, safe_file, stable

REPO = Path(__file__).resolve().parents[2]
ROWS = ['north', 'west', 'south', 'east']


def integers(value, length, minimum=0):
    return (isinstance(value, list) and len(value) == length
            and all(type(x) is int and x >= minimum for x in value))


def identity():
    folder = Path(__file__).parent
    return {'pillow': PIL.__version__, 'code': {name: digest(folder / name)
            for name in ['pack_sources.py', 'build_contract.py']}}


def output_path(repo, output):
    path = Path(output).absolute()
    require(not any(p.is_symlink() for p in [path, *path.parents]), 'Output symlink forbidden')
    lib = Path(repo).resolve() / 'art/characters'
    parts = path.relative_to(lib).parts if path.is_relative_to(lib) else ()
    managed = ((len(parts) == 4 and parts[:2] == ('parts', 'body'))
               or (len(parts) == 4 and parts[0] == 'sources' and parts[2] == 'derived'))
    temporary = path.is_relative_to('/private/tmp') and path.relative_to('/private/tmp').parts[0].startswith('coastal-')
    require(managed or temporary, 'Unmanaged source export output')
    require('..' not in path.parts, 'Invalid output path')
    return path


def prepare(repo, plan_path):
    library = Path(repo).resolve() / 'art/characters'
    try:
        relative = Path(plan_path).absolute().relative_to(library).as_posix()
    except ValueError:
        raise ValueError('Packing plan must be inside source library') from None
    plan_path = safe_file(library, relative, 'sources')
    plan = read_json(plan_path)
    keys(plan, 'kind schema_version resource_root source_id revision cell_px root_px rows frames', 'source packing plan')
    require(plan['kind'] == 'coastal-character-source-atlas-plan-v1'
            and type(plan['schema_version']) is int and plan['schema_version'] == 1,
            'Unsupported source packing plan')
    require(plan['resource_root'] == 'art/characters', 'Wrong source resource root')
    identifier(plan['source_id']); identifier(plan['revision'])
    require(relative == f"sources/{plan['source_id']}/packing/{plan['revision']}.json", 'Source plan identity/path mismatch')
    cell, root = plan['cell_px'], plan['root_px']
    require(integers(cell, 2, 1) and max(cell) <= 2048, 'Invalid target cell')
    require(integers(root, 2) and all(root[i] < cell[i] for i in [0, 1]), 'Invalid target root')
    require(plan['rows'] == ROWS, 'Direction row order must be north/west/south/east')
    frames = plan['frames']
    require(isinstance(frames, list) and frames and len(frames) <= 4096, 'Missing or excessive source frames')
    dependencies = {relative: digest(plan_path)}
    images, groups, poses = {}, {}, set()

    def bind(ref, authoring=False):
        keys(ref, 'file sha256', 'source reference')
        path = safe_file(library, ref['file'])
        namespaces = {'sources', 'templates', 'parts'} | ({'builds'} if authoring else set())
        require(ref['file'].split('/')[0] in namespaces, 'Wrong source namespace')
        actual = digest(path)
        require(actual == ref['sha256'], 'Source SHA mismatch: ' + ref['file'])
        require(ref['file'] not in dependencies or dependencies[ref['file']] == actual, 'Inconsistent source identity')
        dependencies[ref['file']] = actual
        return path

    for frame in frames:
        keys(frame, 'representation action direction frame_index pose_id duration_ms source source_root_px scale authoring_inputs', 'source frame')
        rep, action, direction = frame['representation'], frame['action'], frame['direction']
        identifier(rep); identifier(action); identifier(frame['pose_id'])
        require(direction in ROWS, 'Unknown direction')
        require(type(frame['frame_index']) is int and frame['frame_index'] >= 0, 'Invalid frame index')
        require(type(frame['duration_ms']) is int and 0 < frame['duration_ms'] <= 60000, 'Invalid frame duration')
        pose = (rep, frame['pose_id'])
        require(pose not in poses, 'Duplicate source pose')
        poses.add(pose)
        source = frame['source']
        keys(source, 'file sha256 size_px box_px', 'source image')
        path = bind({k: source[k] for k in ['file', 'sha256']})
        if source['file'] not in images:
            with Image.open(path) as image:
                require(image.format == 'PNG', 'Source image must be PNG')
                images[source['file']] = image.convert('RGBA')
        image = images[source['file']]
        require(integers(source['size_px'], 2, 1) and list(image.size) == source['size_px'], 'Source size mismatch')
        box = source['box_px']
        require(integers(box, 4) and box[2] > 0 and box[3] > 0
                and box[0] + box[2] <= image.width and box[1] + box[3] <= image.height, 'Source box out of bounds')
        anchor, ratio = frame['source_root_px'], frame['scale']
        require(integers(anchor, 2) and all(anchor[i] < box[i + 2] for i in [0, 1]), 'Invalid source root')
        require(integers(ratio, 2, 1) and max(ratio) <= 1000000, 'Invalid whole-frame scale')
        scale = Fraction(*ratio)
        require(Fraction(1, 64) <= scale <= 16, 'Whole-frame scale out of range')
        crop = image.crop((box[0], box[1], box[0] + box[2], box[1] + box[3]))
        bbox = crop.getchannel('A').getbbox()
        require(bbox is not None, 'Empty source alpha')
        for axis in [0, 1]:
            require(root[axis] + (bbox[axis] - anchor[axis]) * scale >= 0
                    and root[axis] + (bbox[axis + 2] - anchor[axis]) * scale <= cell[axis],
                    'Registration would crop source alpha')
        require(isinstance(frame['authoring_inputs'], list), 'Invalid authoring inputs')
        for ref in frame['authoring_inputs']: bind(ref, authoring=True)
        group = groups.setdefault((rep, action), {}).setdefault(direction, {})
        require(frame['frame_index'] not in group, 'Duplicate frame index')
        group[frame['frame_index']] = frame

    for directions in groups.values():
        require(set(directions) == set(ROWS), 'Incomplete direction set')
        count = len(directions['north'])
        require(count <= 32, 'Too many frames per atlas row')
        reference_clock = [directions['north'][i]['duration_ms'] for i in range(count)
                           if i in directions['north']]
        for frames_by_index in directions.values():
            require(set(frames_by_index) == set(range(count)), 'Missing frame or inconsistent row length')
            require([frames_by_index[i]['duration_ms'] for i in range(count)] == reference_clock,
                    'Direction phase clocks differ')
    return {'library': library, 'plan_path': relative, 'plan': plan,
            'dependencies': dict(sorted(dependencies.items())), 'images': images, 'groups': groups}


def render(prepared):
    """One nearest affine transform per complete frame; direct RGBA copy."""
    plan = prepared['plan']; cell = plan['cell_px']; root = plan['root_px']
    layout = {'kind': 'coastal-character-source-layout-v1', 'schema_version': 1,
              'status': 'review-only', 'cell_px': cell, 'root_px': root, 'rows': ROWS,
              'display_scale': 1.0, 'clips': []}
    atlases = []
    for (rep, action), directions in sorted(prepared['groups'].items()):
        count = len(directions['north'])
        atlas = Image.new('RGBA', (cell[0] * count, cell[1] * len(ROWS)))
        name = f'atlases/{rep}/{action}.png'
        for row, direction in enumerate(ROWS):
            clip = {'representation': rep, 'action': action, 'direction': direction,
                    'frames': [], 'source_cycle_ms': 0}
            for index in range(count):
                frame = directions[direction][index]; source = frame['source']; box = source['box_px']
                image = prepared['images'][source['file']].crop((box[0], box[1], box[0] + box[2], box[1] + box[3]))
                inverse = frame['scale'][1] / frame['scale'][0]
                anchor = frame['source_root_px']
                mapped = image.transform(tuple(cell), Image.Transform.AFFINE,
                    (inverse, 0, anchor[0] - root[0] * inverse,
                     0, inverse, anchor[1] - root[1] * inverse),
                    resample=Image.Resampling.NEAREST, fillcolor=(0, 0, 0, 0))
                atlas.paste(mapped, (index * cell[0], row * cell[1]))
                clip['frames'].append({'pose_id': frame['pose_id'], 'duration_ms': frame['duration_ms'],
                    'atlas': name, 'region_px': [index * cell[0], row * cell[1], *cell],
                    'source': source, 'source_root_px': anchor, 'whole_frame_scale': frame['scale']})
                clip['source_cycle_ms'] += frame['duration_ms']
            layout['clips'].append(clip)
        atlases.append((name, atlas))
    return layout, atlases


def artifact(prepared):
    return hashlib.sha256(stable({'inputs': prepared['dependencies'], 'engine': identity()})).hexdigest()


def layout_bytes(layout):
    return (json.dumps(layout, ensure_ascii=False, indent=2) + '\n').encode()


def pack(repo, plan_path, output):
    output = output_path(repo, output)
    require(not output.exists(), 'Output already exists; use a new revision')
    prepared = prepare(repo, plan_path)
    token = artifact(prepared)
    layout, atlases = render(prepared)
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='.source-pack-stage-', dir=output.parent))
    try:
        outputs = []
        for name, image in atlases:
            path = stage / name; path.parent.mkdir(parents=True, exist_ok=True); image.save(path)
            outputs.append({'file': name, 'sha256': digest(path), 'size_px': list(image.size),
                            'rgba_sha256': hashlib.sha256(image.tobytes()).hexdigest()})
        (stage / 'layout.json').write_bytes(layout_bytes(layout))
        outputs.append({'file': 'layout.json', 'sha256': digest(stage / 'layout.json')})
        manifest = {'kind': 'coastal-character-source-atlas-v1', 'schema_version': 1,
                    'status': 'review-only', 'release_eligible': False, 'complete_body_archive': False,
                    'plan': prepared['plan_path'], 'inputs': prepared['dependencies'],
                    'engine': identity(), 'artifact_digest': token, 'outputs': outputs}
        require(artifact(prepare(repo, plan_path)) == token, 'Source inputs changed during packing')
        (stage / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
        output.mkdir()
        try:
            for child in sorted(stage.iterdir(), key=lambda p: p.name == 'manifest.json'):
                os.rename(child, output / child.name)
        except BaseException:
            shutil.rmtree(output)
            raise
        return manifest
    finally:
        shutil.rmtree(stage)


def verify(repo, directory):
    directory = output_path(repo, directory)
    manifest = read_json(safe_file(directory, 'manifest.json'))
    keys(manifest, 'kind schema_version status release_eligible complete_body_archive plan inputs engine artifact_digest outputs', 'source export manifest')
    require(manifest['kind'] == 'coastal-character-source-atlas-v1' and type(manifest['schema_version']) is int
            and manifest['schema_version'] == 1 and manifest['status'] == 'review-only'
            and manifest['release_eligible'] is False and manifest['complete_body_archive'] is False,
            'Source export cannot grant release or archive acceptance')
    lib = Path(repo).resolve() / 'art/characters'
    prepared = prepare(repo, safe_file(lib, manifest['plan'], 'sources'))
    require(manifest['inputs'] == prepared['dependencies'] and manifest['engine'] == identity()
            and manifest['artifact_digest'] == artifact(prepared), 'Source export stale')
    layout, atlases = render(prepared)
    outputs = manifest['outputs']
    require(isinstance(outputs, list) and len(outputs) == len(atlases) + 1, 'Source outputs missing')
    expected_names = {'manifest.json', 'layout.json'}
    for entry, (name, rendered) in zip(outputs[:-1], atlases):
        keys(entry, 'file sha256 size_px rgba_sha256', 'atlas output')
        require(entry['file'] == name, 'Wrong atlas output order')
        path = safe_file(directory, name, 'atlases')
        require(digest(path) == entry['sha256'], 'Atlas SHA mismatch')
        with Image.open(path) as image:
            require(image.mode == 'RGBA' and image.size == rendered.size
                    and entry['size_px'] == list(rendered.size)
                    and image.tobytes() == rendered.tobytes(), 'Atlas pixels differ from actual source')
        require(entry['rgba_sha256'] == hashlib.sha256(rendered.tobytes()).hexdigest(), 'Atlas RGBA mismatch')
        expected_names.add(name)
    last = outputs[-1]; keys(last, 'file sha256', 'layout output')
    require(last['file'] == 'layout.json', 'Missing layout output')
    path = safe_file(directory, 'layout.json')
    require(path.read_bytes() == layout_bytes(layout) and digest(path) == last['sha256'], 'Layout differs from actual plan')
    require({p.relative_to(directory).as_posix() for p in directory.rglob('*') if p.is_file()} == expected_names,
            'Unexpected source export files')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    command = commands.add_parser('pack'); command.add_argument('plan', type=Path)
    command.add_argument('--output', type=Path, required=True)
    command = commands.add_parser('verify'); command.add_argument('directory', type=Path)
    args = parser.parse_args()
    try:
        result = pack(REPO, args.plan, args.output) if args.command == 'pack' else verify(REPO, args.directory)
        print(json.dumps({'passed': True, 'artifact_digest': result['artifact_digest'],
                          'status': result['status'], 'outputs': len(result['outputs'])}))
    except (ValueError, KeyError, TypeError, OSError) as exc:
        parser.exit(1, str(exc) + '\n')


if __name__ == '__main__':
    main()
