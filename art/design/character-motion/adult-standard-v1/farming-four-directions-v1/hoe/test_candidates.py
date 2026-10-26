"""Real source fidelity and rejection gates; CLI can validate each delivered clip."""
import importlib.util,json,unittest,hashlib,tempfile,copy,sys
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parent
class RejectContracts(unittest.TestCase):
 def validator(self):
  self.assertTrue((ROOT/'register_clip.py').exists(),'hoe registration/validation is not implemented')
  spec=importlib.util.spec_from_file_location('hoe_registration',ROOT/'register_clip.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
 def test_missing_clip_rejected(self):
  m=self.validator()
  with self.assertRaises((ValueError,FileNotFoundError)):m.validate(ROOT/'not-produced/candidate.json')
 def test_eight_real_clips_contract(self):
  m=self.validator()
  for d in ['west','east','south','north']:
   for g in ['A','B']:m.validate(ROOT/(d+'-'+g)/'candidate.json')
 def test_duplicate_pose_content_rejected(self):
  m=self.validator();p=ROOT/'west-A/candidate.json';self.assertTrue(p.exists());c=json.loads(p.read_text());c['frames'][1]=copy.deepcopy(c['frames'][0]);c['frames'][1]['pose_id']='hoe_west_key_1';c['frames'][1]['phase']='lift'
  with self.assertRaises(ValueError):m.validate_data(p.parent,c,verify_digest=False)
 def test_wrong_garment_direction_density_rejected(self):
  m=self.validator();p=ROOT/'west-A/candidate.json';self.assertTrue(p.exists());c=json.loads(p.read_text())
  for key,val in [('garment','fixture'),('direction','diagonal'),('source_density_scale_vs_idle',1),('display_scale',0.5)]:
   v=copy.deepcopy(c);v[key]=val
   with self.assertRaises(ValueError):m.validate_data(p.parent,v,verify_digest=False)
 def test_actual_source_background_is_transparent(self):
  paths=list(ROOT.glob('*/candidate.json'));self.assertTrue(paths)
  for path in paths:
   c=json.loads(path.read_text())
   for f in c['frames']:
    a=Image.open(path.parent/f['source']).convert('RGBA').getchannel('A')
    self.assertGreater(a.histogram()[0],1024*1536*0.1,str(path.parent/f['source']))
    self.assertEqual([a.getpixel(p)for p in [(0,0),(1023,0),(0,1535),(1023,1535)]],[0,0,0,0],str(path.parent/f['source']))
 def test_missing_source_dependency_rejected(self):
  m=self.validator();p=ROOT/'west-A/candidate.json';self.assertTrue(p.exists());c=json.loads(p.read_text());c['inputs'].pop(c['frames'][0]['source'])
  with self.assertRaises(ValueError):m.validate_data(p.parent,c,verify_digest=False)
if __name__=='__main__':
 if len(sys.argv)>1 and sys.argv[1]=='--clip':
  obj=RejectContracts();m=obj.validator();m.validate(Path(sys.argv[2]));print('clip structural validation passed')
 else:unittest.main()
