"""Contract tests for truthful registered garment source preprocessing."""
import copy
import hashlib
import importlib
import json
import math
from pathlib import Path
import tempfile
import unittest

from PIL import Image


class RegisteredSourceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='coastal-registered-test-', dir='/private/tmp')
        self.root = Path(self.temp.name)
        self.lib = self.root / 'art/characters'
        self.lib.mkdir(parents=True)
        self.output = self.root / 'coastal-output'
        self.pose_id = 'suit_walk_west_0'
        self.body = Image.new('RGBA', (8, 12))
        for y in range(2, 10):
            for x in range(2, 7):
                self.body.putpixel((x, y), (x * 10, y * 10, 70, 255))
        raw = self.image('sources/body/originals/raw.png', self.body)
        # Independently sample the specified body mapping, without using PIL affine.
        canonical = self.sample(self.body, (6, 7), 2, -2, 0)
        canonical_ref = self.image('templates/adult/motions/body/actions/walk/r001/west/body.png', canonical)
        self.pose_path = 'templates/adult/motions/body/actions/walk/r001/west/poses.json'
        self.poses = {'template_id': 'adult', 'action_id': 'walk', 'direction': 'west', 'variants': {
            'visible': {'canvas_px': [6, 7], 'root_anchor_px': [3, 5], 'display_scale': 1.0,
                        'frames': [{'pose_id': self.pose_id, 'duration_ms': 53, **canonical_ref}]}}}
        pose_ref = self.document(self.pose_path, self.poses)
        prompt = self.document('sources/body/prompts/raw.json', {'prompt': 'fixture'})
        self.registration = {'kind': 'coastal-character-source-atlas-plan-v1', 'schema_version': 1,
            'resource_root': 'art/characters', 'source_id': 'body', 'revision': 'r001',
            'cell_px': [6, 7], 'root_px': [3, 5], 'rows': ['north', 'west', 'south', 'east'],
            'frames': [{'representation': 'body', 'action': 'walk', 'direction': 'west',
                        'frame_index': 0, 'pose_id': self.pose_id, 'duration_ms': 53,
                        'source': {**raw, 'size_px': [8, 12], 'box_px': [0, 0, 8, 12]},
                        'source_root_px': [4, 10], 'scale': [1, 2], 'authoring_inputs': [prompt]}]}
        registration_ref = self.document('sources/body/packing/r001.json', self.registration)
        self.material = Image.new('RGBA', (6, 9))
        colors = [(11, 22, 33, 255), (44, 55, 66, 254), (77, 88, 99, 128), (101, 102, 103, 0)]
        for y in range(9):
            for x in range(6):
                self.material.putpixel((x, y), colors[[0, 0, 1, 2, 2, 3][x]])
        source = self.image('sources/worn/originals/raw.png', self.material)
        self.mask = Image.new('L', (6, 9), 255)
        owner = self.image('sources/worn/ownership/raw.png', self.mask)
        self.plan = {'kind': 'coastal-registered-source-preparation-plan-v1', 'schema_version': 1,
            'resource_root': 'art/characters', 'source_id': 'prepared-r001',
            'registration_plan': registration_ref, 'authoring_inputs': [prompt],
            'frames': [{'pose_id': self.pose_id, 'source': source, 'ownership': owner,
                        'box_px': [0, 0, 6, 9], 'density_ratio': [3, 4],
                        'canonical_poses': pose_ref, 'variant': 'visible'}]}
        self.plan_path = self.lib / 'sources/worn/preparation/r001.json'
        self.write_plan()

    def tearDown(self):
        self.temp.cleanup()

    @staticmethod
    def sample(source, size, inverse, ox, oy):
        result = Image.new(source.mode, size)
        for y in range(size[1]):
            for x in range(size[0]):
                sx, sy = math.floor((x + .5) * inverse + ox), math.floor((y + .5) * inverse + oy)
                if 0 <= sx < source.width and 0 <= sy < source.height:
                    result.putpixel((x, y), source.getpixel((sx, sy)))
        return result

    def ref(self, relative):
        return {'file': relative, 'sha256': hashlib.sha256((self.lib / relative).read_bytes()).hexdigest()}

    def image(self, relative, image):
        path = self.lib / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        image.save(path)
        return self.ref(relative)

    def document(self, relative, data):
        path = self.lib / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data))
        return self.ref(relative)

    def write_plan(self):
        self.document(self.plan_path.relative_to(self.lib).as_posix(), self.plan)

    def module(self):
        path = Path(__file__).parents[1] / 'prepare_registered_source.py'
        self.assertTrue(path.exists(), 'registered source preparation implementation is missing')
        return importlib.import_module('tools.characters.prepare_registered_source')

    def build(self):
        self.write_plan()
        return self.module().build(self.root, self.plan_path, self.output)

    def rejected(self):
        with self.assertRaises(ValueError):
            self.build()
        self.assertFalse(self.output.exists())

    def test_sparse_west_build_preserves_source_rgba_and_fractional_registration(self):
        manifest = self.build()
        expected = self.sample(self.material, (6, 7), 1.5, -1.5, 0)
        for folder in ('materials', 'textures'):
            with Image.open(self.output / folder / f'{self.pose_id}.png') as actual:
                self.assertEqual(actual.tobytes(), expected.tobytes())
                self.assertEqual([actual.getpixel((x, 1))[3] for x in (1, 2, 3, 4)], [255, 254, 128, 0])
                self.assertEqual(actual.getpixel((4, 1)), (101, 102, 103, 0))
        self.assertEqual(manifest['frames'][0]['material_root_px'], [[3, 1], [15, 2]])
        self.assertFalse(manifest['release_eligible'])
        source = json.loads((self.output / 'source.json').read_text())
        self.assertFalse(source['accepted'])
        self.assertFalse(source['runtime_eligible'])
        self.assertNotIn('source_view_pose', source)
        self.assertIn('sources/body/prompts/raw.json', manifest['inputs'])
        self.module().verify(self.root, self.output)

    def test_binary_owner_selects_without_alpha_multiplication(self):
        self.mask.putpixel((2, 2), 0)
        self.plan['frames'][0]['ownership'] = self.image('sources/worn/ownership/raw.png', self.mask)
        self.build()
        with Image.open(self.output / 'textures' / f'{self.pose_id}.png') as tex:
            self.assertEqual(tex.getpixel((2, 1)), (0, 0, 0, 0))
            self.assertEqual(tex.getpixel((3, 1)), (77, 88, 99, 128))

    def test_bad_density_aspect_and_unreduced_ratios(self):
        for ratio, box in [([1, 1], [0, 0, 6, 9]), ([6, 8], [0, 0, 6, 9]), ([3, 4], [0, 0, 5, 9]), ([0, 1], [0, 0, 6, 9])]:
            with self.subTest(ratio=ratio, box=box):
                self.plan['frames'][0]['density_ratio'] = ratio
                self.plan['frames'][0]['box_px'] = box
                self.rejected()

    def test_nonbinary_wrong_mode_or_empty_mask(self):
        for mask in [Image.new('L', (6, 9), 128), Image.new('RGBA', (6, 9)), Image.new('L', (6, 9))]:
            with self.subTest(mode=mask.mode, pixel=mask.getpixel((0, 0))):
                self.plan['frames'][0]['ownership'] = self.image('sources/worn/ownership/raw.png', mask)
                self.rejected()

    def test_unknown_keys_and_arbitrary_fitting_refused(self):
        for scope, key in [(self.plan, 'extra'), (self.plan['frames'][0], 'offset_px'), (self.plan['frames'][0]['source'], 'scale')]:
            scope[key] = [0, 0]
            self.rejected()
            del scope[key]

    def test_duplicate_and_missing_pose_refused(self):
        self.plan['frames'].append(copy.deepcopy(self.plan['frames'][0]))
        self.rejected()
        self.plan['frames'].pop()
        self.plan['frames'][0]['pose_id'] = 'absent'
        self.rejected()

    def test_registration_duplicate_body_pose_refused(self):
        self.registration['frames'].append(copy.deepcopy(self.registration['frames'][0]))
        self.plan['registration_plan'] = self.document('sources/body/packing/r001.json', self.registration)
        self.rejected()

    def test_wrong_sha_refused(self):
        self.plan['frames'][0]['source']['sha256'] = '0' * 64
        self.rejected()

    def test_changed_canonical_even_with_updated_sha_refused(self):
        frame = self.poses['variants']['visible']['frames'][0]
        frame.update(self.image(frame['file'], Image.new('RGBA', (6, 7), 'red')))
        self.plan['frames'][0]['canonical_poses'] = self.document(self.pose_path, self.poses)
        self.rejected()

    def test_pose_template_action_direction_and_duplicate_refused(self):
        for field, value in [('template_id', 'other'), ('action_id', 'run'), ('direction', 'east')]:
            old = self.poses[field]
            self.poses[field] = value
            self.plan['frames'][0]['canonical_poses'] = self.document(self.pose_path, self.poses)
            self.rejected()
            self.poses[field] = old
        frames = self.poses['variants']['visible']['frames']
        frames.append(copy.deepcopy(frames[0]))
        self.plan['frames'][0]['canonical_poses'] = self.document(self.pose_path, self.poses)
        self.rejected()

    def test_cropping_declared_owned_support_refused(self):
        self.registration['root_px'] = [0, 5]
        self.poses['variants']['visible']['root_anchor_px'] = [0, 5]
        canonical = self.sample(self.body, (6, 7), 2, 4, 0)
        f = self.poses['variants']['visible']['frames'][0]
        f.update(self.image(f['file'], canonical))
        self.plan['frames'][0]['canonical_poses'] = self.document(self.pose_path, self.poses)
        self.plan['registration_plan'] = self.document('sources/body/packing/r001.json', self.registration)
        self.rejected()

    def test_output_overwrite_refused(self):
        self.output.mkdir()
        with self.assertRaises(ValueError):
            self.build()

    def test_symlink_file_and_ancestor_refused(self):
        path = self.lib / self.plan['frames'][0]['source']['file']
        original = path.with_suffix('.original.png')
        path.rename(original)
        path.symlink_to(original)
        self.rejected()
        path.unlink()
        original.rename(path)
        folder = path.parent
        moved = folder.with_name('moved')
        folder.rename(moved)
        folder.symlink_to(moved, target_is_directory=True)
        self.rejected()

    def test_plan_and_output_ancestor_symlink_refused(self):
        original = self.plan_path
        alias = original.with_name('alias.json')
        alias.symlink_to(original)
        self.plan_path = alias
        with self.assertRaises(ValueError):
            self.module().build(self.root, alias, self.output)
        self.plan_path = original
        directory = self.root / 'alias'
        directory.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.module().build(self.root, original, directory / 'coastal-output')

    def test_mask_size_source_mode_and_declared_body_size_refused(self):
        frame = self.plan['frames'][0]
        original_owner = frame['ownership']
        frame['ownership'] = self.image('sources/worn/ownership/small.png', Image.new('L', (5, 9), 255))
        self.rejected()
        frame['ownership'] = original_owner
        original_source = frame['source']
        frame['source'] = self.image('sources/worn/originals/rgb.png', self.material.convert('RGB'))
        self.rejected()
        frame['source'] = original_source
        self.registration['frames'][0]['source']['size_px'] = [9, 12]
        self.plan['registration_plan'] = self.document('sources/body/packing/r001.json', self.registration)
        self.rejected()

    def test_empty_body_mapping_refused_even_when_canonical_is_empty(self):
        body = self.registration['frames'][0]
        body['source'].update(self.image(body['source']['file'], Image.new('RGBA', (8, 12))))
        canonical = self.poses['variants']['visible']['frames'][0]
        canonical.update(self.image(canonical['file'], Image.new('RGBA', (6, 7))))
        self.plan['registration_plan'] = self.document('sources/body/packing/r001.json', self.registration)
        self.plan['frames'][0]['canonical_poses'] = self.document(self.pose_path, self.poses)
        self.rejected()

    def test_wrong_raw_body_sha_and_body_authoring_sha_refused(self):
        body = self.registration['frames'][0]
        for ref in (body['source'], body['authoring_inputs'][0]):
            original = ref['sha256']
            ref['sha256'] = '0' * 64
            self.plan['registration_plan'] = self.document('sources/body/packing/r001.json', self.registration)
            self.rejected()
            ref['sha256'] = original

    def test_empty_excessive_frames_and_bad_identifier_refused(self):
        original = self.plan['frames']
        for frames in ([], original * 257):
            self.plan['frames'] = frames
            self.rejected()
        self.plan['frames'] = original
        self.plan['source_id'] = '../escape'
        self.rejected()

    def test_outside_plan_and_wrong_source_output_identity_refused(self):
        outside = self.root / 'plan.json'
        outside.write_text(json.dumps(self.plan))
        with self.assertRaises(ValueError):
            self.module().build(self.root, outside, self.output)
        for output in (self.lib / 'sources/other', Path('/private/tmp')):
            with self.assertRaises(ValueError):
                self.module().build(self.root, self.plan_path, output)

    def test_per_pose_source_root_trajectory_is_copied(self):
        pose = 'suit_walk_west_1'
        body = copy.deepcopy(self.registration['frames'][0])
        body.update(pose_id=pose, frame_index=1, source_root_px=[5, 10])
        self.registration['frames'].append(body)
        canonical = self.sample(self.body, (6, 7), 2, -1, 0)
        canonical_ref = self.image('templates/adult/motions/body/actions/walk/r001/west/body1.png', canonical)
        self.poses['variants']['visible']['frames'].append({'pose_id': pose, 'duration_ms': 53, **canonical_ref})
        pose_ref = self.document(self.pose_path, self.poses)
        self.plan['frames'][0]['canonical_poses'] = pose_ref
        second = copy.deepcopy(self.plan['frames'][0]); second['pose_id'] = pose
        self.plan['frames'].append(second)
        self.plan['registration_plan'] = self.document('sources/body/packing/r001.json', self.registration)
        manifest = self.build()
        self.assertEqual(manifest['frames'][1]['material_root_px'], [[15, 4], [15, 2]])
        with Image.open(self.output / 'materials' / f'{pose}.png') as actual:
            self.assertEqual(actual.tobytes(), self.sample(self.material, (6, 7), 1.5, -.75, 0).tobytes())
        self.module().verify(self.root, self.output)

    def test_verify_rejects_plan_edit_even_if_manifest_plan_sha_forged(self):
        self.build()
        self.plan['authoring_inputs'] = []
        self.write_plan()
        path = self.output / 'manifest.json'
        manifest = json.loads(path.read_text())
        manifest['plan']['sha256'] = hashlib.sha256(self.plan_path.read_bytes()).hexdigest()
        path.write_text(json.dumps(manifest))
        with self.assertRaises(ValueError):
            self.module().verify(self.root, self.output)

    def test_verify_rejects_extra_empty_directory(self):
        self.build()
        (self.output / 'untracked').mkdir()
        with self.assertRaises(ValueError):
            self.module().verify(self.root, self.output)

    def test_verify_detects_parent_tamper(self):
        self.build()
        (self.lib / self.plan['frames'][0]['source']['file']).write_bytes(b'changed')
        with self.assertRaises(ValueError):
            self.module().verify(self.root, self.output)

    def test_verify_detects_forged_output_hashes(self):
        self.build()
        path = self.output / 'textures' / f'{self.pose_id}.png'
        Image.new('RGBA', (6, 7), 'red').save(path)
        manifest_path = self.output / 'manifest.json'
        manifest = json.loads(manifest_path.read_text())
        for item in manifest['outputs']:
            if item['file'] == f'textures/{self.pose_id}.png':
                item['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
                item['rgba_sha256'] = hashlib.sha256(Image.open(path).tobytes()).hexdigest()
        manifest_path.write_text(json.dumps(manifest))
        with self.assertRaises(ValueError):
            self.module().verify(self.root, self.output)

    def test_verify_detects_extra_missing_source_or_symlink(self):
        self.build()
        extra = self.output / 'extra.txt'
        extra.write_text('extra')
        with self.assertRaises(ValueError):
            self.module().verify(self.root, self.output)
        extra.unlink()
        source = self.output / 'source.json'
        old = source.read_bytes()
        source.write_text('{}')
        with self.assertRaises(ValueError):
            self.module().verify(self.root, self.output)
        source.write_bytes(old)
        image = self.output / 'materials' / f'{self.pose_id}.png'
        image.unlink()
        with self.assertRaises(ValueError):
            self.module().verify(self.root, self.output)
        image.symlink_to(self.lib / self.plan['frames'][0]['source']['file'])
        with self.assertRaises(ValueError):
            self.module().verify(self.root, self.output)


if __name__ == '__main__':
    unittest.main()
