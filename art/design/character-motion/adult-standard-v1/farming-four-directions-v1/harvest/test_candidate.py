import copy,json,sys,unittest
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parent
if '--combo' in sys.argv:
 i=sys.argv.index('--combo');COMBOS=[sys.argv[i+1]];del sys.argv[i:i+2]
else:COMBOS=[f'{d}-{g}' for d in ('south','west','east','north') for g in ('A','B')]

class CandidateTest(unittest.TestCase):
 def test_complete_scope_and_inputs(self):
  import build_candidate as b
  for combo in COMBOS:
   with self.subTest(combo=combo):
    path=ROOT/combo/'candidate.json'
    self.assertTrue(path.exists(),f'missing complete {combo}')
    data=json.loads(path.read_text());b.validate_candidate(path.parent,data)
    self.assertFalse(data['modular']);self.assertFalse(data['accepted'])
 def test_whole_frame_rgba_preserved(self):
  for combo in COMBOS:
   with self.subTest(combo=combo):
    data=json.loads((ROOT/combo/'candidate.json').read_text())
    for f in data['frames']:
     src=Image.open(ROOT/combo/f['source']).convert('RGBA');out=Image.open(ROOT/combo/f['file']).convert('RGBA');x,y=f['whole_frame_translation_px']
     self.assertEqual(src.tobytes(),out.crop((x,y,x+src.width,y+src.height)).tobytes())
 def test_missing_phase_rejected(self):
  import build_candidate as b
  path=ROOT/COMBOS[0]/'candidate.json';data=json.loads(path.read_text());data['frames'].pop()
  with self.assertRaises(ValueError):b.validate_candidate(path.parent,data)
 def test_changed_source_hash_rejected(self):
  import build_candidate as b
  path=ROOT/COMBOS[0]/'candidate.json';data=json.loads(path.read_text());data['inputs'][data['frames'][0]['source']]='0'*64
  with self.assertRaises(ValueError):b.validate_candidate(path.parent,data)
if __name__=='__main__':unittest.main()
