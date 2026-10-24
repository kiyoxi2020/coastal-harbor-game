"""Synthetic pixel fixtures only; never character artwork."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from PIL import Image

SCRIPT = Path(__file__).with_name('compose.py')
spec = importlib.util.spec_from_file_location('motion_compose', SCRIPT) if SCRIPT.exists() else None
module = importlib.util.module_from_spec(spec) if spec else None
if spec:
    spec.loader.exec_module(module)


class ComposeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='coastal-motion-', dir='/private/tmp')
        self.root = Path(self.tmp.name)
        (self.root / 'parts').mkdir()
        # Full skin, an opaque shirt patch, a front hand and a translucent edge.
        Image.new('RGBA', (4, 4), (200, 100, 50, 255)).save(self.root / 'parts/skin.png')
        Image.new('RGBA', (1, 1), (0, 80, 200, 255)).save(self.root / 'parts/shirt.png')
        Image.new('RGBA', (1, 1), (250, 150, 100, 255)).save(self.root / 'parts/hand.png')
        Image.new('RGBA', (1, 1), (90, 30, 180, 128)).save(self.root / 'parts/edge.png')
        mask = Image.new('L', (512, 768))
        mask.putpixel((2, 2), 255)
        mask.save(self.root / 'skin-mask.png')
        layers = [
            {'id': 'skin', 'source': 'parts/skin.png', 'offset_px': [0, 0], 'hide_mask': 'skin-mask.png'},
            {'id': 'shirt', 'source': 'parts/shirt.png', 'offset_px': [1, 1]},
            {'id': 'hand_front', 'source': 'parts/hand.png', 'offset_px': [2, 2]},
            {'id': 'transparent_edge', 'source': 'parts/edge.png', 'offset_px': [10, 10]},
        ]
        self.data = {
            'schema_version': 1, 'canvas_px': [512, 768], 'root_anchor_px': [256, 708],
            'display_scale': 0.2371134,
            'frames': [{'pose_id': f'walk_w_{i}', 'duration_ms': 160} for i in range(4)],
            'recipes': {name: {'frames': [{'layers': copy.deepcopy(layers)} for _ in range(4)]} for name in ('A', 'B')},
        }

    def tearDown(self):
        self.tmp.cleanup()

    def run_compose(self, data=None):
        self.assertIsNotNone(module, 'compose.py must implement the requested compositor')
        path = self.root / 'motion.json'
        path.write_text(json.dumps(self.data if data is None else data))
        return module.compose(path)

    def rejected(self, mutate):
        mutate(self.data)
        self.assertIsNotNone(module, 'compose.py must exist before rejection can be tested')
        with self.assertRaises(ValueError):
            self.run_compose()
        self.assertFalse((self.root / 'baked').exists(), 'validation must finish before export')

    def test_mask_targets_only_skin_foreground_hand_survives(self):
        self.run_compose()
        image = Image.open(self.root / 'baked/A_0.png')
        self.assertEqual(image.getpixel((2, 2)), (250, 150, 100, 255))
        self.assertEqual(image.getpixel((1, 1)), (0, 80, 200, 255))
        self.assertEqual(image.getpixel((3, 3)), (200, 100, 50, 255))

    def test_mask_hides_underlying_skin_and_preserves_single_alpha_edge(self):
        for recipe in self.data['recipes'].values():
            for frame in recipe['frames']:
                frame['layers'] = [layer for layer in frame['layers'] if layer['id'] != 'hand_front']
        self.run_compose()
        image = Image.open(self.root / 'baked/A_0.png')
        self.assertEqual(image.getpixel((2, 2))[3], 0)
        self.assertEqual(image.getpixel((10, 10)), (90, 30, 180, 128))

    def test_shared_source_retains_all_pose_mappings_and_hashes(self):
        result = self.run_compose()
        saved = json.loads((self.root / 'baked/export-manifest.json').read_text())
        self.assertEqual(result, saved)
        self.assertEqual(len(saved['recipes']['A']['frames']), 4)
        self.assertEqual(len(saved['inputs']), 6)  # motion + four textures + one mask
        self.assertIn('compose.py', saved['tools'])
        for item in saved['inputs'].values():
            self.assertEqual(item['sha256'], hashlib.sha256((self.root / item['path']).read_bytes()).hexdigest())
        for recipe in saved['recipes'].values():
            for i, frame in enumerate(recipe['frames']):
                self.assertEqual(frame['pose_id'], f'walk_w_{i}')
                self.assertEqual(frame['layers'][0]['source'], 'parts/skin.png')
                self.assertEqual(frame['layers'][0]['hide_mask'], 'skin-mask.png')
                self.assertEqual(frame['sha256'], hashlib.sha256((self.root / 'baked' / frame['file']).read_bytes()).hexdigest())

    def test_source_root_resolves_when_baked_elsewhere(self):
        motion = self.root / 'motion.json'
        motion.write_text(json.dumps(self.data))
        destination = self.root / 'nested' / 'export'
        result = module.compose(motion, destination)
        self.assertEqual((destination / result['source_root']).resolve(), self.root)

    def test_missing_frame_rejected(self):
        self.rejected(lambda d: d['recipes']['B']['frames'].pop())

    def test_unknown_pose_rejected(self):
        self.rejected(lambda d: d['frames'][1].update(pose_id='walk_e_1'))

    def test_duplicate_pose_rejected(self):
        self.rejected(lambda d: d['frames'][1].update(pose_id='walk_w_0'))

    def test_missing_source_rejected(self):
        self.rejected(lambda d: d['recipes']['A']['frames'][0]['layers'][0].update(source='missing.png'))

    def test_missing_mask_rejected(self):
        self.rejected(lambda d: d['recipes']['A']['frames'][0]['layers'][0].update(hide_mask='missing.png'))

    def test_out_of_bounds_source_rejected(self):
        self.rejected(lambda d: d['recipes']['A']['frames'][0]['layers'][0].update(offset_px=[510, 0]))

    def test_fractional_and_negative_offsets_rejected(self):
        for offset in ([0.5, 0], [-1, 0], [True, 0]):
            data = copy.deepcopy(self.data)
            data['recipes']['A']['frames'][0]['layers'][0]['offset_px'] = offset
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                self.run_compose(data)

    def test_invalid_duration_rejected(self):
        for value in (0, -1, 1.5, True):
            data = copy.deepcopy(self.data)
            data['frames'][0]['duration_ms'] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.run_compose(data)

    def test_invalid_scale_rejected(self):
        for value in (0, -1, float('nan'), float('inf'), True, '0.2'):
            data = copy.deepcopy(self.data)
            data['display_scale'] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.run_compose(data)

    def test_wrong_mask_mode_or_size_rejected(self):
        for mode, size in [('RGB', (512, 768)), ('L', (4, 4))]:
            Image.new(mode, size).save(self.root / 'bad-mask.png')
            data = copy.deepcopy(self.data)
            data['recipes']['A']['frames'][0]['layers'][0]['hide_mask'] = 'bad-mask.png'
            with self.subTest(mode=mode, size=size), self.assertRaises(ValueError):
                self.run_compose(data)

    def test_absolute_or_parent_paths_rejected(self):
        for source in ('../outside.png', '/private/tmp/outside.png'):
            data = copy.deepcopy(self.data)
            data['recipes']['A']['frames'][0]['layers'][0]['source'] = source
            with self.subTest(source=source), self.assertRaises(ValueError):
                self.run_compose(data)

    def test_bad_canvas_anchor_or_recipe_rejected(self):
        for key, value in [('canvas_px', [0, 768]), ('root_anchor_px', [513, 708]), ('recipes', {'A': self.data['recipes']['A']})]:
            data = copy.deepcopy(self.data)
            data[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.run_compose(data)


if __name__ == '__main__':
    unittest.main()
