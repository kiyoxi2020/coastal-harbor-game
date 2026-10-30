"""Frozen templates may use A/B in pose names; arbitrary IDs stay lowercase."""
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import build
import test_registered_adaptations as fixtures

class CanonicalPoseTokenTests(unittest.TestCase):
    def setUp(self):
        self.fixture=fixtures.RegisteredAdaptationTests();self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)

    def rename(self,new,canonical=True):
        f=self.fixture;clip=next(c for c in f.recipe['clips'] if c['action_id']!='idle');frame=clip['frames'][0];old=frame['pose_id']
        frame['pose_id']=new
        for layer in frame['layers']:layer['pose_id']=new
        if canonical:
            data=json.loads((f.lib/clip['poses']['file']).read_text());data['variants'][clip['variant']]['frames'][0]['pose_id']=new
            clip['poses']=f.write(clip['poses']['file'],data)
            for row in f.annotations['records']:
                if row['poses']['file']==clip['poses']['file']:row['poses']=clip['poses']
                if row['pose_id']==old:row['pose_id']=new
            f.annotation=f.write(f.annotation_path,f.annotations)
            for view in f.adaptation['views']:view['source_pose']['document']=f.annotation
            for mapping in f.adaptation['mappings']:mapping['target_pose']['document']=f.annotation

    def test_actual_canonical_uppercase_pose_builds_without_renaming_identity(self):
        self.rename('wave_west_B_0');f=self.fixture;f.check()
        output=f.lib/'builds/canonical-case-r001';manifest=build.construct(f.repo,f.path,output);build.verify(f.repo,output)
        self.assertTrue(any(o['file']=='frames/wave/west/wave_west_B_0.png' for o in manifest['outputs']))

    def test_uppercase_noncanonical_rename_is_still_rejected(self):
        self.rename('wave_west_B_0',canonical=False)
        with self.assertRaisesRegex(ValueError,'Wrong pose order'):self.fixture.check()

    def test_canonical_names_cannot_escape_output_paths(self):
        for value in ['../bad','pose/name','pose.name','pose name','名字']:
            with self.subTest(value=value):
                self.rename(value)
                with self.assertRaises(ValueError):self.fixture.check()

    def test_other_registered_identifiers_stay_lowercase(self):
        f=self.fixture;f.adaptation['views'][0]['view_id']='InvalidUpper'
        for row in f.adaptation['mappings']:row['view_id']='InvalidUpper'
        with self.assertRaisesRegex(ValueError,'Invalid identifier'):f.check()
