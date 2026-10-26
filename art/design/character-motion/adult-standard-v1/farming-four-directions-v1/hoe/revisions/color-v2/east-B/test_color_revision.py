from pathlib import Path
import hashlib,json,unittest,importlib.util,sys
from PIL import Image,ImageOps
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parent
class ColorOnly(unittest.TestCase):
 def candidate(self):
  self.assertTrue((R/'candidate.json').exists(),'color-only registered candidate not built');return json.loads((R/'candidate.json').read_text())
 def test_exact_nonpaint_rgba_alpha_and_gpt_rgb(self):
  c=self.candidate();self.assertEqual(c['revision_id'],'color-v2')
  for f,revision in zip(c['frames'],c['color_revision']['frames']):
   phase=f['phase'];self.assertEqual(revision['phase'],phase)
   original=Image.open(R/'references'/('original-'+phase+'.png')).convert('RGBA');out=Image.open(R/f['source']).convert('RGBA');raw=Image.open(R/revision['raw_gpt']).convert('RGBA');mask=Image.open(R/revision['mask']).convert('L')
   self.assertEqual(original.size,(1024,1536));self.assertEqual(out.size,original.size);self.assertEqual(raw.size,original.size)
   self.assertEqual(out.getchannel('A').tobytes(),original.getchannel('A').tobytes())
   expected=raw.copy();expected.putalpha(original.getchannel('A'));expected=Image.composite(expected,original,mask);self.assertEqual(expected.tobytes(),out.tobytes())
   self.assertEqual(Image.composite(out,original,ImageOps.invert(mask)).tobytes(),original.tobytes())
   self.assertGreater(mask.histogram()[255],0);self.assertLessEqual(revision['composition_info']['fallback_fraction'],0.05)
   self.assertIn(revision['mask'],c['inputs']);self.assertIn(revision['raw_gpt'],c['inputs'])
 def test_parent_geometry_timing_and_config_unchanged(self):
  c=self.candidate();parent=json.loads((R/'references/parent-candidate.json.txt').read_text());old=json.loads((R/'references/parent-registration-config.json.txt').read_text());new=json.loads((R/'registration-config.json').read_text())
  for before,after in zip(old['frames'],new['frames']):
   a=before.copy();b=after.copy();a.pop('source');b.pop('source');self.assertEqual(a,b)
  for key in ['canvas_px','root_anchor_px','display_scale','source_density_scale_vs_idle']:self.assertEqual(c[key],parent[key]);self.assertEqual(new[key],old[key])
  self.assertEqual([(f['phase'],f['duration_ms'])for f in c['frames']],[(f['phase'],f['duration_ms'])for f in parent['frames']])
 def test_sources_dependencies_and_candidate_registration(self):
  c=self.candidate();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
  self.assertEqual(c['parent_candidate_sha256'],sha(R/'references/parent-candidate.json.txt'));self.assertEqual(c['color_revision']['parent_candidate_sha256'],c['parent_candidate_sha256']);self.assertEqual(c['color_revision']['compositor_sha256'],sha(R/'references/compose_color.py'))
  for p,h in c['inputs'].items():self.assertEqual(sha(R/p),h,p)
  script=R.parents[2]/'register_clip.py';spec=importlib.util.spec_from_file_location('hoe_registration',script);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);self.assertTrue(m.validate_data(R,c))
 def test_new_palette_pending_acceptance(self):
  c=self.candidate();self.assertFalse(c['accepted']);self.assertFalse(c['native_checked']);self.assertFalse(c['modular']);self.assertEqual(len(c['color_revision']['frames']),4)
if __name__=='__main__':unittest.main()
