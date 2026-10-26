import unittest,json,hashlib,importlib.util
from pathlib import Path
from PIL import Image,ImageChops,ImageOps
ROOT=Path(__file__).resolve().parent
HOE=ROOT.parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load_module():
 spec=importlib.util.spec_from_file_location('hoe_registration',HOE/'register_clip.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
class RevisionTest(unittest.TestCase):
 def test_four_complete_candidates(self):
  m=load_module()
  for direction in ['south','west','east','north']:
   with self.subTest(direction=direction):
    path=ROOT/(direction+'-B')/'candidate.json';self.assertTrue(path.exists(),direction+' corrected shirt not delivered')
    m.validate(path);data=json.loads(path.read_text());old=json.loads((HOE/(direction+'-B')/'candidate.json').read_text())
    self.assertEqual(data['color_revision']['parent_candidate_sha256'],sha(HOE/(direction+'-B')/'candidate.json'))
    for key in ['canvas_px','root_anchor_px','display_scale','source_density_scale_vs_idle']:self.assertEqual(data[key],old[key])
    self.assertEqual([f['duration_ms'] for f in data['frames']],[f['duration_ms'] for f in old['frames']])
    self.assertEqual([f['whole_frame_translation_px'] for f in data['frames']],[f['whole_frame_translation_px'] for f in old['frames']])
 def test_color_patch_origin_and_exact_non_shirt_preservation(self):
  for direction in ['south','west','east','north']:
   folder=ROOT/(direction+'-B');data=json.loads((folder/'candidate.json').read_text());old=json.loads((HOE/(direction+'-B')/'candidate.json').read_text())
   for entry,frame,parent in zip(data['color_revision']['frames'],data['frames'],old['frames']):
    original=Image.open(HOE/(direction+'-B')/parent['source']).convert('RGBA');out=Image.open(folder/frame['source']).convert('RGBA');raw=Image.open(folder/entry['raw_gpt']).convert('RGBA');mask=Image.open(folder/entry['mask']).convert('L')
    self.assertTrue(entry['ownership_polygons']);self.assertEqual(data['inputs'][entry['mask']],sha(folder/entry['mask']));self.assertEqual(data['inputs'][entry['raw_gpt']],sha(folder/entry['raw_gpt']))
    self.assertEqual(set(mask.getdata())-{0,255},set());self.assertGreater(mask.histogram()[255],100)
    self.assertEqual(original.getchannel('A').tobytes(),out.getchannel('A').tobytes())
    outside=ImageChops.multiply(ImageChops.difference(original,out).convert('RGB'),ImageOps.invert(mask).convert('RGB'));self.assertIsNone(outside.getbbox())
    inside=ImageChops.multiply(ImageChops.difference(raw,out).convert('RGB'),mask.convert('RGB'));self.assertIsNone(inside.getbbox())
 def test_parent_accepted_20_catalog_records_unchanged(self):
  catalog_root=HOE.parent;old=json.loads((catalog_root/'catalog-before-color-v2.json').read_text());new=json.loads((catalog_root/'catalog-color-v2.json').read_text());self.assertEqual(len(new['clips']),24)
  for a,b in zip(old['clips'],new['clips']):
   if not (a['action_id']=='hoe' and a['garment']=='B'):self.assertEqual(a,b)
if __name__=='__main__':unittest.main()
