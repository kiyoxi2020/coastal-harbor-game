"""Structural/source checks. These do not certify motion or user acceptance."""
from pathlib import Path
import hashlib, json, unittest
from PIL import Image, ImageChops

ROOT=Path(__file__).resolve().parent
M=json.loads((ROOT/'candidate.json').read_text())

class CandidateTests(unittest.TestCase):
    def test_complete_directions_and_unique_poses(self):
        self.assertEqual(M['directions'],['south','west','east','north'])
        self.assertEqual(len(M['frames']),16)
        self.assertEqual(len({f['pose_id'] for f in M['frames']}),16)
        for d in M['directions']:
            self.assertEqual([f['pose_id'] for f in M['frames'] if f['direction']==d],[f'run_{d}_{i}' for i in range(4)])

    def test_dependency_hashes_and_safe_paths(self):
        for path,digest in M['inputs'].items():
            with self.subTest(path=path):
                self.assertFalse(Path(path).is_absolute())
                self.assertNotIn('..',Path(path).parts)
                self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),digest)

    def test_canvas_alpha_borders_and_durations(self):
        for f in M['frames']:
            with self.subTest(pose=f['pose_id']):
                im=Image.open(ROOT/f['file']);self.assertEqual(im.mode,'RGBA');self.assertEqual(im.size,(512,768))
                self.assertGreater(f['duration_ms'],0)
                a=im.getchannel('A').point(lambda x:255 if x>=128 else 0)
                x0,y0,x1,y1=a.getbbox()
                self.assertTrue(0<x0<x1<512 and 0<y0<y1<768)
                self.assertEqual(hashlib.sha256((ROOT/f['file']).read_bytes()).hexdigest(),f['sha256'])

    def test_whole_cell_registration_no_redraw_or_resampling(self):
        for d,v in [('south',3),('north',2)]:
            sheet=Image.open(ROOT/f'sources/run-{d}-a-v{v}.png').convert('RGBA')
            self.assertEqual(sheet.size,(2048,768))
            for i in range(4):
                expected=Image.new('RGBA',(512,768));expected.paste(sheet.crop((i*512,0,(i+1)*512,768)),(0,11))
                actual=Image.open(ROOT/f'registered/run_{d}_{i}.png').convert('RGBA')
                self.assertEqual(actual.tobytes(),expected.tobytes())

    def test_west_copy_and_east_reflection_lossless(self):
        for i in range(4):
            west=Image.open(ROOT/f'registered/run_west_{i}.png').convert('RGBA')
            original=ROOT.parent/f'run-west-proof-v1/registered/run_west_{i}.png'
            self.assertEqual((ROOT/f'registered/run_west_{i}.png').read_bytes(),original.read_bytes())
            east=Image.open(ROOT/f'registered/run_east_{i}.png').convert('RGBA')
            recovered=Image.new('RGBA',east.size);recovered.paste(east,(-1,0));recovered=recovered.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            # +1 root registration discards only hidden RGB at alpha0 in x0.
            # No visible or partially transparent source pixel may be lost.
            self.assertEqual(west.getchannel('A').crop((0,0,1,768)).getextrema(),(0,0))
            self.assertEqual(recovered.getchannel('A').tobytes(),west.getchannel('A').tobytes())
            self.assertEqual(recovered.crop((1,0,512,768)).tobytes(),west.crop((1,0,512,768)).tobytes())

    def test_distinct_poses_and_contact_airborne_silhouettes(self):
        for d in M['directions']:
            ims=[Image.open(ROOT/f'registered/run_{d}_{i}.png').convert('RGBA') for i in range(4)]
            self.assertEqual(len({im.tobytes() for im in ims}),4)
            bottom=[im.getchannel('A').point(lambda a:255 if a>=128 else 0).getbbox()[3] for im in ims]
            self.assertTrue(700<=bottom[0]<=712 and 700<=bottom[2]<=712,(d,bottom))
            self.assertTrue(bottom[1]<675 and bottom[3]<675,(d,bottom))
            self.assertTrue(min(bottom[0],bottom[2])-max(bottom[1],bottom[3])>=30,(d,bottom))

    def test_no_acceptance_fabricated(self):
        self.assertEqual(M['status'],'unapproved_complete_frame_proof')
        self.assertEqual(M['phase_map_status'],'candidate contact/flight observations; exact target trajectories and transition mapping not frozen')

    def test_walk_compatibility_dependency(self):
        walk=json.loads((ROOT.parent/'locomotion-v1/baked/export-manifest.json').read_text())
        self.assertEqual(M['walk_artifact_digest'],walk['artifact_digest'])

if __name__=='__main__':unittest.main()
