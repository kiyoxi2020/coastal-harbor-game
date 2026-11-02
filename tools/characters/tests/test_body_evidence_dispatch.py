"""Body snapshots select their verifier without bypassing observation checks."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import all_actions_evidence as evidence_module
from build_contract import digest


class BodyEvidenceDispatchTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='coastal-body-dispatch-',dir='/private/tmp')
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.evidence=self.root/'evidence';self.evidence.mkdir()

    def inputs(self,body):
        cp=self.evidence/'input-contract.json'
        cp.write_text(json.dumps({'suite_kind':'coastal-body-character-review-v1'} if body else {}))
        (self.evidence/'report.json').write_text(json.dumps({'input_contract_sha256':digest(cp)}))

    def test_body_uses_body_verifier_and_propagates_strict_rejection(self):
        self.inputs(True)
        with patch('body_review.verify_inputs',side_effect=ValueError('body source rejected')) as body, \
             patch('all_actions_capture.verify_inputs',side_effect=ValueError('legacy source rejected')) as legacy:
            with self.assertRaisesRegex(ValueError,'body source rejected'):
                evidence_module.validate_observation(self.root,self.evidence)
            body.assert_called_once_with(self.root,self.evidence)
            legacy.assert_not_called()

    def test_legacy_retains_original_verifier_and_rejection(self):
        self.inputs(False)
        with patch('body_review.verify_inputs',side_effect=ValueError('body source rejected')) as body, \
             patch('all_actions_capture.verify_inputs',side_effect=ValueError('legacy source rejected')) as legacy:
            with self.assertRaisesRegex(ValueError,'legacy source rejected'):
                evidence_module.validate_observation(self.root,self.evidence)
            legacy.assert_called_once_with(self.root,self.evidence)
            body.assert_not_called()

    def test_successful_body_input_check_still_requires_actual_gpu_report(self):
        self.inputs(True)
        with patch('body_review.verify_inputs',return_value={'passed':True}) as body, \
             patch('all_actions_capture.verify_inputs',side_effect=ValueError('wrong dispatch')) as legacy:
            with self.assertRaisesRegex(ValueError,'GPU observation'):
                evidence_module.validate_observation(self.root,self.evidence)
            body.assert_called_once()
            legacy.assert_not_called()


if __name__=='__main__':unittest.main()
