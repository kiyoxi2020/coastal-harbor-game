"""Real symmetry-repair regression: preserve unaffected art and whole-frame sources."""
import importlib.util
import hashlib
import json
from pathlib import Path
import unittest
from PIL import Image, ImageChops
ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('symmetry_parts', ROOT/'build_parts.py')
parts = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parts)
REVIEW = json.loads((ROOT/'symmetry-review.json').read_text())

class SymmetryRepairTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = parts.build()

    def test_unaffected_sixteen_poses_remain_byte_identical(self):
        self.assertEqual(len(REVIEW['unchanged_baked_baseline']),32)
        for item in REVIEW['unchanged_baked_baseline']:
            self.assertEqual(hashlib.sha256((ROOT/'baked'/item['file']).read_bytes()).hexdigest(),item['sha256'],item['pose_id']+item['garment'])

    def test_new_b_and_hidden_torso_use_same_whole_frame_registration(self):
        for i in range(4):
            pose = f'walk_east_{i}'
            raw = Image.open(ROOT/'sources/walk-east-b-v2.png').convert('RGBA').crop((i*512,0,(i+1)*512,768))
            aligned = Image.new('RGBA',(512,768)); aligned.alpha_composite(raw,(-8,0))
            self.assertIsNone(ImageChops.difference(aligned,parts.source_frame('B',pose)).getbbox(),pose)
            for garment in ['A','B']:
                self.assertEqual(parts.torso_reference(garment,pose),(f'sources/walk-east-torso-{garment.lower()}-v2.png',i))
            if i in [0,1,3]:
                point=(321,490)
                source=parts.source_frame('B',pose)
                self.assertGreater(source.getpixel(point)[2]-source.getpixel(point)[0],12)
                baked=Image.open(ROOT/'baked'/f'B_{12+i}.png').convert('RGBA')
                self.assertEqual(baked.getpixel(point),source.getpixel(point),(pose,'B long sleeve must cover original A wrist skin'))

    def test_current_sources_and_review_are_actually_hash_bound(self):
        manifest = json.loads((ROOT/'baked/export-manifest.json').read_text())
        for path,expected in REVIEW['new_sources'].items():
            self.assertEqual(manifest['source_contract'].get(path),expected,path)
        self.assertEqual(manifest['source_contract'].get('symmetry-review.json'),hashlib.sha256((ROOT/'symmetry-review.json').read_bytes()).hexdigest())
        self.assertEqual(manifest['actions']['walk']['directions']['east'],[f'walk_east_{i}' for i in range(4)])
        self.assertEqual(manifest['move_policy']['walk'],{'base_world_speed':72,'playback_rate':0.75})

    def test_contact_and_passing_geometry_use_recorded_actual_source_extents(self):
        for i in range(4):
            widths=[]; soles=[]
            for direction in ['west','east']:
                alpha=parts.source_frame('A',f'walk_{direction}_{i}').getchannel('A').point(lambda a:255 if a>=128 else 0)
                box=alpha.crop((0,640,512,768)).getbbox()
                widths.append(box[2]-box[0]);soles.append(box[3]+639)
            self.assertEqual(widths,REVIEW['new_geometry_observation']['lower_band_widths_W_E'][i])
            self.assertEqual(soles,REVIEW['new_geometry_observation']['lowest_opaque_y_W_E'][i])
            self.assertLessEqual(abs(widths[1]-widths[0])/widths[0],.06)

if __name__=='__main__': unittest.main()
