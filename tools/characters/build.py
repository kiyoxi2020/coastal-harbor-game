"""Single strict entry point for review-only character construction."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import PIL
from PIL import Image
from build_contract import digest, identifier, keys, read_json, require, safe_file, stable, validate

REPO = Path(__file__).resolve().parents[2]


def engine_identity():
    base = Path(__file__).parent
    return {'pillow': PIL.__version__, 'code': {p: digest(base / p) for p in ('build.py', 'build_contract.py')}}


def artifact(validated):
    return hashlib.sha256(stable({'inputs': validated.dependencies, 'engine': engine_identity()})).hexdigest()


def render(validated):
    for clip in validated.recipe['clips']:
        for frame in clip['frames']:
            layers = {layer['id']: layer for layer in frame['layers']}
            source_canvas, offset = validated.registrations[(clip['action_id'], clip['direction'], frame['pose_id'])]
            image = Image.new('RGBA', tuple(source_canvas))
            for index, layer_id in enumerate(frame['layer_order']):
                layer = layers[layer_id]
                texture = validated.image(layer['texture'])
                if frame['composition'] == 'alpha-over':
                    image = Image.alpha_composite(image, texture)
                elif index == 0:
                    image = texture
                else:
                    with Image.open(safe_file(validated.library, layer['coverage']['file'])) as mask:
                        image = Image.composite(texture, image, mask)

            if source_canvas != clip['canvas_px'] or offset != [0, 0]:
                target = Image.new('RGBA', tuple(clip['canvas_px']))
                target.paste(image, tuple(offset))
                image = target
            name = f"frames/{clip['action_id']}/{clip['direction']}/{frame['pose_id']}.png"
            yield name, image


def output_path(repo, output):
    path = Path(output).absolute()
    # Do not resolve away symlinks before checking them.
    for node in [path, *path.parents]:
        require(not node.is_symlink(), 'Output symlink forbidden')
    library_builds = Path(repo).resolve() / 'art/characters/builds'
    managed = path.parent == library_builds
    temporary = (path.is_relative_to(Path('/private/tmp'))
                 and path.relative_to('/private/tmp').parts[0].startswith('coastal-')
                 and not path.is_relative_to(Path(repo).resolve() / 'godot2d')
                 and not path.is_relative_to(Path(repo).resolve() / 'art'))
    require(managed or temporary, 'Unmanaged output path')
    require(path.name not in {'', '.', '..'} and '..' not in path.parts, 'Invalid output path')
    return path


def construct(repo, recipe, output):
    output = output_path(repo, output)
    require(not output.exists(), 'Output already exists; create a new revision')
    validated = validate(repo, recipe)
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='.character-stage-', dir=output.parent))
    try:
        outputs = []
        for name, image in render(validated):
            path = stage / name
            path.parent.mkdir(parents=True, exist_ok=True)
            image.save(path)
            outputs.append({'file': name, 'sha256': digest(path), 'rgba_sha256': hashlib.sha256(image.tobytes()).hexdigest(), 'size': list(image.size)})
        manifest = {'kind': 'coastal-character-review-build-v1', 'schema_version': 1,
                    'status': 'review-only', 'release_eligible': False,
                    'recipe': validated.recipe_path.relative_to(validated.library).as_posix(),
                    'artifact_digest': artifact(validated), 'inputs': validated.dependencies,
                    'engine': engine_identity(), 'outputs': outputs}
        # Validate once more before publishing; source edits cannot silently be
        # incorporated halfway through a build.
        require(artifact(validate(repo, recipe)) == manifest['artifact_digest'], 'Inputs changed during build')
        (stage / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
        # mkdir is exclusive: even an empty pre-existing output is protected.
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
    manifest_path = safe_file(directory, 'manifest.json')
    manifest = read_json(manifest_path)
    keys(manifest, 'kind schema_version status release_eligible recipe artifact_digest inputs engine outputs', 'build manifest')
    require(manifest['kind'] == 'coastal-character-review-build-v1' and manifest['schema_version'] == 1, 'Unsupported build schema')
    require(manifest['status'] == 'review-only' and manifest['release_eligible'] is False, 'Build is not a production release')
    library = Path(repo).resolve() / 'art/characters'
    recipe = safe_file(library, manifest['recipe'], 'recipes')
    validated = validate(repo, recipe)
    require(manifest['inputs'] == validated.dependencies and manifest['engine'] == engine_identity() and manifest['artifact_digest'] == artifact(validated), 'Build digest stale: input or engine changed')
    expected = list(render(validated))
    outputs = manifest['outputs']
    require(isinstance(outputs, list) and len(outputs) == len(expected), 'Missing build outputs')
    for entry, (name, rendered) in zip(outputs, expected):
        keys(entry, 'file sha256 rgba_sha256 size', 'output')
        require(entry['file'] == name, 'Wrong output pose/order')
        path = safe_file(directory, name, 'frames')
        require(digest(path) == entry['sha256'], 'Output SHA mismatch')
        with Image.open(path) as image:
            require(image.size == rendered.size and entry['size'] == list(rendered.size) and image.convert('RGBA').tobytes() == rendered.tobytes(), 'Output pixel mismatch')
        require(entry['rgba_sha256'] == hashlib.sha256(rendered.tobytes()).hexdigest(), 'Output RGBA digest mismatch')
    expected_files = {'manifest.json', *(name for name, _ in expected)}
    require({p.relative_to(directory).as_posix() for p in directory.rglob('*') if p.is_file()} == expected_files, 'Unexpected build files')
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    command = commands.add_parser('build')
    command.add_argument('recipe', type=Path)
    command.add_argument('--output', type=Path, required=True)
    command = commands.add_parser('verify')
    command.add_argument('directory', type=Path)
    args = parser.parse_args(argv)
    try:
        result = construct(REPO, args.recipe, args.output) if args.command == 'build' else verify(REPO, args.directory)
        print(json.dumps({'passed': True, 'artifact_digest': result['artifact_digest'], 'frames': len(result['outputs']), 'status': result['status']}))
    except (ValueError, KeyError, TypeError, OSError) as exc:
        parser.exit(1, str(exc) + '\n')

if __name__ == '__main__':
    main()
