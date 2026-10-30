"""A complete synthetic package uses real construct/verify before review launch."""
import copy
import json
from pathlib import Path
import sys
import unittest
import contextlib
import io
from unittest.mock import patch
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build
import review
import test_registered_headwear as head_fixture
from test_build_contract import sha


class FullPackagePreflightTests(unittest.TestCase):
    def setUp(self):
        self.head = head_fixture.RegisteredHeadwearTests()
        self.head.fixed_profile = True
        self.head.setUp()
        self.addCleanup(self.head.tearDown)
        base = self.head.fixture
        old_base_clips = copy.deepcopy(base.recipe['clips'])
        old_head_clips = copy.deepcopy(self.head.recipe['clips'])
        old_base_rows = copy.deepcopy(base.annotations['records'])
        old_head_rows = json.loads((base.lib/self.head.annotation['file']).read_text())['records']
        old_base_mappings = copy.deepcopy(base.adaptation['mappings'])
        old_head_mappings = {slot: copy.deepcopy(data['mappings'])
                             for slot, data in self.head.adaptations.items()}
        for data in self.head.adaptations.values(): data['mappings'] = []
        base.recipe['clips'] = []; self.head.recipe['clips'] = []
        base.annotations['records'] = []; base.adaptation['mappings'] = []
        head_annotations = []
        actions = {}
        for action in ['idle', 'walk', 'run', 'hoe', 'water', 'harvest']:
            directions = {}
            clips = []
            for direction in ['south', 'west', 'east', 'north']:
                index = 0 if action == 'idle' else 1
                clip = copy.deepcopy(old_base_clips[index])
                head_clip = copy.deepcopy(old_head_clips[index])
                clip.update(action_id=action, direction=direction)
                head_clip.update(action_id=action, direction=direction)
                originals = []
                for i, (frame, head_frame) in enumerate(zip(clip['frames'], head_clip['frames'])):
                    old_pose = frame['pose_id']; pose = f'{action}_{direction}_{i}'
                    frame['pose_id'] = pose; head_frame['pose_id'] = pose
                    for layer in frame['layers']:
                        layer['pose_id'] = pose
                        if layer['slot'] != 'body': layer['view_binding']['mapping_id'] = pose
                    original = {'pose_id': pose, 'duration_ms': frame['duration_ms'],
                                **frame['layers'][0]['texture']}
                    originals.append(original)
                    row = copy.deepcopy(next(r for r in old_base_rows if r['pose_id'] == old_pose))
                    row.update(record_id=pose, pose_id=pose)
                    base.annotations['records'].append(row)
                    head_row = copy.deepcopy(next(r for r in old_head_rows if r['pose_id'] == old_pose))
                    head_row.update(record_id=pose, pose_id=pose)
                    head_annotations.append(head_row)
                    mapping = copy.deepcopy(next(m for m in old_base_mappings if m['mapping_id'] == old_pose))
                    mapping['mapping_id'] = pose
                    mapping['target_pose']['record'] = pose
                    old_texture = base.lib/mapping['texture']['file']
                    with Image.open(old_texture) as image:
                        mapping['texture'] = base.write(base.namespace + '/' + pose + '.png', image.copy())
                    frame['layers'][1]['texture'] = mapping['texture']
                    base.adaptation['mappings'].append(mapping)
                    for layer in head_frame['layers']:
                        role, slot = layer['id'], layer['slot']
                        layer['pose_id'] = pose
                        mapping_id = role + '-' + pose
                        layer['view_binding']['mapping_id'] = mapping_id
                        head_mapping = copy.deepcopy(next(m for m in old_head_mappings[slot]
                                                         if m['mapping_id'] == role + '-' + old_pose))
                        head_mapping.update(mapping_id=mapping_id)
                        head_mapping['target_pose']['record'] = pose
                        head_mapping['texture']['file'] = f'parts/{slot}/adaptations/test/motion/r002/{mapping_id}.png'
                        self.head.adaptations[slot]['mappings'].append(head_mapping)
                pose_path = f'templates/test/motions/motion/actions/{action}/r001/{direction}/poses.json'
                variant = {field: clip[field] for field in ['canvas_px', 'root_anchor_px', 'display_scale']}
                variant['frames'] = originals
                clip['poses'] = base.write(pose_path, {'template_id': 'test', 'action_id': action,
                    'direction': direction, 'variants': {'A': variant}})
                directions[direction] = pose_path
                for row in base.annotations['records'] + head_annotations:
                    if row['pose_id'].startswith(action + '_' + direction + '_'): row['poses'] = clip['poses']
                clips.append(clip)
                self.head.recipe['clips'].append(head_clip)
            path = f'templates/test/motions/motion/actions/{action}/r001/action.json'
            action_ref = base.write(path, {'action_id': action, 'revision': 'r001',
                                           'loop': action in ['idle', 'walk', 'run'], 'directions': directions})
            actions[action] = path
            for clip in clips: clip['action'] = action_ref
            base.recipe['clips'].extend(clips)
        motion_path = base.recipe['motion_set']['file']
        base.recipe['motion_set'] = base.write(motion_path, {'template_id': 'test', 'motion_set_id': 'motion', 'actions': actions})
        base.recipe['required_capabilities'] = [{key: clip[key] for key in ['action_id', 'direction']}
                                                for clip in base.recipe['clips']]
        base.annotation = base.write(base.annotation_path, base.annotations)
        for view in base.adaptation['views']: view['source_pose']['document'] = base.annotation
        for mapping in base.adaptation['mappings']: mapping['target_pose']['document'] = base.annotation
        base.refresh()
        # Explicit finite original-pants/shoes identities, each with real
        # source/view/mapping layers in this deliberately synthetic fixture.
        for slot in ['pants', 'shoes']:
            design = 'original-' + slot
            base.recipe['slots'][slot] = base.write(f'parts/{design}/revisions/r002/design.json',
                {'design_id': design, 'category': slot, 'revision': 'r002'})
            data = copy.deepcopy(base.adaptation)
            data['design_id'] = design
            base.recipe['adaptations'][slot] = base.write(
                f'parts/{design}/adaptations/adult-standard-v1/review-motion-v1/r002/views.json', data)
            for clip in base.recipe['clips']:
                for frame in clip['frames']:
                    layer = copy.deepcopy(frame['layers'][1])
                    layer.update(id=slot, slot=slot)
                    # Mapping textures must belong to this selected design.
                    mapping = next(m for m in data['mappings'] if m['mapping_id'] == frame['pose_id'])
                    with Image.open(base.lib/mapping['texture']['file']) as texture:
                        mapping['texture'] = base.write(f'parts/{design}/adaptations/adult-standard-v1/review-motion-v1/r002/{frame["pose_id"]}.png', texture.copy())
                    layer['texture'] = mapping['texture']
                    frame['layers'].append(layer); frame['layer_order'].append(slot)
            base.recipe['adaptations'][slot] = base.write(base.recipe['adaptations'][slot]['file'], data)
        base.save()
        annotation = json.loads((base.lib/self.head.annotation['file']).read_text())
        annotation['records'] = head_annotations
        self.head.annotation = base.write(self.head.annotation['file'], annotation)
        for data in self.head.adaptations.values():
            for view in data['views']: view['source_pose']['document'] = self.head.annotation
            for mapping in data['mappings']: mapping['target_pose']['document'] = self.head.annotation
        self.head.recipe['base_recipe']['sha256'] = sha(base.path)
        self.head.rebind_hat_compatibility()
        self.head.refresh()
        output = base.lib/'builds/full-hair-hat-r001'
        build.construct(base.repo, self.head.path, output)
        manifest = output/'manifest.json'
        self.suite = {'kind': 'coastal-character-construction-review-v1', 'schema_version': 2,
            'resource_root': 'art/characters', 'scope': 'review-only', 'head_state': 'hair_hat',
            'manifest': {'manifest': manifest.relative_to(base.repo).as_posix(), 'sha256': sha(manifest)},
            'samples': [{'id': clip['action_id'] + '-' + clip['direction'], 'action_id': clip['action_id'],
                         'direction': clip['direction']} for clip in base.recipe['clips'] if clip['action_id'] != 'idle'],
            'canonical_idle': {clip['direction']: [f['pose_id'] for f in clip['frames']]
                               for clip in base.recipe['clips'] if clip['action_id'] == 'idle'}}
        self.suite['runtime'] = {'schema_version': 1, 'movement': {
            'walk': {'base_world_speed': 72}, 'run': {'base_world_speed': 108}},
            'default_speed_factor': 0.75,
            'locomotion_transition': {'kind': 'stable-idle-v1', 'duration_ms': 100},
            'clips': {clip['action_id']+'-'+clip['direction']: {'playback_rate': 1,
                'events': ([{'event_id': 'contact', 'at_ms': clip['frames'][0]['duration_ms'],
                            'pose_id': clip['frames'][1]['pose_id']}]
                           if clip['action_id'] in ['hoe', 'water', 'harvest'] else [])}
                      for clip in base.recipe['clips']}}
        self.suite_path = base.lib/'reviews/full/review.json'

    def preflight(self):
        self.suite_path.parent.mkdir(parents=True, exist_ok=True)
        self.suite_path.write_text(json.dumps(self.suite))
        return review.construction_preflight(self.head.repo, self.suite_path)

    def test_complete_real_built_package_is_accepted(self):
        self.assertEqual(self.preflight(), self.suite)
        self.assertEqual(len(self.suite['samples']), 20)

    def test_fixed_outfit_identity_requires_all_requested_parts(self):
        base = copy.deepcopy(self.head.fixture.recipe)
        base['slots'].pop('pants', None)
        with self.assertRaisesRegex(ValueError, 'Fixed outfit'):
            review.validate_fixed_identity(self.head.fixture.lib, base, self.head.recipe)

    def test_unused_view_is_not_an_actual_input_dependency(self):
        unused = copy.deepcopy(self.head.adaptations['hair']['views'][0])
        unused['view_id'] = 'unused-alternative'
        unused['compatibility'] = {'file': 'parts/hair-chestnut-short-v1/adaptations/adult-standard-v1/review-motion-v1/r002/compatibility/unselected.json', 'sha256': '0'*64}
        self.head.adaptations['hair']['views'].append(unused)
        self.head.refresh()
        output = self.head.fixture.lib/'builds/full-unused-view-r001'
        manifest = build.construct(self.head.repo, self.head.path, output)
        self.assertNotIn(unused['compatibility']['file'], manifest['inputs'])
        self.suite['manifest'] = {'manifest': (output/'manifest.json').relative_to(self.head.repo).as_posix(),
                                 'sha256': sha(output/'manifest.json')}
        self.assertEqual(self.preflight(), self.suite)

    def test_full_package_requires_explicit_runtime_policy(self):
        self.suite.pop('runtime', None)
        with self.assertRaises(ValueError): self.preflight()

    def test_full_review_launcher_targets_full_trial_after_real_preflight(self):
        self.preflight()
        target = self.head.fixture.lib/'reviews/all-actions-construction/review.json'
        target.parent.mkdir(parents=True)
        target.write_text(self.suite_path.read_text())
        output = io.StringIO()
        with patch.object(review, 'REPO', self.head.repo), patch.object(sys, 'argv',
                ['review.py', 'all-actions-construction', '--dry-run']), contextlib.redirect_stdout(output):
            review.main()
        command = json.loads(output.getvalue())
        self.assertIn('res://dev/characters/character_headwear_trial.tscn', command)
        self.assertIn('--construction-suite='+str(target), command)

    def test_complete_build_still_requires_complete_suite_and_canonical_idle(self):
        original = copy.deepcopy(self.suite)
        for mode in ['sample', 'duplicate', 'idle']:
            with self.subTest(mode=mode):
                self.suite = copy.deepcopy(original)
                if mode == 'sample': self.suite['samples'].pop()
                if mode == 'duplicate': self.suite['samples'][-1] = self.suite['samples'][0]
                if mode == 'idle': self.suite['canonical_idle']['north'] = ['idle_south_0']
                with self.assertRaisesRegex(ValueError, 'samples incomplete|Invalid full-action sample|canonical idle differs'):
                    self.preflight()


if __name__ == '__main__':
    unittest.main()
