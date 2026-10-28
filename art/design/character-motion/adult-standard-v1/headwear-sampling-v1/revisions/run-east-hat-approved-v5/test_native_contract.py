"""Guard the bounded native rerun without accepting partial or unrelated clips."""
from pathlib import Path
import copy
import importlib.util
import sys
import unittest
from unittest.mock import patch

P=Path(__file__).resolve().parent
sys.path.insert(0,str(P.parents[1]))
import test_contract as fixtures

class BoundedNativeTests(unittest.TestCase):
    def test_called_validation_tools_are_frozen_and_tamper_rejected(self):
        spec=importlib.util.spec_from_file_location('bounded_tools',P/'native_contract.py')
        m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        frozen=m.tool_dependencies()
        helper=Path(m.legacy.__file__).relative_to(m.ROOT).as_posix()
        self.assertIn(helper,frozen)
        self.assertIn(Path(m.legacy.base.__file__).relative_to(m.ROOT).as_posix(),frozen)
        m.assert_tool_dependencies(frozen)
        real_sha=m.sha
        def changed(path):return 'modified-gate' if Path(path).resolve()==Path(m.legacy.__file__).resolve() else real_sha(path)
        with patch.object(m,'sha',side_effect=changed),self.assertRaises(ValueError):m.assert_tool_dependencies(frozen)

    def test_complete_east_only_and_missing_frame_rejection(self):
        spec=importlib.util.spec_from_file_location('bounded',P/'native_contract.py')
        m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        fixture=fixtures.ContractTests();fixture.setUp()
        try:
            contract=fixture.root/'input.json';contract.write_text('{}')
            r=fixture.complete_report(contract)
            r['clips']={'run-east':r['clips']['run-east']}
            r['checks']={k:v for k,v in r['checks'].items() if k.startswith('run-east-') or not any(k.startswith(x) for x in ['hoe-west','water-south','harvest-north']) and not k.startswith('capture_') or k.startswith('capture_run-east-') or k=='capture_overview'}
            r['output_hashes']={k:v for k,v in r['output_hashes'].items() if 'run-east-' in k or k=='overview.png'}
            r['captures']=[k for k in r['captures'] if 'run-east-' in k]
            r['samples']=[x for x in r['samples'] if x['clip']=='run-east']
            ids=m.legacy.IDS.copy();m.check_coverage(r,r['clips']);self.assertEqual(m.legacy.IDS,ids)
            broken=copy.deepcopy(r);broken['output_hashes'].pop('sequence/run-east-hat-world-3.png')
            with self.assertRaises(ValueError):m.check_coverage(broken,r['clips'])
            self.assertEqual(m.legacy.IDS,ids)
            unrelated=copy.deepcopy(r);unrelated['clips']['hoe-west']={}
            with self.assertRaises(ValueError):m.check_coverage(unrelated,r['clips'])
        finally:fixture.tearDown()

if __name__=='__main__':unittest.main()
