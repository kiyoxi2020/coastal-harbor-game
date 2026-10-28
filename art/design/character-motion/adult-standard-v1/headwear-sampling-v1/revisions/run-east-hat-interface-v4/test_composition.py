from pathlib import Path
from PIL import Image
import importlib.util,unittest
HERE=Path(__file__).resolve().parent
class CompositionTests(unittest.TestCase):
 def module(self):
  p=HERE/'composition.py';self.assertTrue(p.exists(),'fixed-coordinate compositor missing');s=importlib.util.spec_from_file_location('composition',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 def test_patch_cannot_touch_frozen_or_unapproved_pixels(self):
  m=self.module();size=(3,1);source=Image.new('RGBA',size,(220,160,40,253));patch=Image.new('RGBA',size,(20,30,40,254));old=Image.new('L',size,255);own=Image.new('L',size);own.putpixel((1,0),255);allowed=own.copy();frozen=Image.new('L',size);frozen.putpixel((0,0),255);remove=own.copy()
  hat,tags=m.assemble_hat(source,old,patch,own,allowed,remove,frozen)
  self.assertEqual(hat.getpixel((0,0)),source.getpixel((0,0)));self.assertEqual(hat.getpixel((1,0)),patch.getpixel((1,0)));self.assertEqual(list(tags.get_flattened_data()),[3,4,3])
  own.putpixel((0,0),255)
  with self.assertRaises(ValueError):m.assemble_hat(source,old,patch,own,allowed,remove,frozen)
  own=Image.new('L',size);remove.putpixel((0,0),255)
  with self.assertRaises(ValueError):m.assemble_hat(source,old,patch,own,allowed,remove,frozen)
 def test_depth_and_transparent_rgb(self):
  m=self.module();base=Image.new('RGBA',(3,1),(9,8,7,0));base.putpixel((0,0),(250,180,130,253));hat=Image.new('RGBA',(3,1));hat.putpixel((0,0),(200,160,30,253));hat.putpixel((1,0),(200,160,30,253));tags=Image.new('L',(3,1),3);rear=Image.new('L',(3,1));rear.putpixel((0,0),255)
  out,owners,edit=m.render(base,hat,tags,rear)
  self.assertEqual(out.getpixel((0,0)),base.getpixel((0,0)));self.assertEqual(out.getpixel((1,0)),hat.getpixel((1,0)));self.assertEqual(out.getpixel((2,0)),(9,8,7,0));self.assertEqual(list(owners.get_flattened_data()),[1,3,0])
if __name__=='__main__':unittest.main()
