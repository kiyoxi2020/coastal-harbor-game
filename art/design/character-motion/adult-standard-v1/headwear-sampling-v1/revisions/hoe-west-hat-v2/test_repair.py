from pathlib import Path
import importlib.util
import unittest

P=Path(__file__).resolve().parent

class RepairGateTests(unittest.TestCase):
    def test_new_hair_view_must_bind_the_exact_audited_hat(self):
        spec=importlib.util.spec_from_file_location('hoe_hair_gate',P/'build_repair.py')
        m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        hat={'full_hair_compatible':False}
        with self.assertRaises(ValueError):m.require_hair_compatibility(hat,None,'hat-sha')
        good={'runtime_candidate_allowed':True,'compatible_hat_manifest_sha256':'hat-sha'}
        m.require_hair_compatibility(hat,good,'hat-sha')
        with self.assertRaises(ValueError):m.require_hair_compatibility(hat,good,'different-hat')
        with self.assertRaises(ValueError):m.require_hair_compatibility(hat,dict(good,runtime_candidate_allowed=False),'hat-sha')

    def test_full_hair_requires_explicit_real_compatibility(self):
        spec=importlib.util.spec_from_file_location('hoe_build',P/'build_repair.py')
        m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        m.require_full_hair_compatible({'full_hair_compatible':True})
        for value in [None,False,1,'true']:
            with self.subTest(value=value),self.assertRaises(ValueError):m.require_full_hair_compatible({'full_hair_compatible':value})

if __name__=='__main__':unittest.main()
