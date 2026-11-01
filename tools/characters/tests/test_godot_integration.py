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

REPO = Path(__file__).resolve().parents[3]
BUILD = Path('art/characters/builds/adult-standard-v2-visible-r001')
PACKAGE = Path('godot2d/assets/characters/integrations/adult-standard-v2-visible-r001')
FRAMES = Path('godot2d/resources/player_body_frames.tres')


class AnimationDataTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads((REPO / BUILD / 'manifest.json').read_text())
        self.recipe = json.loads((REPO / 'art/characters' / self.manifest['recipe']).read_text())

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
        manifest = json.loads((REPO / BUILD / 'manifest.json').read_text())
        for relative in manifest['inputs']:
            source = REPO / 'art/characters' / relative
            target = cls.repo / 'art/characters' / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        shutil.copytree(REPO / BUILD, cls.repo / BUILD)
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


if __name__ == '__main__': unittest.main()
