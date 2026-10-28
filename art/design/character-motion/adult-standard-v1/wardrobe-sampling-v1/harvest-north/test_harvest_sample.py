import copy,json,unittest
from pathlib import Path
from PIL import Image,ImageChops
import build_harvest_sample as b
from audit_source_semantics import audit
D=Path(__file__).resolve().parent

class SamplingContract(unittest.TestCase):
    def test_actual_frozen_sample(self):
        self.assertTrue(b.validate('harvest-north')['slot_bake_rgba_exact'])
    def test_source_semantics_red_to_green(self):
        before=json.loads((D/'evidence/source-semantics-before.json').read_text())
        self.assertFalse(before['passed']);self.assertTrue(audit(D)['passed'])
    def test_non_clothing_and_alpha_fail_closed(self):
        old=Image.new('RGBA',(3,3),(80,100,120,255));mask=Image.new('L',(3,3))
        changed=old.copy();changed.putpixel((0,0),(81,100,120,255))
        with self.assertRaisesRegex(ValueError,'non-clothing'):b.check_exact(old,changed,mask)
        changed=old.copy();changed.putpixel((0,0),(80,100,120,254))
        with self.assertRaisesRegex(ValueError,'alpha'):b.check_exact(old,changed,mask)
    def test_uncovered_or_overlapping_slot_rejected(self):
        old=Image.new('RGBA',(3,3),(80,100,120,255));m=Image.new('L',(3,3),255)
        with self.assertRaisesRegex(ValueError,'overlap'):b.compose_visible(old,{'top':old,'pants':old},{'top':m,'pants':m})
        with self.assertRaisesRegex(ValueError,'missing GPT'):b.compose_visible(old,{'top':Image.new('RGBA',(3,3))},{'top':m})
    def test_four_distinct_pose_contract(self):
        spec=json.loads((D/'sample.json').read_text());bad=copy.deepcopy(spec);bad['frames'][1]['pose_id']=bad['frames'][0]['pose_id']
        with self.assertRaisesRegex(ValueError,'four distinct'):b.validate_structure(bad)
    def test_registered_geometry_and_order_preserved(self):
        spec=json.loads((D/'sample.json').read_text());parent=json.loads((D/'references/parent-candidate.json.txt').read_text())
        for key in ['canvas_px','root_anchor_px','display_scale','source_density_scale_vs_idle']:self.assertEqual(spec[key],parent[key])
        for frame,pf in zip(spec['frames'],parent['frames']):
            for key in ['pose_id','phase','duration_ms','whole_frame_translation_px','source_box_px']:self.assertEqual(frame[key],pf[key])
        self.assertEqual(spec['idle']['canvas_px'],[512,768]);self.assertEqual(spec['idle']['root_anchor_px'],[256,708])
    def test_final_original_top_and_shoes_only_pants_sampled(self):
        spec=json.loads((D/'sample.json').read_text())
        self.assertEqual(spec['recipe']['slots'],{'top':'original-blue-long-sleeve','pants':'pants02','shoes':'original-shoes'})
        self.assertEqual(spec['recipe']['changed_slots'],['pants'])
        for frame in spec['frames']+[spec['idle']]:
            phase=frame['phase'];old=Image.open(D/f'references/original-{phase}.png').convert('RGB')
            self.assertFalse(frame['source_surface_repairs'])
            for slot in ['top','shoes']:
                part=Image.open(D/f'parts/{phase}/{slot}-complete-source.png').convert('RGB');m=Image.open(D/f'masks/{phase}-{slot}-visible-coverage.png').convert('RGB')
                self.assertIsNone(ImageChops.multiply(ImageChops.difference(old,part),m).getbbox())
                layer=next(l for l in frame['layers'] if l['id']==slot)
                self.assertEqual(layer['source_references'],[f'references/original-{phase}.png'])

if __name__=='__main__':unittest.main()
