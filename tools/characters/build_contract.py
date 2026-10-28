"""Strict construction contract for the single character authoring library.

Only registered full-frame interfaces are supported. Migration manifests are
references, never implicit construction recipes or release attestations.
"""
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
from PIL import Image

KIND = 'coastal-character-construction-v1'
MODEL = 'unified-composable-character-v1'
SLOTS = {'body', 'top', 'pants', 'shoes', 'hair', 'hat', 'tool'}
DIRECTIONS = {'south', 'west', 'east', 'north'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def keys(data, expected, label):
    require(isinstance(data, dict) and set(data) == set(expected.split()), label + ': unexpected or missing fields')


def identifier(value):
    require(isinstance(value, str) and re.fullmatch(r'[a-z][a-z0-9_-]*', value), 'Invalid identifier')
    return value


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def stable(data):
    return json.dumps(data, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()


def read_json(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, 'Duplicate JSON field: ' + key)
            result[key] = value
        return result
    return json.loads(Path(path).read_text(), object_pairs_hook=unique,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError('Non-finite JSON: ' + value)))


def safe_file(root, relative, namespace=None):
    require(isinstance(relative, str) and relative and '\\' not in relative and ':' not in relative, 'Invalid resource path')
    parts = relative.split('/')
    require(not relative.startswith('/') and all(p not in {'', '.', '..'} for p in parts), 'Invalid resource path')
    require(namespace is None or relative.startswith(namespace + '/'), 'Wrong semantic namespace: ' + relative)
    path = root
    require(not any(node.is_symlink() for node in [root, *root.parents]), 'Library parent symlink forbidden')
    for part in parts:
        path = path / part
        require(not path.is_symlink(), 'Resource symlink forbidden: ' + relative)
    require(path.is_file() and path.resolve().is_relative_to(root.resolve()), 'Missing resource path: ' + relative)
    return path


@dataclass
class Validated:
    repo: Path
    library: Path
    recipe_path: Path
    recipe: dict
    dependencies: dict
    registrations: dict

    def image(self, ref):
        with Image.open(safe_file(self.library, ref['file'])) as img:
            return img.convert('RGBA')


def validate(repo, recipe_path):
    repo = Path(repo).resolve()
    library = repo / 'art/characters'
    # Check the lexical path before resolving it, so a symlink cannot disappear.
    recipe_path = Path(recipe_path).absolute()
    require(recipe_path.is_relative_to(library), 'Recipe path must be in art/characters')
    relative = recipe_path.relative_to(library).as_posix()
    safe_file(library, relative, 'recipes')
    dependencies = {}
    registrations = {}

    def bind(path):
        dependencies[path] = digest(safe_file(library, path))

    def reference(ref, namespace=None, image_size=None):
        keys(ref, 'file sha256', 'reference')
        require(isinstance(ref['sha256'], str) and re.fullmatch('[0-9a-f]{64}', ref['sha256']), 'Invalid SHA256')
        path = safe_file(library, ref['file'], namespace)
        require(digest(path) == ref['sha256'], 'SHA mismatch: ' + ref['file'])
        bind(ref['file'])
        if image_size is not None:
            with Image.open(path) as image:
                require(image.format == 'PNG' and image.size == tuple(image_size), 'Image canvas mismatch: ' + ref['file'])
        return path

    def record(ref, namespace=None):
        return read_json(reference(ref, namespace))

    recipe = read_json(recipe_path)
    keys(recipe, 'kind schema_version resource_root character_model_id recipe_id revision template motion_set slots required_capabilities clips authoring_inputs', 'recipe')
    require(recipe['kind'] == KIND and type(recipe['schema_version']) is int and recipe['schema_version'] == 1, 'Unsupported schema')
    require(recipe['resource_root'] == 'art/characters', 'Wrong resource root')
    require(recipe['character_model_id'] == MODEL, 'Wrong character model')
    identifier(recipe['recipe_id']); identifier(recipe['revision'])
    require(relative == f"recipes/{recipe['recipe_id']}/{recipe['revision']}.json", 'Recipe identity/path mismatch')
    bind(relative)
    require(isinstance(recipe['authoring_inputs'], list) and recipe['authoring_inputs'], 'Missing authoring inputs')
    for ref in recipe['authoring_inputs']:
        require(ref['file'].split('/')[0] in {'sources', 'templates', 'parts', 'builds'}, 'Wrong authoring namespace')
        reference(ref)
    template = record(recipe['template'], 'templates')
    template_id = identifier(template['template_id'])
    require(recipe['template']['file'] == f'templates/{template_id}/template.json', 'Template identity/path mismatch')
    motion = record(recipe['motion_set'], f'templates/{template_id}/motions')
    require(template['motion_set'] == recipe['motion_set']['file'] and motion['template_id'] == template_id, 'Template/motion identity mismatch')
    motion_id = identifier(motion['motion_set_id'])
    require(recipe['motion_set']['file'] == f'templates/{template_id}/motions/{motion_id}/motion-set.json', 'Motion identity/path mismatch')
    require(isinstance(template.get('active_revision'), str) and template['active_revision'], 'Template revision missing')
    slots = recipe['slots']
    require(isinstance(slots, dict) and set(slots) <= SLOTS and slots.get('body', 'missing') is None, 'Unknown or missing body slot')
    for slot, ref in slots.items():
        if slot == 'body':
            continue
        design = record(ref, 'parts')
        require(design['category'] == slot, 'Part slot mismatch')
        require(ref['file'] == f"parts/{identifier(design['design_id'])}/design.json", 'Part identity/path mismatch')

    required = recipe['required_capabilities']
    require(isinstance(required, list) and required, 'Required capabilities missing')
    caps = []
    for cap in required:
        keys(cap, 'action_id direction', 'capability')
        identifier(cap['action_id'])
        require(cap['direction'] in DIRECTIONS, 'Unknown direction')
        caps.append((cap['action_id'], cap['direction']))
    require(len(set(caps)) == len(caps), 'Duplicate capabilities')
    require(isinstance(recipe['clips'], list) and recipe['clips'], 'Missing clips')
    actual = []
    for clip in recipe['clips']:
        keys(clip, 'action_id direction action poses variant canvas_px root_anchor_px display_scale frames', 'clip')
        action_id, direction = clip['action_id'], clip['direction']
        identifier(action_id)
        require(direction in DIRECTIONS, 'Unknown direction')
        actual.append((action_id, direction))
        require(motion['actions'].get(action_id) == clip['action']['file'], 'Action not registered in motion set')
        action = record(clip['action'], f'templates/{template_id}/motions/{motion_id}/actions/{action_id}')
        require(action['action_id'] == action_id and type(action['loop']) is bool, 'Action identity mismatch')
        require(action['directions'].get(direction) == clip['poses']['file'], 'Direction not registered')
        poses = record(clip['poses'], str(PurePosixPath(clip['action']['file']).parent))
        require((poses['template_id'], poses['action_id'], poses['direction']) == (template_id, action_id, direction), 'Pose identity mismatch')
        require(clip['variant'] in poses['variants'], 'Missing actual pose variant')
        variant = poses['variants'][clip['variant']]
        canvas, anchor, scale = clip['canvas_px'], clip['root_anchor_px'], clip['display_scale']
        require(isinstance(canvas, list) and len(canvas) == 2 and all(type(n) is int and 0 < n <= 8192 for n in canvas), 'Invalid canvas')
        require(isinstance(anchor, list) and len(anchor) == 2 and all(type(n) in (int, float) and math.isfinite(n) and 0 <= n <= canvas[i] for i, n in enumerate(anchor)), 'Invalid root anchor')
        require(type(scale) in (int, float) and math.isfinite(scale) and scale > 0, 'Invalid display scale')
        for name in ('canvas_px', 'root_anchor_px', 'display_scale'):
            require(clip[name] == variant.get(name), 'Pose geometry mismatch: ' + name)
        expected = variant.get('frames')
        require(isinstance(expected, list) and expected, 'Template has no real pose frames')
        frames = clip['frames']
        require(isinstance(frames, list) and len(frames) == len(expected), 'Missing or extra pose')
        require(len({f['pose_id'] for f in frames}) == len(frames), 'Duplicate pose')
        for frame, original in zip(frames, expected):
            keys(frame, 'pose_id duration_ms layers layer_order registration composition', 'frame')
            identifier(frame['pose_id'])
            require(frame['pose_id'] == original['pose_id'], 'Wrong pose order')
            duration = frame['duration_ms']
            require(type(duration) in (int, float) and math.isfinite(duration) and duration > 0 and duration == original['duration_ms'], 'Wrong pose timing')
            source_canvas, offset = canvas, [0, 0]
            if frame['registration'] is not None:
                registration = frame['registration']
                keys(registration, 'document record', 'registration')
                document = record(registration['document'])
                require(registration['document']['file'].split('/')[0] in {'sources', 'templates', 'builds'}, 'Wrong registration namespace')
                pointer = registration['record']
                require(isinstance(pointer, str) and re.fullmatch(r'/(frames/[0-9]+|idle)', pointer), 'Invalid registration record')
                registered = document
                for token in pointer[1:].split('/'):
                    registered = registered[int(token)] if isinstance(registered, list) else registered[token]
                require(registered['pose_id'] == frame['pose_id'] and registered['duration_ms'] == duration, 'Registration pose/timing mismatch')
                box = registered['source_box_px']
                offset = registered['whole_frame_translation_px']
                require(isinstance(box, list) and len(box) == 4 and box[:2] == [0, 0] and all(type(n) is int for n in box) and all(n > 0 for n in box[2:]), 'Unsupported registration source box')
                require(isinstance(offset, list) and len(offset) == 2 and all(type(n) is int for n in offset), 'Invalid registration offset')
                require(box == original.get('source_box_px') and offset == original.get('whole_frame_translation_px'), 'Registration differs from template pose')
                require(registered.get('density_normalization') is None, 'Normalize whole-source density before construction')
                source_canvas = box[2:]
                require(all(0 <= offset[i] and offset[i] + source_canvas[i] <= canvas[i] for i in (0, 1)), 'Registration would crop source frame')
            registrations[(action_id, direction, frame['pose_id'])] = (source_canvas, offset)
            require(isinstance(frame['layers'], list) and frame['layers'], 'Missing layers')
            ids = [layer['id'] for layer in frame['layers']]
            require(frame['composition'] in {'alpha-over', 'ownership-replace'}, 'Unsupported composition rule')
            order = frame['layer_order']
            require(len(ids) == len(set(ids)) and isinstance(order, list) and len(order) == len(ids) and set(order) == set(ids), 'Invalid layer order')
            require({layer['slot'] for layer in frame['layers']} == set(slots), 'Missing or unknown layer slot')
            if frame['composition'] == 'ownership-replace':
                bodies = [layer['id'] for layer in frame['layers'] if layer['slot'] == 'body']
                require(len(bodies) == 1 and order[0] == bodies[0], 'Ownership composition requires one first body layer')
            for layer in frame['layers']:
                keys(layer, 'id slot pose_id texture source source_bundle ownership coverage occlusion interface_scope placement_mode offset_px local_scale', 'layer')
                identifier(layer['id'])
                require(layer['pose_id'] == frame['pose_id'], 'Layer pose mismatch')
                require(layer['placement_mode'] == 'full_frame' and layer['offset_px'] == [0, 0] and layer['local_scale'] == [1, 1], 'Unsupported registration transform')
                slot = layer['slot']
                if slot == 'body':
                    require(layer['interface_scope'] == 'same-pose-reference' and all(layer[k] is None for k in ('ownership','coverage','occlusion')), 'Invalid body reference interface')
                    namespace = f'templates/{template_id}/motions/{motion_id}/body-views'
                else:
                    require(layer['interface_scope'] == 'registered-component', 'Unsupported component interface')
                    namespace = str(PurePosixPath(slots[slot]['file']).parent) + f'/adaptations/{template_id}/{motion_id}'
                    for mask in ('ownership', 'coverage', 'occlusion'):
                        require(isinstance(layer[mask], dict), 'Missing component mask: ' + mask)
                        # Ownership may use original source coordinates; coverage and
                        # occlusion must be registered in the target canvas.
                        reference(layer[mask], image_size=source_canvas if mask != 'ownership' else None)
                        require(layer[mask]['file'].split('/')[0] in {'parts', 'templates', 'sources'}, 'Wrong mask namespace')
                        try:
                            with Image.open(safe_file(library, layer[mask]['file'])) as image:
                                require(image.format == 'PNG' and image.mode in {'L', 'RGBA'}, 'Invalid mask image')
                        except OSError as exc:
                            raise ValueError('Invalid mask image') from exc
                        if mask == 'coverage' and frame['composition'] == 'ownership-replace':
                            with Image.open(safe_file(library, layer[mask]['file'])) as image:
                                require(image.mode == 'L' and set(image.get_flattened_data()) <= {0, 255}, 'Ownership coverage must be binary L mask')
                reference(layer['texture'], namespace, source_canvas)
                source_path = reference(layer['source'], 'sources')
                source_base = PurePosixPath(layer['source']['file']).parents[1]
                require(layer['source_bundle']['file'] == str(source_base / 'source.json'), 'Noncanonical source bundle')
                bundle = record(layer['source_bundle'], str(PurePosixPath(layer['source']['file']).parents[1]))
                require(bundle.get('source_id') == source_base.name, 'Source bundle identity mismatch')
                require(source_path.suffix.lower() == '.png', 'Source must be original PNG')
                try:
                    with Image.open(source_path) as source_image:
                        require(source_image.format == 'PNG', 'Source PNG format invalid')
                        source_image.verify()
                except OSError as exc:
                    raise ValueError('Source PNG cannot be decoded') from exc
                require(any(x.get('new_path') == 'art/characters/' + layer['source']['file'] and x.get('new_sha256') == layer['source']['sha256'] for x in bundle.get('assets', [])), 'Source not bound by source bundle')
    require(len(actual) == len(set(actual)) and set(actual) == set(caps), 'Required capabilities differ from actual clips')
    require(all(('idle', direction) in actual for _, direction in actual), 'Matching idle capability missing')
    return Validated(repo, library, recipe_path, recipe, dict(sorted(dependencies.items())), registrations)
