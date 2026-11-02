"""The tracked main-game PNGs are the real construction oracle."""
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build
from runtime_art_fixture import runtime_png, write_fixture


class RealConstructionTest(unittest.TestCase):
    def test_current_main_game_pixels_survive_strict_construction(self):
        with tempfile.TemporaryDirectory(prefix='coastal-real-build-', dir='/private/tmp') as temp:
            fixture = write_fixture(Path(temp))
            manifest = build.construct(fixture['repo'], fixture['path'], fixture['output'])
            clips = fixture['runtime']['clips']
            self.assertEqual(len(clips), 24)
            self.assertEqual(len(manifest['outputs']), 108)
            self.assertEqual({len(c['frames']) for c in clips}, {1, 4, 6})
            for clip in clips:
                for frame in clip['frames']:
                    with self.subTest(clip=(clip['action'], clip['direction']), pose=frame['pose_id']):
                        path = fixture['output']/f"frames/{clip['action']}/{clip['direction']}/{frame['pose_id']}.png"
                        with Image.open(path) as actual, Image.open(runtime_png(frame)) as expected:
                            self.assertEqual(actual.size, expected.size)
                            pixels = actual.convert('RGBA').tobytes()
                            self.assertEqual(pixels, expected.convert('RGBA').tobytes())
                            self.assertEqual(hashlib.sha256(pixels).hexdigest(), frame['rgba_sha256'])
            build.verify(fixture['repo'], fixture['output'])


if __name__ == '__main__': unittest.main()
