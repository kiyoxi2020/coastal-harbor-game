"""Source preparation, not character composition or art acceptance."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pack_sources


class SourcePackingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='coastal-source-pack-', dir='/private/tmp')
        self.repo = Path(self.temp.name)
        self.lib = self.repo / 'art/characters'
        self.source = self.lib / 'sources/test/originals.png'
        self.source.parent.mkdir(parents=True)
        image = Image.new('RGBA', (4, 4), (9, 8, 7, 0))
        for xy, color in [((0, 0), (210, 60, 80, 128)), ((1, 0), (23, 45, 67, 0)),
                          ((0, 1), (30, 40, 50, 255)), ((1, 1), (50, 60, 70, 64)),
                          ((2, 2), (10, 220, 30, 255)), ((3, 3), (110, 120, 130, 128))]:
            image.putpixel(xy, color)
        image.save(self.source)
        self.plan = {'kind': 'coastal-character-source-atlas-plan-v1', 'schema_version': 1,
                     'resource_root': 'art/characters', 'source_id': 'test', 'revision': 'r001',
                     'cell_px': [4, 4], 'root_px': [1, 2],
                     'rows': ['north', 'west', 'south', 'east'], 'frames': []}
        for direction in self.plan['rows']:
            for index in range(2):
                self.plan['frames'].append({'representation': 'body', 'action': 'wave',
                    'direction': direction, 'frame_index': index,
                    'pose_id': f'wave_{direction}_{index}', 'duration_ms': 50 + index,
                    'source': {'file': 'sources/test/originals.png',
                               'sha256': hashlib.sha256(self.source.read_bytes()).hexdigest(),
                               'size_px': [4, 4], 'box_px': [index * 2, index * 2, 2, 2]},
                    'source_root_px': [0, 1], 'scale': [1, 1], 'authoring_inputs': []})
        self.path = self.lib / 'sources/test/packing/r001.json'
        self.output = self.repo / 'packed'
        self.save()

    def tearDown(self):
        self.temp.cleanup()

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.plan))

    def pack(self):
        self.save()
        return pack_sources.pack(self.repo, self.path, self.output)

    def test_regions_row_order_and_soft_alpha_keep_original_rgba(self):
        original = self.source.read_bytes()
        manifest = self.pack()
        self.assertEqual(manifest['status'], 'review-only')
        self.assertFalse(manifest['complete_body_archive'])
        with Image.open(self.output / 'atlases/body/wave.png') as atlas:
            self.assertEqual(atlas.size, (8, 16))
            for row in range(4):
                self.assertEqual(atlas.getpixel((1, row * 4 + 1)), (210, 60, 80, 128))
                self.assertEqual(atlas.getpixel((2, row * 4 + 1)), (23, 45, 67, 0))
                self.assertEqual(atlas.getpixel((5, row * 4 + 1)), (10, 220, 30, 255))
        self.assertEqual(self.source.read_bytes(), original)
        self.assertEqual(pack_sources.verify(self.repo, self.output)['artifact_digest'], manifest['artifact_digest'])

    def test_whole_frame_nearest_scale_has_no_interpolation_or_alpha_blending(self):
        self.plan['root_px'] = [0, 0]
        for frame in self.plan['frames']:
            frame['scale'] = [2, 1]
            frame['source_root_px'] = [0, 0]
        self.pack()
        with Image.open(self.output / 'atlases/body/wave.png') as atlas:
            self.assertEqual(atlas.crop((0, 0, 4, 4)).tobytes(),
                             Image.open(self.source).crop((0, 0, 2, 2)).resize((4, 4), Image.Resampling.NEAREST).tobytes())

    def test_rejects_bad_source_and_geometry_before_creating_output(self):
        cases = [('sha', lambda f: f['source'].update(sha256='0' * 64)),
                 ('size', lambda f: f['source'].update(size_px=[9, 9])),
                 ('box', lambda f: f['source'].update(box_px=[3, 3, 2, 2])),
                 ('crop', lambda f: f.update(source_root_px=[2, 2])),
                 ('duration', lambda f: f.update(duration_ms=0)),
                 ('scale', lambda f: f.update(scale=[0, 1])),
                 ('boolean', lambda f: f.update(duration_ms=True)),
                 ('path', lambda f: f['source'].update(file='../escape.png'))]
        baseline = copy.deepcopy(self.plan)
        for name, change in cases:
            with self.subTest(name=name):
                self.plan = copy.deepcopy(baseline)
                change(self.plan['frames'][0])
                with self.assertRaises(ValueError): self.pack()
                self.assertFalse(self.output.exists())

    def test_rejects_missing_direction_frame_duplicate_or_unknown_field(self):
        baseline = copy.deepcopy(self.plan)
        for mutate in [lambda p: p['frames'].pop(),
                       lambda p: p['frames'].append(copy.deepcopy(p['frames'][0])),
                       lambda p: p['frames'][0].update(local_scale=[2, 2])]:
            self.plan = copy.deepcopy(baseline)
            mutate(self.plan)
            with self.assertRaises(ValueError): self.pack()

    def test_existing_output_is_never_overwritten(self):
        self.pack()
        before = (self.output / 'manifest.json').read_bytes()
        with self.assertRaises(ValueError): self.pack()
        self.assertEqual((self.output / 'manifest.json').read_bytes(), before)

    def test_valid_source_anchor_still_cannot_crop_any_nonzero_alpha(self):
        self.plan['root_px'] = [0, 0]
        self.plan['frames'][0]['source_root_px'] = [1, 1]
        with self.assertRaisesRegex(ValueError, 'crop source alpha'): self.pack()
        self.assertFalse(self.output.exists())

    def test_historical_build_can_be_bound_as_authoring_reference(self):
        historical = self.lib / 'builds/reference/frames/pose.png'
        historical.parent.mkdir(parents=True)
        historical.write_bytes(self.source.read_bytes())
        self.plan['frames'][0]['authoring_inputs'] = [{'file': 'builds/reference/frames/pose.png',
            'sha256': hashlib.sha256(historical.read_bytes()).hexdigest()}]
        self.pack()
        pack_sources.verify(self.repo, self.output)

    def test_verify_rebuilds_pixels_even_if_output_hash_was_forged(self):
        self.pack()
        atlas = self.output / 'atlases/body/wave.png'
        Image.new('RGBA', (8, 16), (1, 2, 3, 255)).save(atlas)
        m = self.output / 'manifest.json'
        data = json.loads(m.read_text())
        entry = next(x for x in data['outputs'] if x['file'] == 'atlases/body/wave.png')
        entry['sha256'] = hashlib.sha256(atlas.read_bytes()).hexdigest()
        m.write_text(json.dumps(data))
        with self.assertRaises(ValueError): pack_sources.verify(self.repo, self.output)

    def test_verify_rejects_changed_input_layout_and_extra_files(self):
        self.pack()
        layout = self.output / 'layout.json'
        original = layout.read_bytes()
        layout.write_text('{}')
        with self.assertRaises(ValueError): pack_sources.verify(self.repo, self.output)
        layout.write_bytes(original)
        extra = self.output / 'unexpected.png'; extra.write_bytes(b'not an image')
        with self.assertRaises(ValueError): pack_sources.verify(self.repo, self.output)
        extra.unlink()
        Image.new('RGBA', (4, 4), 'red').save(self.source)
        with self.assertRaises(ValueError): pack_sources.verify(self.repo, self.output)

    def test_verify_rejects_stale_plan(self):
        self.pack()
        self.plan['frames'][0]['duration_ms'] += 1
        self.save()
        with self.assertRaises(ValueError): pack_sources.verify(self.repo, self.output)


if __name__ == '__main__':
    unittest.main()
