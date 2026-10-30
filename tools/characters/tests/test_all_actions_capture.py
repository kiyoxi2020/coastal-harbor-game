"""Full native inputs must bind actual selected artifacts and runtime closure."""
import json
from pathlib import Path
import shutil
import sys
import unittest
import tempfile
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import test_all_actions_preflight as fixture
from build_contract import digest


class MalformedCaptureInputTests(unittest.TestCase):
    def test_nonobject_contract_is_rejected_with_valueerror(self):
        import all_actions_capture as capture
        with tempfile.TemporaryDirectory(prefix='coastal-native-bad-input-',dir='/private/tmp') as folder:
            evidence=Path(folder)
            for value in [[],None,3]:
                (evidence/'input-contract.json').write_text(json.dumps(value))
                with self.assertRaises(ValueError):capture.verify_inputs(evidence,evidence)


class FullCaptureSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.fixture=fixture.FullPackagePreflightTests();self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.preflight();self.repo=self.fixture.head.repo
        self.output=self.repo.parent/(self.repo.name+'-native-evidence')
        self.addCleanup(lambda:shutil.rmtree(self.output,ignore_errors=True))
        files={
            'godot2d/project.godot':'config_version=5\n',
            'godot2d/tests/characters/capture_registered_transitions.gd':'extends "res://tests/helper.gd"\n',
            'godot2d/tests/characters/capture_registered_spatial.gd':'extends "res://tests/helper.gd"\n',
            'godot2d/tests/characters/capture_registered_locomotion_timing.gd':'extends "res://tests/helper.gd"\n',
            'godot2d/tests/characters/capture_registered_actions_world.gd':'extends "res://tests/helper.gd"\n',
            'godot2d/tests/helper.gd':'extends SceneTree\n',
            'godot2d/dev/characters/character_motion_lane.tscn':'[gd_scene format=3]\n',
            'godot2d/dev/characters/character_headwear_trial.tscn':'[gd_scene format=3]\n'}
        for rel,text in files.items():
            p=self.repo/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
        source=Path(__file__).resolve().parents[1]
        for name in ['all_actions_capture.py','all_actions_native.py','construction_native.py','native_contract.py','review.py','build.py','build_contract.py','composition_contract.py']:
            dest=self.repo/'tools/characters'/name;dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(source/name,dest)

    def snapshot(self):
        import all_actions_capture as capture
        return capture.snapshot(self.repo,self.fixture.suite_path,self.output,'transitions')

    def test_binds_full_package_runtime_closure_and_capture_plan(self):
        contract=self.snapshot()
        self.assertEqual(len(contract['plan']['clips']),24)
        self.assertEqual(len(contract['transitions']),96)
        self.assertEqual(contract['capture_scene'],'res://dev/characters/character_motion_lane.tscn')
        self.assertIn('godot2d/tests/helper.gd',contract['files'])
        self.assertEqual(contract['files']['godot2d/tests/helper.gd'],digest(self.repo/'godot2d/tests/helper.gd'))
        self.assertTrue(any('/frames/' in rel for rel in contract['files']))
        import all_actions_capture as capture
        self.assertEqual(capture.verify_inputs(self.repo,self.output)['files_verified'],len(contract['files']))

    def test_stale_source_or_runtime_is_rejected_without_receipt(self):
        contract=self.snapshot()
        import all_actions_capture as capture
        for rel in ['godot2d/tests/helper.gd','tools/characters/native_contract.py',next(p for p in contract['files'] if '/frames/' in p)]:
            p=self.repo/rel;old=p.read_bytes();p.write_bytes(old+b'changed')
            with self.assertRaisesRegex(ValueError,'changed'):capture.verify_inputs(self.repo,self.output)
            p.write_bytes(old)

    def test_spatial_observer_uses_original_harbor_scene(self):
        import all_actions_capture as capture
        contract=capture.snapshot(self.repo,self.fixture.suite_path,self.output,'spatial')
        self.assertEqual(contract['capture_scene'],'res://dev/characters/character_headwear_trial.tscn')
        self.assertIn('godot2d/dev/characters/character_headwear_trial.tscn',contract['files'])
        self.assertNotIn('godot2d/dev/characters/character_motion_lane.tscn',contract['files'])

    def test_locomotion_timing_keeps_the_full_eighty_scenario_plan(self):
        import all_actions_capture as capture
        contract=capture.snapshot(self.repo,self.fixture.suite_path,self.output,'locomotion-timing')
        self.assertEqual(contract['capture_scene'],'res://dev/characters/character_motion_lane.tscn')
        scenarios=contract['plan']['time_scenarios']
        self.assertEqual(sum(map(len,scenarios.values())),80)
        self.assertEqual(sum(len(v) for k,v in scenarios.items() if k.startswith(('walk-','run-'))),32)

    def test_full_world_capture_requires_every_rendered_frame(self):
        import all_actions_capture as capture
        contract=capture.snapshot(self.repo,self.fixture.suite_path,self.output,'world')
        self.assertIs(contract['capture_every_rendered_frame'],True)

    def test_rehashed_contract_cannot_drop_an_actual_input_or_weaken_plan(self):
        contract=self.snapshot()
        import all_actions_capture as capture
        path=self.output/'input-contract.json'
        original=json.loads(path.read_text())
        for defect in ['drop-input','weaken-plan']:
            changed=json.loads(json.dumps(original))
            if defect=='drop-input':changed['files'].pop('godot2d/tests/helper.gd')
            else:changed['plan']['clips']['walk-west']['minimum_repetitions']=1
            changed['contract_digest']=capture.contract_digest(changed)
            path.write_text(json.dumps(changed))
            with self.assertRaisesRegex(ValueError,'closure or plan changed'):
                capture.verify_inputs(self.repo,self.output)

    def test_partial_suite_and_undeclared_observer_cannot_create_full_snapshot(self):
        import all_actions_capture as capture
        with self.assertRaisesRegex(ValueError,'observer'):
            capture.snapshot(self.repo,self.fixture.suite_path,self.output,'arbitrary-script')
        self.fixture.suite['schema_version']=1
        self.fixture.suite_path.write_text(json.dumps(self.fixture.suite))
        with self.assertRaises(ValueError):self.snapshot()
        self.assertFalse(self.output.exists())
