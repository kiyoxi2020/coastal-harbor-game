"""Metadata assembly retains the strict builder as the only image compositor."""
import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build
import recipe_assembly
import test_all_actions_preflight as fixtures


class RecipeAssemblyTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.FullPackagePreflightTests(); self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.repo = self.fixture.head.repo
        self.output = self.fixture.head.fixture.lib/'builds/full-hair-hat-r001'

    def test_real_build_union_deduplicates_only_identical_idle_and_preserves_pixels(self):
        # Split one actually constructed fixture into two authoritative parent
        # builds, sharing the exact south idle and no other capability.
        parent = self.fixture.head
        base = parent.fixture
        parents = []
        original_base = copy.deepcopy(base.recipe)
        original_head = copy.deepcopy(parent.recipe)
        for index, action in enumerate(['walk', 'run']):
            body = copy.deepcopy(original_base)
            body['recipe_id']=f'parent-base-{index}'
            body['clips'] = [c for c in body['clips'] if c['direction']=='south' and c['action_id'] in ['idle',action]]
            body['required_capabilities'] = [{k:c[k] for k in ['action_id','direction']} for c in body['clips']]
            body_ref=base.write(f"recipes/{body['recipe_id']}/{body['revision']}.json",body)
            head = copy.deepcopy(original_head)
            head['recipe_id']=f'parent-head-{index}'
            head['base_recipe']=body_ref
            head['clips'] = [c for c in head['clips'] if c['direction']=='south' and c['action_id'] in ['idle',action]]
            head_ref=base.write(f"recipes/{head['recipe_id']}/{head['revision']}.json",head)
            output=base.lib/f'builds/assembly-parent-{index}'
            build.construct(self.repo,base.lib/head_ref['file'],output)
            parents.append(output)
        result=recipe_assembly.assemble(self.repo,parents,'assembled-test','r001')
        output=base.lib/'builds/assembled-test-r001'
        manifest=build.construct(self.repo,result,output)
        build.verify(self.repo,output)
        self.assertEqual(len(manifest['outputs']),7)
        merged=json.loads(result.read_text())
        self.assertEqual(len(merged['clips']),3)
        # Namespace-qualified mapping IDs must not change intrinsic hat/hair
        # compatibility claims; construct/verify above actually checks this.
        self.assertEqual(merged['head_state'],'hair_hat')
        snapshots=list((base.lib/'sources/registered-recipe-assembly-v1/metadata').glob('*parent-*.json'))
        self.assertEqual(len(snapshots),4)
        for path in snapshots:
            snapshot=json.loads(path.read_text())
            self.assertEqual(snapshot['kind'],'coastal-recipe-authoring-snapshot-v1')
            self.assertEqual(json.loads(snapshot['original_json'])['kind'],'coastal-character-construction-v1')

    def test_duplicate_motion_rejected_before_authoring_files_written(self):
        with self.assertRaisesRegex(ValueError,'Duplicate nonidle'):
            recipe_assembly.assemble(self.repo,[self.output,self.output],'invalid-test','r001')
        self.assertFalse((self.repo/'art/characters/recipes/invalid-test/r001.json').exists())
