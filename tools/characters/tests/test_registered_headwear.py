"""Registered head parts share the base mapper and retain real hat compatibility."""
import copy
import json
from pathlib import Path
import sys
import unittest

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build
from composition_contract import hat_source_identity, component_source_identity
from build_contract import validate
from test_build_contract import sha
import test_registered_adaptations as adaptation_fixture


class RegisteredHeadwearTests(unittest.TestCase):
    def setUp(self):
        self.fixture = adaptation_fixture.RegisteredAdaptationTests()
        self.fixture.fixed_profile = getattr(self, 'fixed_profile', False)
        self.fixture.setUp()
        self.fixture.check()
        self.repo, self.lib = self.fixture.repo, self.fixture.lib
        self.write = self.fixture.write
        self.path = self.lib/'recipes/mapped-head/r001.json'
        annotation = copy.deepcopy(self.fixture.annotations)
        annotation['revision'] = 'head-r001'
        for row in annotation['records']:
            surface = row['surfaces']['torso']['mask']
            row['surfaces'] = {'head': {'layer_id': 'base', 'mask': surface}}
        self.annotation = self.write('templates/test/motions/motion/annotations/head-r001/poses.json', annotation)
        hat = Image.new('RGBA', (2, 2))
        hat.putpixel((0, 0), (240, 20, 30, 128))
        hat.putpixel((1, 1), (20, 30, 240, 200))
        hair = Image.new('RGBA', (2, 2))
        hair.putpixel((1, 0), (20, 210, 30, 128))
        self.sources = {'hat': self.write('sources/cap/originals/source.png', hat),
                        'hair': self.write('sources/locks/originals/source.png', hair)}
        self.masks = {}
        for role, point in [('far_hat', (0, 0)), ('near_hat', (1, 1)), ('under_hat_hair', (1, 0))]:
            mask = Image.new('L', (2, 2)); mask.putpixel(point, 255)
            self.masks[role] = self.write('parts/' + ('hat/hat' if role != 'under_hat_hair' else 'hair/hair')
                                           + '/test/motion/r002/' + role + '-owner.png', mask)
        full = Image.new('L', (2, 2)); full.putpixel((0, 0), 255); full.putpixel((1, 1), 255)
        owner = self.write('parts/hat/hat/test/motion/r002/full-hat-owner.png', full)
        self.compatibility = {'hat_source': self.sources['hat'], 'hat_ownership': owner}
        self.bundles = {}
        for slot, source_id in [('hat', 'cap'), ('hair', 'locks')]:
            data = {'source_id': source_id,
                    'assets': [{'new_path': 'art/characters/' + self.sources[slot]['file'],
                                'new_sha256': self.sources[slot]['sha256']}]}
            self.bundles[slot] = self.write('sources/' + source_id + '/source.json', data)
        self.recipe = {'kind': 'coastal-character-construction-v1', 'schema_version': 2,
                       'resource_root': 'art/characters', 'character_model_id': 'unified-composable-character-v1',
                       'recipe_id': 'mapped-head', 'revision': 'r001',
                       'base_recipe': {'file': 'recipes/test/r001.json', 'sha256': sha(self.fixture.path)},
                       'head_state': 'hair_hat', 'slots': {}, 'adaptations': {},
                       'clips': [], 'authoring_inputs': []}
        self.adaptations = {}
        for slot in ['hair', 'hat']:
            self.recipe['slots'][slot] = self.write('parts/' + slot + '/' + slot + '/revisions/r002/design.json',
                {'design_id': slot, 'category': slot, 'revision': 'r002'})
            self.adaptations[slot] = {'kind': 'coastal-registered-adaptations-v1', 'schema_version': 1,
                'design_id': slot, 'design_revision': 'r002', 'template_id': 'test', 'motion_set_id': 'motion',
                'views': [], 'mappings': []}
        for role in ['far_hat', 'under_hat_hair', 'near_hat']:
            slot = 'hair' if role == 'under_hat_hair' else 'hat'
            self.adaptations[slot]['views'].append({'view_id': role, 'role': 'full-source-component',
                'source_pose': {'document': self.annotation, 'record': 'idle_west_0'},
                'source': self.sources[slot], 'source_bundle': self.bundles[slot],
                'canvas_px': [2, 2], 'root_anchor_px': [1, 1],
                'source_ownership': {'role': 'source-ownership', 'mask': self.masks[role]},
                'extraction': {'kind': 'binary-rgba-extract-v1', 'density_normalization': None}})
        for clip in self.fixture.recipe['clips']:
            frames = []
            for frame in clip['frames']:
                target = next(row for row in annotation['records'] if row['pose_id'] == frame['pose_id'])
                layers = []
                for role in ['far_hat', 'under_hat_hair', 'near_hat']:
                    slot = 'hair' if role == 'under_hat_hair' else 'hat'
                    texture = {'file': f'parts/{slot}/{slot}/test/motion/r002/{role}-{frame["pose_id"]}.png', 'sha256': ''}
                    self.adaptations[slot]['mappings'].append({'mapping_id': role + '-' + frame['pose_id'],
                        'view_id': role, 'texture': texture,
                        'target_pose': {'document': self.annotation, 'record': frame['pose_id']},
                        'target_surface': {'surface_id': 'head', 'layer_id': 'base'},
                        'interface_scope': 'same-cut-surface', 'role': 'component-surface',
                        'anchors': {'name': 'cloth', 'source_px': [1, 1],
                                    'target_px': target['landmarks_px']['cloth']},
                        'coverage': None, 'occlusion': None})
                    layers.append({'id': role, 'slot': slot, 'pose_id': frame['pose_id'],
                        'texture': texture, 'source': self.sources[slot], 'source_bundle': self.bundles[slot],
                        'ownership': self.masks[role], 'coverage': None, 'occlusion': None,
                        'interface_scope': 'registered-component', 'placement_mode': 'full_frame',
                        'offset_px': [0, 0], 'local_scale': [1, 1],
                        'view_binding': {'view_id': role, 'mapping_id': role + '-' + frame['pose_id']}})
                frames.append({'pose_id': frame['pose_id'], 'operation': 'supported-alpha-stack',
                    'layers': layers, 'layer_order': ['far_hat', 'base', 'under_hat_hair', 'near_hat'],
                    'compatibility': copy.deepcopy(self.compatibility)})
            self.recipe['clips'].append({'action_id': clip['action_id'], 'direction': clip['direction'], 'frames': frames})
        self.rebind_hat_compatibility()
        self.refresh()

    def tearDown(self):
        self.fixture.tearDown()

    def test_head_parts_cannot_inherit_skin_alpha_as_material(self):
        view = self.adaptations['hair']['views'][0]
        row = self.fixture.annotations['records'][0]
        view['extraction'] = {'kind': 'canonical-surface-alpha-v1', 'schema_version': 1,
            'scope': 'finite-canonical-material', 'material_extraction': view['extraction'],
            'alpha_reference': row['reference_frame']}
        self.refresh()
        with self.assertRaisesRegex(ValueError, 'finite canonical material'):
            self.check()

    def rebind_hat_compatibility(self):
        views = {view['view_id']: view for view in self.adaptations['hat']['views']}
        self.compatibility['hat_identity_sha256'] = hat_source_identity(
            views['near_hat'], views.get('far_hat'), self.compatibility['hat_ownership'])
        for clip in self.recipe['clips']:
            for frame in clip['frames']:
                frame['compatibility'] = copy.deepcopy(self.compatibility)
        for view in self.adaptations['hair']['views']:
            claim = {'kind': 'coastal-head-compatibility-v1', 'schema_version': 1,
                     'hair_identity_sha256': component_source_identity(view),
                     'hat_identity_sha256': self.compatibility['hat_identity_sha256']}
            view['compatibility'] = self.write(
                'parts/hair/hair/test/motion/r002/compatibility/' + view['view_id'] + '.json', claim)

    def refresh(self):
        for clip, base_clip in zip(self.recipe['clips'], self.fixture.recipe['clips']):
            for frame in clip['frames']:
                for layer in frame['layers']:
                    data = self.adaptations[layer['slot']]
                    view = next(v for v in data['views'] if v['view_id'] == layer['view_binding']['view_id'])
                    mapping = next(m for m in data['mappings'] if m['mapping_id'] == layer['view_binding']['mapping_id'])
                    with Image.open(self.lib/view['source']['file']) as source, Image.open(self.lib/view['source_ownership']['mask']['file']) as mask:
                        extracted = Image.composite(source.convert('RGBA'), Image.new('RGBA', source.size), mask)
                    texture = Image.new('RGBA', tuple(base_clip['canvas_px']))
                    delta = tuple(mapping['anchors']['target_px'][i] - mapping['anchors']['source_px'][i] for i in (0, 1))
                    texture.paste(extracted, delta)
                    mapping['texture'] = self.write(mapping['texture']['file'], texture)
                    layer.update(texture=mapping['texture'], source=view['source'], source_bundle=view['source_bundle'],
                                 ownership=view['source_ownership']['mask'])
        for slot, data in self.adaptations.items():
            self.recipe['adaptations'][slot] = self.write(f'parts/{slot}/{slot}/test/motion/r002/views.json', data)
        self.save()

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.recipe))

    def check(self):
        self.save()
        return validate(self.repo, self.path)

    def test_registered_hair_hat_real_build_and_verify(self):
        try:
            value = self.check()
        except ValueError as exc:
            self.fail('Registered hair_hat over schema3 must validate: ' + str(exc))
        self.assertEqual(value.base.recipe['schema_version'], 3)
        output = self.repo/'coastal-head-output'
        result = build.construct(self.repo, self.path, output)
        build.verify(self.repo, output)
        self.assertEqual(len(result['outputs']), 4)
        self.assertIn(self.annotation['file'], result['inputs'])
        self.assertIn(self.sources['hat']['file'], result['inputs'])
        self.assertIn(self.sources['hair']['file'], result['inputs'])

    def test_overlapping_near_far_hat_ownership_rejected_after_reconstruction(self):
        view = next(v for v in self.adaptations['hat']['views'] if v['view_id'] == 'near_hat')
        view['source_ownership']['mask'] = self.masks['far_hat']
        self.refresh()
        with self.assertRaisesRegex(ValueError, 'Hat ownership overlap'):
            self.check()

    def test_under_hat_compatibility_is_bound_to_actual_hat(self):
        view = self.adaptations['hair']['views'][0]
        claim = json.loads((self.lib/view['compatibility']['file']).read_text())
        claim['hat_identity_sha256'] = '0' * 64
        view['compatibility'] = self.write(view['compatibility']['file'], claim)
        self.refresh()
        with self.assertRaisesRegex(ValueError, 'Under-hat compatibility'):
            self.check()

    def test_wrong_head_state_or_layer_transform_rejected(self):
        original = copy.deepcopy(self.recipe)
        for mode in ['state', 'scale', 'pose', 'order']:
            with self.subTest(mode=mode):
                self.recipe = copy.deepcopy(original)
                if mode == 'state': self.recipe['head_state'] = 'bare'
                if mode == 'scale': self.recipe['clips'][0]['frames'][0]['layers'][0]['local_scale'] = [2, 2]
                if mode == 'pose': self.recipe['clips'][0]['frames'][0]['pose_id'] = 'wrong_pose'
                if mode == 'order': self.recipe['clips'][0]['frames'][0]['layer_order'].reverse()
                with self.assertRaisesRegex(ValueError, 'hair_hat|transform|pose|order'):
                    self.check()

    def test_hat_ownership_must_cover_the_complete_registered_hat(self):
        mask = Image.new('L', (2, 2)); mask.putpixel((0, 0), 255)
        ref = self.write('parts/hat/hat/test/motion/r002/incomplete-hat.png', mask)
        for clip in self.recipe['clips']:
            for frame in clip['frames']:
                frame['compatibility']['hat_ownership'] = ref
        with self.assertRaisesRegex(ValueError, 'Hat ownership does not reconstruct'):
            self.check()

    def test_hat_added_source_invalidates_old_under_hat_compatibility(self):
        extra_image = Image.new('RGBA', (2, 2), (160, 150, 140, 200))
        extra = self.write('sources/cap-extra/originals/source.png', extra_image)
        bundle = self.write('sources/cap-extra/source.json', {
            'source_id': 'cap-extra', 'assets': [{'new_path': 'art/characters/' + extra['file'],
                                                'new_sha256': extra['sha256']}]})
        normalization = {'kind': 'whole-source-rational-v1', 'filter': 'nearest',
                         'numerator': 1, 'denominator': 1, 'raw_canvas_px': [2, 2],
                         'raw_root_anchor_px': [1, 1], 'normalized_canvas_px': [2, 2],
                         'normalized_root_anchor_px': [1, 1]}
        for view in self.adaptations['hat']['views']:
            view['extraction'] = {'kind': 'normalized-source-selection-v1', 'schema_version': 1,
                'normalization': normalization, 'ownership_space': 'normalized-source-full-frame',
                'selection_space': 'normalized-source-full-frame', 'selections': [{
                    'selection_id': 'new-cap', 'source': extra, 'source_bundle': bundle,
                    'source_pose': view['source_pose'], 'normalization': normalization,
                    'selection': {'role': 'source-selection', 'mask': self.compatibility['hat_ownership']}}]}
        for clip, base_clip in zip(self.recipe['clips'], self.fixture.recipe['clips']):
            for frame in clip['frames']:
                for layer in frame['layers']:
                    if layer['slot'] != 'hat': continue
                    mapping = next(m for m in self.adaptations['hat']['mappings']
                                   if m['mapping_id'] == layer['view_binding']['mapping_id'])
                    with Image.open(self.lib/layer['ownership']['file']) as owner:
                        extracted = Image.composite(extra_image, Image.new('RGBA', (2, 2)), owner)
                    texture = Image.new('RGBA', tuple(base_clip['canvas_px']))
                    delta = tuple(mapping['anchors']['target_px'][i] - mapping['anchors']['source_px'][i]
                                  for i in (0, 1))
                    texture.paste(extracted, delta)
                    mapping['texture'] = self.write(mapping['texture']['file'], texture)
                    layer['texture'] = mapping['texture']
        self.recipe['adaptations']['hat'] = self.write('parts/hat/hat/test/motion/r002/views.json',
                                                       self.adaptations['hat'])
        with self.assertRaisesRegex(ValueError, 'Hat compatibility identity'):
            self.check()

    def test_equal_pixels_from_different_hat_sources_cannot_be_paired(self):
        with Image.open(self.lib/self.sources['hat']['file']) as original:
            source = self.write('sources/other-cap/originals/source.png', original.copy())
        bundle = self.write('sources/other-cap/source.json', {
            'source_id': 'other-cap', 'assets': [{'new_path': 'art/characters/' + source['file'],
                                                'new_sha256': source['sha256']}]})
        near = next(view for view in self.adaptations['hat']['views'] if view['view_id'] == 'near_hat')
        near.update(source=source, source_bundle=bundle)
        self.refresh()
        with self.assertRaisesRegex(ValueError, 'Near/far hat must share'):
            self.check()

    def test_actual_complete_near_hat_does_not_require_a_fake_far_part(self):
        hat = self.adaptations['hat']
        hat['views'] = [view for view in hat['views'] if view['view_id'] != 'far_hat']
        hat['mappings'] = [mapping for mapping in hat['mappings'] if mapping['view_id'] != 'far_hat']
        hat['views'][0]['source_ownership']['mask'] = self.compatibility['hat_ownership']
        for clip in self.recipe['clips']:
            for frame in clip['frames']:
                frame['layers'] = [layer for layer in frame['layers'] if layer['id'] != 'far_hat']
                frame['layer_order'] = ['base', 'under_hat_hair', 'near_hat']
        self.rebind_hat_compatibility()
        self.refresh()
        try:
            value = self.check()
        except ValueError as exc:
            self.fail('A complete near-only hat must not require fabricated far art: ' + str(exc))
        self.assertEqual(len(list(build.render(value))), 4)

    def test_nonobject_base_rejected_as_contract_error(self):
        path = self.lib/'recipes/bad/r001.json'
        path.parent.mkdir(parents=True)
        path.write_text('[]')
        self.recipe['base_recipe'] = {'file': 'recipes/bad/r001.json', 'sha256': sha(path)}
        with self.assertRaisesRegex(ValueError, 'schema3 base'):
            self.check()

    def test_one_real_atlas_bundle_can_supply_both_hair_and_hat(self):
        with Image.open(self.lib/self.sources['hat']['file']) as cap, Image.open(self.lib/self.sources['hair']['file']) as locks:
            atlas = cap.convert('RGBA')
            atlas.putpixel((1, 0), locks.getpixel((1, 0)))
        source = self.write('sources/shared/originals/atlas.png', atlas)
        bundle = self.write('sources/shared/source.json', {
            'source_id': 'shared', 'assets': [{'new_path': 'art/characters/' + source['file'],
                                             'new_sha256': source['sha256']}]})
        self.sources = {'hair': source, 'hat': source}
        self.bundles = {'hair': bundle, 'hat': bundle}
        self.compatibility['hat_source'] = source
        for data in self.adaptations.values():
            for view in data['views']:
                view.update(source=source, source_bundle=bundle)
        self.rebind_hat_compatibility()
        self.refresh()
        try:
            value = self.check()
        except ValueError as exc:
            self.fail('A real shared source bundle must not create a compatibility hash cycle: ' + str(exc))
        self.assertEqual(len(list(build.render(value))), 4)


if __name__ == '__main__':
    unittest.main()
