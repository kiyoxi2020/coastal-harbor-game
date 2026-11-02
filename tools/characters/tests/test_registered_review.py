"""Actual strict/source-prep fixtures for the finite registered review adapter."""
import copy
import hashlib
import importlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

from PIL import Image

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
import build
import prepare_registered_source as preparation


def fixture(root):
    """Small genuine schema3 + prepared-source build, independent of current art."""
    library = root / 'art/characters'
    def write(name, value):
        path = library / name; path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(value, dict): path.write_text(json.dumps(value))
        else: value.save(path)
        return {'file': name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    def ref(name):
        return {'file': name, 'sha256': hashlib.sha256((library / name).read_bytes()).hexdigest()}
    raw = write('sources/body/originals/body.png', Image.new('RGBA', (2, 2), (30, 40, 50, 255)))
    body_bundle = write('sources/body/source.json', {'source_id': 'body', 'assets': [
        {'new_path': 'art/characters/' + raw['file'], 'new_sha256': raw['sha256']}]})
    cloth = write('sources/cloth/originals/cloth.png', Image.new('RGBA', (2, 2), (210, 20, 30, 128)))
    owner = write('sources/cloth/ownership/cloth.png', Image.new('L', (2, 2), 255))
    canonical = write('templates/fixture/motions/motion/body-views/body.png', Image.new('RGBA', (2, 2), (30, 40, 50, 255)))
    surface = write('templates/fixture/motions/motion/annotations/r001/surface.png', Image.new('L', (2, 2), 255))
    geometry = {'canvas_px': [2, 2], 'root_anchor_px': [1, 1], 'display_scale': 1.0}
    clips, actions, registrations, preparations, records = [], {}, [], [], []
    for action, count in [('idle', 1), ('walk', 2)]:
        frames = [{'pose_id': f'{action}_east_{i}', 'duration_ms': 70 + i * 20} for i in range(count)]
        poses = write(f'templates/fixture/motions/motion/actions/{action}/r001/east/poses.json', {
            'template_id': 'fixture', 'action_id': action, 'direction': 'east',
            'variants': {'visible': {**geometry, 'frames': [{**f, **canonical} for f in frames]}}})
        act = write(f'templates/fixture/motions/motion/actions/{action}/r001/action.json', {
            'action_id': action, 'revision': 'r001', 'loop': True, 'directions': {'east': poses['file']}})
        actions[action] = act['file']
        clips.append({**geometry, 'action_id': action, 'direction': 'east', 'action': act,
                      'poses': poses, 'variant': 'visible', 'frames': frames})
        for i, frame in enumerate(frames):
            registrations.append({'representation': 'body', 'action': action, 'direction': 'east',
                'frame_index': i, **frame, 'source': {**raw, 'size_px': [2, 2], 'box_px': [0, 0, 2, 2]},
                'source_root_px': [1, 1], 'scale': [1, 1], 'authoring_inputs': []})
            preparations.append({'pose_id': frame['pose_id'], 'source': cloth, 'ownership': owner,
                'box_px': [0, 0, 2, 2], 'density_ratio': [1, 1], 'canonical_poses': poses, 'variant': 'visible'})
            records.append({'record_id': frame['pose_id'], 'poses': poses, 'variant': 'visible',
                'pose_id': frame['pose_id'], 'reference_frame': canonical, **geometry,
                'landmarks_px': {'root': [1, 1]}, 'surfaces': {'torso': {'layer_id': 'body', 'mask': surface}}})
    packing = write('sources/body/packing/r001.json', {'kind': 'coastal-character-source-atlas-plan-v1',
        'schema_version': 1, 'resource_root': 'art/characters', 'source_id': 'body', 'revision': 'r001',
        'cell_px': [2, 2], 'root_px': [1, 1], 'rows': ['north', 'west', 'south', 'east'], 'frames': registrations})
    plan = write('sources/cloth/preparation/r001.json', {'kind': preparation.PLAN_KIND, 'schema_version': 1,
        'resource_root': 'art/characters', 'source_id': 'prepared', 'registration_plan': packing,
        'frames': preparations, 'authoring_inputs': []})
    prepared_dir = library / 'sources/prepared'
    prepared = preparation.build(root, library / plan['file'], prepared_dir)
    bundle = ref('sources/prepared/source.json')
    motion = write('templates/fixture/motions/motion/motion-set.json', {'template_id': 'fixture', 'motion_set_id': 'motion', 'actions': actions})
    template = write('templates/fixture/template.json', {'template_id': 'fixture', 'active_revision': 'r001', 'motion_set': motion['file']})
    design = write('parts/top/red/revisions/r001/design.json', {'design_id': 'red', 'category': 'top', 'revision': 'r001'})
    annotation = write('templates/fixture/motions/motion/annotations/r001/poses.json', {
        'kind': 'coastal-pose-annotations-v1', 'schema_version': 1, 'template_id': 'fixture',
        'motion_set_id': 'motion', 'revision': 'r001', 'records': records})
    views, mappings = [], []
    for clip in clips:
        for frame in clip['frames']:
            pose = frame['pose_id']
            source = ref(f'sources/prepared/materials/{pose}.png')
            mask = ref(f'sources/prepared/ownership/{pose}.png')
            texture_name = f'parts/top/red/fixture/motion/r001/textures/{pose}.png'
            texture_path = library / texture_name; texture_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(library / f'sources/prepared/textures/{pose}.png', texture_path)
            texture = ref(texture_name)
            selector = {'document': annotation, 'record': pose}
            views.append({'view_id': pose, 'role': 'full-source-component', 'source_pose': selector,
                'source': source, 'source_bundle': bundle, **{k: geometry[k] for k in ('canvas_px', 'root_anchor_px')},
                'source_ownership': {'role': 'source-ownership', 'mask': mask},
                'extraction': {'kind': 'binary-rgba-extract-v1', 'density_normalization': None}})
            mappings.append({'mapping_id': pose, 'view_id': pose, 'texture': texture, 'target_pose': selector,
                'target_surface': {'surface_id': 'torso', 'layer_id': 'body'}, 'interface_scope': 'same-cut-surface',
                'role': 'component-surface', 'anchors': {'name': 'root', 'source_px': [1, 1], 'target_px': [1, 1]},
                'coverage': None, 'occlusion': None})
            layers = []
            for slot in ('body', 'top'):
                layers.append({'id': slot, 'slot': slot, 'pose_id': pose, 'texture': canonical if slot == 'body' else texture,
                    'source': raw if slot == 'body' else source, 'source_bundle': body_bundle if slot == 'body' else bundle,
                    'ownership': None if slot == 'body' else mask, 'coverage': None, 'occlusion': None,
                    'interface_scope': 'same-pose-reference' if slot == 'body' else 'registered-component',
                    'placement_mode': 'full_frame', 'offset_px': [0, 0], 'local_scale': [1, 1],
                    **({} if slot == 'body' else {'view_binding': {'view_id': pose, 'mapping_id': pose}})})
            frame.update(layers=layers, layer_order=['body', 'top'], registration=None, composition='alpha-over')
    adaptation = write('parts/top/red/fixture/motion/r001/views.json', {'kind': 'coastal-registered-adaptations-v1',
        'schema_version': 1, 'design_id': 'red', 'design_revision': 'r001', 'template_id': 'fixture',
        'motion_set_id': 'motion', 'views': views, 'mappings': mappings})
    authoring = [ref(name) for name in prepared['inputs']]
    authoring += [ref('sources/prepared/manifest.json'), bundle]
    authoring += [ref('sources/prepared/' + row['file']) for row in prepared['outputs'] if row['file'].endswith('.png')]
    recipe = {'kind': 'coastal-character-construction-v1', 'schema_version': 3, 'resource_root': 'art/characters',
        'character_model_id': 'unified-composable-character-v1', 'recipe_id': 'review', 'revision': 'r001',
        'template': template, 'motion_set': motion, 'slots': {'body': None, 'top': design},
        'required_capabilities': [{'action_id': c['action_id'], 'direction': c['direction']} for c in clips],
        'clips': clips, 'authoring_inputs': authoring, 'adaptations': {'top': adaptation}}
    recipe_ref = write('recipes/review/r001.json', recipe)
    output = library / 'builds/review-r001'
    manifest = build.construct(root, library / recipe_ref['file'], output)
    suite = {'kind': 'coastal-registered-character-review-v1', 'schema_version': 1, 'resource_root': 'art/characters',
        'scope': 'review-only', 'manifest': ref('builds/review-r001/manifest.json'),
        'prepared_sources': [ref('sources/prepared/manifest.json')],
        'runtime': {'world_scale': .25, 'walk_world_speed': 72.0, 'speed_factor': .75}}
    suite_path = library / 'reviews/registered/review.json'
    write(suite_path.relative_to(library).as_posix(), suite)
    for name in ('build.py', 'build_contract.py', 'composition_contract.py', 'prepare_registered_source.py'):
        destination = root / 'tools/characters' / name; destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(TOOLS / name, destination)
    return {'root': root, 'library': library, 'suite': suite, 'path': suite_path, 'recipe': recipe,
            'manifest': manifest, 'prepared': prepared, 'write': write, 'ref': ref, 'output': output}


class RegisteredReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='coastal-registered-review-', dir='/private/tmp')
        self.addCleanup(self.temp.cleanup)
        self.f = fixture(Path(self.temp.name))

    def module(self):
        self.assertTrue((TOOLS / 'registered_review.py').exists(), 'registered review preflight missing')
        return importlib.import_module('registered_review')

    def preflight(self):
        self.f['write']('reviews/registered/review.json', self.f['suite'])
        return self.module().preflight(self.f['root'], self.f['path'])

    def test_real_strict_prepared_finite_fixture_and_generic_direction(self):
        self.assertEqual(self.preflight(), self.f['suite'])

    def test_suite_unknown_fields_runtime_types_ranges_and_schema(self):
        original = copy.deepcopy(self.f['suite'])
        for defect in ('extra', 'schema', 'scope', 'world', 'speed', 'factor', 'runtime-extra'):
            with self.subTest(defect=defect):
                suite = copy.deepcopy(original)
                if defect == 'extra': suite['extra'] = True
                if defect == 'schema': suite['schema_version'] = True
                if defect == 'scope': suite['scope'] = 'production'
                if defect == 'world': suite['runtime']['world_scale'] = True
                if defect == 'speed': suite['runtime']['walk_world_speed'] = -1
                if defect == 'factor': suite['runtime']['speed_factor'] = 1.1
                if defect == 'runtime-extra': suite['runtime']['extra'] = 1
                self.f['suite'] = suite
                with self.assertRaises(ValueError): self.preflight()

    def test_prepared_sources_missing_duplicate_wrong_hash_and_decorative(self):
        original = copy.deepcopy(self.f['suite']['prepared_sources'])
        for refs in ([], original * 2, [{'file': original[0]['file'], 'sha256': '0' * 64}]):
            self.f['suite']['prepared_sources'] = refs
            with self.assertRaises(ValueError): self.preflight()

    def test_paths_symlink_ancestors_and_manifest_hash_refused(self):
        original = copy.deepcopy(self.f['suite']['manifest'])
        for name in ('../manifest.json', '/private/tmp/manifest.json', 'sources/prepared/manifest.json'):
            self.f['suite']['manifest'] = {'file': name, 'sha256': original['sha256']}
            with self.assertRaises(ValueError): self.preflight()
        self.f['suite']['manifest'] = original
        source = self.f['library'] / 'sources/prepared/materials'
        moved = source.with_name('moved'); source.rename(moved); source.symlink_to(moved, target_is_directory=True)
        with self.assertRaises(ValueError): self.preflight()

    def rebuild(self):
        self.f['write']('recipes/review/r001.json', self.f['recipe'])
        shutil.rmtree(self.f['output'])
        self.f['manifest'] = build.construct(self.f['root'], self.f['library'] / 'recipes/review/r001.json', self.f['output'])
        self.f['suite']['manifest'] = self.f['ref']('builds/review-r001/manifest.json')

    def test_missing_direct_preparation_parent_refused_even_for_valid_strict_build(self):
        inputs = self.f['recipe']['authoring_inputs']
        inputs[:] = [r for r in inputs if r['file'] != 'sources/body/packing/r001.json']
        self.rebuild()
        with self.assertRaisesRegex(ValueError, 'closure|bound|input'): self.preflight()

    def test_missing_original_prepared_texture_refused_even_with_valid_parts_copy(self):
        inputs = self.f['recipe']['authoring_inputs']
        inputs[:] = [r for r in inputs if r['file'] != 'sources/prepared/textures/walk_east_1.png']
        self.rebuild()
        with self.assertRaises(ValueError): self.preflight()

    def test_unpaired_idle_rejected_without_silent_fallback(self):
        recipe = self.f['recipe']
        recipe['clips'] = [c for c in recipe['clips'] if c['action_id'] != 'idle']
        recipe['required_capabilities'] = [{'action_id': 'walk', 'direction': 'east'}]
        with self.assertRaises(ValueError): self.rebuild()

    def test_wrong_pose_prepared_material_refused_after_strict_reconstruction(self):
        # Identical synthetic pixels let strict construction pass; pose binding must still refuse.
        recipe = self.f['recipe']
        adaptation_path = recipe['adaptations']['top']['file']
        adaptation = json.loads((self.f['library'] / adaptation_path).read_text())
        replacement = self.f['ref']('sources/prepared/materials/idle_east_0.png')
        adaptation['views'][1]['source'] = replacement
        recipe['clips'][1]['frames'][0]['layers'][1]['source'] = replacement
        recipe['adaptations']['top'] = self.f['write'](adaptation_path, adaptation)
        self.rebuild()
        with self.assertRaises(ValueError): self.preflight()

    def test_source_annotation_must_match_actual_prepared_pose_even_with_equal_pixels(self):
        # A valid strict cross-pose mapping is outside this finite same-pose
        # review interface, even when equal pixels and anchors hide the mismatch.
        recipe = self.f['recipe']
        adaptation_path = recipe['adaptations']['top']['file']
        adaptation = json.loads((self.f['library'] / adaptation_path).read_text())
        adaptation['views'][1]['source_pose']['record'] = 'idle_east_0'
        recipe['adaptations']['top'] = self.f['write'](adaptation_path, adaptation)
        self.rebuild()  # Proves the ordinary strict construction contract accepts it.
        with self.assertRaisesRegex(ValueError, 'annotation|pose'): self.preflight()

    def test_wrong_canonical_body_layer_refused(self):
        # Strict build permits equal RGBA body copies; review A must use the actual canonical reference.
        recipe = self.f['recipe']
        copied = self.f['write']('templates/fixture/motions/motion/body-views/copy.png', Image.new('RGBA', (2, 2), (30, 40, 50, 255)))
        recipe['clips'][1]['frames'][0]['layers'][0]['texture'] = copied
        self.rebuild()
        with self.assertRaises(ValueError): self.preflight()

    def test_valid_strict_reversed_layers_are_outside_registered_review_scope(self):
        for clip in self.f['recipe']['clips']:
            for frame in clip['frames']:
                frame['layer_order'] = ['top', 'body']
        self.rebuild()  # Legal strict alpha-over build; this review only supports body then top.
        with self.assertRaisesRegex(ValueError, 'layer|scope|order'): self.preflight()

    def test_valid_strict_normalized_extraction_is_outside_registered_review_scope(self):
        recipe = self.f['recipe']
        path = recipe['adaptations']['top']['file']
        adaptation = json.loads((self.f['library'] / path).read_text())
        adaptation['views'][1]['extraction'] = {
            'kind': 'normalized-source-selection-v1', 'schema_version': 1,
            'normalization': {'kind': 'whole-source-rational-v1', 'filter': 'nearest',
                'numerator': 1, 'denominator': 1, 'raw_canvas_px': [2, 2], 'raw_root_anchor_px': [1, 1],
                'normalized_canvas_px': [2, 2], 'normalized_root_anchor_px': [1, 1]},
            'ownership_space': 'normalized-source-full-frame', 'selection_space': 'normalized-source-full-frame',
            'selections': []}
        recipe['adaptations']['top'] = self.f['write'](path, adaptation)
        self.rebuild()  # A genuine legal strict identity normalization, outside the GD adapter's interface.
        with self.assertRaisesRegex(ValueError, 'extraction|binary|scope'): self.preflight()

    def test_registered_scope_rejects_coverage_and_occlusion(self):
        original = self.f['recipe']
        for field in ('coverage', 'occlusion'):
            with self.subTest(field=field):
                recipe = copy.deepcopy(original)
                recipe['clips'][1]['frames'][0]['layers'][1][field] = recipe['clips'][1]['frames'][0]['layers'][1]['ownership']
                with self.assertRaises(ValueError): self.module().locomotion_clips(recipe)

    def test_scope_rejects_run_duplicate_caps_and_inconsistent_geometry(self):
        module = self.module()
        original = self.f['recipe']
        for defect in ('run', 'duplicate', 'capability', 'geometry'):
            with self.subTest(defect=defect):
                recipe = copy.deepcopy(original)
                if defect == 'run': recipe['clips'][1]['action_id'] = 'run'
                if defect == 'duplicate': recipe['clips'].append(copy.deepcopy(recipe['clips'][1]))
                if defect == 'capability': recipe['required_capabilities'][1]['direction'] = 'west'
                if defect == 'geometry': recipe['clips'][1]['root_anchor_px'] = [0, 1]
                with self.assertRaises(ValueError): module.locomotion_clips(recipe)

    def test_unsupported_composition_is_explicitly_refused(self):
        # Existing synthetic fixture is same-pose/identity; this adapter's
        # presentation supports that precise finite interface only.
        recipe = self.f['recipe']
        for clip in recipe['clips']:
            for frame in clip['frames']:
                frame['composition'] = 'ownership-replace'
                frame['layers'][1]['coverage'] = frame['layers'][1]['ownership']
        # Inspect scope directly: no alternate rendering/composition path.
        with self.assertRaises(ValueError): self.module().locomotion_clips(recipe)

    def test_launcher_registered_choice_and_shared_scene(self):
        text = (TOOLS / 'review.py').read_text()
        self.assertIn("'registered'", text)
        self.assertIn('character_registered_trial.tscn', text)
        self.assertIn('--registered-suite=', text)


if __name__ == '__main__': unittest.main()
