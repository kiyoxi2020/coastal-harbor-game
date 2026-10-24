import unittest
from pathlib import Path
from PIL import Image, ImageChops
import build_parts

ROOT = Path(__file__).resolve().parent


class PartsTests(unittest.TestCase):
    def test_exposed_neck_is_body_not_clothing(self):
        original = Image.open(ROOT / 'registered/v5/walk_w_0.png').convert('RGBA')
        self.assertEqual(build_parts.partition(original, 0)['base'].getpixel((234, 391)), original.getpixel((234, 391)))

    def test_far_hand_border_is_shared_body_and_not_a_garment(self):
        a = build_parts.source_frame('A', 2)
        body, sleeve = build_parts.split_arm(build_parts.partition(a, 2)['far'], 2, 'far', 'A')
        self.assertEqual(body.getpixel((335, 520)), a.getpixel((335, 520)))
        self.assertEqual(sleeve.getpixel((335, 520))[3], 0)

    def test_blue_sleeve_does_not_own_wrist_skin(self):
        b = build_parts.source_frame('B', 2)
        _, sleeve = build_parts.split_arm(build_parts.partition(b, 2)['far'], 2, 'far', 'B')
        self.assertEqual(sleeve.getpixel((371, 494))[3], 0)

    def test_shared_body_does_not_carry_short_sleeve_cuff(self):
        a = build_parts.source_frame('A', 0)
        body, _ = build_parts.split_arm(build_parts.partition(a, 0)['near'], 0, 'near', 'A')
        self.assertEqual(body.getpixel((329, 491))[3], 0)

    def test_disjoint_source_ownership_reconstructs_each_actual_pose(self):
        for index in range(4):
            original = Image.open(ROOT / f'registered/v5/walk_w_{index}.png').convert('RGBA')
            partition = build_parts.partition(original, index)
            result = Image.new('RGBA', original.size)
            for layer in partition.values():
                result.alpha_composite(layer)
            mask = original.getchannel('A').point(lambda a: 255 if a else 0)
            self.assertIsNone(ImageChops.multiply(ImageChops.difference(original, result).convert('RGB').convert('L'), mask).getbbox())
            self.assertIsNone(ImageChops.difference(original.getchannel('A'), result.getchannel('A')).getbbox())

    def test_hidden_fill_has_pixels_behind_front_hand(self):
        for garment in ['A', 'B']:
            torso = build_parts.complete_torso(garment)
            self.assertGreater(torso.getpixel((244, 501))[3], 240)
            self.assertGreater(torso.getpixel((302, 470))[3], 240)

    def test_body_and_sleeve_partition_reconstructs_arm(self):
        for index in range(4):
            original = Image.open(ROOT / f'registered/v5/walk_w_{index}.png').convert('RGBA')
            parts = build_parts.partition(original, index)
            for side in ['near', 'far']:
                body, sleeve = build_parts.split_arm(parts[side], index, side, 'A')
                combined = Image.alpha_composite(body, sleeve)
                delta = ImageChops.difference(combined, parts[side])
                self.assertIsNone(delta.getchannel('A').getbbox())
                visible = parts[side].getchannel('A').point(lambda a: 255 if a else 0)
                for channel in range(3):
                    self.assertIsNone(ImageChops.multiply(delta.getchannel(channel), visible).getbbox())


if __name__ == '__main__':
    unittest.main()
