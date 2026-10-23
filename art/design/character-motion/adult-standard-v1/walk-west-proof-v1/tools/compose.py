#!/usr/bin/env python3
"""Bake registered layers. No drawing, scaling, pose synthesis or hidden-pixel repair."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import tempfile

from PIL import Image, ImageChops

EXPECTED_POSES = [f'walk_w_{i}' for i in range(4)]


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def pair(value, label):
    require(isinstance(value, list) and len(value) == 2 and all(type(x) is int for x in value), f'{label}: expected two integers')
    return tuple(value)


def compose(motion_path, output_dir=None):
    motion_path = Path(motion_path).resolve()
    root = motion_path.parent
    try:
        data = json.loads(motion_path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f'cannot read motion: {error}') from error
    require(isinstance(data, dict) and type(data.get('schema_version')) is int and data['schema_version'] == 1, 'schema_version must be 1')
    canvas = pair(data.get('canvas_px'), 'canvas_px')
    require(canvas == (512, 768), 'this proof requires canvas_px=[512,768]')
    anchor = pair(data.get('root_anchor_px'), 'root_anchor_px')
    require(0 <= anchor[0] < canvas[0] and 0 <= anchor[1] < canvas[1], 'root_anchor_px outside canvas')
    scale = data.get('display_scale')
    require(type(scale) in (float, int) and math.isfinite(scale) and 0 < scale <= 1, 'display_scale must be finite in (0,1]')
    frames = data.get('frames')
    require(isinstance(frames, list) and len(frames) == 4, 'exactly four timeline frames required')
    for i, frame in enumerate(frames):
        require(isinstance(frame, dict) and frame.get('pose_id') == EXPECTED_POSES[i], f'frame {i}: expected pose_id={EXPECTED_POSES[i]}')
        require(type(frame.get('duration_ms')) is int and frame['duration_ms'] > 0, f'frame {i}: duration_ms must be positive integer')
    recipes = data.get('recipes')
    require(isinstance(recipes, dict) and set(recipes) == {'A', 'B'}, 'exactly A and B recipes required')
    inputs = {'motion.json': {'path': motion_path.name, 'sha256': sha256(motion_path)}}
    image_cache = {}

    def read_image(reference, is_mask=False):
        require(isinstance(reference, str) and reference, 'source/mask must be a nonempty relative path')
        rel = Path(reference)
        require(not rel.is_absolute() and '..' not in rel.parts, f'unsafe relative path: {reference}')
        path = (root / rel).resolve()
        require(path.is_relative_to(root) and path.is_file(), f'missing or external resource: {reference}')
        key = (reference, is_mask)
        if key not in image_cache:
            try:
                with Image.open(path) as opened:
                    require(opened.format == 'PNG', f'PNG required: {reference}')
                    if is_mask:
                        require(opened.mode == 'L' and opened.size == canvas, f'mask must be full-canvas L PNG: {reference}')
                        image_cache[key] = opened.copy()
                    else:
                        image_cache[key] = opened.convert('RGBA')
            except (OSError, Image.DecompressionBombError) as error:
                raise ValueError(f'invalid image {reference}: {error}') from error
            inputs[reference] = {'path': reference, 'sha256': sha256(path), 'size_px': list(image_cache[key].size), 'mode': image_cache[key].mode}
        return image_cache[key]

    # Resolve/validate every frame before writing anything. A source can map to all poses.
    for recipe_id, recipe in recipes.items():
        require(isinstance(recipe, dict) and isinstance(recipe.get('frames'), list) and len(recipe['frames']) == 4, f'{recipe_id}: four mapped frames required')
        for index, frame in enumerate(recipe['frames']):
            require(isinstance(frame, dict), f'{recipe_id}/{index}: frame object required')
            if 'pose_id' in frame:
                require(frame['pose_id'] == EXPECTED_POSES[index], f'{recipe_id}/{index}: mismatched pose')
            layers = frame.get('layers')
            require(isinstance(layers, list) and layers, f'{recipe_id}/{index}: nonempty layers required')
            ids = set()
            for layer in layers:
                require(isinstance(layer, dict), 'layer object required')
                layer_id = layer.get('id')
                require(isinstance(layer_id, str) and layer_id and layer_id not in ids, f'{recipe_id}/{index}: missing/duplicate layer id')
                ids.add(layer_id)
                image = read_image(layer.get('source'))
                x, y = pair(layer.get('offset_px'), f'{recipe_id}/{index}/{layer_id} offset_px')
                require(x >= 0 and y >= 0 and x + image.width <= canvas[0] and y + image.height <= canvas[1], f'{recipe_id}/{index}/{layer_id}: source exceeds canvas')
                if 'hide_mask' in layer:
                    read_image(layer['hide_mask'], True)

    tool_root = Path(__file__).parent
    tools = {path.name: sha256(path) for path in sorted(tool_root.iterdir()) if path.suffix in ('.py', '.gd', '.tscn', '.godot') and path.is_file()}
    manifest = {
        'schema_version': 1, 'canvas_px': list(canvas), 'root_anchor_px': list(anchor),
        'display_scale': scale, 'frames': frames, 'inputs': inputs, 'tools': tools,
        'mask_semantics': 'full_canvas_L_white_hides_target_layer_only',
        'recipes': {}, 'verification_scope': 'structure_and_compositing_only',
    }
    digest_input = json.dumps({'inputs': inputs, 'tools': tools}, sort_keys=True, separators=(',', ':')).encode()
    manifest['artifact_digest'] = hashlib.sha256(digest_input).hexdigest()
    destination = Path(output_dir).resolve() if output_dir else root / 'baked'
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='coastal-motion-bake-', dir=destination.parent) as scratch:
        stage = Path(scratch)
        for recipe_id, recipe in recipes.items():
            baked_frames = []
            for i, frame in enumerate(recipe['frames']):
                result = Image.new('RGBA', canvas)
                for layer in frame['layers']:
                    source = read_image(layer['source']).copy()
                    x, y = layer['offset_px']
                    if 'hide_mask' in layer:
                        mask = read_image(layer['hide_mask'], True).crop((x, y, x + source.width, y + source.height))
                        source.putalpha(ImageChops.multiply(source.getchannel('A'), ImageChops.invert(mask)))
                    result.alpha_composite(source, (x, y))
                filename = f'{recipe_id}_{i}.png'
                result.save(stage / filename)
                baked_frames.append({'file': filename, 'sha256': sha256(stage / filename), 'pose_id': frames[i]['pose_id'], 'duration_ms': frames[i]['duration_ms'], 'layers': frame['layers']})
            manifest['recipes'][recipe_id] = {'frames': baked_frames}
        (stage / 'export-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
        destination.mkdir(parents=True, exist_ok=True)
        # Publish manifest last so an interrupted write never advertises incomplete output.
        for path in sorted(stage.glob('*.png')):
            os.replace(path, destination / path.name)
        os.replace(stage / 'export-manifest.json', destination / 'export-manifest.json')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--motion', required=True, type=Path)
    parser.add_argument('--output-dir', type=Path)
    args = parser.parse_args()
    try:
        result = compose(args.motion, args.output_dir)
    except ValueError as error:
        parser.exit(2, f'Invalid motion: {error}\n')
    print(json.dumps({'artifact_digest': result['artifact_digest'], 'recipes': list(result['recipes']), 'frames_per_recipe': 4}))


if __name__ == '__main__':
    main()
