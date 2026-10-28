"""Real accepted artwork is the oracle, not a duplicate of the compositor."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build

REPO = Path(__file__).resolve().parents[3]

class RealConstructionTest(unittest.TestCase):
    def test_west_hoe_and_idle_exact_accepted_rgba(self):
        recipe = REPO/'art/characters/recipes/wardrobe-hoe-west/r002.json'
        original = json.loads((REPO/'art/characters/builds/wardrobe-hoe-west-r001/sample.json').read_text())
        with tempfile.TemporaryDirectory(prefix='coastal-real-build-',dir='/private/tmp') as temp:
            output = Path(temp)/'result'
            manifest = build.construct(REPO,recipe,output)
            self.assertEqual(len(manifest['outputs']),5)
            for action, frames in [('hoe', original['frames']), ('idle', [original['idle']])]:
                for frame in frames:
                    with self.subTest(pose=frame['pose_id']):
                        current = output/f"frames/{action}/west/{frame['pose_id']}.png"
                        with Image.open(current) as actual, Image.open(REPO/'art/characters'/frame['file']) as expected:
                            self.assertEqual(actual.size,expected.size)
                            self.assertEqual(actual.convert('RGBA').tobytes(),expected.convert('RGBA').tobytes())
            build.verify(REPO,output)

if __name__ == '__main__':unittest.main()
