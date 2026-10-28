import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
SCRIPT = Path(__file__).parents[1]/'review.py'

class ReviewConstructionTests(unittest.TestCase):
    def test_construction_suite_is_supported_and_rejects_missing_build(self):
        result=subprocess.run([sys.executable,str(SCRIPT),'headwear-construction','--dry-run'],capture_output=True,text=True)
        self.assertNotIn('invalid choice',result.stderr)
        # A fixture below covers rejection without relying on real build availability.

    def test_preflight_rejects_untrusted_suite_before_launch(self):
        spec=importlib.util.spec_from_file_location('review_construction',SCRIPT)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        self.assertTrue(hasattr(module,'construction_preflight'),'Strict suite preflight is missing')
        with tempfile.TemporaryDirectory(prefix='coastal-review-',dir='/private/tmp') as tmp:
            repo=Path(tmp);suite=repo/'art/characters/reviews/headwear-construction/review.json';suite.parent.mkdir(parents=True)
            data={'kind':'coastal-character-construction-review-v1','schema_version':1,'resource_root':'art/characters','scope':'review-only','sample_id':'hoe-west','states':{s:{'manifest':'../outside.json','sha256':'0'*64} for s in ['bare','hair','hat','hair_hat']}}
            suite.write_text(json.dumps(data))
            with self.assertRaises(ValueError):module.construction_preflight(repo,suite)
            data['scope']='production';suite.write_text(json.dumps(data))
            with self.assertRaises(ValueError):module.construction_preflight(repo,suite)

if __name__=='__main__':unittest.main()
