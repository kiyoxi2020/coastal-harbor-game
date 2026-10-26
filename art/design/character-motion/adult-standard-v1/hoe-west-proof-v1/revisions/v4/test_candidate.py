"""Source fidelity and head-density gate; never claims dynamics/rigidity approval."""
import hashlib,json,unittest
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parent
class CandidateStructure(unittest.TestCase):
 def data(self):
  self.assertTrue((ROOT/'candidate.json').is_file(),'v4 registered candidate not built yet')
  return json.loads((ROOT/'candidate.json').read_text())
 def test_four_complete_distinct_phases(self):
  c=self.data()
  self.assertEqual([f['phase'] for f in c['frames']],['ready','lift','contact','recovery'])
  self.assertEqual([f['duration_ms'] for f in c['frames']],[180,220,140,260])
  self.assertEqual(len({f['sha256'] for f in c['frames']}),4)
  self.assertFalse(c['accepted']);self.assertFalse(c['gameplay_available']);self.assertFalse(c['loop'])
 def test_full_original_rgba_preserved_by_integer_registration(self):
  c=self.data()
  for f in c['frames']:
   original=Image.open(ROOT/f['source']).convert('RGBA')
   registered=Image.open(ROOT/f['file']).convert('RGBA')
   dx,dy=f['whole_frame_translation_px']
   self.assertTrue(all(type(v)is int and v>=0 for v in [dx,dy]))
   self.assertEqual(original.size,(1024,1536));self.assertEqual(registered.size,(1536,1792))
   self.assertLessEqual(dx+original.width,registered.width);self.assertLessEqual(dy+original.height,registered.height)
   expected=Image.new('RGBA',registered.size);expected.paste(original,(dx,dy))
   self.assertEqual(registered.tobytes(),expected.tobytes())
 def test_actual_dependencies_frames_and_config_hashes(self):
  c=self.data()
  for path,digest in c['inputs'].items():self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),digest,path)
  for f in c['frames']:
   self.assertEqual(hashlib.sha256((ROOT/f['file']).read_bytes()).hexdigest(),f['sha256'])
   self.assertEqual(hashlib.sha256((ROOT/f['source']).read_bytes()).hexdigest(),f['source_sha256'])
  value=c.copy();digest=value.pop('artifact_digest')
  self.assertEqual(hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest(),digest)
 def test_observed_head_gate_and_unapproved_contact_scope(self):
  c=self.data();m=json.loads((ROOT/'measurements.json').read_text());p=json.loads((ROOT/'poses.json').read_text())
  self.assertEqual(c['root_anchor_px'],[768,1544]);self.assertEqual(c['source_density_scale_vs_idle'],2)
  self.assertAlmostEqual(c['display_scale'],138/1164)
  for f,measured,pose in zip(c['frames'],m['frames'],p['poses']):
   self.assertEqual(measured['source_sha256'],f['source_sha256']);self.assertEqual(pose['pose_id'],f['pose_id'])
   for size,reference in zip(measured['head_size_px'],[473,488]):self.assertLessEqual(abs(size/reference-1),0.05)
   self.assertIsNone(pose['landmarks_source_px']['hip_joint'])
   self.assertIsNone(pose['landmarks_source_px']['near_knee_joint'])
   dx,dy=f['whole_frame_translation_px']
   for name,point in pose['landmarks_source_px'].items():
    expected=None if point is None else [point[0]+dx,point[1]+dy]
    self.assertEqual(pose['landmarks_registered_px'][name],expected)
  self.assertFalse(m['acceptance']['rigid_tool']);self.assertFalse(m['acceptance']['precise_support']);self.assertFalse(m['acceptance']['user_accepted'])
if __name__=='__main__':unittest.main()
