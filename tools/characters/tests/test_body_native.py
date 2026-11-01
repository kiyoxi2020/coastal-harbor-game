"""Frozen input tests with tiny strict assets; no native/physical claims."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import body_native
import test_build_contract as fixtures
from build import construct


class BodyNativeInputsTests(unittest.TestCase):
    def setUp(self):
        f=fixtures.ConstructionTests();f.setUp();self.addCleanup(f.tearDown);self.fixture=f
        self.repo=f.repo
        f.recipe.update(schema_version=3,slots={'body':None},adaptations={})
        for clip in f.recipe['clips']:
            pd=f.lib/clip['poses']['file'];poses=json.loads(pd.read_text())
            for frame,original in zip(clip['frames'],poses['variants']['A']['frames']):
                layer=next(l for l in frame['layers'] if l['slot']=='body')
                frame['layers']=[layer];frame['layer_order']=['body'];original.update(layer['texture'])
            pd.write_text(json.dumps(poses));clip['poses']['sha256']=hashlib.sha256(pd.read_bytes()).hexdigest()
        f.save();self.output=f.lib/'builds/strict';construct(f.repo,f.path,self.output)
        clip=f.recipe['clips'][0];frame=clip['frames'][0];ref=frame['layers'][0]['texture']
        self.points=f.repo/'points.json'
        self.points.write_text(json.dumps({'kind':'coastal-independent-actual-farm-contact-source-review-v1','rows':[{
            'action':clip['action_id'],'direction':clip['direction'],'pose_id':frame['pose_id'],'variant':clip['variant'],
            'canonical_pose_document':clip['poses'],'canonical_reference':ref,'full_original_or_legacy_derived_source':ref,
            'whole_frame_translation_px':[0,0],'canvas_px':clip['canvas_px'],'root_anchor_px':clip['root_anchor_px'],
            'display_scale':clip['display_scale'],'target':{'kind':'soil-candidate','source_ground_contact_proven':False},
            'points':[{'id':'material','canonical_px':[0,0],'source_px':[0,0],'RGBA':[10,20,30,255],
                       'material':'synthetic fixture pixel','visible':True,'hidden_mechanical_contact_observable':False}]}]}))
        for name in body_native.OBSERVER_INPUTS:
            p=f.repo/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('# input-only fixture\n')
        for name in ['build.py','build_contract.py','composition_contract.py']:
            p=f.repo/'tools/characters'/name;p.parent.mkdir(parents=True,exist_ok=True)
            p.write_bytes((Path(__file__).resolve().parents[1]/name).read_bytes())
        self.evidence=f.repo/'native'

    def test_freezes_actual_build_points_and_observer_before_capture(self):
        c=body_native.snapshot(self.repo,self.output,self.points,self.evidence)
        self.assertEqual(len(c['plan']),4);self.assertEqual(c['observer'],'source-poses')
        self.assertEqual(c['source_points']['sha256'],hashlib.sha256(self.points.read_bytes()).hexdigest())
        self.assertTrue(body_native.verify_inputs(self.repo,self.evidence)['passed'])
        self.assertEqual({p.name for p in self.evidence.iterdir()},{'input-contract.json'})
        with self.assertRaises(ValueError):body_native.snapshot(self.repo,self.output,self.points,self.evidence)

    def test_observer_points_or_source_changes_invalidate_capture(self):
        body_native.snapshot(self.repo,self.output,self.points,self.evidence)
        for path in [self.repo/body_native.OBSERVER_INPUTS[0],self.points]:
            old=path.read_bytes();path.write_bytes(old+b' ')
            with self.assertRaises(ValueError):body_native.verify_inputs(self.repo,self.evidence)
            path.write_bytes(old)
        self.assertTrue(body_native.verify_inputs(self.repo,self.evidence)['passed'])

    def test_rehashed_contract_cannot_drop_pose_or_dependencies(self):
        body_native.snapshot(self.repo,self.output,self.points,self.evidence)
        cp=self.evidence/'input-contract.json';original=cp.read_text()
        for mutate in [lambda c:c['plan'].pop(),lambda c:c['files'].pop(next(iter(c['files'])))]:
            c=json.loads(original);mutate(c);c['contract_digest']=body_native.contract_digest(c);cp.write_text(json.dumps(c))
            with self.assertRaises(ValueError):body_native.verify_inputs(self.repo,self.evidence)

    def test_head_or_clothing_recipe_cannot_enter_bare_body_observer(self):
        original=self.fixture.recipe['slots'];self.fixture.recipe['slots']={'body':None,'top':{}}
        self.fixture.save()
        with self.assertRaises(ValueError):body_native.snapshot(self.repo,self.output,self.points,self.evidence)
        self.assertFalse(self.evidence.exists());self.fixture.recipe['slots']=original

    def test_project_parent_literal_is_not_a_runtime_resource_escape(self):
        p=self.repo/'godot2d/dev/characters/character_walk_trial.gd'
        p.write_text('var repo=ProjectSettings.globalize_path("res://..")\n')
        body_native.snapshot(self.repo,self.output,self.points,self.evidence)
        self.assertTrue(body_native.verify_inputs(self.repo,self.evidence)['passed'])
