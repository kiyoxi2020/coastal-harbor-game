"""Real registered pixels: ownership, shared body, complete cloth and exact west reuse."""
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest
from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parent
SCRIPT = ROOT / 'build_parts.py'
spec = importlib.util.spec_from_file_location('locomotion_parts', SCRIPT) if SCRIPT.exists() else None
module = importlib.util.module_from_spec(spec) if spec else None
if spec:
    spec.loader.exec_module(module)


def equal_visible(a, b):
    if ImageChops.difference(a.getchannel('A'), b.getchannel('A')).getbbox():
        return False
    visible = a.getchannel('A').point(lambda x: 255 if x else 0)
    return all(ImageChops.multiply(channel, visible).getbbox() is None for channel in ImageChops.difference(a, b).split()[:3])


class LocomotionPartsTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(module, 'build_parts.py must implement actual source extraction')

    def test_disjoint_ownership_reconstructs_all_twenty_registered_poses(self):
        self.assertEqual(len(module.pose_ids()), 20)
        for pose_id in module.pose_ids():
            original = module.source_frame('A', pose_id)
            parts = module.partition(original, pose_id)
            reconstructed = Image.new('RGBA', original.size)
            for part in parts.values(): reconstructed.alpha_composite(part)
            self.assertTrue(equal_visible(original, reconstructed), pose_id)

    def test_arm_body_and_cloth_reconstruct_source_without_invented_pixels(self):
        for pose_id in module.new_pose_ids():
            for garment in ['A', 'B']:
                parts = module.partition(module.source_frame(garment, pose_id), pose_id)
                for side in ['arm_left', 'arm_right']:
                    body, cloth = module.split_arm(parts[side], pose_id, side, garment)
                    self.assertTrue(equal_visible(parts[side], Image.alpha_composite(body, cloth)), (pose_id, garment, side))
                    bounds = cloth.getchannel('A').getbbox()
                    for pixel in (cloth.crop(bounds).get_flattened_data() if bounds else []):
                        r, g, b, a = pixel
                        self.assertFalse(a > 240 and r > 100 and r - g >= 45 and g - b >= 25, (pose_id, garment, side, pixel))

    def test_complete_torso_views_have_real_cloth_behind_declared_arm_occlusion(self):
        for pose_id in module.new_pose_ids():
            for garment in ['A', 'B']:
                torso = module.complete_torso(garment, pose_id)
                for point in module.REGIONS['poses'][pose_id]['hidden_cloth_probes']:
                    self.assertGreater(torso.getpixel(tuple(point))[3], 200, (pose_id, garment, point))

    def test_a_bake_exactly_reconstructs_pose_and_b_keeps_actual_a_palms(self):
        module.build()
        palms = {
            'idle_south_0': [(140,535),(370,535)], 'idle_west_0': [(330,540)],
            'idle_east_0': [(207,540)], 'idle_north_0': [(140,535),(370,535)],
            'walk_south_0': [(153,500),(370,512)], 'walk_south_1': [(142,500),(345,490)],
            'walk_south_2': [(140,510),(354,499)], 'walk_south_3': [(155,500),(375,505)],
            'walk_north_0': [(130,540)], 'walk_north_1': [(130,540)],
            'walk_north_2': [(380,540)], 'walk_north_3': [(380,540)],
            'walk_east_0': [(145,525),(345,505)], 'walk_east_1': [(175,535),(335,522)],
            'walk_east_2': [(288,520),(148,520)], 'walk_east_3': [(176,535),(336,522)]}
        for pose in module.new_pose_ids():
            index = module.pose_ids().index(pose)
            source = module.source_frame('A', pose)
            a = Image.open(ROOT / 'baked' / f'A_{index}.png').convert('RGBA')
            self.assertTrue(equal_visible(source, a), pose)
            b = Image.open(ROOT / 'baked' / f'B_{index}.png').convert('RGBA')
            for point in palms[pose]:
                if pose.startswith('walk_east_'):
                    self.assertGreater(source.getpixel(point)[3],240,(pose,point))
                    self.assertGreater(source.getpixel(point)[0]-source.getpixel(point)[1],40,(pose,point))
                self.assertEqual(b.getpixel(point), source.getpixel(point), (pose, point))

    def test_profile_shoulder_and_north_fringe_are_not_old_cream_body(self):
        for pose, points in {'walk_east_0':[(155,456),(173,479),(320,450)], 'idle_east_0':[(165,470)],
                             'walk_north_0':[(342,382),(348,387),(208,518),(292,518)]}.items():
            parts = module.partition(module.source_frame('A',pose),pose)
            for point in points:
                self.assertEqual(parts['body_base'].getpixel(point)[3], 0, (pose, point))

    def test_b_torso_does_not_export_recolored_source_neck_skin(self):
        for pose in module.new_pose_ids():
            torso = module.complete_torso('B',pose)
            bounds = torso.getchannel('A').getbbox()
            for x in range(bounds[0], bounds[2]):
                for y in range(bounds[1], bounds[3]):
                    r,g,b,a = torso.getpixel((x,y))
                    self.assertFalse(a>240 and r>100 and r-g>=45 and g-b>=25, (pose,(x,y),(r,g,b,a)))

    def test_arm_ownership_does_not_capture_shirt_hem_or_trousers(self):
        for pose, point in [('idle_south_0', (194,526)), ('idle_west_0',(203,530)),
                            ('idle_east_0',(254,527)), ('walk_south_2',(203,536)),
                            ('walk_east_0',(270,550))]:
            parts = module.partition(module.source_frame('A',pose),pose)
            for side in ['arm_left','arm_right']:
                self.assertEqual(parts[side].getpixel(point)[3], 0, (pose, side, point))

    def test_cream_collar_and_side_seams_are_cloth_not_shared_body(self):
        for pose, points in {
            'walk_north_0': [(219, 378), (191, 420), (185, 506), (288, 517)],
            'walk_south_0': [(295, 380), (240, 400)],
            'walk_east_1': [(277, 400), (206, 496), (268, 504)]
        }.items():
            parts = module.partition(module.source_frame('A', pose), pose)
            for point in points:
                self.assertEqual(parts['body_base'].getpixel(point)[3], 0, (pose, point))
                cloth_alpha = [parts['torso'].getpixel(point)[3]]
                for side in ['arm_left','arm_right']:
                    cloth_alpha.append(module.split_arm(parts[side],pose,side,'A')[1].getpixel(point)[3])
                self.assertGreater(max(cloth_alpha), 240, (pose, point))

    def test_trouser_highlights_are_not_misclassified_as_cream_cloth(self):
        for pose, point in [('walk_south_1', (215, 517)), ('walk_south_3', (282, 520)),
                            ('walk_east_0', (270, 550)), ('walk_east_2', (256, 550)),
                            ('walk_east_3', (250, 555))]:
            image = module.source_frame('A', pose)
            self.assertEqual(module.partition(image, pose)['body_base'].getpixel(point), image.getpixel(point), (pose, point))

    def test_visible_torso_keeps_actual_pose_source_and_fill_is_only_hidden(self):
        for pose in module.new_pose_ids():
            for garment in ['A', 'B']:
                source = module.source_frame(garment, pose)
                visible = module.partition(source, pose)['torso']
                complete = module.complete_torso(garment, pose)
                for point in [(256, 430), (256, 500)]:
                    if visible.getpixel(point)[3] > 240:
                        self.assertEqual(complete.getpixel(point), visible.getpixel(point), (pose, garment, point))

    def test_final_build_retains_shared_body_and_never_puts_ownership_in_hide_mask(self):
        result = module.build()
        manifest = json.loads((ROOT / 'baked/export-manifest.json').read_text())
        self.assertEqual(len(manifest['frames']), 20)
        self.assertEqual(manifest['schema_version'], 2)
        for pose_id in module.new_pose_ids():
            index = next(i for i, frame in enumerate(manifest['frames']) if frame['pose_id'] == pose_id)
            original = module.source_frame('A', pose_id)
            for garment in ['A', 'B']:
                baked = Image.open(ROOT / 'baked' / f'{garment}_{index}.png').convert('RGBA')
                for box in [(0, 0, 512, 350), (0, 585, 512, 768)]:
                    self.assertTrue(equal_visible(original.crop(box), baked.crop(box)), (pose_id, garment, box))
                layers = manifest['recipes'][garment]['frames'][index]['layers']
                self.assertTrue(all('ownership' not in layer.get('hide_mask', '') for layer in layers))
        records = json.loads((ROOT / 'parts-manifest.json').read_text())['artifacts']
        for record in records:
            if record.get('complete_hidden_cloth'):
                for key in ['visible_mask', 'hidden_mask', 'occlusion_mask']:
                    self.assertIn(key, record, record['path'])
                    self.assertTrue((ROOT / record[key]).is_file(), record[key])
                    self.assertEqual(manifest['source_contract'].get(record[key]), hashlib.sha256((ROOT / record[key]).read_bytes()).hexdigest(), record[key])
                hidden_record = next(r for r in records if r['path'] == record['hidden_mask'])
                self.assertEqual(hidden_record['purpose'], 'hidden_source_extraction')
        self.assertEqual(result['review_status'], 'unverified')

    def test_west_walk_parts_masks_and_baked_pixels_are_exact_reuse(self):
        module.build()
        old = ROOT.parent / 'walk-west-proof-v1'
        old_manifest = json.loads((old / 'baked/export-manifest.json').read_text())
        manifest = json.loads((ROOT / 'baked/export-manifest.json').read_text())
        for i in range(4):
            global_index = next(j for j, frame in enumerate(manifest['frames']) if frame['pose_id'] == f'walk_west_{i}')
            for garment in ['A', 'B']:
                old_frame = old_manifest['recipes'][garment]['frames'][i]
                new_frame = manifest['recipes'][garment]['frames'][global_index]
                for original, copied in zip(old_frame['layers'], new_frame['layers']):
                    self.assertEqual(hashlib.sha256((old / original['source']).read_bytes()).hexdigest(), hashlib.sha256((ROOT / copied['source']).read_bytes()).hexdigest())
                    if 'hide_mask' in original:
                        self.assertEqual(hashlib.sha256((old / original['hide_mask']).read_bytes()).hexdigest(), hashlib.sha256((ROOT / copied['hide_mask']).read_bytes()).hexdigest())
                self.assertEqual(hashlib.sha256((old / 'baked' / old_frame['file']).read_bytes()).hexdigest(), hashlib.sha256((ROOT / 'baked' / new_frame['file']).read_bytes()).hexdigest())


if __name__ == '__main__':
    unittest.main()
