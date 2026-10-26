"""Scope-specific art provenance/registration checks; no claim of dynamic compatibility."""
from pathlib import Path
import copy,hashlib,importlib.util,json,unittest
from PIL import Image
ROOT=Path(__file__).resolve().parent
COMBOS=[f'{d}-{g}' for d in ['south','west','east','north'] for g in ['A','B']]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
class WaterEightGroups(unittest.TestCase):
 def validator(self):
  path=ROOT/'validate_water.py';self.assertTrue(path.exists(),'source/capability validator missing')
  spec=importlib.util.spec_from_file_location('water_validator',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
  return module.validate_candidate
 def test_validator_accepts_existing_complete_clip(self):
  directory=ROOT/'west-A';c=json.loads((directory/'candidate.json').read_text());self.assertTrue(self.validator()(c,directory))
 def test_missing_phase_rejected(self):
  directory=ROOT/'west-A';c=json.loads((directory/'candidate.json').read_text());c['frames'].pop()
  with self.assertRaises(ValueError):self.validator()(c,directory)
 def test_unknown_direction_and_garment_rejected(self):
  directory=ROOT/'west-A'
  for key,value in [('direction','northeast'),('garment','C')]:
   c=json.loads((directory/'candidate.json').read_text());c[key]=value
   with self.assertRaises(ValueError):self.validator()(c,directory)
 def test_duplicate_pose_texture_rejected(self):
  directory=ROOT/'west-A';c=json.loads((directory/'candidate.json').read_text());c['frames'][3]['sha256']=c['frames'][0]['sha256']
  with self.assertRaises(ValueError):self.validator()(c,directory)
 def test_actual_source_hash_tamper_rejected_in_memory(self):
  directory=ROOT/'west-A';c=json.loads((directory/'candidate.json').read_text());target=c['frames'][0]['source']
  def read(rel):return (directory/rel).read_bytes()+(b' changed' if rel==target else b'')
  with self.assertRaises(ValueError):self.validator()(c,directory,read=read)
 def test_known_south_pour_root_excludes_water_near_shoe(self):
  for garment in ['A','B']:
   cfg=json.loads((ROOT/('south-'+garment)/'registration-config.json').read_text())
   self.assertEqual(cfg['frames'][2]['source_root_px'],[512,1320],'Water next to shoe is not a support sole; source sole bottoms1324')
 def candidates(self):
  for combo in COMBOS:
   path=ROOT/combo/'candidate.json';self.assertTrue(path.exists(),'missing full clip '+combo)
   yield path.parent,json.loads(path.read_text())
 def test_all_eight_four_real_phases(self):
  for directory,c in self.candidates():
   self.assertEqual(c['schema_version'],1);self.assertEqual(c['action_id'],'water');self.assertEqual(c['template_id'],'adult-standard-v1')
   self.assertEqual(directory.name,c['direction']+'-'+c['garment']);self.assertEqual(c['source_density_scale_vs_idle'],2)
   self.assertAlmostEqual(c['display_scale'],138/1164);self.assertGreaterEqual(len(c['frames']),4)
   self.assertEqual([f['phase'] for f in c['frames']],['ready','raise','pour','recovery'])
   self.assertEqual(len({f['sha256'] for f in c['frames']}),4,'repeated PNG cannot become another phase')
   self.assertEqual(len({f['pose_id'] for f in c['frames']}),4)
   self.assertTrue(800<=sum(f['duration_ms'] for f in c['frames'])<=1200)
 def test_full_cell_rgba_preserved_without_scale_or_mirror(self):
  for directory,c in self.candidates():
   for f in c['frames']:
    source=Image.open(directory/f['source']).convert('RGBA');box=f['source_box_px'];cell=source.crop(tuple(box))
    self.assertEqual(cell.size,(1024,1536));dx,dy=f['whole_frame_translation_px']
    self.assertTrue(all(type(v)is int for v in [*box,dx,dy]));self.assertGreaterEqual(dx,0);self.assertGreaterEqual(dy,0)
    self.assertLessEqual(dx+cell.width,c['canvas_px'][0]);self.assertLessEqual(dy+cell.height,c['canvas_px'][1])
    expected=Image.new('RGBA',tuple(c['canvas_px']));expected.paste(cell,(dx,dy));actual=Image.open(directory/f['file']).convert('RGBA')
    self.assertEqual(actual.tobytes(),expected.tobytes())
 def test_all_declared_hashes_match(self):
  for directory,c in self.candidates():
   for rel,digest in c['inputs'].items():self.assertEqual(sha(directory/rel),digest,rel)
   for f in c['frames']:
    self.assertEqual(sha(directory/f['source']),f['source_sha256']);self.assertEqual(sha(directory/f['file']),f['sha256'])
    self.assertIn(f['source'],c['inputs']);self.assertGreater(f['duration_ms'],0)
 def test_fixed_outfit_scope_not_modular_or_accepted(self):
  for directory,c in self.candidates():
   self.assertFalse(c['accepted']);self.assertFalse(c['native_checked']);self.assertFalse(c['modular']);self.assertFalse(c['gameplay_available'])
   self.assertFalse(c['loop']);self.assertEqual(c['events'],[])
   m=json.loads((directory/'measurements.json').read_text());self.assertEqual(len(m['frames']),4)
   for f in m['frames']:
    self.assertIsNone(f['hidden_joints_px']['hip']);self.assertIn('visible_grip_points_px',f);self.assertIn('visible_foot_points_px',f)
if __name__=='__main__':unittest.main()
