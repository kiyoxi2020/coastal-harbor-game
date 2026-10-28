"""Failure gates for geometry, source ownership and preserved real hat pixels."""
from pathlib import Path
import importlib.util,unittest
from PIL import Image
HERE=Path(__file__).resolve().parent
class InterfaceTests(unittest.TestCase):
 def load_checker(self):
  path=HERE/'contract_checks.py';self.assertTrue(path.exists(),'interface checker not implemented')
  spec=importlib.util.spec_from_file_location('checks',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
 def fixture(self):
  size=(4,4);base=Image.new('RGBA',size,(230,170,130,253));hat=Image.new('RGBA',size,(230,190,40,253));mask=Image.new('L',size);mask.putpixel((1,1),255)
  return {'base':base,'old_hat':hat.copy(),'hat':hat.copy(),'final':hat.copy(),'owners':Image.new('L',size,3),'required_cover':mask.copy(),'required_contact':mask.copy(),'frozen_hat':mask.copy(),'allowed_edit':Image.new('L',size,255),'source_checks':[{'ownership':mask.copy(),'forbidden':Image.new('L',size)}]}
 def test_good_and_each_distinct_failure(self):
  m=self.load_checker();contract={'placement_px':[0,0],'minimum_solid_alpha':200}
  self.assertTrue(m.assess(contract,self.fixture())['passed'])
  for defect,field in [('scalp','uncovered_scalp'),('gap','contact_alpha_gaps'),('wrong_contact_owner','uncovered_contact'),('source_face','non_hat_source_pixels'),('cut_hat','changed_frozen_hat_pixels'),('body_edit','outside_authorized_rgba_differences')]:
   images=self.fixture()
   if defect=='scalp':images['owners'].putpixel((1,1),1)
   if defect=='gap':images['final'].putpixel((1,1),(0,0,0,0))
   if defect=='wrong_contact_owner':images['owners'].putpixel((1,1),1)
   if defect=='source_face':images['source_checks'][0]['forbidden'].putpixel((1,1),255)
   if defect=='cut_hat':images['hat'].putpixel((1,1),(0,0,0,0))
   if defect=='body_edit':images['allowed_edit'].putpixel((0,0),0)
   with self.subTest(defect=defect):
    report=m.assess(contract,images);self.assertFalse(report['passed']);self.assertGreater(report[field],0)
  self.assertFalse(m.assess({'placement_px':[1,0]},self.fixture())['passed'])
 def test_true_hat_may_still_invade_the_fixed_opening(self):
  m=self.load_checker();images=self.fixture();images['required_opening']=images['required_contact'].copy()
  report=m.assess({'placement_px':[0,0]},images)
  self.assertFalse(report['passed']);self.assertGreater(report['hat_inside_required_opening'],0)
 def test_opaque_body_cannot_hide_a_translucent_hat_contact(self):
  images=self.fixture();images['hat'].putpixel((1,1),(30,15,0,90));images['frozen_hat']=Image.new('L',(4,4))
  report=self.load_checker().assess({'placement_px':[0,0]},images)
  self.assertFalse(report['passed']);self.assertGreater(report['contact_alpha_gaps'],0)
 def test_near_hat_cannot_invade_head_beyond_first_four_opening_rows(self):
  images=self.fixture();mask=Image.new('L',(4,4));mask.putpixel((2,2),255);images['visible_head_in_edit_band']=mask
  report=self.load_checker().assess({'placement_px':[0,0]},images)
  self.assertFalse(report['passed']);self.assertGreater(report['hat_inside_visible_head'],0)
 def test_transparent_rgb_is_preserved(self):
  m=self.load_checker();images=self.fixture();images['base'].putpixel((0,0),(10,20,30,0));images['final'].putpixel((0,0),(0,0,0,0));images['allowed_edit'].putpixel((0,0),0)
  self.assertEqual(m.assess({'placement_px':[0,0]},images)['outside_authorized_rgba_differences'],1)
if __name__=='__main__':unittest.main()
