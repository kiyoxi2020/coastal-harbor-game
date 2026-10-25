"""Protect original pixels during whole-frame registration; not art acceptance."""
import importlib.util
from pathlib import Path
import unittest
from PIL import Image

ROOT = Path(__file__).resolve().parent

class RegistrationTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('run_candidate', ROOT / 'build_candidate.py')
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def test_translation_preserves_rgba_without_part_transforms(self):
        source = Image.new('RGBA', (512, 768))
        source.putpixel((200, 500), (31, 74, 100, 127))
        source.putpixel((300, 700), (50, 20, 80, 255))
        out = self.module.register_frame(source, (2, -3))
        self.assertEqual(out.getpixel((202, 497)), (31, 74, 100, 127))
        self.assertEqual(out.getpixel((302, 697)), (50, 20, 80, 255))
        self.assertEqual(sum(out.getchannel('A').histogram()[1:]), 2)

    def test_visible_crop_is_rejected(self):
        source = Image.new('RGBA', (512, 768))
        source.putpixel((511, 700), (1, 2, 3, 255))
        with self.assertRaisesRegex(ValueError, 'crop'):
            self.module.register_frame(source, (1, 0))

    def test_only_recorded_alpha_one_border_noise_may_be_cropped(self):
        source = Image.new('RGBA', (512, 768))
        source.putpixel((511, 767), (1, 2, 3, 1))
        source.putpixel((200, 500), (100, 20, 80, 254))
        out = self.module.register_frame(source, (0, 11))
        self.assertEqual(out.getpixel((200, 511)), (100, 20, 80, 254))

    def test_noninteger_offset_is_rejected(self):
        with self.assertRaises(ValueError):
            self.module.register_frame(Image.new('RGBA', (512, 768)), (0.5, 0))

if __name__ == '__main__': unittest.main()
