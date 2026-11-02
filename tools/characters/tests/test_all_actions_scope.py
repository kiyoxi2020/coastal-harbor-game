"""The full fixed-hat review must not turn partial samples into a full character."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import review


class FullActionScopeTests(unittest.TestCase):
    def setUp(self):
        self.base = {'clips': [], 'required_capabilities': []}
        self.head = {'head_state': 'hair_hat', 'clips': []}
        for action in ['idle', 'walk', 'run', 'hoe', 'water', 'harvest']:
            for direction in ['south', 'west', 'east', 'north']:
                frames = [{'pose_id': f'{action}_{direction}_{i}', 'duration_ms': 80 + i}
                          for i in range(1 if action == 'idle' else 3)]
                self.base['clips'].append({'action_id': action, 'direction': direction,
                                           'frames': frames})
                self.base['required_capabilities'].append({'action_id': action,
                                                           'direction': direction})
                self.head['clips'].append({'action_id': action, 'direction': direction,
                                          'frames': [{'pose_id': f['pose_id']} for f in frames]})

    def validate(self):
        function = getattr(review, 'full_action_clips', None)
        self.assertTrue(callable(function), 'Full-action scope validation is missing')
        return function(self.base, self.head)

    def test_complete_hair_hat_scope_accepts_variable_frame_count(self):
        clips = self.validate()
        self.assertEqual(set(clips), {(a, d) for a in ['idle', 'walk', 'run', 'hoe', 'water', 'harvest']
                                     for d in ['south', 'west', 'east', 'north']})
        self.assertEqual(len(clips[('walk', 'south')]['frames']), 3)

    def test_missing_or_duplicated_clip_cannot_claim_full_scope(self):
        original = copy.deepcopy(self.base)
        for mode in ['missing', 'duplicate', 'extra', 'required']:
            with self.subTest(mode=mode):
                self.base = copy.deepcopy(original)
                if mode == 'missing': self.base['clips'].pop()
                if mode == 'duplicate': self.base['clips'][-1] = copy.deepcopy(self.base['clips'][0])
                if mode == 'extra': self.base['clips'].append(dict(self.base['clips'][0], action_id='collect'))
                if mode == 'required': self.base['required_capabilities'].pop()
                with self.assertRaisesRegex(ValueError, 'Full-action capability'):
                    self.validate()

    def test_other_head_states_are_not_new_deliverables(self):
        for state in ['bare', 'hair', 'hat']:
            with self.subTest(state=state):
                self.head['head_state'] = state
                with self.assertRaisesRegex(ValueError, 'hair_hat'):
                    self.validate()

    def test_head_clip_and_pose_coverage_must_match_base(self):
        original = copy.deepcopy(self.head)
        for mode in ['clip', 'pose', 'order']:
            with self.subTest(mode=mode):
                self.head = copy.deepcopy(original)
                if mode == 'clip': self.head['clips'].pop()
                if mode == 'pose': self.head['clips'][4]['frames'].pop()
                if mode == 'order': self.head['clips'][4]['frames'].reverse()
                with self.assertRaisesRegex(ValueError, 'Full-action head'):
                    self.validate()

    def test_partial_build_cannot_be_relabelled_as_full_package(self):
        import build
        from composition_fixture import CompositionFixture
        fixture = CompositionFixture()
        self.addCleanup(fixture.cleanup)
        repo = fixture.repo
        output = fixture.lib/'builds/partial-head'
        build.construct(repo, fixture.recipes['hair_hat'], output)
        manifest = output/'manifest.json'
        suite = {'kind': 'coastal-character-construction-review-v1', 'schema_version': 2,
                 'resource_root': 'art/characters', 'scope': 'review-only',
                 'head_state': 'hair_hat',
                 'manifest': {'manifest': manifest.relative_to(repo).as_posix(),
                              'sha256': hashlib.sha256(manifest.read_bytes()).hexdigest()},
                 'samples': [], 'canonical_idle': {}, 'runtime': {}}
        path = fixture.lib/'reviews/partial/review.json'
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(suite))
        with self.assertRaisesRegex(ValueError, 'Full-action capability'):
            review.construction_preflight(repo, path)


if __name__ == '__main__':
    unittest.main()
