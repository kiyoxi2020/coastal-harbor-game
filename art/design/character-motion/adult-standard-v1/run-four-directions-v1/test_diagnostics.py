"""Diagnostic registration preserves rejected source pixels and provenance."""
from pathlib import Path
import hashlib,json,unittest
from PIL import Image
ROOT=Path(__file__).resolve().parent
class DiagnosticRegistrationTests(unittest.TestCase):
    def manifest(self):
        self.assertTrue((ROOT/'run-diagnostics.json').is_file(),'Explicit diagnostic manifest required')
        return json.loads((ROOT/'run-diagnostics.json').read_text())
    def test_actual_diagnostic_dependencies_and_scope(self):
        m=self.manifest()
        self.assertEqual(m['status'],'diagnostic_only_not_accepted')
        self.assertEqual({r['direction'] for r in m['records']},{'south','north'})
        for path,sha in m['inputs'].items():self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),sha,path)
        self.assertTrue(all(r['garment']=='B' and len(r['frames'])==4 for r in m['records']))
    def test_south_full_frames_are_exact_source_crop_and_translation(self):
        m=self.manifest();record=next(r for r in m['records'] if r['direction']=='south')
        with Image.open(ROOT/'sources/run-south-b-v2.png') as source:
            for i,entry in enumerate(record['frames']):
                expected=Image.new('RGBA',(512,768));expected.paste(source.crop((i*512,0,(i+1)*512,768)),(0,11))
                with Image.open(ROOT/entry['file']) as actual:self.assertEqual(expected.tobytes(),actual.tobytes())
    def test_north_uses_existing_failed_layered_frames_without_repair(self):
        m=self.manifest();record=next(r for r in m['records'] if r['direction']=='north')
        self.assertEqual([r['file'] for r in record['frames']],[f'baked/B_north_{i}.png' for i in range(4)])
if __name__=='__main__':unittest.main()
