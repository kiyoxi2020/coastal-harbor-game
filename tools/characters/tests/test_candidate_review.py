"""Bounded internal review uses the same strict artifacts, without full claims."""
import copy
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build
import review
import test_all_actions_preflight as full_fixture
from test_build_contract import sha


class CandidateReviewTests(unittest.TestCase):
    def setUp(self):
        self.full = full_fixture.FullPackagePreflightTests(); self.full.setUp()
        self.addCleanup(self.full.doCleanups)
        self.head = self.full.head; base = self.head.fixture
        base.recipe['clips'] = [c for c in base.recipe['clips']
                                if c['direction']=='west' and c['action_id'] in ['idle', 'walk']]
        base.recipe['required_capabilities'] = [{k:c[k] for k in ['action_id','direction']}
                                                 for c in base.recipe['clips']]
        base.save()
        self.head.recipe['base_recipe']['sha256'] = sha(base.path)
        self.head.recipe['clips'] = [c for c in self.head.recipe['clips']
                                    if c['direction']=='west' and c['action_id'] in ['idle','walk']]
        self.head.refresh()
        output = base.lib/'builds/candidate-hair-hat-r001'
        build.construct(base.repo, self.head.path, output)
        self.suite = copy.deepcopy(self.full.suite)
        self.suite.update(kind='coastal-character-construction-candidate-v1', schema_version=1,
            scope='internal-review-only', capabilities=base.recipe['required_capabilities'],
            manifest={'manifest':(output/'manifest.json').relative_to(base.repo).as_posix(),
                      'sha256':sha(output/'manifest.json')},
            samples=[{'id':'walk-west','action_id':'walk','direction':'west'}],
            canonical_idle={'west':['idle_west_0']})
        self.suite['runtime']['clips'] = {k:v for k,v in self.suite['runtime']['clips'].items()
                                          if k in ['idle-west','walk-west']}
        self.path = base.lib/'reviews/candidate/review.json'

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.suite))

    def test_actual_bounded_build_accepted_only_as_internal_candidate(self):
        self.save()
        self.assertEqual(review.candidate_preflight(self.head.repo,self.path),self.suite)
        with self.assertRaises(ValueError): review.construction_preflight(self.head.repo,self.path)

    def test_candidate_cannot_claim_missing_capabilities_idle_or_fixed_parts(self):
        original = copy.deepcopy(self.suite)
        for defect in ['capability','idle','scope','sample']:
            with self.subTest(defect=defect):
                self.suite = copy.deepcopy(original)
                if defect=='capability': self.suite['capabilities'].append({'action_id':'run','direction':'west'})
                if defect=='idle': self.suite['canonical_idle']['west']=['idle_south_0']
                if defect=='scope': self.suite['scope']='review-only'
                if defect=='sample': self.suite['samples'].append({'id':'run-west','action_id':'run','direction':'west'})
                self.save()
                with self.assertRaises(ValueError):review.candidate_preflight(self.head.repo,self.path)
