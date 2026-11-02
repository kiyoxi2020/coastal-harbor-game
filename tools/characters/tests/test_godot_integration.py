"""Godot delivery keeps the strict build's pixels, timing and review identity."""
import copy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import godot_integration as integration

from runtime_art_fixture import (REPO, BUILD, PACKAGE, FRAMES, animation_inputs,
                                 runtime_manifest, write_fixture)
import build


class AnimationDataTests(unittest.TestCase):
    def setUp(self):
        self.recipe, self.manifest = animation_inputs(runtime_manifest())

    def test_runtime_oracle_matches_default_player(self):
        scene = (REPO/'godot2d/scenes/actors/player.tscn').read_text()
        frames_path = 'res://' + FRAMES.relative_to('godot2d').as_posix()
        self.assertIn('path="' + frames_path + '"', scene)
        self.assertEqual(runtime_manifest()['sprite_frames']['file'], FRAMES.as_posix())

    def clips(self):
        return integration.animation_data(self.recipe, self.manifest['outputs'], 'res://assets/test')

    def test_variable_frames_and_exact_millisecond_timing(self):
        clips = self.clips()
        self.assertEqual(len(clips), 24)
        self.assertEqual(sum(len(c['frames']) for c in clips), 108)
        self.assertEqual({len(c['frames']) for c in clips}, {1, 4, 6})
        for source, clip in zip(self.recipe['clips'], clips):
            self.assertEqual([f['duration_ms'] for f in clip['frames']],
                             [f['duration_ms'] for f in source['frames']])
            self.assertEqual(clip['loop'], source['action_id'] in {'idle', 'walk', 'run'})
        text = integration.sprite_frames(clips)
        self.assertIn('"speed": 1000.0', text)
        self.assertIn('&"idle_south"', text)

    def test_actual_pixel_digest_is_carried_for_godot_import_validation(self):
        frames = [frame for clip in self.clips() for frame in clip['frames']]
        self.assertEqual([f['rgba_sha256'] for f in frames],
                         [f['rgba_sha256'] for f in self.manifest['outputs']])

    def test_missing_action_rejected(self):
        self.recipe['clips'].pop()
        with self.assertRaisesRegex(ValueError, '24|capabilit'): self.clips()

    def test_duplicate_clip_rejected(self):
        self.recipe['clips'][-1] = copy.deepcopy(self.recipe['clips'][0])
        with self.assertRaisesRegex(ValueError, '24|duplicate|capabilit'): self.clips()

    def test_missing_output_rejected(self):
        self.manifest['outputs'].pop()
        with self.assertRaisesRegex(ValueError, 'output'): self.clips()

    def test_extra_output_rejected(self):
        self.manifest['outputs'].append(copy.deepcopy(self.manifest['outputs'][0]))
        with self.assertRaisesRegex(ValueError, 'output'): self.clips()

    def test_inconsistent_root_rejected(self):
        self.recipe['clips'][0]['root_anchor_px'][0] += 1
        with self.assertRaisesRegex(ValueError, 'geometry'): self.clips()

    def test_body_reference_cannot_omit_tools(self):
        self.recipe['clips'][0]['variant'] = 'body-reference'
        with self.assertRaisesRegex(ValueError, 'visible'): self.clips()

    def test_nonpositive_duration_rejected(self):
        self.recipe['clips'][0]['frames'][0]['duration_ms'] = 0
        with self.assertRaisesRegex(ValueError, 'duration'): self.clips()


class IntegrationPackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='coastal-godot-integration-', dir='/private/tmp')
        cls.repo = Path(cls.temp.name)
        fixture = write_fixture(cls.repo)
        build.construct(cls.repo, fixture['path'], cls.repo/BUILD)
        cls.original = integration.create(cls.repo, cls.repo / BUILD, cls.repo / PACKAGE, cls.repo / FRAMES)
        cls.backup = cls.repo / 'backup'
        shutil.copytree(cls.repo / PACKAGE, cls.backup)
        cls.frames_bytes = (cls.repo / FRAMES).read_bytes()

    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()

    def tearDown(self):
        shutil.rmtree(self.repo / PACKAGE)
        shutil.copytree(self.backup, self.repo / PACKAGE)
        (self.repo / FRAMES).write_bytes(self.frames_bytes)

    def verify(self): return integration.verify(self.repo, self.repo / PACKAGE / 'manifest.json')

    def test_roundtrip_and_review_only_source(self):
        self.assertEqual(self.verify(), self.original)
        self.assertFalse(self.original['production_release'])
        self.assertEqual(self.original['status'], 'local-development-integration')
        self.assertFalse(json.loads((self.repo / BUILD / 'manifest.json').read_text())['release_eligible'])

    def test_modified_authoring_recipe_is_rejected_by_strict_verifier(self):
        manifest = json.loads((self.repo/BUILD/'manifest.json').read_text())
        path = self.repo/'art/characters'/manifest['recipe']
        original = path.read_bytes()
        try:
            recipe = json.loads(original)
            recipe['clips'][0]['frames'][0]['duration_ms'] += 1
            path.write_text(json.dumps(recipe))
            with self.assertRaisesRegex(ValueError, 'SHA|recipe|input|timing'):
                self.verify()
        finally:
            path.write_bytes(original)

    def test_output_overwrite_rejected(self):
        with self.assertRaisesRegex(ValueError, 'exists'):
            integration.create(self.repo, self.repo / BUILD, self.repo / PACKAGE, self.repo / FRAMES)

    def test_corrupt_runtime_png_rejected(self):
        next((self.repo / PACKAGE / 'frames').rglob('*.png')).write_bytes(b'corrupted')
        with self.assertRaisesRegex(ValueError, 'SHA|pixel'): self.verify()

    def test_modified_timing_rejected(self):
        path = self.repo / PACKAGE / 'manifest.json'
        data = json.loads(path.read_text())
        data['clips'][0]['frames'][0]['duration_ms'] += 1
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, 'manifest|binding'): self.verify()

    def test_modified_spriteframes_rejected(self):
        (self.repo / FRAMES).write_text(self.frames_bytes.decode().replace('1000.0', '999.0'))
        with self.assertRaisesRegex(ValueError, 'SpriteFrames'): self.verify()

    def test_unlisted_runtime_file_rejected(self):
        (self.repo / PACKAGE / 'unlisted.png').write_bytes(b'pixels')
        with self.assertRaisesRegex(ValueError, 'Unexpected'): self.verify()

    def test_import_pixel_processing_tamper_rejected(self):
        path = next((self.repo / PACKAGE / 'frames').rglob('*.png'))
        Path(str(path) + '.import').write_text('[params]\nprocess/fix_alpha_border=true\n')
        with self.assertRaisesRegex(ValueError, 'Import'): self.verify()

    def test_symlink_frame_rejected(self):
        path = next((self.repo / PACKAGE / 'frames').rglob('*.png'))
        source = self.backup / path.relative_to(self.repo / PACKAGE)
        path.unlink()
        path.symlink_to(source)
        with self.assertRaisesRegex(ValueError, 'symlink'): self.verify()

    def test_forged_release_rejected(self):
        path = self.repo / PACKAGE / 'manifest.json'
        data = json.loads(path.read_text()); data['production_release'] = True
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, 'manifest|binding'): self.verify()


class RuntimeOnlyPackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='coastal-runtime-only-', dir='/private/tmp')
        cls.repo = Path(cls.temp.name)
        shutil.copytree(REPO/PACKAGE, cls.repo/PACKAGE)
        (cls.repo/FRAMES).parent.mkdir(parents=True)
        shutil.copyfile(REPO/FRAMES, cls.repo/FRAMES)
        cls.original = runtime_manifest()
        cls.backup = cls.repo/'backup'
        shutil.copytree(cls.repo/PACKAGE, cls.backup)
        cls.frames_bytes = (cls.repo/FRAMES).read_bytes()

    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()

    def tearDown(self):
        shutil.rmtree(self.repo/PACKAGE)
        shutil.copytree(self.backup, self.repo/PACKAGE)
        (self.repo/FRAMES).write_bytes(self.frames_bytes)

    def verify(self):
        return integration.verify_runtime(self.repo, self.repo/PACKAGE/'manifest.json')

    def manifest(self, change):
        path = self.repo/PACKAGE/'manifest.json'
        value = json.loads(path.read_text())
        change(value)
        path.write_text(json.dumps(value))

    def test_runtime_verification_does_not_require_authoring_or_generator(self):
        for key in ['source_build', 'recipe', 'generator']:
            self.assertFalse((self.repo/self.original[key]['file']).exists())
        self.assertFalse((self.repo/'art').exists())
        self.assertEqual(self.verify(), self.original)
        self.assertEqual(len(self.original['clips']), 24)
        self.assertEqual(sum(len(c['frames']) for c in self.original['clips']), 108)

    def test_strict_verification_still_requires_authoring(self):
        with self.assertRaises((ValueError, OSError)):
            integration.verify(self.repo, self.repo/PACKAGE/'manifest.json')

    def test_finder_metadata_is_not_a_game_resource(self):
        for folder in ['', 'frames', 'frames/harvest']:
            (self.repo/PACKAGE/folder/'.DS_Store').write_bytes(b'Finder metadata')
        self.assertEqual(self.verify(), self.original)

    def test_runtime_png_sha_and_rgba_tampering_rejected(self):
        path = next((self.repo/PACKAGE/'frames').rglob('*.png'))
        path.write_bytes(b'corrupted')
        with self.assertRaises(ValueError): self.verify()

    def test_runtime_manifest_rgba_digest_tampering_rejected(self):
        self.manifest(lambda d: d['clips'][0]['frames'][0].update(rgba_sha256='0'*64))
        with self.assertRaises(ValueError): self.verify()

    def test_runtime_timing_tampering_rejected_by_exact_spriteframes(self):
        self.manifest(lambda d: d['clips'][0]['frames'][0].update(duration_ms=1001))
        with self.assertRaises(ValueError): self.verify()

    def test_runtime_import_pixel_processing_tampering_rejected(self):
        path = next((self.repo/PACKAGE/'frames').rglob('*.png'))
        Path(str(path)+'.import').write_text('[params]\nprocess/premult_alpha=true\n')
        with self.assertRaises(ValueError): self.verify()

    def test_runtime_spriteframes_and_unlisted_files_rejected(self):
        (self.repo/FRAMES).write_text(self.frames_bytes.decode().replace('1000.0','999.0'))
        with self.assertRaises(ValueError): self.verify()
        (self.repo/FRAMES).write_bytes(self.frames_bytes)
        (self.repo/PACKAGE/'extra.png').write_bytes(b'extra')
        with self.assertRaises(ValueError): self.verify()

    def test_runtime_missing_clip_duplicate_pose_and_unsafe_paths_rejected(self):
        for defect in ['clip', 'duplicate', 'texture', 'recipe', 'build', 'geometry', 'duration']:
            with self.subTest(defect=defect):
                value = copy.deepcopy(self.original)
                if defect == 'clip': value['clips'].pop()
                if defect == 'duplicate': value['clips'][0]['frames'].append(copy.deepcopy(value['clips'][0]['frames'][0]))
                if defect == 'texture': value['clips'][0]['frames'][0]['texture'] = 'res://../outside.png'
                if defect == 'recipe': value['recipe']['file'] = 'art/characters/recipes/../../outside.json'
                if defect == 'build': value['source_build']['file'] = 'art/characters/builds/../../outside.json'
                if defect == 'geometry': value['geometry']['canvas_px'] = [1, 1]
                if defect == 'duration': value['clips'][0]['frames'][0]['duration_ms'] = True
                (self.repo/PACKAGE/'manifest.json').write_text(json.dumps(value))
                with self.assertRaises(ValueError): self.verify()


if __name__ == '__main__': unittest.main()
