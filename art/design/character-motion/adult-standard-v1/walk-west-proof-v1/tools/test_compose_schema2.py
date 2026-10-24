"""Schema2 locomotion contracts, diagnostic pixels only; no character artwork."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from PIL import Image
from compose import compose

DIRECTIONS = ('south', 'west', 'east', 'north')


def fixture(root):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    # One real full-frame source may be explicitly reused; pose indices remain distinct.
    image = Image.new('RGBA', (512, 768))
    image.paste((80, 130, 200, 255), (210, 430, 302, 708))
    image.save(root / 'source.png')
    (root / 'source-contract.json').write_text('{"kind":"pixel_fixture_only"}\n')
    frames, actions = [], {}
    for action, count in [('idle', 1), ('walk', 4)]:
        actions[action] = {'loop': True, 'directions': {}}
        for direction in DIRECTIONS:
            poses = []
            for index in range(count):
                pose_id = f'{action}_{direction}_{index}'
                poses.append(pose_id)
                frames.append({'pose_id': pose_id, 'duration_ms': 80 if action == 'walk' else 200,
                               'action': action, 'direction': direction})
            actions[action]['directions'][direction] = poses
    data = {'schema_version': 2, 'template_id': 'adult-standard-v1', 'motion_set_id': 'locomotion-v1',
            'canvas_px': [512, 768], 'root_anchor_px': [256, 708], 'display_scale': 138 / 582,
            'frames': frames, 'actions': actions,
            'move_policy': {'walk': {'base_world_speed': 72, 'playback_rate': .75},
                            'idle': {'base_world_speed': 0, 'playback_rate': 1}},
            'source_contract': {'source-contract.json': hashlib.sha256((root / 'source-contract.json').read_bytes()).hexdigest()},
            'recipes': {recipe: {'frames': [{'pose_id': f['pose_id'], 'layers': [
                {'id': 'diagnostic', 'source': 'source.png', 'offset_px': [0, 0]}
            ]} for f in frames]} for recipe in ['A', 'B']}}
    (root / 'motion.json').write_text(json.dumps(data, indent=2) + '\n')
    return data


class Schema2Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='coastal-locomotion-', dir='/private/tmp')
        self.root = Path(self.tmp.name)
        self.data = fixture(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def bake(self, data=None):
        (self.root / 'motion.json').write_text(json.dumps(self.data if data is None else data))
        return compose(self.root / 'motion.json')

    def test_exports_twenty_real_frames_and_exact_action_contracts(self):
        result = self.bake()
        self.assertEqual(result['schema_version'], 2)
        for key in ['template_id', 'motion_set_id', 'frames', 'actions', 'move_policy', 'source_contract']:
            self.assertEqual(result[key], self.data[key])
        self.assertEqual(len(result['recipes']['A']['frames']), 20)
        for recipe in result['recipes'].values():
            for frame, original in zip(recipe['frames'], self.data['frames']):
                for key in ['pose_id', 'duration_ms', 'action', 'direction']:
                    self.assertEqual(frame[key], original[key])
                path = self.root / 'baked' / frame['file']
                self.assertEqual(frame['sha256'], hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertEqual(result['inputs']['source-contract.json']['sha256'], self.data['source_contract']['source-contract.json'])

    def test_explicit_extra_walk_pose_needs_no_compositor_fork(self):
        frame = {'pose_id': 'walk_north_4', 'duration_ms': 110, 'action': 'walk', 'direction': 'north'}
        self.data['frames'].append(frame)
        self.data['actions']['walk']['directions']['north'].append(frame['pose_id'])
        for recipe in self.data['recipes'].values():
            entry = copy.deepcopy(recipe['frames'][-1])
            entry['pose_id'] = frame['pose_id']
            recipe['frames'].append(entry)
        result = self.bake()
        self.assertEqual(len(result['frames']), 21)
        self.assertEqual(result['recipes']['A']['frames'][-1]['duration_ms'], 110)

    def test_actual_source_dependency_change_invalidates_digest(self):
        first = self.bake()
        (self.root / 'source-contract.json').write_text('{"kind":"changed_fixture"}')
        self.data['source_contract']['source-contract.json'] = hashlib.sha256((self.root / 'source-contract.json').read_bytes()).hexdigest()
        second = self.bake()
        self.assertNotEqual(first['artifact_digest'], second['artifact_digest'])

    def test_rejects_incomplete_or_ambiguous_contract_before_export(self):
        mutations = [
            lambda d: d['actions'].pop('idle'),
            lambda d: d['actions']['walk']['directions'].pop('north'),
            lambda d: d['actions']['walk']['directions']['south'].pop(),
            lambda d: d['actions']['walk']['directions']['south'].__setitem__(1, d['actions']['walk']['directions']['south'][0]),
            lambda d: d['frames'][0].update(action='walk'),
            lambda d: d['frames'][1].update(direction='south'),
            lambda d: d['frames'][1].update(pose_id=d['frames'][0]['pose_id']),
            lambda d: d['frames'][0].update(duration_ms=0),
            lambda d: d['recipes']['B']['frames'].pop(),
            lambda d: d['recipes']['B']['frames'][1].update(pose_id=d['frames'][0]['pose_id']),
            lambda d: d['move_policy']['walk'].update(base_world_speed=-1),
            lambda d: d['move_policy']['walk'].update(playback_rate=0),
            lambda d: d['move_policy']['idle'].update(base_world_speed=72),
            lambda d: d['source_contract'].update({'source-contract.json': '0' * 64}),
            lambda d: d['source_contract'].update({'missing-source.json': '0' * 64}),
            lambda d: d.update(source_contract={}),
            lambda d: d['source_contract'].update({'../external.json': '0' * 64}),
            lambda d: d['recipes']['A']['frames'][0]['layers'][0].update(offset_px=[1, 0]),
        ]
        for mutate in mutations:
            data = copy.deepcopy(self.data)
            mutate(data)
            with self.subTest(mutation=mutations.index(mutate)), self.assertRaises(ValueError):
                self.bake(data)
            self.assertFalse((self.root / 'baked').exists())


if __name__ == '__main__':
    unittest.main()
