"""Run-part artifact acceptance: exact A, shared body, real hidden-source provenance."""
from pathlib import Path
import hashlib
import json
import unittest
from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parent

class RunPartsAcceptance(unittest.TestCase):
    def manifest(self):
        path = ROOT / 'parts-manifest.json'
        self.assertTrue(path.is_file(), 'Run layered build must publish its own manifest')
        return json.loads(path.read_text())

    def test_run_identity_and_actual_input_hashes(self):
        data = self.manifest()
        self.assertEqual(data['action_id'], 'run')
        self.assertEqual(data['direction'], 'west')
        for path, expected in data['inputs'].items():
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(), expected, path)

    def test_A_reconstruction_retains_all_approved_RGBA(self):
        self.manifest()
        for i in range(4):
            expected = Image.open(ROOT/f'registered/run_west_{i}.png').convert('RGBA')
            actual = Image.open(ROOT/f'baked/A_{i}.png').convert('RGBA')
            self.assertEqual(actual.tobytes(), expected.tobytes(), f'A frame {i} must preserve exact RGBA')

    def test_B_only_changes_declared_clothing_surfaces(self):
        self.manifest()
        for i in range(4):
            a = Image.open(ROOT/f'baked/A_{i}.png').convert('RGBA')
            b = Image.open(ROOT/f'baked/B_{i}.png').convert('RGBA')
            allowed = Image.open(ROOT/f'masks/B_editable_{i}.png').convert('L')
            delta = ImageChops.difference(a,b)
            outside = Image.new('L',a.size)
            for channel in delta.split():
                outside=ImageChops.lighter(outside,ImageChops.multiply(channel,ImageChops.invert(allowed)))
            self.assertIsNone(outside.getbbox(), f'B frame {i} changes face/hands/pants/shoes')
            self.assertNotEqual(a.tobytes(), b.tobytes(), 'B must contain actual distinct garment')

    def test_shared_A_hands_keep_RGB_and_alpha_in_B(self):
        self.manifest()
        for i in range(4):
            a=Image.open(ROOT/f'baked/A_{i}.png').convert('RGBA')
            b=Image.open(ROOT/f'baked/B_{i}.png').convert('RGBA')
            hands=Image.open(ROOT/f'masks/protected_hands_{i}.png').convert('L')
            for channel in ImageChops.difference(a,b).split():
                self.assertIsNone(ImageChops.multiply(channel,hands).getbbox(), f'Hand source modified in frame {i}')

    def test_complete_torsos_have_independent_GPT_hidden_source(self):
        data = self.manifest()
        for garment in ('A','B'):
            for record in data['recipes'][garment]['frames']:
                self.assertEqual(record['pose_id'].split('_')[0], 'run')
                torso = next(x for x in record['layers'] if x['id']=='torso')
                self.assertTrue(torso['hidden_source'].startswith('sources/run-torso-'))
                self.assertIn(torso['hidden_source'], data['inputs'])
                self.assertEqual(torso['placement'], {'mode':'full_frame','offset_px':[0,0]})
                complete = Image.open(ROOT/torso['source']).convert('RGBA')
                hidden = Image.open(ROOT/torso['hidden_mask']).convert('L')
                self.assertIsNotNone(ImageChops.multiply(complete.getchannel('A'),hidden).getbbox(), 'Complete torso needs real hidden cloth')

    def test_actual_pants_pixels_remain_body_owned(self):
        # Observed brown trouser pixels, independently sampled below the cream hem.
        samples = {2: [(297,512),(293,514),(301,514)], 3: [(200,490),(207,493),(214,496)]}
        for i, points in samples.items():
            owner = Image.open(ROOT/f'masks/ownership_{i}_body_base.png').convert('L')
            for point in points:
                self.assertEqual(owner.getpixel(point),255,f'Actual pants at {i}/{point} must not be extracted as shirt outline')

    def test_B_waist_interface_has_no_new_transparent_holes(self):
        self.manifest()
        bands=[(210,501,327,515),(230,482,320,498),(205,501,302,515),(185,481,287,501)]
        for i,box in enumerate(bands):
            a=Image.open(ROOT/f'baked/A_{i}.png').getchannel('A').crop(box)
            b=Image.open(ROOT/f'baked/B_{i}.png').getchannel('A').crop(box)
            missing=ImageChops.multiply(a.point(lambda x:255 if x>=240 else 0), b.point(lambda x:255 if x<128 else 0))
            self.assertIsNone(missing.getbbox(),f'New transparent waist gap in B frame {i}')

if __name__ == '__main__':
    unittest.main()
