import unittest,importlib.util
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parent
class ComposeTest(unittest.TestCase):
 def module(self):
  self.assertTrue((ROOT/'compose_color.py').exists(),'color-only compositor missing')
  spec=importlib.util.spec_from_file_location('compose_color',ROOT/'compose_color.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
 def fixture(self):
  old=Image.new('RGBA',(4,4),(180,120,80,254));old.putpixel((1,1),(60,110,180,254));old.putpixel((2,2),(30,65,110,0))
  new=Image.new('RGBA',(4,4),(255,30,20,255));new.putpixel((1,1),(40,75,115,255));return old,new
 def test_only_owned_blue_rgb_changes(self):
  m=self.module();old,new=self.fixture();out,mask,info=m.compose(old,new,[[(0,0),(3,0),(3,3),(0,3)]])
  self.assertEqual(out.getpixel((1,1)),(40,75,115,254));self.assertEqual(out.getpixel((0,0)),old.getpixel((0,0)));self.assertEqual(out.getpixel((2,2)),old.getpixel((2,2)))
  self.assertEqual(out.getchannel('A').tobytes(),old.getchannel('A').tobytes());self.assertEqual(info['outside_mask_rgba_differences'],0)
 def test_empty_manual_ownership_rejected(self):
  m=self.module();old,new=self.fixture()
  with self.assertRaises(ValueError):m.compose(old,new,[])
 def test_moved_clothing_rejected(self):
  m=self.module();old,new=self.fixture();new.putpixel((1,1),(230,170,130,254))
  with self.assertRaises(ValueError):m.compose(old,new,[[(0,0),(3,0),(3,3),(0,3)]])
 def test_canvas_mismatch_rejected(self):
  m=self.module();old,new=self.fixture()
  with self.assertRaises(ValueError):m.compose(old,Image.new('RGBA',(2,2)),[[(0,0),(3,0),(3,3),(0,3)]])
if __name__=='__main__':unittest.main()
