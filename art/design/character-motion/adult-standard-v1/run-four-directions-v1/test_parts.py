from pathlib import Path
import hashlib,json,unittest
from PIL import Image,ImageChops
from build_parts import compose,reflect
from check_garments import holes
ROOT=Path(__file__).resolve().parent
M=json.loads((ROOT/'parts-manifest.json').read_text())
G=json.loads((ROOT/'run-garments.json').read_text())
class PartTests(unittest.TestCase):
    def test_all_recorded_dependencies(self):
        for manifest in [M,G]:
            for p,digest in manifest['inputs'].items():
                with self.subTest(path=p):self.assertEqual(hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),digest)
    def test_same_pose_layer_recomposition(self):
        for g in ['A','B']:
            for f in M['recipes'][g]['frames']:
                seed=Image.open(ROOT/f'registered/{f["pose_id"]}.png').convert('RGBA')
                actual=compose(f['layers'],seed);bake=Image.open(ROOT/f['file']).convert('RGBA')
                self.assertEqual(actual.tobytes(),bake.tobytes(),(g,f['pose_id']))
    def test_A_reconstructs_original_RGBA(self):
        for f in M['recipes']['A']['frames']:
            original=Image.open(ROOT/f'registered/{f["pose_id"]}.png').convert('RGBA')
            baked=Image.open(ROOT/f['file']).convert('RGBA')
            self.assertEqual(original.tobytes(),baked.tobytes(),f['pose_id'])
    def test_B_west_copy_and_east_whole_frame_reflection(self):
        for i in range(4):
            original=Image.open(ROOT.parent/f'run-west-proof-v1/baked/B_{i}.png').convert('RGBA')
            self.assertEqual(original.tobytes(),Image.open(ROOT/f'baked/B_west_{i}.png').convert('RGBA').tobytes())
            self.assertEqual(reflect(original).tobytes(),Image.open(ROOT/f'baked/B_east_{i}.png').convert('RGBA').tobytes())
    def test_north_B_noneditable_body_pixels_unchanged(self):
        for i in range(4):
            a=Image.open(ROOT/f'registered/run_north_{i}.png').convert('RGBA');b=Image.open(ROOT/f'baked/B_north_{i}.png').convert('RGBA');mask=Image.open(ROOT/f'masks/run_north_{i}_B_editable.png').convert('L')
            delta=ImageChops.difference(a,b);outside=ImageChops.invert(mask)
            self.assertFalse(any(ImageChops.multiply(channel,outside).getbbox() for channel in delta.split()))
    def test_quality_gate_rejects_actual_north_holes(self):
        for i in range(4):self.assertGreater(len(holes(Image.open(ROOT/f'baked/B_north_{i}.png').convert('RGBA'))),0)
        self.assertEqual(set(G['recipes']['B']),{'west','east'})
        self.assertNotIn('north',G['recipes']['B']);self.assertNotIn('south',G['recipes']['B'])
    def test_no_local_part_placement_or_false_acceptance(self):
        for g in M['recipes'].values():
            for f in g['frames']:
                for l in f['layers']:self.assertEqual(l['placement'],{'mode':'full_frame','offset_px':[0,0]})
        self.assertFalse(M['user_accepted']);self.assertFalse(G['user_accepted'])
if __name__=='__main__':unittest.main()
