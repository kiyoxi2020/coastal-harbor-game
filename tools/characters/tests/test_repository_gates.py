import json
from pathlib import Path
import sys
import unittest
import test_build_contract as fixtures
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

class RepositoryGateTests(unittest.TestCase):
    def setUp(self):
        self.fixture=fixtures.ConstructionTests()
        self.fixture.setUp()
        self.repo=self.fixture.repo
        p=self.repo/'godot2d/assets/player-unified-v4/player.png';p.parent.mkdir(parents=True);p.write_bytes(b'approved pixels')
        p=self.repo/'godot2d/scripts/player.gd';p.parent.mkdir(parents=True);p.write_text('extends CharacterBody2D\n')
        p=self.repo/'godot2d/scenes/player.tscn';p.parent.mkdir(parents=True);p.write_text('[node name="Player" type="CharacterBody2D"]\n')
        import check
        self.policy=check.capture_baseline(self.repo)

    def tearDown(self):self.fixture.tearDown()

    def check(self):
        import check
        return check.check_repository(self.repo,self.policy)


    def test_review_cannot_reintroduce_retired_paths(self):
        p=self.repo/'godot2d/dev/characters/rogue.gd';p.parent.mkdir(parents=True)
        p.write_text('const ROOT = "art/design/character-motion/old"\n')
        with self.assertRaisesRegex(ValueError,'retired'):self.check()

    def test_art_cannot_ship_per_batch_builder(self):
        p=self.repo/'art/characters/build_again.py';p.write_text('print("other pipeline")')
        with self.assertRaisesRegex(ValueError,'authoring code'):self.check()

    def test_current_recipe_and_production_baseline_pass(self):
        result=self.check();self.assertEqual(result['strict_recipes'],1)

    def test_old_root_recreation_rejected(self):
        (self.repo/'art/design/character-motion').mkdir(parents=True)
        with self.assertRaisesRegex(ValueError,'retired'):self.check()

    def test_new_production_asset_rejected(self):
        (self.repo/'godot2d/assets/player-unified-v4/new.png').write_bytes(b'new')
        with self.assertRaisesRegex(ValueError,'production'):self.check()

    def test_changed_character_controller_rejected(self):
        (self.repo/'godot2d/scripts/player.gd').write_text('extends Sprite2D\n')
        with self.assertRaisesRegex(ValueError,'production'):self.check()

    def test_new_direct_character_reference_rejected(self):
        (self.repo/'godot2d/scenes/rogue.tscn').write_text('[ext_resource path="res://../art/characters/builds/a.png"]\n')
        with self.assertRaisesRegex(ValueError,'reference'):self.check()

    def test_new_character_body_not_registered_rejected(self):
        (self.repo/'godot2d/scripts/rogue.gd').write_text('extends CharacterBody2D\n')
        with self.assertRaisesRegex(ValueError,'character'):self.check()

    def test_new_legacy_recipe_rejected(self):
        p=self.repo/'art/characters/recipes/rogue/r001.json';p.parent.mkdir();p.write_text('{}')
        with self.assertRaisesRegex(ValueError,'legacy'):self.check()

    def test_orphan_build_rejected(self):
        p=self.repo/'art/characters/builds/rogue/frames/a.png';p.parent.mkdir(parents=True);p.write_bytes(b'png')
        with self.assertRaisesRegex(ValueError,'build'):self.check()

    def test_managed_build_reverified(self):
        import build
        out=self.repo/'art/characters/builds/test-r001'
        build.construct(self.repo,self.fixture.path,out)
        self.assertEqual(self.check()['strict_builds'],1)
        (out/'frames/wave/west/wave_west_0.png').write_bytes(b'bad')
        with self.assertRaisesRegex(ValueError,'SHA'):self.check()

    def test_new_recipe_is_not_silently_skipped(self):
        d=self.fixture.recipe;d['clips'][1]['frames'].pop();self.fixture.save()
        with self.assertRaisesRegex(ValueError,'pose'):self.check()

if __name__=='__main__':unittest.main()
