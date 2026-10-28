from pathlib import Path
from PIL import Image
import copy
import importlib.util
import unittest
import json
import tempfile

HERE=Path(__file__).resolve().parent

def module():
    spec=importlib.util.spec_from_file_location('approved_build',HERE/'build_approved.py')
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value)
    return value

class ApprovedBuildTests(unittest.TestCase):
    def test_extraction_requires_matching_pose_and_explicit_candidate(self):
        with tempfile.TemporaryDirectory(prefix='coastal-hat-pose-gate-',dir='/private/tmp') as folder:
            path=Path(folder)/'manifest.json'
            good={'pose_id':'run_east_2','runtime_candidate_allowed':True,'runtime_full_frame_placement_px':[0,0],'sha256':{}}
            m=module();path.write_text(json.dumps(good));m.load_extraction(path,'run_east_2')
            for defect in ['wrong_pose','missing_permission','numeric_permission']:
                bad=copy.deepcopy(good)
                if defect=='wrong_pose':bad['pose_id']='run_east_3'
                elif defect=='missing_permission':bad.pop('runtime_candidate_allowed')
                else:bad['runtime_candidate_allowed']=1
                path.write_text(json.dumps(bad))
                with self.subTest(defect=defect),self.assertRaises(ValueError):m.load_extraction(path,'run_east_2')

    def test_real_idle_reconstructs_reviewed_original_body_composite(self):
        p=HERE/'idle-extraction'
        images=[Image.open(p/name).convert('RGBA') for name in ['original-body.png','hat-near.png','hat-far.png']]
        actual,_=module().compose(images[0],images[1],images[2])
        expected=Image.open(p/'original-body-with-approved-hat.png').convert('RGBA')
        self.assertEqual(actual.tobytes(),expected.tobytes())

    def test_far_hat_under_soft_body_and_hidden_rgb_are_preserved(self):
        body=Image.new('RGBA',(2,1),(9,8,7,0));body.putpixel((0,0),(240,160,120,100))
        far=Image.new('RGBA',(2,1));far.putpixel((0,0),(80,40,0,255));near=Image.new('RGBA',(2,1))
        actual,edit=module().compose(body,near,far)
        self.assertEqual(actual.getpixel((0,0)),Image.alpha_composite(far,body).getpixel((0,0)))
        self.assertEqual(actual.getpixel((1,0)),(9,8,7,0));self.assertEqual(edit.getpixel((1,0)),0)

    def test_bare_hair_and_timing_cannot_change(self):
        f={'pose_id':'run_east_0','duration_ms':80,'states':{'bare':{'sha256':'bare'},'hair':{'sha256':'hair'}}}
        original={'frames':[f],'idle':dict(f,pose_id='idle_east_0')}
        m=module();m.assert_preserved(original,copy.deepcopy(original))
        for key in ['bare','hair','duration_ms','pose_id']:
            changed=copy.deepcopy(original)
            if key in ['bare','hair']:changed['frames'][0]['states'][key]['sha256']='wrong'
            else:changed['frames'][0][key]='wrong'
            with self.subTest(key=key),self.assertRaises(ValueError):m.assert_preserved(original,changed)

if __name__=='__main__':unittest.main()
