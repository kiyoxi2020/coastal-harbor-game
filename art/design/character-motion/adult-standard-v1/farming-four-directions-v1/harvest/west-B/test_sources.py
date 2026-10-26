"""Four original fixed-outfit source rasters, independent of shared registration."""
from pathlib import Path
import hashlib,json,unittest
from PIL import Image
R=Path(__file__).resolve().parent
PHASES=['ready','reach','pluck','recovery']
class Sources(unittest.TestCase):
 def images(self):
  out=[]
  for phase in PHASES:
   p=R/'sources'/(phase+'.png');self.assertTrue(p.is_file(),'missing complete '+phase+' source');out.append(Image.open(p).convert('RGBA'))
  return out
 def test_four_genuine_distinct_original_rasters(self):
  images=self.images();self.assertEqual(len({hashlib.sha256(i.tobytes()).hexdigest()for i in images}),4)
 def test_true_source_density_and_alpha_exterior(self):
  for i in self.images():
   self.assertEqual(i.size,(1024,1536));a=i.getchannel('A');self.assertEqual(a.getextrema()[0],0);self.assertGreater(a.histogram()[0],1024*1536*0.1);self.assertEqual([a.getpixel(p)for p in[(0,0),(1023,0),(0,1535),(1023,1535)]],[0,0,0,0])
 def test_source_and_reference_hashes(self):
  self.images();p=R/'provenance.json';self.assertTrue(p.exists());v=json.loads(p.read_text())
  for path,digest in v['inputs'].items():self.assertEqual(hashlib.sha256((R/path).read_bytes()).hexdigest(),digest,path)
  for f in v['selected']:
   self.assertEqual((R/f['source']).read_bytes(),(R/f['original_attempt']).read_bytes(),'Canonical source must be exact original selected GPT file')
 def test_no_false_registration_or_modularity_claim(self):
  self.images();v=json.loads((R/'measurements.json').read_text());self.assertFalse(v['modular']);self.assertFalse(v['native_checked']);self.assertFalse(v['precise_support_checked']);self.assertEqual(len(v['frames']),4)
if __name__=='__main__':unittest.main()
