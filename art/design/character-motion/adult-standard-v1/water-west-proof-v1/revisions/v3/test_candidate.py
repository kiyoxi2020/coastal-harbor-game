import unittest,json,hashlib
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parent
class CandidateStructure(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.c=json.loads((ROOT/'candidate.json').read_text())
 def test_full_rgba_preserved_and_no_source_crop(self):
  for f in self.c['frames']:
   source=Image.open(ROOT/f['source']).convert('RGBA');registered=Image.open(ROOT/f['file']).convert('RGBA')
   dx,dy=f['whole_frame_translation_px']
   self.assertGreaterEqual(dx,0);self.assertGreaterEqual(dy,0)
   self.assertLessEqual(dx+source.width,registered.width);self.assertLessEqual(dy+source.height,registered.height)
   expected=Image.new('RGBA',tuple(self.c['canvas_px']));expected.paste(source,(dx,dy))
   self.assertEqual(registered.tobytes(),expected.tobytes())
 def test_actual_dependencies_and_digest(self):
  for name,sha in self.c['inputs'].items():self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),sha,name)
  c=self.c.copy();digest=c.pop('artifact_digest')
  self.assertEqual(hashlib.sha256(json.dumps(c,sort_keys=True,separators=(',',':')).encode()).hexdigest(),digest)
  for f in self.c['frames']:self.assertEqual(hashlib.sha256((ROOT/f['file']).read_bytes()).hexdigest(),f['sha256'])
 def test_pose_coordinate_registration_and_unknowns(self):
  poses=json.loads((ROOT/'poses.json').read_text())['poses']
  self.assertEqual(len(poses),len(self.c['frames']))
  for p,f in zip(poses,self.c['frames']):
   self.assertEqual(p['pose_id'],f['pose_id']);dx,dy=f['whole_frame_translation_px']
   for name,v in p['source_landmarks_px'].items():
    translated=p['registered_landmarks_px'][name]
    if v is None:self.assertIsNone(translated)
    else:self.assertEqual(translated,[v[0]+dx,v[1]+dy])
   self.assertIsNone(p['source_landmarks_px']['hip_joint'])
 def test_proof_cannot_claim_complete_action_or_gameplay(self):
  self.assertFalse(self.c['accepted']);self.assertFalse(self.c['gameplay_available']);self.assertFalse(self.c['modular'])
  self.assertFalse(self.c['loop']);self.assertEqual(self.c['events'],[])
  ids=[]
  for f in self.c['frames']:
   self.assertGreater(f['duration_ms'],0);ids.append(f['sha256'])
  self.assertEqual(len(set(ids)),len(ids))
if __name__=='__main__':unittest.main()
