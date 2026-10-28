import importlib.util,json,unittest
from pathlib import Path
from PIL import Image
HERE=Path(__file__).resolve().parent
BASE=HERE.parents[1]/'run-east'
class DepthTests(unittest.TestCase):
 def test_reported_forehead_is_in_front_of_far_brim(self):
  folder=HERE if (HERE/'sample.json').exists() else BASE
  sample=json.loads((folder/'sample.json').read_text());f=sample['frames'][0]
  bare=Image.open(folder/f['states']['bare']['file']).convert('RGBA')
  hat=Image.open(folder/f['states']['hat']['file']).convert('RGBA')
  self.assertEqual(hat.getpixel((350,228)),bare.getpixel((350,228)),'Far brim must be behind same-pose forehead; do not paint over skin.')
 def test_depth_compositor(self):
  self.assertTrue((HERE/'compose_revision.py').exists())
  spec=importlib.util.spec_from_file_location('depth',HERE/'compose_revision.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
  base=Image.new('RGBA',(4,1));base.putpixel((0,0),(250,180,130,253));base.putpixel((1,0),(250,180,130,253))
  rear=Image.new('RGBA',(4,1),(120,60,10,254));front=Image.new('RGBA',(4,1));front.putpixel((1,0),(230,190,40,253))
  hair=Image.new('RGBA',(4,1));hair.putpixel((0,0),(80,40,20,253))
  out=m.compose(base,rear,front,None)
  self.assertEqual(out.getpixel((0,0)),base.getpixel((0,0)))
  self.assertEqual(out.getpixel((1,0)),front.getpixel((1,0)))
  self.assertEqual(out.getpixel((2,0)),rear.getpixel((2,0)))
  out=m.compose(base,rear,front,hair)
  self.assertEqual(out.getpixel((0,0)),hair.getpixel((0,0)))
if __name__=='__main__':unittest.main()
