"""Strict construction contract for the single character authoring library.

Only registered full-frame interfaces are supported. Migration manifests are
references, never implicit construction recipes or release attestations.
"""
from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
from PIL import Image, ImageChops

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
    base: object = None

    def image(self, ref):
        with Image.open(safe_file(self.library, ref['file'])) as img:
            return img.convert('RGBA')


def whole_frame_padding(geometry, padding):
    """Derive a transparent output envelope without altering canonical poses."""
    require(isinstance(padding, list) and len(padding) == 4
            and all(type(v) is int and 0 <= v <= 512 for v in padding),
            'Invalid whole-frame output padding')
    left, top, right, bottom = padding
    return dict(geometry,
                canvas_px=[geometry['canvas_px'][0] + left + right,
                           geometry['canvas_px'][1] + top + bottom],
                root_anchor_px=[geometry['root_anchor_px'][0] + left,
                                geometry['root_anchor_px'][1] + top])


class RegisteredAdaptations:
    """Bounded schema3: source-wide binary extraction and integer registration.

    Pose annotations are versioned sidecars: canonical pose files remain frozen.
    This validates source reconstruction, not visual or anatomical correctness.
    """
    def __init__(self, library, recipe, reference, record, template_id, motion, designs):
        self.library, self.reference, self.record = library, reference, record
        self.template_id, self.motion = template_id, motion
        self.motion_id = motion['motion_set_id']
        self.base = f'templates/{template_id}/motions/{self.motion_id}'
        self.annotations = {}
        self.adaptations = {}
        require(isinstance(recipe['adaptations'], dict) and set(recipe['adaptations']) == set(designs),
                'Missing or unknown slot adaptation')
        for slot, design in designs.items():
            namespace = f"parts/{design['design_id']}/adaptations/{template_id}/{self.motion_id}"
            data = record(recipe['adaptations'][slot], namespace)
            keys(data, 'kind schema_version design_id design_revision template_id motion_set_id views mappings', 'adaptation')
            require(data['kind'] == 'coastal-registered-adaptations-v1' and type(data['schema_version']) is int
                    and data['schema_version'] == 1, 'Unsupported adaptation schema')
            require((data['design_id'], data['design_revision'], data['template_id'], data['motion_set_id']) ==
                    (design['design_id'], design['revision'], template_id, self.motion_id), 'Adaptation identity/revision mismatch')
            require(isinstance(data['views'], list) and data['views'] and isinstance(data['mappings'], list)
                    and data['mappings'], 'Missing adaptation views/mappings')
            views, mappings = {}, {}
            for view in data['views']:
                compatibility = slot == 'hair' and isinstance(view, dict) and 'compatibility' in view
                keys(view, 'view_id role source_pose source source_bundle canvas_px root_anchor_px source_ownership extraction'
                     + (' compatibility' if compatibility else ''), 'source view')
                if compatibility:
                    keys(view['compatibility'], 'file sha256', 'hair compatibility reference')
                name = identifier(view['view_id'])
                require(name not in views, 'Duplicate source view')
                require(view['role'] == 'full-source-component', 'Invalid source view role')
                extraction = view['extraction']
                require(isinstance(extraction, dict), 'Invalid source extraction')
                if extraction.get('kind') == 'canonical-surface-alpha-v1':
                    keys(extraction, 'kind schema_version scope material_extraction alpha_reference', 'material alpha extraction')
                    require(type(extraction['schema_version']) is int and extraction['schema_version'] == 1
                            and extraction['scope'] == 'finite-canonical-material'
                            and slot in {'top', 'pants', 'shoes'}, 'Only finite canonical material supports inherited alpha')
                    keys(extraction['alpha_reference'], 'file sha256', 'canonical material alpha reference')
                    extraction = extraction['material_extraction']
                    require(isinstance(extraction, dict), 'Invalid material source extraction')
                if extraction.get('kind') == 'binary-rgba-extract-v1':
                    keys(extraction, 'kind density_normalization', 'source extraction')
                    require(extraction['density_normalization'] is None, 'Unsupported whole-source density normalization')
                elif extraction.get('kind') == 'normalized-source-selection-v1':
                    keys(extraction, 'kind schema_version normalization ownership_space selection_space selections', 'source extraction')
                    require(type(extraction['schema_version']) is int and extraction['schema_version'] == 1,
                            'Unsupported normalized extraction schema')
                    require(extraction['ownership_space'] == extraction['selection_space'] == 'normalized-source-full-frame',
                            'Unsupported ownership/selection coordinate space')
                    require(isinstance(extraction['selections'], list), 'Invalid source selections')
                    selection_ids = set()
                    for selection in extraction['selections']:
                        keys(selection, 'selection_id source source_bundle source_pose normalization selection', 'source selection')
                        selection_id = identifier(selection['selection_id'])
                        require(selection_id not in selection_ids, 'Duplicate source selection')
                        selection_ids.add(selection_id)
                        keys(selection['selection'], 'role mask', 'source selection mask')
                        require(selection['selection']['role'] == 'source-selection', 'Invalid source selection role')
                elif extraction.get('kind') == 'registered-source-atlas-v1':
                    keys(extraction, 'kind schema_version atlas_canvas_px normalization atlas_ownership registration', 'atlas extraction')
                    require(type(extraction['schema_version']) is int and extraction['schema_version'] == 1,
                            'Unsupported atlas extraction schema')
                    keys(extraction['atlas_ownership'], 'role coordinate_space mask', 'atlas ownership')
                    require(extraction['atlas_ownership']['role'] == 'source-atlas-ownership', 'Invalid atlas ownership role')
                    require(extraction['atlas_ownership']['coordinate_space'] == 'normalized-source-atlas',
                            'Invalid atlas ownership space')
                    keys(extraction['registration'], 'kind atlas_anchor_px pose_anchor_name pose_anchor_px', 'atlas registration')
                    require(extraction['registration']['kind'] == 'atlas-to-source-pose-anchor-v1', 'Unsupported atlas registration')
                    identifier(extraction['registration']['pose_anchor_name'])
                else:
                    raise ValueError('Unsupported source extraction kind')
                keys(view['source_ownership'], 'role mask', 'source ownership')
                require(view['source_ownership']['role'] == 'source-ownership', 'Invalid source ownership role')
                views[name] = view
            for mapping in data['mappings']:
                keys(mapping, 'mapping_id view_id texture target_pose target_surface interface_scope role anchors coverage occlusion', 'mapping')
                name = identifier(mapping['mapping_id'])
                require(name not in mappings, 'Duplicate mapping')
                identifier(mapping['view_id'])
                require(mapping['view_id'] in views, 'Mapping source view missing')
                require(mapping['role'] == 'component-surface' and mapping['interface_scope'] == 'same-cut-surface',
                        'Unsupported mapping interface/role')
                keys(mapping['target_surface'], 'surface_id layer_id', 'target surface')
                identifier(mapping['target_surface']['surface_id']); identifier(mapping['target_surface']['layer_id'])
                keys(mapping['anchors'], 'name source_px target_px', 'mapping anchors')
                identifier(mapping['anchors']['name'])
                mappings[name] = mapping
            self.adaptations[slot] = (views, mappings, namespace)

    def mask(self, ref, size):
        require(isinstance(ref, dict), 'Missing binary mask')
        path = self.reference(ref, image_size=size)
        require(ref['file'].split('/')[0] in {'parts', 'templates', 'sources'}, 'Wrong mask namespace')
        with Image.open(path) as image:
            require(image.format == 'PNG' and image.mode == 'L'
                    and set(image.get_flattened_data()) <= {0, 255}, 'Schema3 masks must be binary L')
            return image.copy()

    def annotation(self, selector):
        keys(selector, 'document record', 'pose annotation selector')
        require(isinstance(selector['record'], str), 'Invalid annotation record')
        document = self.record(selector['document'], self.base + '/annotations')
        cache_key = (selector['document']['file'], selector['document']['sha256'], selector['record'])
        if cache_key in self.annotations:
            return self.annotations[cache_key]
        keys(document, 'kind schema_version template_id motion_set_id revision records', 'pose annotations')
        require(document['kind'] == 'coastal-pose-annotations-v1' and type(document['schema_version']) is int
                and document['schema_version'] == 1, 'Unsupported pose annotation schema')
        revision = identifier(document['revision'])
        require(selector['document']['file'] == f'{self.base}/annotations/{revision}/poses.json'
                and document['template_id'] == self.template_id and document['motion_set_id'] == self.motion_id,
                'Pose annotation identity/path mismatch')
        require(isinstance(document['records'], list) and document['records'], 'Missing annotation records')
        records = {}
        for item in document['records']:
            keys(item, 'record_id poses variant pose_id reference_frame canvas_px root_anchor_px display_scale landmarks_px surfaces', 'pose annotation record')
            name = identifier(item['record_id'])
            require(name not in records, 'Duplicate annotation record')
            records[name] = item
        require(selector['record'] in records, 'Missing annotation record')
        item = records[selector['record']]
        pose_doc = self.record(item['poses'], self.base + '/actions')
        require(pose_doc.get('template_id') == self.template_id, 'Annotation canonical template mismatch')
        action_id, direction = pose_doc.get('action_id'), pose_doc.get('direction')
        require(isinstance(action_id, str) and action_id in self.motion['actions']
                and isinstance(direction, str) and direction in DIRECTIONS, 'Annotation canonical action missing')
        action_file = self.motion['actions'][action_id]
        action = self.record({'file': action_file, 'sha256': digest(safe_file(self.library, action_file))},
                             self.base + '/actions/' + action_id)
        require(action.get('directions', {}).get(direction) == item['poses']['file'], 'Annotation noncanonical poses')
        require(isinstance(pose_doc.get('variants'), dict) and isinstance(item['variant'], str)
                and item['variant'] in pose_doc['variants'], 'Annotation variant missing')
        variant = pose_doc['variants'][item['variant']]
        matches = [frame for frame in variant.get('frames', []) if frame.get('pose_id') == item['pose_id']]
        require(len(matches) == 1, 'Annotation canonical pose missing')
        original = matches[0]
        for field in ('canvas_px', 'root_anchor_px', 'display_scale'):
            require(item[field] == variant.get(field), 'Pose annotation geometry mismatch: ' + field)
        require(item['reference_frame'] == {'file': original.get('file'), 'sha256': original.get('sha256')},
                'Pose annotation reference frame mismatch')
        require(item['reference_frame']['file'].split('/')[0] in {'templates', 'builds', 'sources'},
                'Wrong annotation frame namespace')
        self.reference(item['reference_frame'], image_size=item['canvas_px'])
        require(isinstance(item['landmarks_px'], dict) and item['landmarks_px'], 'Missing annotation landmarks')
        for name, point in item['landmarks_px'].items():
            identifier(name)
            require(isinstance(point, list) and len(point) == 2
                    and all(type(v) is int and 0 <= v <= item['canvas_px'][i] for i, v in enumerate(point)),
                    'Invalid annotation anchor')
        require(isinstance(item['surfaces'], dict) and item['surfaces'], 'Missing annotation surfaces')
        for name, surface in item['surfaces'].items():
            identifier(name); keys(surface, 'layer_id mask', 'annotation surface')
            identifier(surface['layer_id']); self.mask(surface['mask'], item['canvas_px'])
        result = (item, original, action_id, direction)
        self.annotations[cache_key] = result
        return result

    def source_png(self, source, source_bundle, canvas, pose_id=None):
        """Read a full original source, with canonical bundle and actual bytes bound."""
        try:
            path = self.reference(source, 'sources', canvas)
            source_base = PurePosixPath(source['file']).parents[1]
            keys(source_bundle, 'file sha256', 'source bundle reference')
            require(source_bundle['file'] == str(source_base / 'source.json'), 'Noncanonical source bundle')
            bundle = self.record(source_bundle, str(source_base))
            require(isinstance(bundle, dict), 'Source bundle must be an object')
            require(bundle.get('source_id') == source_base.name, 'Source bundle identity mismatch')
            require(pose_id is None or bundle.get('source_view_pose', pose_id) == pose_id,
                    'Declared source bundle pose differs from annotation')
            require(isinstance(bundle.get('assets'), list) and all(isinstance(asset, dict) for asset in bundle['assets']),
                    'Source bundle assets must be a list of objects')
            require(any(
                asset.get('new_path') == 'art/characters/' + source['file']
                and asset.get('new_sha256') == source['sha256'] for asset in bundle['assets']),
                'Source not bound by source bundle')
            with Image.open(path) as image:
                require(image.format == 'PNG', 'Source PNG format invalid')
                return image.convert('RGBA')
        except OSError as exc:
            raise ValueError('Source PNG cannot be decoded') from exc

    def normalized_source(self, source, source_bundle, normalization, canvas, root, pose_id):
        """Normalize the entire original source using one explicit rational ratio."""
        padded = isinstance(normalization, dict) and normalization.get('kind') == 'whole-source-rational-pad-v1'
        keys(normalization, 'kind filter numerator denominator raw_canvas_px raw_root_anchor_px normalized_canvas_px normalized_root_anchor_px'
             + (' whole_frame_offset_px' if padded else ''),
             'source normalization')
        require(isinstance(normalization['kind'], str)
                and normalization['kind'] in {'whole-source-rational-v1', 'whole-source-rational-pad-v1'} and normalization['filter'] == 'nearest',
                'Unsupported whole-source normalization/filter')
        numerator, denominator = normalization['numerator'], normalization['denominator']
        require(type(numerator) is int and type(denominator) is int and numerator > 0 and denominator > 0
                and math.gcd(numerator, denominator) == 1, 'Normalization ratio must be positive reduced rational')
        raw_canvas = normalization['raw_canvas_px']; raw_root = normalization['raw_root_anchor_px']
        require(isinstance(raw_canvas, list) and len(raw_canvas) == 2
                and all(type(v) is int and 0 < v <= 8192 for v in raw_canvas), 'Invalid normalization raw canvas')
        require(normalization['normalized_canvas_px'] == canvas and normalization['normalized_root_anchor_px'] == root,
                'Normalization canvas/root differs from registered source pose')
        require(isinstance(raw_root, list) and len(raw_root) == 2 and all(
            type(v) in (int, float) and math.isfinite(v) and 0 <= v <= raw_canvas[i]
            for i, v in enumerate(raw_root)), 'Invalid normalization raw root')
        if padded:
            offset = normalization['whole_frame_offset_px']
            require(isinstance(offset, list) and len(offset) == 2 and all(type(v) is int and v >= 0 for v in offset),
                    'Invalid whole-frame normalization offset')
            extent = [(v * numerator + denominator - 1) // denominator for v in raw_canvas]
            require(all(offset[i] + extent[i] <= canvas[i] for i in (0, 1)),
                    'Normalization padding would crop complete raw source extent')
            ratio = Fraction(numerator, denominator)
            require(all(Fraction(str(raw_root[i])) * ratio + offset[i] == Fraction(str(root[i])) for i in (0, 1)),
                    'Normalization root is not the registered padded whole-source root')
        else:
            require(all(raw_canvas[i] * numerator == canvas[i] * denominator for i in (0, 1)),
                    'Normalization must be source-wide uniform and integral canvas')
            require(all(raw_root[i] * numerator == root[i] * denominator for i in (0, 1)),
                    'Normalization root is not the registered whole-source root')
        full = self.source_png(source, source_bundle, raw_canvas, pose_id)
        if padded:
            inverse = denominator / numerator
            return full.transform(tuple(canvas), Image.Transform.AFFINE,
                                  (inverse, 0, -offset[0] * inverse, 0, inverse, -offset[1] * inverse),
                                  resample=Image.Resampling.NEAREST, fillcolor=(0, 0, 0, 0))
        return full.resize(tuple(canvas), Image.Resampling.NEAREST)

    def source_pixels(self, view, annotation):
        """Rebuild normalized/selected source pixels; never accept a derived PNG as original."""
        extraction = view['extraction']
        if extraction['kind'] == 'canonical-surface-alpha-v1':
            require(extraction['alpha_reference'] == annotation['reference_frame'],
                    'Material alpha must use the canonical source frame')
            material = self.source_pixels(dict(view, extraction=extraction['material_extraction']), annotation)
            owner = self.mask(view['source_ownership']['mask'], view['canvas_px'])
            alpha = material.getchannel('A')
            require(ImageChops.subtract(owner, alpha.point(lambda a: 255 if a else 0)).getbbox() is None,
                    'Canonical alpha cannot fill missing material pixels')
            reference = self.reference(extraction['alpha_reference'], image_size=view['canvas_px'])
            with Image.open(reference) as image:
                canonical_alpha = image.convert('RGBA').getchannel('A')
            require(ImageChops.subtract(owner, canonical_alpha.point(lambda a: 255 if a else 0)).getbbox() is None,
                    'Material ownership exceeds canonical source support')
            material.putalpha(Image.composite(canonical_alpha, alpha, owner))
            return material
        if extraction['kind'] == 'binary-rgba-extract-v1':
            return self.source_png(view['source'], view['source_bundle'], view['canvas_px'], annotation['pose_id'])
        if extraction['kind'] == 'registered-source-atlas-v1':
            return self.atlas_source(view, annotation)
        require(extraction['kind'] == 'normalized-source-selection-v1', 'Unsupported source extraction kind')
        canvas, root = annotation['canvas_px'], annotation['root_anchor_px']
        selected = self.normalized_source(view['source'], view['source_bundle'], extraction['normalization'], canvas, root, annotation['pose_id'])
        for entry in extraction['selections']:
            require(entry['source_pose'] == view['source_pose'], 'Selection source pose differs from registered base source pose')
            # The same annotation is explicitly bound for every complete source;
            # no independent offsets or anatomy/pose substitutions are allowed.
            extra_annotation, _, _, _ = self.annotation(entry['source_pose'])
            require(extra_annotation == annotation, 'Selection source pose registration mismatch')
            overlay = self.normalized_source(entry['source'], entry['source_bundle'], entry['normalization'], canvas, root, annotation['pose_id'])
            selection = self.mask(entry['selection']['mask'], canvas)
            selected = Image.composite(overlay, selected, selection)
        return selected

    def atlas_source(self, view, annotation):
        """Select an owned atlas view, then register it into canonical source space.

        Image origins used for whole-atlas density are not actor world roots.
        Anatomical anchor meaning remains the measured authoring declaration.
        """
        extraction = view['extraction']; canvas = extraction['atlas_canvas_px']
        require(isinstance(canvas, list) and len(canvas) == 2
                and all(type(v) is int and 0 < v <= 8192 for v in canvas), 'Invalid source atlas canvas')
        normalization = extraction['normalization']
        padded = isinstance(normalization, dict) and normalization.get('kind') == 'whole-source-rational-pad-v1'
        keys(normalization, 'kind filter numerator denominator raw_canvas_px raw_origin_px normalized_canvas_px normalized_origin_px'
             + (' whole_frame_offset_px' if padded else ''), 'atlas normalization')
        for field in ('raw_origin_px', 'normalized_origin_px'):
            require(isinstance(normalization[field], list) and len(normalization[field]) == 2
                    and all(type(v) is int and v == 0 for v in normalization[field]),
                    'Atlas normalization origin must be the zero image origin')
        require(normalization['normalized_canvas_px'] == canvas, 'Atlas normalization canvas mismatch')
        # Adapt explicit image-origin anchors to the one existing normalizer;
        # no world-root claim is stored in this source-atlas contract.
        density = dict(normalization)
        density['raw_root_anchor_px'] = density.pop('raw_origin_px')
        density['normalized_root_anchor_px'] = density.pop('normalized_origin_px')
        atlas = self.normalized_source(view['source'], view['source_bundle'], density, canvas, [0, 0], annotation['pose_id'])
        owner = self.mask(extraction['atlas_ownership']['mask'], canvas)
        owned = Image.composite(atlas, Image.new('RGBA', tuple(canvas)), owner)
        registration = extraction['registration']; anchor = registration['atlas_anchor_px']
        require(isinstance(anchor, list) and len(anchor) == 2
                and all(type(v) is int and 0 <= v <= canvas[i] for i, v in enumerate(anchor)), 'Invalid source atlas anchor')
        name, point = registration['pose_anchor_name'], registration['pose_anchor_px']
        require(name in annotation['landmarks_px'] and point == annotation['landmarks_px'][name],
                'Atlas pose anchor differs from source pose annotation')
        delta = [point[i] - anchor[i] for i in (0, 1)]
        bounds = owned.getchannel('A').getbbox(); target = annotation['canvas_px']
        require(bounds is not None, 'Atlas reconstruction has no owned alpha support')
        require(all(0 <= bounds[i] + delta[i] and bounds[i+2] + delta[i] <= target[i] for i in (0, 1)),
                'Atlas registration would crop owned alpha support')
        registered = Image.new('RGBA', tuple(target)); registered.paste(owned, tuple(delta))
        return registered

    def component(self, layer, clip, frame, output_padding=None):
        try:
            return self._component(layer, clip, frame, output_padding)
        except OSError as exc:
            raise ValueError('Invalid schema3 source/texture/mask PNG') from exc

    def _component(self, layer, clip, frame, output_padding=None):
        require(isinstance(layer, dict) and isinstance(layer.get('slot'), str)
                and layer['slot'] in self.adaptations, 'Unknown registered component slot')
        views, mappings, namespace = self.adaptations[layer['slot']]
        binding = layer['view_binding']
        keys(binding, 'view_id mapping_id', 'view binding')
        identifier(binding['view_id']); identifier(binding['mapping_id'])
        require(binding['view_id'] in views and binding['mapping_id'] in mappings, 'Missing registered view/mapping')
        view, mapping = views[binding['view_id']], mappings[binding['mapping_id']]
        require(mapping['view_id'] == binding['view_id'], 'Mapping/view identity mismatch')
        if 'compatibility' in view:
            self.reference(view['compatibility'], namespace)
        source, _, _, _ = self.annotation(view['source_pose'])
        target, original, action_id, direction = self.annotation(mapping['target_pose'])
        require((target['pose_id'], action_id, direction, target['poses'], target['variant']) ==
                (frame['pose_id'], clip['action_id'], clip['direction'], clip['poses'], clip['variant']),
                'Mapping target pose mismatch')
        require(layer['interface_scope'] == 'registered-component', 'Unsupported component interface')
        require(view['canvas_px'] == source['canvas_px'] and view['root_anchor_px'] == source['root_anchor_px'],
                'Source view/annotation geometry mismatch')
        require(layer['source'] == view['source'] and layer['source_bundle'] == view['source_bundle'],
                'Layer/source view identity mismatch')
        require(layer['ownership'] == view['source_ownership']['mask'], 'Source ownership binding mismatch')
        require(layer['texture'] == mapping['texture'], 'Mapping texture mismatch')
        full = self.source_pixels(view, source)
        ownership = self.mask(view['source_ownership']['mask'], view['canvas_px'])
        extracted = Image.composite(full, Image.new('RGBA', full.size), ownership)
        anchors = mapping['anchors']; name = anchors['name']
        require(name in source['landmarks_px'] and name in target['landmarks_px']
                and anchors['source_px'] == source['landmarks_px'][name]
                and anchors['target_px'] == target['landmarks_px'][name], 'Mapping anchor differs from annotation')
        delta = [anchors['target_px'][i] - anchors['source_px'][i] for i in (0, 1)]
        canvas = clip['canvas_px']
        if output_padding is not None:
            require(layer['slot'] in {'hair', 'hat'} and layer['coverage'] is None
                    and layer['occlusion'] is None and frame['composition'] == 'alpha-over',
                    'Output envelope only supports registered alpha head layers')
            canvas = whole_frame_padding(clip, output_padding)['canvas_px']
            delta = [delta[0] + output_padding[0], delta[1] + output_padding[1]]
        bounds = extracted.getchannel('A').getbbox()
        require(bounds is not None, 'Source reconstruction has no owned alpha support')
        require(all(type(v) is int and 0 <= bounds[i] + v and bounds[i + 2] + v <= canvas[i]
                    for i, v in enumerate(delta)), 'Registration would crop owned component alpha support')
        registered = Image.new('RGBA', tuple(canvas)); registered.paste(extracted, tuple(delta))
        surface_id, surface_layer = mapping['target_surface']['surface_id'], mapping['target_surface']['layer_id']
        require(surface_id in target['surfaces'] and target['surfaces'][surface_id]['layer_id'] == surface_layer,
                'Unregistered target surface')
        require(any(item['id'] == surface_layer and item['slot'] == 'body' for item in frame['layers']),
                'Target surface must bind an actual body layer')
        coverage = mapping['coverage']
        if coverage is None:
            require(layer['coverage'] is None and frame['composition'] == 'alpha-over', 'Binary replacement requires coverage')
        else:
            keys(coverage, 'role mask target_surface', 'target coverage')
            require(coverage['role'] == 'target-coverage', 'Invalid coverage role')
            require(coverage['target_surface'] == mapping['target_surface'], 'Coverage target surface mismatch')
            require(frame['composition'] == 'ownership-replace' and layer['coverage'] == coverage['mask'],
                    'Unsupported alpha-over coverage or coverage binding')
            cover = self.mask(coverage['mask'], canvas)
            surface = self.mask(target['surfaces'][surface_id]['mask'], canvas)
            require(ImageChops.subtract(cover, surface).getbbox() is None, 'Coverage exceeds registered target surface')
        occlusion = mapping['occlusion']
        if occlusion is None:
            require(layer['occlusion'] is None, 'Occlusion binding mismatch')
        else:
            keys(occlusion, 'role mask foreground_layers', 'target occlusion')
            require(occlusion['role'] == 'target-occlusion' and layer['occlusion'] == occlusion['mask'],
                    'Invalid occlusion role/binding')
            foreground = occlusion['foreground_layers']; order = frame['layer_order']
            require(isinstance(foreground, list) and foreground and all(isinstance(name, str) for name in foreground)
                    and len(foreground) == len(set(foreground))
                    and all(name in order and order.index(name) > order.index(layer['id']) for name in foreground),
                    'Occlusion foreground differs from ordered layers')
            hidden = self.mask(occlusion['mask'], canvas)
            opaque_foreground_support = Image.new('L', tuple(canvas))
            for item in frame['layers']:
                if item['id'] in foreground:
                    with Image.open(self.reference(item['texture'], image_size=canvas)) as image:
                        support = image.convert('RGBA').getchannel('A').point(lambda alpha: 255 if alpha == 255 else 0)
                    opaque_foreground_support = ImageChops.lighter(opaque_foreground_support, support)
            require(ImageChops.subtract(hidden, opaque_foreground_support).getbbox() is None,
                    'Occlusion exceeds fully opaque foreground support')
            registered = Image.composite(Image.new('RGBA', tuple(canvas)), registered, hidden)
        path = self.reference(layer['texture'], namespace, canvas)
        with Image.open(path) as image:
            require(image.convert('RGBA').tobytes() == registered.tobytes(), 'Registered texture reconstruction mismatch')
        return namespace


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
    if isinstance(recipe, dict) and type(recipe.get('schema_version')) is int and recipe['schema_version'] == 2:
        from composition_contract import validate_composition
        return validate_composition(repo, recipe_path, recipe)
    schema3 = isinstance(recipe, dict) and type(recipe.get('schema_version')) is int and recipe['schema_version'] == 3
    keys(recipe, 'kind schema_version resource_root character_model_id recipe_id revision template motion_set slots required_capabilities clips authoring_inputs' + (' adaptations' if schema3 else ''), 'recipe')
    require(recipe['kind'] == KIND and type(recipe['schema_version']) is int and recipe['schema_version'] in {1, 3}, 'Unsupported schema')
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
    designs = {}
    for slot, ref in slots.items():
        if slot == 'body':
            continue
        design = record(ref, 'parts')
        if schema3:
            require(isinstance(design, dict) and all(name in design for name in ('design_id', 'category')),
                    'Part definition identity missing')
        require(design['category'] == slot, 'Part slot mismatch')
        design_id = identifier(design['design_id'])
        if schema3:
            require(isinstance(design.get('revision'), str), 'Part definition revision missing')
            revision = identifier(design['revision'])
            require(ref['file'] == f'parts/{design_id}/revisions/{revision}/design.json', 'Part revision identity/path mismatch')
            designs[slot] = design
        else:
            require(ref['file'] == f'parts/{design_id}/design.json', 'Part identity/path mismatch')
    adaptations = RegisteredAdaptations(library, recipe, reference, record, template_id, motion, designs) if schema3 else None

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
            if schema3:
                # Pose identity belongs to the frozen canonical template, whose
                # historical A/B tokens are case-sensitive. This is not a new
                # naming rule for recipes, parts, views or legacy schemas.
                require(isinstance(frame['pose_id'], str)
                        and re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]*', frame['pose_id']),
                        'Invalid canonical pose token')
            else:
                identifier(frame['pose_id'])
            require(frame['pose_id'] == original['pose_id'], 'Wrong pose order')
            duration = frame['duration_ms']
            require(type(duration) in (int, float) and math.isfinite(duration) and duration > 0 and duration == original['duration_ms'], 'Wrong pose timing')
            source_canvas, offset = canvas, [0, 0]
            if schema3:
                require(frame['registration'] is None, 'Schema3 uses target-registered views, not additional frame registration')
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
                keys(layer, 'id slot pose_id texture source source_bundle ownership coverage occlusion interface_scope placement_mode offset_px local_scale' + (' view_binding' if schema3 and layer['slot'] != 'body' else ''), 'layer')
                identifier(layer['id'])
                require(layer['pose_id'] == frame['pose_id'], 'Layer pose mismatch')
                require(layer['placement_mode'] == 'full_frame' and layer['offset_px'] == [0, 0] and layer['local_scale'] == [1, 1], 'Unsupported registration transform')
                slot = layer['slot']
                if slot == 'body':
                    require(layer['interface_scope'] == 'same-pose-reference' and all(layer[k] is None for k in ('ownership','coverage','occlusion')), 'Invalid body reference interface')
                    namespace = f'templates/{template_id}/motions/{motion_id}/body-views'
                else:
                    require(layer['interface_scope'] == 'registered-component', 'Unsupported component interface')
                    namespace = adaptations.component(layer, clip, frame) if schema3 else str(PurePosixPath(slots[slot]['file']).parent) + f'/adaptations/{template_id}/{motion_id}'
                    for mask in (() if schema3 else ('ownership', 'coverage', 'occlusion')):
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
                if schema3 and slot == 'body':
                    canonical = {'file': original.get('file'), 'sha256': original.get('sha256')}
                    require(isinstance(canonical['file'], str) and canonical['file'].split('/')[0] in {'templates', 'sources', 'builds'},
                            'Schema3 canonical body frame missing or invalid')
                    try:
                        canonical_path = reference(canonical, image_size=canvas)
                        with Image.open(canonical_path) as image:
                            expected_body = image.convert('RGBA')
                        with Image.open(safe_file(library, layer['texture']['file'])) as image:
                            require(image.convert('RGBA').tobytes() == expected_body.tobytes(),
                                    'Schema3 body texture differs from canonical body frame')
                    except OSError as exc:
                        raise ValueError('Invalid canonical body PNG') from exc
                source_path = reference(layer['source'], 'sources')
                source_base = PurePosixPath(layer['source']['file']).parents[1]
                require(layer['source_bundle']['file'] == str(source_base / 'source.json'), 'Noncanonical source bundle')
                bundle = record(layer['source_bundle'], str(PurePosixPath(layer['source']['file']).parents[1]))
                if schema3:
                    require(isinstance(bundle, dict), 'Source bundle must be an object')
                    require(isinstance(bundle.get('assets'), list) and all(isinstance(asset, dict) for asset in bundle['assets']),
                            'Source bundle assets must be a list of objects')
                require(bundle.get('source_id') == source_base.name, 'Source bundle identity mismatch')
                require(source_path.suffix.lower() == '.png', 'Source must be original PNG')
                try:
                    with Image.open(source_path) as source_image:
                        require(source_image.format == 'PNG', 'Source PNG format invalid')
                        source_image.verify()
                except OSError as exc:
                    raise ValueError('Source PNG cannot be decoded') from exc
                require(any(x.get('new_path') == 'art/characters/' + layer['source']['file'] and x.get('new_sha256') == layer['source']['sha256'] for x in bundle.get('assets', [])), 'Source not bound by source bundle')
            if schema3:
                require(sum(layer['slot'] == 'body' for layer in frame['layers']) == 1,
                        'Schema3 requires one canonical body layer')
    require(len(actual) == len(set(actual)) and set(actual) == set(caps), 'Required capabilities differ from actual clips')
    require(all(('idle', direction) in actual for _, direction in actual), 'Matching idle capability missing')
    return Validated(repo, library, recipe_path, recipe, dict(sorted(dependencies.items())), registrations)
