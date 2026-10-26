import hashlib,json,unittest
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parent
class SouthWaterProof(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  assert (ROOT/'candidate.json').exists(),'Missing candidate: complete registered two-pose artifact must be built'
  cls.c=json.loads((ROOT/'candidate.json').read_text())
 def test_complete_rgba_only_integer_whole_frame_translation(self):
  for f in self.c['frames']:
   source=Image.open(ROOT/f['source']).convert('RGBA');actual=Image.open(ROOT/f['file']).convert('RGBA')
   dx,dy=f['whole_frame_translation_px'];self.assertIs(type(dx),int);self.assertIs(type(dy),int)
   self.assertGreaterEqual(dx,0);self.assertGreaterEqual(dy,0)
   self.assertLessEqual(dx+source.width,actual.width);self.assertLessEqual(dy+source.height,actual.height)
   expected=Image.new('RGBA',tuple(self.c['canvas_px']));expected.paste(source,(dx,dy))
   self.assertEqual(actual.tobytes(),expected.tobytes())
 def test_hashes_bind_inputs_and_output(self):
  for name,digest in self.c['inputs'].items():self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),digest,name)
  for f in self.c['frames']:self.assertEqual(hashlib.sha256((ROOT/f['file']).read_bytes()).hexdigest(),f['sha256'])
  c=self.c.copy();digest=c.pop('artifact_digest')
  self.assertEqual(hashlib.sha256(json.dumps(c,sort_keys=True,separators=(',',':')).encode()).hexdigest(),digest)
 def test_registered_observations_and_unknown_joints(self):
  poses=json.loads((ROOT/'poses.json').read_text())['poses'];self.assertEqual(len(poses),2)
  for p,f in zip(poses,self.c['frames']):
   self.assertEqual(p['pose_id'],f['pose_id']);dx,dy=f['whole_frame_translation_px']
   for group in ['landmarks','visible_foot_points','tool']:
    for name,v in p['source_'+group+'_px'].items():
     r=p['registered_'+group+'_px'][name]
     self.assertEqual(r,None if v is None else [v[0]+dx,v[1]+dy])
   self.assertIsNone(p['source_landmarks_px']['hip_joint'])
 def test_scope_and_full_stream_do_not_become_acceptance(self):
  self.assertEqual(self.c['direction'],'south');self.assertEqual(self.c['garment'],'A')
  self.assertFalse(self.c['accepted']);self.assertFalse(self.c['modular']);self.assertFalse(self.c['native_checked'])
  self.assertFalse(self.c['gameplay_available']);self.assertFalse(self.c['loop']);self.assertEqual(self.c['events'],[])
  self.assertEqual([f['phase'] for f in self.c['frames']],['ready','pour'])
  self.assertEqual(len({f['sha256'] for f in self.c['frames']}),2)
  for f in self.c['frames']:self.assertGreater(f['duration_ms'],0)
  cfg=json.loads((ROOT/'registration-config.json').read_text())
  self.assertIsNone(cfg['frames'][0]['tool_source_px']['water_landing'])
  self.assertIsNotNone(cfg['frames'][1]['tool_source_px']['water_landing'])
if __name__=='__main__':unittest.main()
