"""Real schema3 source reconstruction and versioned pose annotation contracts."""
import copy
from fractions import Fraction
import json
from pathlib import Path
import shutil
import sys
import unittest

from PIL import Image, ImageChops, PngImagePlugin

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
import build
import build_contract as contract
from build_contract import validate
import test_build_contract as base_fixture
from test_build_contract import sha


class RegisteredAdaptationTests(unittest.TestCase):
    def setUp(self):
        self.base = base_fixture.ConstructionTests(methodName='test_three_frame_action_and_matching_idle')
        self.base.fixed_profile = getattr(self, 'fixed_profile', False)
        self.base.setUp()
        self.repo, self.lib, self.path = self.base.repo, self.base.lib, self.base.path
        self.write = self.base.write
        self.recipe = self.base.recipe
        self.recipe['schema_version'] = 3
        self.namespace = 'parts/top/top/test/motion/r002'
        self.annotation_path = 'templates/test/motions/motion/annotations/r002/poses.json'
        source_image = Image.new('RGBA', (2, 2), (11, 12, 13, 0))
        source_image.putpixel((0, 0), (200, 30, 40, 128))
        source_image.putpixel((1, 1), (30, 40, 200, 200))
        self.source_image = source_image
        self.source = self.write('sources/test/originals/source.png', source_image)
        self.bundle = self.write('sources/test/source.json', {
            'source_id': 'test', 'assets': [{'new_path': 'art/characters/' + self.source['file'],
                                          'new_sha256': self.source['sha256']}]})
        ownership = Image.new('L', (2, 2), 0)
        ownership.putpixel((0, 0), 255); ownership.putpixel((1, 1), 255)
        self.ownership = self.write(self.namespace + '/ownership.png', ownership)
        definition = self.write('parts/top/top/revisions/r002/design.json', {
            'design_id': 'top', 'category': 'top', 'revision': 'r002'})
        self.recipe['slots']['top'] = definition
        self.recipe['authoring_inputs'] = [self.source]
        self.annotations = {
            'kind': 'coastal-pose-annotations-v1', 'schema_version': 1,
            'template_id': 'test', 'motion_set_id': 'motion', 'revision': 'r002', 'records': []}
        self.adaptation = {
            'kind': 'coastal-registered-adaptations-v1', 'schema_version': 1,
            'design_id': 'top', 'design_revision': 'r002', 'template_id': 'test',
            'motion_set_id': 'motion', 'views': [], 'mappings': []}
        for clip in self.recipe['clips']:
            size = [2, 2] if clip['action_id'] == 'idle' else [4, 4]
            clip['canvas_px'] = size
            clip['root_anchor_px'] = [s // 2 for s in size]
            body = self.write('templates/test/motions/motion/body-views/' + clip['action_id'] + '.png',
                              Image.new('RGBA', size, (10, 20, 30, 255)))
            surface = self.write(self.namespace + '/' + clip['action_id'] + '-surface.png',
                                 Image.new('L', size, 255))
            poses = json.loads((self.lib / clip['poses']['file']).read_text())
            poses['variants']['A']['canvas_px'] = size
            poses['variants']['A']['root_anchor_px'] = clip['root_anchor_px']
            for i, (frame, original) in enumerate(zip(clip['frames'], poses['variants']['A']['frames'])):
                original.update(file=body['file'], sha256=body['sha256'])
                frame['layers'][0]['texture'] = body
                for layer in frame['layers']:
                    layer['source'] = self.source
                    layer['source_bundle'] = self.bundle
                anchor = [1, 1] if clip['action_id'] == 'idle' else [[1, 1], [2, 1], [1, 2]][i]
                record = {'record_id': frame['pose_id'], 'poses': None, 'variant': 'A',
                          'pose_id': frame['pose_id'], 'reference_frame': body,
                          'canvas_px': size, 'root_anchor_px': clip['root_anchor_px'], 'display_scale': 1,
                          'landmarks_px': {'cloth': anchor},
                          'surfaces': {'torso': {'layer_id': 'body', 'mask': surface}}}
                self.annotations['records'].append(record)
                texture_image = Image.new('RGBA', size)
                extracted = Image.new('RGBA', (2, 2))
                extracted.putpixel((0, 0), source_image.getpixel((0, 0)))
                extracted.putpixel((1, 1), source_image.getpixel((1, 1)))
                texture_image.paste(extracted, (anchor[0] - 1, anchor[1] - 1))
                texture = self.write(self.namespace + '/' + frame['pose_id'] + '.png', texture_image)
                top = frame['layers'][1]
                top.update(texture=texture, ownership=self.ownership, coverage=None, occlusion=None,
                           view_binding={'view_id': 'idle-cloth', 'mapping_id': frame['pose_id']})
                self.adaptation['mappings'].append({
                    'mapping_id': frame['pose_id'], 'view_id': 'idle-cloth', 'texture': texture,
                    'target_pose': None, 'target_surface': {'surface_id': 'torso', 'layer_id': 'body'},
                    'interface_scope': 'same-cut-surface', 'role': 'component-surface',
                    'anchors': {'name': 'cloth', 'source_px': [1, 1], 'target_px': anchor},
                    'coverage': None, 'occlusion': None})
            clip['poses'] = self.write(clip['poses']['file'], poses)
            for record in self.annotations['records']:
                if record['pose_id'].startswith(clip['action_id'] + '_'):
                    record['poses'] = clip['poses']
        self.annotation = self.write(self.annotation_path, self.annotations)
        for mapping in self.adaptation['mappings']:
            mapping['target_pose'] = {'document': self.annotation, 'record': mapping['mapping_id']}
        self.adaptation['views'] = [{
            'view_id': 'idle-cloth', 'role': 'full-source-component',
            'source_pose': {'document': self.annotation, 'record': 'idle_west_0'},
            'source': self.source, 'source_bundle': self.bundle,
            'canvas_px': [2, 2], 'root_anchor_px': [1, 1],
            'source_ownership': {'role': 'source-ownership', 'mask': self.ownership},
            'extraction': {'kind': 'binary-rgba-extract-v1', 'density_normalization': None}}]
        self.refresh()

    def tearDown(self):
        self.base.tearDown()

    def refresh(self):
        self.recipe['adaptations'] = {'top': self.write(self.namespace + '/views.json', self.adaptation)}
        self.save()

    def save(self):
        self.path.write_text(json.dumps(self.recipe))

    def check(self):
        self.refresh()
        return validate(self.repo, self.path)

    def rejected(self, message):
        with self.assertRaisesRegex(ValueError, message):
            self.check()

    def first_layer(self):
        return self.recipe['clips'][0]['frames'][0]['layers'][1]

    def surface_alpha_material(self):
        view = self.adaptation['views'][0]
        source = next(r for r in self.annotations['records'] if r['record_id'] == 'idle_west_0')
        view['extraction'] = {'kind': 'canonical-surface-alpha-v1', 'schema_version': 1,
            'scope': 'finite-canonical-material', 'material_extraction': view['extraction'],
            'alpha_reference': source['reference_frame']}
        for clip in self.recipe['clips']:
            for frame in clip['frames']:
                mapping = next(m for m in self.adaptation['mappings'] if m['mapping_id'] == frame['pose_id'])
                with Image.open(self.lib/mapping['texture']['file']) as original:
                    image = original.copy()
                    image.putalpha(image.getchannel('A').point(lambda a: 255 if a else 0))
                texture = self.write(mapping['texture']['file'], image)
                mapping['texture'] = texture; frame['layers'][1]['texture'] = texture
        return view

    def test_material_rgb_inherits_bound_canonical_surface_alpha_real_build(self):
        view = self.surface_alpha_material()
        valid = self.check()
        output = self.lib/'builds/canonical-material-alpha-r001'
        build.construct(self.repo, self.path, output); build.verify(self.repo, output)
        image = valid.image(self.adaptation['mappings'][0]['texture'])
        self.assertEqual(image.getpixel((0, 0)), (200, 30, 40, 255))
        self.assertEqual(image.getpixel((1, 1)), (30, 40, 200, 255))
        self.assertIn(view['extraction']['alpha_reference']['file'], valid.dependencies)

    def test_material_alpha_cannot_be_taken_from_an_unrelated_frame(self):
        view = self.surface_alpha_material()
        view['extraction']['alpha_reference'] = self.source
        self.rejected('canonical source frame')

    def test_material_alpha_cannot_claim_an_entire_hidden_garment(self):
        view = self.surface_alpha_material()
        view['extraction']['scope'] = 'full-hidden-garment'
        self.rejected('finite canonical material')

    def test_material_alpha_cannot_fill_missing_raw_material(self):
        view = self.surface_alpha_material()
        image = self.source_image.copy(); image.putpixel((0, 0), (200, 30, 40, 0))
        self.source = self.write(self.source['file'], image)
        self.bundle = self.write(self.bundle['file'], {'source_id': 'test', 'assets': [
            {'new_path': 'art/characters/'+self.source['file'], 'new_sha256': self.source['sha256']}]})
        view.update(source=self.source, source_bundle=self.bundle)
        self.recipe['authoring_inputs'] = [self.source]
        for clip in self.recipe['clips']:
            for frame in clip['frames']:
                for layer in frame['layers']: layer.update(source=self.source, source_bundle=self.bundle)
        self.rejected('cannot fill missing material pixels')

    def test_material_alpha_wrapper_cannot_be_nested(self):
        view = self.surface_alpha_material()
        view['extraction']['material_extraction'] = copy.deepcopy(view['extraction'])
        self.rejected('Unsupported source extraction kind')

    def test_material_alpha_cannot_create_surface_outside_canonical_support(self):
        view = self.surface_alpha_material()
        clip = self.recipe['clips'][0]; row = self.annotations['records'][0]
        with Image.open(self.lib/row['reference_frame']['file']) as original:
            image = original.copy(); image.putpixel((0, 0), (10, 20, 30, 0))
        body = self.write(row['reference_frame']['file'], image)
        poses = json.loads((self.lib/clip['poses']['file']).read_text())
        poses['variants']['A']['frames'][0].update(file=body['file'], sha256=body['sha256'])
        clip['poses'] = self.write(clip['poses']['file'], poses)
        row.update(poses=clip['poses'], reference_frame=body)
        clip['frames'][0]['layers'][0]['texture'] = body
        self.annotation = self.write(self.annotation_path, self.annotations)
        view['source_pose']['document'] = self.annotation
        view['extraction']['alpha_reference'] = body
        for mapping in self.adaptation['mappings']: mapping['target_pose']['document'] = self.annotation
        self.rejected('exceeds canonical source support')

    def test_material_inherits_real_nonopaque_alpha_verbatim(self):
        view = self.surface_alpha_material()
        clip = self.recipe['clips'][0]; row = self.annotations['records'][0]
        with Image.open(self.lib/row['reference_frame']['file']) as original:
            image = original.copy(); image.putalpha(73)
        body = self.write(row['reference_frame']['file'], image)
        poses = json.loads((self.lib/clip['poses']['file']).read_text())
        poses['variants']['A']['frames'][0].update(file=body['file'], sha256=body['sha256'])
        clip['poses'] = self.write(clip['poses']['file'], poses)
        row.update(poses=clip['poses'], reference_frame=body)
        clip['frames'][0]['layers'][0]['texture'] = body
        self.annotation = self.write(self.annotation_path, self.annotations)
        view['source_pose']['document'] = self.annotation
        view['extraction']['alpha_reference'] = body
        for mapping in self.adaptation['mappings']:
            mapping['target_pose']['document'] = self.annotation
            with Image.open(self.lib/mapping['texture']['file']) as original:
                image = original.copy(); image.putalpha(image.getchannel('A').point(lambda a: 73 if a else 0))
            texture = self.write(mapping['texture']['file'], image); mapping['texture'] = texture
            for target in self.recipe['clips']:
                for frame in target['frames']:
                    if frame['pose_id'] == mapping['mapping_id']: frame['layers'][1]['texture'] = texture
        valid = self.check()
        self.assertEqual(valid.image(self.adaptation['mappings'][0]['texture']).getpixel((0, 0)), (200, 30, 40, 73))
        output = self.lib/'builds/nonopaque-canonical-material-r001'
        build.construct(self.repo, self.path, output); build.verify(self.repo, output)

    def test_versioned_definition_shared_source_view_real_build_verify(self):
        valid = self.check()
        self.assertEqual(valid.recipe['schema_version'], 3)
        self.assertIn(self.annotation_path, valid.dependencies)
        output = self.repo / 'coastal-schema3'
        result = build.construct(self.repo, self.path, output)
        self.assertEqual(len(result['outputs']), 4)
        build.verify(self.repo, output)
        with Image.open(output / 'frames/wave/west/wave_west_1.png') as actual:
            expected = Image.alpha_composite(Image.new('RGBA', (4, 4), (10, 20, 30, 255)),
                                            valid.image(self.adaptation['mappings'][2]['texture']))
            self.assertEqual(actual.tobytes(), expected.tobytes())
        self.assertEqual(valid.image(self.adaptation['mappings'][0]['texture']).getpixel((0, 0)),
                         (200, 30, 40, 128))

    def test_binary_coverage_preserves_source_soft_alpha(self):
        for clip in self.recipe['clips']:
            for frame in clip['frames']:
                frame['composition'] = 'ownership-replace'
                mapping = next(m for m in self.adaptation['mappings'] if m['mapping_id'] == frame['pose_id'])
                surface = next(r for r in self.annotations['records'] if r['record_id'] == frame['pose_id'])['surfaces']['torso']['mask']
                mapping['coverage'] = {'role': 'target-coverage', 'mask': surface,
                                       'target_surface': mapping['target_surface']}
                frame['layers'][1]['coverage'] = surface
        self.refresh()
        output = self.repo / 'coastal-schema3-owned'
        build.construct(self.repo, self.path, output); build.verify(self.repo, output)
        with Image.open(output / 'frames/idle/west/idle_west_0.png') as actual:
            self.assertEqual(actual.getpixel((0, 0)), (200, 30, 40, 128))

    def test_alpha_over_occlusion_is_reconstructed_in_texture(self):
        # A declared later foreground body layer genuinely hides selected cloth.
        mapping = self.adaptation['mappings'][0]
        occlusion = self.write(self.namespace + '/occlusion.png', Image.new('L', (2, 2), 255))
        mapping['occlusion'] = {'role': 'target-occlusion', 'mask': occlusion,
                                'foreground_layers': ['body']}
        frame = self.recipe['clips'][0]['frames'][0]
        frame['layer_order'] = ['top', 'body']
        frame['layers'][1]['occlusion'] = occlusion
        texture = self.write(mapping['texture']['file'], Image.new('RGBA', (2, 2)))
        mapping['texture'] = texture; frame['layers'][1]['texture'] = texture
        self.check()

    def test_mapping_pose_and_view_identity_are_not_recipe_offsets(self):
        for field, value in [('mapping_id', 'missing'), ('view_id', 'missing')]:
            with self.subTest(field=field):
                old = self.first_layer()['view_binding'][field]
                self.first_layer()['view_binding'][field] = value
                self.rejected('view|mapping')
                self.first_layer()['view_binding'][field] = old
        self.adaptation['mappings'][0]['target_pose']['record'] = 'wave_west_0'
        self.rejected('target pose')

    def test_source_pose_and_target_anchor_are_bound_to_annotations(self):
        self.adaptation['views'][0]['source_pose']['record'] = 'missing'
        self.rejected('annotation record')
        self.adaptation['views'][0]['source_pose']['record'] = 'idle_west_0'
        self.adaptation['mappings'][0]['anchors']['target_px'] = [0, 0]
        self.rejected('anchor')

    def test_rehashed_annotation_cannot_change_canonical_geometry_or_frame(self):
        for field, value in [('canvas_px', [3, 3]), ('reference_frame', self.source)]:
            with self.subTest(field=field):
                original = self.annotations['records'][0][field]
                self.annotations['records'][0][field] = value
                updated = self.write(self.annotation_path, self.annotations)
                self.adaptation['views'][0]['source_pose']['document'] = updated
                for mapping in self.adaptation['mappings']:
                    mapping['target_pose']['document'] = updated
                self.rejected('annotation.*(geometry|frame)')
                self.annotations['records'][0][field] = original

    def test_unknown_fields_interfaces_and_roles_rejected(self):
        for obj, field, value in [(self.adaptation, 'surprise', True),
                                  (self.adaptation['mappings'][0], 'interface_scope', 'any-clothes'),
                                  (self.adaptation['views'][0]['source_ownership'], 'role', 'target-coverage')]:
            with self.subTest(field=field):
                old = obj.get(field, 'absent')
                obj[field] = value
                self.rejected('fields|interface|role')
                if old == 'absent': obj.pop(field)
                else: obj[field] = old

    def test_missing_versioned_identity_and_wrong_namespace_rejected(self):
        path = self.recipe['slots']['top']['file']
        self.recipe['slots']['top'] = self.write(path, {'design_id': 'top', 'category': 'top'})
        self.rejected('revision')

    def test_texture_rehash_cannot_hide_changed_pixels(self):
        layer = self.first_layer()
        texture = self.write(layer['texture']['file'], Image.new('RGBA', (2, 2), (1, 2, 3, 255)))
        layer['texture'] = texture; self.adaptation['mappings'][0]['texture'] = texture
        self.rejected('reconstruct')

    def test_ownership_rehash_cannot_hide_changed_extraction(self):
        changed = self.write(self.ownership['file'], Image.new('L', (2, 2), 0))
        self.adaptation['views'][0]['source_ownership']['mask'] = changed
        for clip in self.recipe['clips']:
            for frame in clip['frames']: frame['layers'][1]['ownership'] = changed
        self.rejected('reconstruct')

    def test_source_rehash_cannot_hide_changed_extraction(self):
        source = self.write(self.source['file'], Image.new('RGBA', (2, 2), (99, 88, 77, 255)))
        bundle = self.write(self.bundle['file'], {'source_id': 'test', 'assets': [
            {'new_path': 'art/characters/' + source['file'], 'new_sha256': source['sha256']}]})
        self.adaptation['views'][0].update(source=source, source_bundle=bundle)
        self.recipe['authoring_inputs'] = [source]
        for clip in self.recipe['clips']:
            for frame in clip['frames']:
                for layer in frame['layers']: layer.update(source=source, source_bundle=bundle)
        self.rejected('reconstruct')

    def test_nullable_masks_do_not_enable_role_mixing_or_fake_surfaces(self):
        mapping = self.adaptation['mappings'][0]
        mapping['target_surface']['surface_id'] = 'face'
        self.rejected('surface')
        mapping['target_surface']['surface_id'] = 'torso'
        mapping['coverage'] = {'role': 'source-ownership', 'mask': self.ownership,
                               'target_surface': mapping['target_surface']}
        self.first_layer()['coverage'] = self.ownership
        self.rejected('role|coverage')

    def test_uniform_density_and_multisource_unsupported_not_silently_accepted(self):
        self.adaptation['views'][0]['extraction']['density_normalization'] = {'scale': [0.5, 0.5]}
        self.rejected('density normalization')
        self.adaptation['views'][0]['extraction']['density_normalization'] = None
        self.adaptation['views'][0]['source_views'] = [self.source, self.source]
        self.rejected('fields')

    def test_local_transform_and_nonbinary_ownership_rejected(self):
        self.first_layer()['local_scale'] = [0.5, 0.5]
        self.rejected('registration transform')
        self.first_layer()['local_scale'] = [1, 1]
        mask = self.write(self.ownership['file'], Image.new('L', (2, 2), 128))
        self.adaptation['views'][0]['source_ownership']['mask'] = mask
        self.first_layer()['ownership'] = mask
        self.rejected('binary')

    def test_source_or_adaptation_missing_hash_tamper_and_output_tamper(self):
        self.refresh()
        output = self.repo / 'coastal-schema3-integrity'
        build.construct(self.repo, self.path, output)
        manifest = json.loads((output / 'manifest.json').read_text())
        entry = manifest['outputs'][0]
        Image.new('RGBA', (2, 2)).save(output / entry['file'])
        entry['sha256'] = sha(output / entry['file'])
        (output / 'manifest.json').write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, 'pixel|digest'):
            build.verify(self.repo, output)
        (self.lib / self.source['file']).unlink()
        self.rejected('path')

    def test_missing_design_identity_is_a_contract_error(self):
        path = self.recipe['slots']['top']['file']
        self.recipe['slots']['top'] = self.write(path, {'category': 'top', 'revision': 'r002'})
        self.rejected('identity')

    def test_rehashed_nonimage_ownership_is_a_contract_error(self):
        path = self.lib / self.ownership['file']
        path.write_bytes(b'not a PNG')
        ref = {'file': self.ownership['file'], 'sha256': sha(path)}
        self.adaptation['views'][0]['source_ownership']['mask'] = ref
        for clip in self.recipe['clips']:
            for frame in clip['frames']: frame['layers'][1]['ownership'] = ref
        self.rejected('mask|PNG')

    def test_adaptation_sha_and_annotation_anchor_changes_invalidate_existing_build(self):
        self.refresh()
        output = self.repo / 'coastal-schema3-stale'
        build.construct(self.repo, self.path, output)
        self.annotations['records'][0]['landmarks_px']['cloth'] = [0, 0]
        self.write(self.annotation_path, self.annotations)
        with self.assertRaisesRegex(ValueError, 'SHA|stale'):
            build.verify(self.repo, output)
        self.annotations['records'][0]['landmarks_px']['cloth'] = [1, 1]
        self.write(self.annotation_path, self.annotations)
        ref = self.recipe['adaptations']['top']
        (self.lib / ref['file']).write_text('{}')
        with self.assertRaisesRegex(ValueError, 'SHA'):
            validate(self.repo, self.path)

    def test_coverage_cannot_escape_named_target_surface(self):
        self.annotations['records'][0]['surfaces']['torso']['mask'] = self.write(
            self.namespace + '/small-surface.png', Image.new('L', (2, 2), 0))
        annotation = self.write(self.annotation_path, self.annotations)
        self.adaptation['views'][0]['source_pose']['document'] = annotation
        for mapping in self.adaptation['mappings']: mapping['target_pose']['document'] = annotation
        coverage = self.write(self.namespace + '/outside-cover.png', Image.new('L', (2, 2), 255))
        mapping = self.adaptation['mappings'][0]
        mapping['coverage'] = {'role': 'target-coverage', 'mask': coverage,
                               'target_surface': mapping['target_surface']}
        self.first_layer()['coverage'] = coverage
        self.recipe['clips'][0]['frames'][0]['composition'] = 'ownership-replace'
        self.rejected('exceeds.*surface')

    def test_versioned_definition_does_not_move_texture_namespace(self):
        ref = self.write('parts/top/top/revisions/r002/test/motion/wrong.png',
                         Image.new('RGBA', (2, 2)))
        self.first_layer()['texture'] = ref
        self.adaptation['mappings'][0]['texture'] = ref
        self.rejected('namespace')

    def test_adaptation_path_binds_category_design_template_and_motion(self):
        for path in [
            'parts/pants/top/test/motion/r002/views.json',
            'parts/top/another/test/motion/r002/views.json',
            'parts/top/top/another/motion/r002/views.json',
            'parts/top/top/test/another/r002/views.json',
            'parts/top/top/adaptations/test/motion/r002/views.json',
        ]:
            with self.subTest(path=path):
                self.refresh()
                self.recipe['adaptations']['top'] = self.write(path, self.adaptation)
                self.save()
                with self.assertRaisesRegex(ValueError, 'namespace'):
                    validate(self.repo, self.path)

    def test_occlusion_cannot_erase_where_declared_foreground_has_no_pixels(self):
        frame = self.recipe['clips'][0]['frames'][0]
        foreground = copy.deepcopy(frame['layers'][0]); foreground['id'] = 'skin'
        foreground['texture'] = self.write('templates/test/motions/motion/body-views/empty.png',
                                           Image.new('RGBA', (2, 2)))
        frame['layers'].append(foreground); frame['layer_order'].append('skin')
        hidden = self.write(self.namespace + '/unphysical-occlusion.png', Image.new('L', (2, 2), 255))
        frame['layers'][1]['occlusion'] = hidden
        mapping = self.adaptation['mappings'][0]
        mapping['occlusion'] = {'role': 'target-occlusion', 'mask': hidden, 'foreground_layers': ['skin']}
        texture = self.write(mapping['texture']['file'], Image.new('RGBA', (2, 2)))
        mapping['texture'] = texture; frame['layers'][1]['texture'] = texture
        self.rejected('foreground.*support')

    def padded_source_fixture(self, cropped=False):
        source_image = Image.new('RGBA', (4, 4))
        source_image.putpixel((1, 1), (200, 30, 40, 128))
        source_image.putpixel((2, 2), (30, 40, 200, 200))
        source = self.write(self.source['file'], source_image)
        bundle = self.write(self.bundle['file'], {'source_id': 'test', 'assets': [
            {'new_path': 'art/characters/' + source['file'], 'new_sha256': source['sha256']}]})
        ownership_image = Image.new('L', (4, 4), 0)
        ownership_image.putpixel((1, 1), 255); ownership_image.putpixel((2, 2), 255)
        ownership = self.write(self.ownership['file'], ownership_image)
        self.recipe['authoring_inputs'] = [source]
        for clip in self.recipe['clips']:
            clip.update(canvas_px=[4, 4], root_anchor_px=[2, 2])
            body = self.write('templates/test/motions/motion/body-views/' + clip['action_id'] + '.png',
                              Image.new('RGBA', (4, 4), (10, 20, 30, 255)))
            surface = self.write(self.namespace + '/' + clip['action_id'] + '-surface.png', Image.new('L', (4, 4), 255))
            poses = json.loads((self.lib / clip['poses']['file']).read_text())
            poses['variants']['A'].update(canvas_px=[4, 4], root_anchor_px=[2, 2])
            for i, (frame, original) in enumerate(zip(clip['frames'], poses['variants']['A']['frames'])):
                original.update(file=body['file'], sha256=body['sha256'])
                frame['layers'][0]['texture'] = body
                for layer in frame['layers']: layer.update(source=source, source_bundle=bundle)
                anchor = [2, 2] if clip['action_id'] == 'idle' else [[3, 1], [1, 2], [2, 3]][i]
                if cropped and clip['action_id'] == 'wave' and i == 0: anchor = [4, 0]
                annotation = next(r for r in self.annotations['records'] if r['record_id'] == frame['pose_id'])
                annotation.update(canvas_px=[4, 4], root_anchor_px=[2, 2], reference_frame=body,
                                  landmarks_px={'cloth': anchor}, surfaces={'torso': {'layer_id': 'body', 'mask': surface}})
                mapping = next(m for m in self.adaptation['mappings'] if m['mapping_id'] == frame['pose_id'])
                mapping['anchors'] = {'name': 'cloth', 'source_px': [2, 2], 'target_px': anchor}
                image = Image.new('RGBA', (4, 4)); image.paste(source_image, (anchor[0]-2, anchor[1]-2))
                mapping['texture'] = self.write(mapping['texture']['file'], image)
                frame['layers'][1].update(texture=mapping['texture'], ownership=ownership)
            clip['poses'] = self.write(clip['poses']['file'], poses)
            for record in self.annotations['records']:
                if record['pose_id'].startswith(clip['action_id'] + '_'): record['poses'] = clip['poses']
        annotation = self.write(self.annotation_path, self.annotations)
        for mapping in self.adaptation['mappings']: mapping['target_pose']['document'] = annotation
        self.adaptation['views'][0].update(source=source, source_bundle=bundle, canvas_px=[4, 4], root_anchor_px=[2, 2],
                                           source_pose={'document': annotation, 'record': 'idle_west_0'},
                                           source_ownership={'role': 'source-ownership', 'mask': ownership})

    def test_signed_same_canvas_mapping_preserves_owned_alpha_and_only_loses_padding(self):
        self.padded_source_fixture()
        self.refresh()
        output = self.repo / 'coastal-schema3-signed'
        build.construct(self.repo, self.path, output); build.verify(self.repo, output)
        with Image.open(output / 'frames/wave/west/wave_west_0.png') as actual:
            self.assertEqual(actual.size, (4, 4))
            texture = self.adaptation['mappings'][1]['texture']
            with Image.open(self.lib / texture['file']) as registered:
                self.assertEqual(registered.getpixel((2, 0)), (200, 30, 40, 128))
                self.assertEqual(registered.getpixel((3, 1)), (30, 40, 200, 200))

    def test_signed_mapping_that_loses_real_alpha_content_is_rejected(self):
        self.padded_source_fixture(cropped=True)
        self.rejected('crop.*(alpha|component)|alpha.*crop')

    def public_mapper(self):
        # Real callbacks mirror a second consumer's content-addressed I/O.
        def reference(ref, namespace=None, image_size=None):
            contract.keys(ref, 'file sha256', 'reference')
            path = contract.safe_file(self.lib, ref['file'], namespace)
            contract.require(sha(path) == ref['sha256'], 'SHA mismatch')
            if image_size is not None:
                with Image.open(path) as image:
                    contract.require(image.format == 'PNG' and list(image.size) == list(image_size), 'PNG canvas mismatch')
            return path
        def record(ref, namespace=None):
            return contract.read_json(reference(ref, namespace))
        self.refresh()
        motion = record(self.recipe['motion_set'])
        designs = {'top': record(self.recipe['slots']['top'])}
        return contract.RegisteredAdaptations(self.lib, self.recipe, reference, record, 'test', motion, designs)

    def test_public_mapper_itself_binds_canonical_source_bundle(self):
        bad_bundle = self.write(self.bundle['file'], {'source_id': 'test', 'assets': []})
        self.adaptation['views'][0]['source_bundle'] = bad_bundle
        self.first_layer()['source_bundle'] = bad_bundle
        mapper = self.public_mapper()
        clip = self.recipe['clips'][0]; frame = clip['frames'][0]
        with self.assertRaisesRegex(ValueError, 'Source not bound.*bundle'):
            mapper.component(self.first_layer(), clip, frame)

    def normalized_source_fixture(self, selections=True):
        raw = self.source_image.resize((4, 4), Image.Resampling.NEAREST)
        source = self.write(self.source['file'], raw)
        bundle = self.write(self.bundle['file'], {'source_id': 'test', 'assets': [
            {'new_path': 'art/characters/' + source['file'], 'new_sha256': source['sha256']}]})
        norm = {'kind': 'whole-source-rational-v1', 'filter': 'nearest', 'numerator': 1, 'denominator': 2,
                'raw_canvas_px': [4, 4], 'raw_root_anchor_px': [2, 2],
                'normalized_canvas_px': [2, 2], 'normalized_root_anchor_px': [1, 1]}
        view = self.adaptation['views'][0]
        view.update(source=source, source_bundle=bundle)
        view['extraction'] = {'kind': 'normalized-source-selection-v1', 'schema_version': 1,
                              'normalization': norm, 'ownership_space': 'normalized-source-full-frame',
                              'selection_space': 'normalized-source-full-frame', 'selections': []}
        expected = self.source_image.copy()
        if selections:
            repair = Image.new('RGBA', (2, 2), (1, 2, 3, 0))
            repair.putpixel((0, 0), (17, 33, 77, 73))
            repair.putpixel((1, 1), (8, 99, 42, 111))
            extra = self.write('sources/repair/originals/repair.png', repair.resize((4, 4), Image.Resampling.NEAREST))
            extra_bundle = self.write('sources/repair/source.json', {'source_id': 'repair', 'assets': [
                {'new_path': 'art/characters/' + extra['file'], 'new_sha256': extra['sha256']}]})
            mask = Image.new('L', (2, 2), 0); mask.putpixel((0, 0), 255)
            selection = self.write(self.namespace + '/source-selection.png', mask)
            view['extraction']['selections'] = [{
                'selection_id': 'collar', 'source': extra, 'source_bundle': extra_bundle,
                'source_pose': copy.deepcopy(view['source_pose']), 'normalization': copy.deepcopy(norm),
                'selection': {'role': 'source-selection', 'mask': selection}}]
            expected.putpixel((0, 0), repair.getpixel((0, 0)))
        self.recipe['authoring_inputs'] = [source]
        for clip in self.recipe['clips']:
            for frame in clip['frames']:
                for layer in frame['layers']: layer.update(source=source, source_bundle=bundle)
                mapping = next(m for m in self.adaptation['mappings'] if m['mapping_id'] == frame['pose_id'])
                anchor = mapping['anchors']['target_px']
                registered = Image.new('RGBA', tuple(clip['canvas_px']))
                extracted = Image.new('RGBA', (2, 2))
                extracted.putpixel((0, 0), expected.getpixel((0, 0)))
                extracted.putpixel((1, 1), expected.getpixel((1, 1)))
                registered.paste(extracted, (anchor[0]-1, anchor[1]-1))
                mapping['texture'] = self.write(mapping['texture']['file'], registered)
                frame['layers'][1]['texture'] = mapping['texture']
        return expected

    def test_sourcewide_rational_nearest_normalization_builds_and_verifies(self):
        self.normalized_source_fixture(selections=False)
        self.refresh()
        output = self.repo / 'coastal-schema3-normalized'
        build.construct(self.repo, self.path, output); build.verify(self.repo, output)
        with Image.open(self.lib / self.first_layer()['texture']['file']) as image:
            self.assertEqual(image.getpixel((0, 0)), (200, 30, 40, 128))

    def test_binary_source_selection_preserves_rgba_without_alpha_over_or_remultiplication(self):
        self.normalized_source_fixture()
        self.refresh()
        output = self.repo / 'coastal-schema3-selected'
        build.construct(self.repo, self.path, output); build.verify(self.repo, output)
        with Image.open(self.lib / self.first_layer()['texture']['file']) as image:
            self.assertEqual(image.getpixel((0, 0)), (17, 33, 77, 73))
            self.assertEqual(image.getpixel((1, 1)), (30, 40, 200, 200))
        valid = validate(self.repo, self.path)
        for path in ['sources/repair/originals/repair.png', 'sources/repair/source.json', self.namespace + '/source-selection.png']:
            self.assertIn(path, valid.dependencies)

    def test_normalization_rejects_unknown_transform_anisotropy_and_unbound_roots(self):
        self.normalized_source_fixture()
        norm = self.adaptation['views'][0]['extraction']['normalization']
        for field, value in [('kind', []), ('filter', 'bilinear'), ('numerator', 2), ('denominator', 0),
                             ('normalized_canvas_px', [2, 3]), ('raw_root_anchor_px', [3, 2]),
                             ('normalized_root_anchor_px', [0, 1]), ('raw_canvas_px', [8, 4])]:
            with self.subTest(field=field):
                old = norm[field]; norm[field] = value
                try: self.rejected('normalization|rational|root|canvas')
                finally: norm[field] = old
        norm['local_scale'] = [0.5, 0.5]
        self.rejected('fields')

    def test_selection_spaces_roles_and_pose_cannot_be_interchanged(self):
        self.normalized_source_fixture()
        extraction = self.adaptation['views'][0]['extraction']
        for field in ['ownership_space', 'selection_space']:
            old = extraction[field]; extraction[field] = 'target-pose-full-frame'
            self.rejected('space'); extraction[field] = old
        selection = extraction['selections'][0]
        selection['selection']['role'] = 'target-coverage'
        self.rejected('role')
        selection['selection']['role'] = 'source-selection'
        selection['source_pose']['record'] = 'wave_west_0'
        self.rejected('source pose')

    def test_selection_mask_must_be_binary_in_normalized_canvas(self):
        self.normalized_source_fixture()
        selection = self.adaptation['views'][0]['extraction']['selections'][0]['selection']
        for size, value in [((4, 4), 255), ((2, 2), 128)]:
            selection['mask'] = self.write(self.namespace + '/wrong-selection.png', Image.new('L', size, value))
            self.rejected('canvas|binary')

    def test_extra_source_bundle_and_source_hash_are_verified_independently(self):
        self.normalized_source_fixture()
        extra = self.adaptation['views'][0]['extraction']['selections'][0]
        old = extra['source_bundle']
        extra['source_bundle'] = self.write('sources/repair/source.json', {'source_id': 'repair', 'assets': []})
        self.rejected('Source not bound.*bundle')
        extra['source_bundle'] = self.write('sources/repair/source.json', {'source_id': 'repair', 'assets': [
            {'new_path': 'art/characters/' + extra['source']['file'], 'new_sha256': extra['source']['sha256']}]})
        (self.lib / extra['source']['file']).write_bytes(b'changed')
        self.rejected('SHA')

    def test_rehashed_extra_source_or_selection_mask_cannot_fake_reconstruction(self):
        self.normalized_source_fixture()
        extra = self.adaptation['views'][0]['extraction']['selections'][0]
        original_mask = extra['selection']['mask']
        extra['selection']['mask'] = self.write(original_mask['file'], Image.new('L', (2, 2), 0))
        self.rejected('reconstruct')
        mask = Image.new('L', (2, 2)); mask.putpixel((0, 0), 255)
        extra['selection']['mask'] = self.write(original_mask['file'], mask)
        extra['source'] = self.write(extra['source']['file'], Image.new('RGBA', (4, 4), (99, 88, 77, 63)))
        extra['source_bundle'] = self.write(extra['source_bundle']['file'], {'source_id': 'repair', 'assets': [
            {'new_path': 'art/characters/' + extra['source']['file'], 'new_sha256': extra['source']['sha256']}]})
        self.rejected('reconstruct')

    def test_extra_source_changes_invalidate_previously_verified_build(self):
        self.normalized_source_fixture(); self.refresh()
        output = self.repo / 'coastal-schema3-selected-stale'
        build.construct(self.repo, self.path, output); build.verify(self.repo, output)
        extra = self.adaptation['views'][0]['extraction']['selections'][0]
        (self.lib / extra['source']['file']).write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'SHA|stale'):
            build.verify(self.repo, output)

    def test_new_extraction_rejects_missing_version_and_unknown_selection_fields(self):
        self.normalized_source_fixture()
        extraction = self.adaptation['views'][0]['extraction']
        extraction['schema_version'] = 2
        self.rejected('extraction schema')
        extraction['schema_version'] = 1
        extraction['selections'][0]['offset_px'] = [1, 0]
        self.rejected('fields')

    def test_ordered_overlapping_source_selections_choose_last_rgba_verbatim(self):
        self.normalized_source_fixture()
        extraction = self.adaptation['views'][0]['extraction']
        extra = copy.deepcopy(extraction['selections'][0])
        extra['selection_id'] = 'second-collar'
        extra['source'] = self.write('sources/second/originals/repair.png', Image.new('RGBA', (4, 4), (44, 55, 66, 51)))
        extra['source_bundle'] = self.write('sources/second/source.json', {'source_id': 'second', 'assets': [
            {'new_path': 'art/characters/' + extra['source']['file'], 'new_sha256': extra['source']['sha256']}]})
        extraction['selections'].append(extra)
        for mapping in self.adaptation['mappings']:
            with Image.open(self.lib / mapping['texture']['file']) as texture: image = texture.convert('RGBA')
            x, y = mapping['anchors']['target_px']; image.putpixel((x-1, y-1), (44, 55, 66, 51))
            mapping['texture'] = self.write(mapping['texture']['file'], image)
            frame = next(f for c in self.recipe['clips'] for f in c['frames'] if f['pose_id'] == mapping['mapping_id'])
            frame['layers'][1]['texture'] = mapping['texture']
        self.check()
        extraction['selections'][1]['selection_id'] = 'collar'
        self.rejected('Duplicate source selection')

    def test_declared_extra_source_bundle_pose_cannot_contradict_annotation(self):
        self.normalized_source_fixture()
        extra = self.adaptation['views'][0]['extraction']['selections'][0]
        data = contract.read_json(self.lib / extra['source_bundle']['file'])
        data['source_view_pose'] = 'another_pose'
        extra['source_bundle'] = self.write(extra['source_bundle']['file'], data)
        self.rejected('source.*pose|pose.*source')

    def test_collar_selection_reconstructs_only_owned_visible_surface(self):
        expected = self.normalized_source_fixture()
        value = self.check()
        view = self.adaptation['views'][0]
        selection = view['extraction']['selections'][0]
        for ref in [view['source'], view['source_bundle'], selection['source'],
                    selection['source_bundle'], selection['selection']['mask'],
                    view['source_ownership']['mask']]:
            self.assertIn(ref['file'], value.dependencies)
        for mapping in self.adaptation['mappings']:
            texture = value.image(mapping['texture'])
            x, y = mapping['anchors']['target_px']
            self.assertEqual(texture.getpixel((x-1, y-1)), expected.getpixel((0, 0)))
            self.assertEqual(texture.getpixel((x, y)), expected.getpixel((1, 1)))
            self.assertEqual(texture.getpixel((x, y-1)), (0, 0, 0, 0))
        self.assertEqual(expected.getpixel((0, 0)), (17, 33, 77, 73))
        output = self.repo/'coastal-collar-selected'
        build.construct(self.repo, self.path, output); build.verify(self.repo, output)
        # A self-consistently rehashed texture cannot insert unowned material.
        mapping = self.adaptation['mappings'][0]
        changed = value.image(mapping['texture']).copy()
        changed.putpixel((1, 0), (99, 88, 77, 255))
        mapping['texture'] = self.write(mapping['texture']['file'], changed)
        self.first_layer()['texture'] = mapping['texture']
        self.rejected('reconstruct|RGBA|support')

    def test_binary_occlusion_rejects_partial_foreground_and_alpha_order_keeps_underlayer(self):
        clip = self.recipe['clips'][0]; frame = clip['frames'][0]; mapping = self.adaptation['mappings'][0]
        frame['layer_order'] = ['top', 'body']
        mask = Image.new('L', (2, 2), 0); mask.putpixel((0, 0), 255)
        hidden = self.write(self.namespace + '/soft-foreground-occlusion.png', mask)
        for alpha in [1, 128, 254]:
            with self.subTest(alpha=alpha):
                body_ref = frame['layers'][0]['texture']
                with Image.open(self.lib / body_ref['file']) as image: body = image.convert('RGBA')
                body.putpixel((0, 0), (10, 20, 30, alpha))
                body_ref = self.write(body_ref['file'], body); frame['layers'][0]['texture'] = body_ref
                poses = contract.read_json(self.lib / clip['poses']['file'])
                poses['variants']['A']['frames'][0].update(file=body_ref['file'], sha256=body_ref['sha256'])
                clip['poses'] = self.write(clip['poses']['file'], poses)
                self.annotations['records'][0].update(poses=clip['poses'], reference_frame=body_ref)
                annotation = self.write(self.annotation_path, self.annotations)
                self.adaptation['views'][0]['source_pose']['document'] = annotation
                for item in self.adaptation['mappings']: item['target_pose']['document'] = annotation
                mapping['occlusion'] = {'role': 'target-occlusion', 'mask': hidden, 'foreground_layers': ['body']}
                self.first_layer()['occlusion'] = hidden
                with Image.open(self.lib / mapping['texture']['file']) as image: stripped = image.convert('RGBA')
                stripped.putpixel((0, 0), (0, 0, 0, 0))
                mapping['texture'] = self.write(mapping['texture']['file'], stripped)
                self.first_layer()['texture'] = mapping['texture']
                self.rejected('occlusion.*opaque|opaque.*foreground')
                mapping['occlusion'] = None; self.first_layer()['occlusion'] = None
                complete = stripped.copy(); complete.putpixel((0, 0), (200, 30, 40, 128))
                mapping['texture'] = self.write(mapping['texture']['file'], complete)
                self.first_layer()['texture'] = mapping['texture']; self.refresh()
                output = self.repo / ('coastal-alpha-foreground-' + str(alpha))
                build.construct(self.repo, self.path, output); build.verify(self.repo, output)
                with Image.open(output / 'frames/idle/west/idle_west_0.png') as actual:
                    self.assertEqual(actual.getpixel((0, 0)), Image.alpha_composite(complete, body).getpixel((0, 0)))
                    if alpha == 128: self.assertEqual(actual.getpixel((0, 0)), (73, 23, 33, 192))

    def test_null_asset_is_a_valueerror_in_public_mapper_and_schema3_validate(self):
        bad = self.write(self.bundle['file'], {'source_id': 'test', 'assets': [None]})
        self.adaptation['views'][0]['source_bundle'] = bad
        for clip in self.recipe['clips']:
            for frame in clip['frames']:
                for layer in frame['layers']: layer['source_bundle'] = bad
        mapper = self.public_mapper(); clip = self.recipe['clips'][0]
        with self.assertRaisesRegex(ValueError, 'assets'):
            mapper.component(self.first_layer(), clip, clip['frames'][0])
        self.rejected('assets')

    def test_unhashable_view_mapping_and_variant_are_valueerrors(self):
        binding = self.first_layer()['view_binding']
        for field in ['view_id', 'mapping_id']:
            with self.subTest(field=field):
                old = binding[field]; binding[field] = []
                try: self.rejected('identifier|view|mapping')
                finally: binding[field] = old
        original = self.adaptation['mappings'][0]['view_id']
        self.adaptation['mappings'][0]['view_id'] = []
        try: self.rejected('identifier|view|mapping')
        finally: self.adaptation['mappings'][0]['view_id'] = original
        self.annotations['records'][0]['variant'] = []
        annotation = self.write(self.annotation_path, self.annotations)
        self.adaptation['views'][0]['source_pose']['document'] = annotation
        for item in self.adaptation['mappings']: item['target_pose']['document'] = annotation
        self.rejected('variant')

    def test_unhashable_foreground_layer_is_a_valueerror(self):
        hidden = self.write(self.namespace + '/bad-foreground.png', Image.new('L', (2, 2), 0))
        self.adaptation['mappings'][0]['occlusion'] = {'role': 'target-occlusion', 'mask': hidden, 'foreground_layers': [[]]}
        self.first_layer()['occlusion'] = hidden
        self.rejected('foreground')

    def odd_source(self):
        raw = Image.new('RGBA', (3, 5))
        for y in range(5):
            for x in range(3): raw.putpixel((x, y), (40*x+1, 30*y+2, 90, 7 if (x, y) == (2, 4) else 128))
        source = self.write('sources/odd/originals/full.png', raw)
        bundle = self.write('sources/odd/source.json', {'source_id': 'odd', 'assets': [
            {'new_path': 'art/characters/' + source['file'], 'new_sha256': source['sha256']}]})
        return raw, source, bundle

    def pad_normalization(self, canvas=(4, 6), offset=(0, 0), root=(2, 4)):
        return {'kind': 'whole-source-rational-pad-v1', 'filter': 'nearest', 'numerator': 8, 'denominator': 7,
                'raw_canvas_px': [3, 5], 'raw_root_anchor_px': [1.75, 3.5],
                'normalized_canvas_px': list(canvas), 'normalized_root_anchor_px': list(root),
                'whole_frame_offset_px': list(offset)}

    def test_rational_padding_uses_one_uniform_affine_and_preserves_low_alpha_tail(self):
        raw, source, bundle = self.odd_source(); mapper = self.public_mapper()
        norm = self.pad_normalization()
        image = mapper.normalized_source(source, bundle, norm, [4, 6], [2, 4], 'idle_west_0')
        expected = Image.new('RGBA', (4, 6))
        # Independent rational pixel-center nearest sampling. Here inverse7/8
        # is exactly representable, including the partial last scaled column.
        for y in range(6):
            for x in range(4):
                sx = (Fraction(2*x+1, 2) * Fraction(7, 8)).numerator // (Fraction(2*x+1, 2) * Fraction(7, 8)).denominator
                sy = (Fraction(2*y+1, 2) * Fraction(7, 8)).numerator // (Fraction(2*y+1, 2) * Fraction(7, 8)).denominator
                if 0 <= sx < 3 and 0 <= sy < 5: expected.putpixel((x, y), raw.getpixel((sx, sy)))
        self.assertEqual(image.tobytes(), expected.tobytes())
        self.assertNotEqual(image.tobytes(), raw.resize((4, 6), Image.Resampling.NEAREST).tobytes())
        self.assertEqual(image.getpixel((2, 5)), raw.getpixel((2, 4)))
        self.assertEqual(image.getpixel((2, 5))[3], 7)
        self.assertTrue(all(image.getpixel((3, y)) == (0, 0, 0, 0) for y in range(6)))
        legacy = copy.deepcopy(norm); legacy['kind'] = 'whole-source-rational-v1'; legacy.pop('whole_frame_offset_px')
        with self.assertRaisesRegex(ValueError, 'uniform|integral'):
            mapper.normalized_source(source, bundle, legacy, [4, 6], [2, 4], 'idle_west_0')

    def test_rational_padding_offset_moves_the_entire_source_with_bound_root(self):
        _, source, bundle = self.odd_source(); mapper = self.public_mapper()
        baseline = mapper.normalized_source(source, bundle, self.pad_normalization(), [4, 6], [2, 4], 'idle_west_0')
        norm = self.pad_normalization(canvas=(6, 9), offset=(1, 2), root=(3, 6))
        image = mapper.normalized_source(source, bundle, norm, [6, 9], [3, 6], 'idle_west_0')
        expected = Image.new('RGBA', (6, 9)); expected.paste(baseline, (1, 2))
        self.assertEqual(image.tobytes(), expected.tobytes())
        self.assertEqual(image.getpixel((3, 7))[3], 7)

    def test_pad_normalization_rejects_crop_wrong_root_ratio_and_offset(self):
        _, source, bundle = self.odd_source(); mapper = self.public_mapper()
        norm = self.pad_normalization()
        changes = [('normalized_canvas_px', [3, 6]), ('whole_frame_offset_px', [-1, 0]),
                   ('whole_frame_offset_px', [0.5, 0]), ('raw_root_anchor_px', [1.75, 3.4]),
                   ('numerator', 16), ('denominator', 0)]
        for field, value in changes:
            with self.subTest(field=field, value=value):
                changed = copy.deepcopy(norm); changed[field] = value
                with self.assertRaisesRegex(ValueError, 'normalization|Normalization|rational|root|offset|crop'):
                    mapper.normalized_source(source, bundle, changed, changed['normalized_canvas_px'], [2, 4], 'idle_west_0')
        changed = self.pad_normalization(canvas=(5, 6), offset=(1, 0))
        with self.assertRaisesRegex(ValueError, 'root'):
            mapper.normalized_source(source, bundle, changed, [5, 6], [2, 4], 'idle_west_0')

    def test_pad_kind_is_reconstructed_through_real_build_and_legacy_kind_is_strict(self):
        self.normalized_source_fixture()
        extraction = self.adaptation['views'][0]['extraction']
        for norm in [extraction['normalization']] + [s['normalization'] for s in extraction['selections']]:
            norm.update(kind='whole-source-rational-pad-v1', whole_frame_offset_px=[0, 0])
        self.refresh(); output = self.repo / 'coastal-pad-build'
        build.construct(self.repo, self.path, output); build.verify(self.repo, output)
        extraction['normalization']['kind'] = 'whole-source-rational-v1'
        self.rejected('fields')

    def test_actual_underhat_dimensions_and_fractional_root_need_only_whole_source_padding(self):
        # The production case's exact dimensions/root on a synthetic sparse
        # full source. This tests geometry, not the real under-hat artwork.
        raw = Image.new('RGBA', (1122, 1402)); raw.putpixel((1121, 1401), (150, 45, 10, 7))
        source = self.write('sources/underhat-probe/originals/full.png', raw)
        bundle = self.write('sources/underhat-probe/source.json', {'source_id': 'underhat-probe', 'assets': [
            {'new_path': 'art/characters/' + source['file'], 'new_sha256': source['sha256']}]})
        norm = {'kind': 'whole-source-rational-pad-v1', 'filter': 'nearest', 'numerator': 256, 'denominator': 187,
                'raw_canvas_px': [1122, 1402], 'raw_root_anchor_px': [561, 1168.75],
                'normalized_canvas_px': [1536, 1920], 'normalized_root_anchor_px': [768, 1600],
                'whole_frame_offset_px': [0, 0]}
        mapper = self.public_mapper()
        image = mapper.normalized_source(source, bundle, norm, [1536, 1920], [768, 1600], 'idle_west_0')
        self.assertEqual(image.size, (1536, 1920))
        self.assertEqual(image.getpixel((1535, 1918)), (150, 45, 10, 7))
        self.assertIsNone(image.getchannel('A').crop((0, 1919, 1536, 1920)).getbbox())
        norm['raw_root_anchor_px'][1] = 1168.750000001
        with self.assertRaisesRegex(ValueError, 'root'):
            mapper.normalized_source(source, bundle, norm, [1536, 1920], [768, 1600], 'idle_west_0')

    def test_schema3_body_cannot_be_replaced_and_rehashed_with_different_same_size_body(self):
        body = self.recipe['clips'][0]['frames'][0]['layers'][0]
        body['texture'] = self.write('templates/test/motions/motion/body-views/another-body.png',
                                     Image.new('RGBA', (2, 2), (211, 13, 147, 255)))
        self.rejected('canonical.*body|body.*canonical')

    def test_schema3_cannot_stack_the_complete_canonical_body_twice(self):
        frame = self.recipe['clips'][0]['frames'][0]
        duplicate = copy.deepcopy(frame['layers'][0]); duplicate['id'] = 'body-again'
        frame['layers'].append(duplicate); frame['layer_order'].append('body-again')
        self.rejected('one canonical body')

    def test_body_only_rgba_alias_is_valid_and_canonical_frame_is_a_dependency(self):
        clip = self.recipe['clips'][0]; body = clip['frames'][0]['layers'][0]
        canonical = copy.deepcopy(body['texture'])
        path = self.lib/'templates/test/motions/motion/body-views/body-alias.png'
        metadata = PngImagePlugin.PngInfo(); metadata.add_text('provenance', 'same canonical RGBA, different PNG bytes')
        with Image.open(self.lib/canonical['file']) as im: im.save(path, pnginfo=metadata)
        body['texture'] = {'file': path.relative_to(self.lib).as_posix(), 'sha256': sha(path)}
        self.assertNotEqual(canonical['sha256'], body['texture']['sha256'])
        self.recipe['slots'] = {'body': None}; self.recipe['adaptations'] = {}
        for row in self.recipe['clips']:
            for frame in row['frames']:
                frame['layers'] = [frame['layers'][0]]; frame['layer_order'] = ['body']
        self.save()
        value = validate(self.repo, self.path)
        self.assertIn(canonical['file'], value.dependencies)
        output = self.repo/'coastal-canonical-body-alias'
        build.construct(self.repo, self.path, output); build.verify(self.repo, output)

    def atlas_source_fixture(self):
        # A real four-cell source: only bottom-left is the selected view.
        atlas = Image.new('RGBA', (4, 4), (240, 20, 20, 255))
        atlas.paste(Image.new('RGBA', (2, 2), (20, 240, 20, 255)), (2, 0))
        atlas.paste(Image.new('RGBA', (2, 2), (240, 240, 20, 255)), (2, 2))
        atlas.paste(self.source_image, (0, 2))
        source = self.write('sources/atlas/originals/full.png', atlas)
        bundle = self.write('sources/atlas/source.json', {'source_id': 'atlas', 'assets': [
            {'new_path': 'art/characters/' + source['file'], 'new_sha256': source['sha256']}]})
        owner = Image.new('L', (4, 4)); owner.paste(Image.new('L', (2, 2), 255), (0, 2))
        owner_ref = self.write(self.namespace + '/atlas-owner.png', owner)
        view = self.adaptation['views'][0]
        view.update(source=source, source_bundle=bundle)
        view['extraction'] = {'kind': 'registered-source-atlas-v1', 'schema_version': 1,
            'atlas_canvas_px': [4, 4], 'normalization': {
                'kind': 'whole-source-rational-v1', 'filter': 'nearest', 'numerator': 1, 'denominator': 1,
                'raw_canvas_px': [4, 4], 'raw_origin_px': [0, 0],
                'normalized_canvas_px': [4, 4], 'normalized_origin_px': [0, 0]},
            'atlas_ownership': {'role': 'source-atlas-ownership', 'coordinate_space': 'normalized-source-atlas', 'mask': owner_ref},
            'registration': {'kind': 'atlas-to-source-pose-anchor-v1', 'atlas_anchor_px': [1, 3],
                             'pose_anchor_name': 'cloth', 'pose_anchor_px': [1, 1]}}
        self.recipe['authoring_inputs'].append(source)
        for clip in self.recipe['clips']:
            for frame in clip['frames']:
                # The body retains its separate original canonical source.
                frame['layers'][1].update(source=source, source_bundle=bundle)
        return atlas

    def test_complete_source_atlas_selects_one_cell_then_registers_soft_rgba_once(self):
        self.atlas_source_fixture(); self.refresh()
        value = validate(self.repo, self.path)
        view = self.adaptation['views'][0]
        self.assertEqual(view['canvas_px'], [2, 2])
        self.assertEqual(view['root_anchor_px'], [1, 1])
        self.assertEqual(view['extraction']['atlas_canvas_px'], [4, 4])
        for mapping in self.adaptation['mappings']:
            texture = value.image(mapping['texture'])
            x, y = mapping['anchors']['target_px']
            self.assertEqual(texture.getpixel((x-1, y-1)), (200, 30, 40, 128))
            self.assertEqual(texture.getpixel((x, y)), (30, 40, 200, 200))
        output = self.repo/'coastal-atlas-built'
        build.construct(self.repo, self.path, output); build.verify(self.repo, output)
        self.assertIn(view['extraction']['atlas_ownership']['mask']['file'], value.dependencies)

    def test_atlas_spaces_roles_and_anchors_are_not_interchangeable(self):
        self.atlas_source_fixture(); extraction = self.adaptation['views'][0]['extraction']
        owner, registration = extraction['atlas_ownership'], extraction['registration']
        for obj, field, value, error in [
            (owner, 'role', 'source-ownership', 'role'),
            (owner, 'coordinate_space', 'target-pose-full-frame', 'space'),
            (registration, 'pose_anchor_px', [0, 0], 'pose anchor'),
            (registration, 'pose_anchor_name', 'missing', 'pose anchor'),
            (registration, 'atlas_anchor_px', [9, 3], 'atlas anchor'),
            (registration, 'atlas_anchor_px', [1, 2], 'crop|reconstruct')]:
            with self.subTest(field=field, value=value):
                old = obj[field]; obj[field] = value
                try: self.rejected(error)
                finally: obj[field] = old

    def test_atlas_registration_cannot_crop_owned_pixels_even_when_final_view_mask_would_hide_them(self):
        self.atlas_source_fixture(); extraction = self.adaptation['views'][0]['extraction']
        with Image.open(self.lib/extraction['atlas_ownership']['mask']['file']) as im: owner = im.copy()
        owner.putpixel((2, 0), 255)  # Foreign opaque cell would move above canonical canvas.
        extraction['atlas_ownership']['mask'] = self.write(extraction['atlas_ownership']['mask']['file'], owner)
        self.rejected('crop.*alpha|crop.*atlas|atlas.*crop')

    def test_atlas_origin_does_not_replace_world_root_or_canonical_geometry(self):
        self.atlas_source_fixture(); view = self.adaptation['views'][0]
        view['root_anchor_px'] = [0, 0]
        self.rejected('geometry')
        view['root_anchor_px'] = [1, 1]; view['canvas_px'] = [4, 4]
        self.rejected('geometry')
        view['canvas_px'] = [2, 2]
        view['extraction']['normalization']['raw_root_anchor_px'] = [0, 0]
        self.rejected('fields')

    def test_atlas_mask_is_full_normalized_atlas_binary_and_origin_is_not_arbitrary_offset(self):
        self.atlas_source_fixture(); extraction = self.adaptation['views'][0]['extraction']
        original = extraction['atlas_ownership']['mask']
        for size, value in [((2, 2), 255), ((4, 4), 128)]:
            with self.subTest(size=size, value=value):
                extraction['atlas_ownership']['mask'] = self.write(self.namespace + '/wrong-atlas-mask.png', Image.new('L', size, value))
                self.rejected('canvas|binary')
        extraction['atlas_ownership']['mask'] = original
        extraction['normalization']['raw_origin_px'] = [1, 0]
        self.rejected('origin')

    def test_atlas_component_preserves_pose_root_and_rejects_fake_world_root(self):
        self.atlas_source_fixture()
        value = self.check()
        view = self.adaptation['views'][0]
        extraction = view['extraction']
        self.assertEqual(extraction['registration']['atlas_anchor_px'], [1, 3])
        self.assertEqual(extraction['registration']['pose_anchor_px'], [1, 1])
        self.assertEqual(view['canvas_px'], [2, 2])
        self.assertEqual(view['root_anchor_px'], [1, 1])
        self.assertNotEqual(view['source']['file'], self.adaptation['mappings'][0]['texture']['file'])
        for mapping in self.adaptation['mappings']:
            image = value.image(mapping['texture'])
            x, y = mapping['anchors']['target_px']
            self.assertEqual(image.getpixel((x-1, y-1)), (200, 30, 40, 128))
            self.assertEqual(image.getpixel((x, y)), (30, 40, 200, 200))
        for ref in [view['source'], view['source_bundle'], extraction['atlas_ownership']['mask']]:
            self.assertIn(ref['file'], value.dependencies)
        # Atlas coordinates must not be substituted for the world-space root.
        view['root_anchor_px'] = extraction['registration']['atlas_anchor_px']
        self.rejected('geometry')


    def test_binary_source_bundle_declared_pose_must_match_source_annotation(self):
        bundle = contract.read_json(self.lib/self.bundle['file'])
        bundle['source_view_pose'] = 'wave_west_0'
        ref = self.write(self.bundle['file'], bundle)
        self.adaptation['views'][0]['source_bundle'] = ref
        for clip in self.recipe['clips']:
            for frame in clip['frames']:
                for layer in frame['layers']: layer['source_bundle'] = ref
        self.rejected('source.*pose|pose.*annotation')

    def test_atlas_extraction_cannot_bypass_an_explicit_conflicting_bundle_pose(self):
        self.atlas_source_fixture()
        view = self.adaptation['views'][0]
        bundle = contract.read_json(self.lib/view['source_bundle']['file'])
        bundle['source_view_pose'] = 'wave_west_0'
        ref = self.write(view['source_bundle']['file'], bundle)
        view['source_bundle'] = ref
        for clip in self.recipe['clips']:
            for frame in clip['frames']: frame['layers'][1]['source_bundle'] = ref
        self.rejected('source.*pose|pose.*annotation')

    def hair_compatibility_fixture(self):
        # This generic two-pixel design ID is opaque; its category is hair.
        old_root, new_root = 'parts/top/top/', 'parts/hair/top/'
        (self.lib / new_root).parent.mkdir(parents=True, exist_ok=True)
        shutil.move(self.lib / old_root, self.lib / new_root)
        def recategorize(value):
            if isinstance(value, str): return value.replace(old_root, new_root)
            if isinstance(value, dict): return {k: recategorize(v) for k, v in value.items()}
            if isinstance(value, list): return [recategorize(v) for v in value]
            return value
        self.recipe = recategorize(self.recipe)
        self.adaptation = recategorize(self.adaptation)
        self.annotations = recategorize(self.annotations)
        self.namespace = self.namespace.replace(old_root, new_root)
        self.annotation = self.write(self.annotation_path, self.annotations)
        for view in self.adaptation['views']: view['source_pose']['document'] = self.annotation
        for mapping in self.adaptation['mappings']: mapping['target_pose']['document'] = self.annotation
        self.recipe['slots'].pop('top')
        self.recipe['slots']['hair'] = self.write('parts/hair/top/revisions/r002/design.json', {'design_id': 'top', 'category': 'hair', 'revision': 'r002'})
        for clip in self.recipe['clips']:
            for frame in clip['frames']: frame['layers'][1]['slot'] = 'hair'
        ref = self.write(self.namespace + '/compatibility/source-fit.json', {
            'kind': 'fixture-compatibility-reference', 'schema_version': 1,
            'hair_identity_sha256': '0'*64, 'hat_identity_sha256': '1'*64})
        self.adaptation['views'][0]['compatibility'] = ref
        self.recipe['adaptations'] = {'hair': self.write(self.namespace+'/views.json', self.adaptation)}
        self.save()
        return ref

    def test_optional_hair_compatibility_reference_is_a_real_dependency_without_core_parsing(self):
        ref = self.hair_compatibility_fixture()
        value = validate(self.repo, self.path)
        self.assertIn(ref['file'], value.dependencies)
        output = self.repo/'coastal-hair-compatibility-ref'
        build.construct(self.repo, self.path, output); build.verify(self.repo, output)
        (self.lib/ref['file']).write_text('{}')
        with self.assertRaisesRegex(ValueError, 'SHA|stale'):
            build.verify(self.repo, output)

    def test_hair_compatibility_reference_has_its_own_adaptation_namespace_and_shape(self):
        self.hair_compatibility_fixture()
        wrong = self.write('parts/hair/other/test/motion/r002/compatibility/fit.json', {'probe': True})
        self.adaptation['views'][0]['compatibility'] = wrong
        self.recipe['adaptations']['hair'] = self.write(self.namespace+'/views.json', self.adaptation); self.save()
        with self.assertRaisesRegex(ValueError, 'namespace'):
            validate(self.repo, self.path)
        self.adaptation['views'][0]['compatibility'] = []
        self.recipe['adaptations']['hair'] = self.write(self.namespace+'/views.json', self.adaptation); self.save()
        with self.assertRaisesRegex(ValueError, 'fields'):
            validate(self.repo, self.path)

    def test_compatibility_reference_is_not_an_untyped_field_on_other_slots(self):
        ref = self.write(self.namespace+'/compatibility/not-hair.json', {'probe': True})
        self.adaptation['views'][0]['compatibility'] = ref
        self.rejected('fields')


if __name__ == '__main__':
    unittest.main()
