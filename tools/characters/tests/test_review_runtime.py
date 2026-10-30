"""Reject ambiguous timing or events that do not belong to a real pose."""
import copy
import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import review


class ReviewRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.clips = {(action, direction): {'frames': [
            {'pose_id': action+'_'+direction+'_0', 'duration_ms': 80},
            {'pose_id': action+'_'+direction+'_1', 'duration_ms': 120}]}
            for action in ['idle', 'walk', 'run', 'hoe', 'water', 'harvest']
            for direction in ['south', 'west', 'east', 'north']}
        self.runtime = {'schema_version': 1, 'movement': {
            'walk': {'base_world_speed': 72}, 'run': {'base_world_speed': 108}},
            'default_speed_factor': 0.75,
            'locomotion_transition': {'kind': 'stable-idle-v1', 'duration_ms': 100},
            'clips': {action+'-'+direction: {'playback_rate': 1, 'events': (
                [{'event_id': 'contact', 'at_ms': 80, 'pose_id': action+'_'+direction+'_1'}]
                if action in ['hoe', 'water', 'harvest'] else [])}
                for action, direction in self.clips}}

    def test_explicit_stable_transition_and_pose_bound_events_accepted(self):
        self.assertIs(review.validate_runtime(self.runtime, self.clips), self.runtime)

    def test_missing_phase_policy_cannot_inherit_legacy_frame_indices(self):
        del self.runtime['locomotion_transition']
        with self.assertRaises(ValueError): review.validate_runtime(self.runtime, self.clips)

    def test_missing_clip_invalid_speed_and_unbounded_events_rejected(self):
        for mode in ['clip', 'speed', 'rate', 'movement-rate', 'pose', 'time', 'duplicate', 'order', 'loop-event', 'policy']:
            with self.subTest(mode=mode):
                data = copy.deepcopy(self.runtime)
                event = data['clips']['hoe-west']['events'][0]
                if mode == 'clip': del data['clips']['idle-north']
                if mode == 'speed': data['movement']['walk']['base_world_speed'] = True
                if mode == 'rate': data['clips']['hoe-west']['playback_rate'] = 0
                if mode == 'movement-rate': data['clips']['walk-west']['playback_rate'] = 2
                if mode == 'pose': event['pose_id'] = 'hoe_east_1'
                if mode == 'time': event['at_ms'] = 79
                if mode == 'duplicate': data['clips']['hoe-west']['events'].append(copy.deepcopy(event))
                if mode == 'order': data['clips']['hoe-west']['events'].append({'event_id': 'ready', 'at_ms': 0, 'pose_id': 'hoe_west_0'})
                if mode == 'loop-event': data['clips']['walk-west']['events'] = [event]
                if mode == 'policy': data['locomotion_transition']['kind'] = 'same-frame-index'
                with self.assertRaises(ValueError): review.validate_runtime(data, self.clips)
