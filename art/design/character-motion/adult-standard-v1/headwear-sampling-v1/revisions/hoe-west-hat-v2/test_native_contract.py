from pathlib import Path
import copy
import importlib.util
import json
import os
import sys
import tempfile
import unittest

P=Path(__file__).resolve().parent
sys.path.insert(0,str(P.parents[1]))
import test_contract as fixtures

class HoeNativeScopeTests(unittest.TestCase):
    def test_receipt_cannot_overwrite_any_capture_or_file_alias(self):
        spec=importlib.util.spec_from_file_location('hoe_native_alias',P/'native_contract.py')
        m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        with tempfile.TemporaryDirectory(prefix='coastal-receipt-',dir='/private/tmp') as tmp:
            root=Path(tmp);contract=root/'input.json';contract.write_text('{}')
            capture=root/'capture.png';capture.write_bytes(b'original capture bytes')
            report=root/'report.json';report.write_text(json.dumps({'output_hashes':{'capture.png':'test'}}))
            symlink=root/'symlink.png';symlink.symlink_to(capture)
            hardlink=root/'hardlink.png';os.link(capture,hardlink)
            for target in [capture,symlink,hardlink,report,contract]:
                with self.subTest(target=target.name),self.assertRaises(ValueError):
                    m.validate(contract,report,target)
                self.assertEqual(capture.read_bytes(),b'original capture bytes')

    def test_hoe_requires_tool_start_and_every_world_pose(self):
        spec=importlib.util.spec_from_file_location('hoe_native',P/'native_contract.py')
        m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        fixture=fixtures.ContractTests();fixture.setUp()
        try:
            contract=fixture.root/'input.json';contract.write_text('{}');r=fixture.complete_report(contract)
            r['clips']={'hoe-west':r['clips']['hoe-west']}
            base={'real_gpu','four_head_samples_loaded','sample_controls_fit','head_controls_fit','motion_panel_fits','capture_overview'}
            r['checks']={k:v for k,v in r['checks'].items() if k in base or k.startswith('hoe-west-') or k.startswith('capture_hoe-west-')}
            r['output_hashes']={k:v for k,v in r['output_hashes'].items() if 'hoe-west-' in k or k=='overview.png'}
            r['captures']=[k for k in r['captures'] if 'hoe-west-' in k]
            r['samples']=[x for x in r['samples'] if x['clip']=='hoe-west']
            m.check_coverage(r,r['clips'])
            for defect in ['tool_start','world_pose']:
                broken=copy.deepcopy(r)
                if defect=='tool_start':broken['checks'].pop('hoe-west-hat_tool_starts')
                else:broken['output_hashes'].pop('sequence/hoe-west-hat-world-3.png')
                with self.subTest(defect=defect),self.assertRaises(ValueError):m.check_coverage(broken,r['clips'])
        finally:fixture.tearDown()

if __name__=='__main__':unittest.main()
