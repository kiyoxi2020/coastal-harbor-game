"""Two-pose diagnostic structure and whole-frame fidelity; no dynamics claim."""
import hashlib,json,unittest
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parent
class CandidateStructure(unittest.TestCase):
 def data(self):
  self.assertTrue((ROOT/'candidate.json').is_file(),'Long-sleeve two-pose candidate has not been registered')
  return json.loads((ROOT/'candidate.json').read_text())
 def test_two_complete_distinct_poses_only(self):
  c=self.data()
  self.assertEqual(c['garment'],'B');self.assertEqual(c['direction'],'west')
  self.assertEqual([f['phase'] for f in c['frames']],['ready','contact'])
  self.assertEqual([f['pose_id'] for f in c['frames']],['hoe_west_key_0','hoe_west_key_2'])
  self.assertEqual(len({f['sha256'] for f in c['frames']}),2)
  for name in ['accepted','native_checked','modular','gameplay_available','loop']:self.assertFalse(c[name],name)
  self.assertEqual(c['events'],[]);self.assertFalse(c['review_repeat'])
 def test_entire_source_rgba_preserved(self):
  for f in self.data()['frames']:
   source=Image.open(ROOT/f['source']).convert('RGBA');out=Image.open(ROOT/f['file']).convert('RGBA')
   self.assertEqual(source.size,(1024,1536));self.assertEqual(out.size,(1536,1792))
   dx,dy=f['whole_frame_translation_px'];self.assertTrue(all(type(v)is int and v>=0 for v in [dx,dy]))
   self.assertLessEqual(dx+source.width,out.width);self.assertLessEqual(dy+source.height,out.height)
   expected=Image.new('RGBA',out.size);expected.paste(source,(dx,dy));self.assertEqual(out.tobytes(),expected.tobytes())
   a=source.getchannel('A');self.assertEqual(a.getextrema()[0],0);self.assertGreaterEqual(a.getextrema()[1],250);self.assertGreater(a.histogram()[0],source.width*source.height*0.1)
   bbox=a.getbbox();self.assertGreater(bbox[0],0);self.assertGreater(bbox[1],0);self.assertLess(bbox[2],source.width);self.assertLess(bbox[3],source.height)
 def test_dependencies_and_digest(self):
  c=self.data()
  for path,digest in c['inputs'].items():self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),digest,path)
  for f in c['frames']:
   for key,path in [('sha256',f['file']),('source_sha256',f['source'])]:self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),f[key])
  value=c.copy();digest=value.pop('artifact_digest');self.assertEqual(hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest(),digest)
 def test_coordinate_registration_and_honest_measurements(self):
  c=self.data();p=json.loads((ROOT/'poses.json').read_text());m=json.loads((ROOT/'measurements.json').read_text())
  self.assertEqual(c['canvas_px'],[1536,1792]);self.assertEqual(c['root_anchor_px'],[768,1544]);self.assertAlmostEqual(c['display_scale'],138/1164)
  self.assertEqual(len(p['poses']),2);self.assertEqual(len(m['frames']),2)
  for f,pose,measurement in zip(c['frames'],p['poses'],m['frames']):
   self.assertEqual(pose['pose_id'],f['pose_id']);self.assertEqual(measurement['source_sha256'],f['source_sha256'])
   dx,dy=f['whole_frame_translation_px']
   for group in ['landmarks','foot_points','tool_points']:
    for name,point in pose[group+'_source_px'].items():self.assertEqual(pose[group+'_registered_px'][name],None if point is None else[point[0]+dx,point[1]+dy])
   for name in ['hip_joint','near_knee_joint','near_ankle_joint']:self.assertIsNone(pose['landmarks_source_px'][name])
  for value in m['acceptance'].values():self.assertFalse(value)
if __name__=='__main__':unittest.main()
