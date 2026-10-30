"""Native capture requirements cover the complete package and actual pose counts."""
import copy
import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import construction_native as native
import test_all_actions_scope as scope_fixture


class FullNativePlanTests(unittest.TestCase):
    def setUp(self):
        fixture = scope_fixture.FullActionScopeTests(); fixture.setUp()
        self.base, self.head = fixture.base, fixture.head
        for clip in self.base['clips']:
            clip.update(canvas_px=[512, 768], root_anchor_px=[256, 708], display_scale=138/582)

    def test_plan_requires_all_twentyfour_cells_and_twenty_ten_cycle_groups(self):
        plan = native.full_capture_plan(self.base, self.head)
        self.assertEqual(len(plan['clips']), 24)
        self.assertEqual(sum(c['minimum_repetitions'] == 10 for c in plan['clips'].values()), 20)
        self.assertEqual(sum(c['minimum_repetitions'] == 0 for c in plan['clips'].values()), 4)
        self.assertIn('walk-west-to-run-west', plan['transitions'])
        self.assertIn('run-north-to-walk-north', plan['transitions'])
        self.assertIn('run-east-to-run-north', plan['transitions'])
        self.assertIn('harvest-south-to-idle-south', plan['transitions'])
        self.assertTrue(plan['requires_contact_measurements'])

    def test_variable_pose_counts_drive_every_required_still(self):
        clip = next(c for c in self.base['clips'] if c['action_id']=='run' and c['direction']=='north')
        head = next(c for c in self.head['clips'] if c['action_id']=='run' and c['direction']=='north')
        for i in [3, 4]:
            clip['frames'].append({'pose_id': f'run_north_{i}', 'duration_ms': 90+i})
            head['frames'].append({'pose_id': f'run_north_{i}'})
        plan = native.full_capture_plan(self.base, self.head)
        self.assertEqual(plan['clips']['run-north']['pose_ids'][-1], 'run_north_4')
        for name in ['stills/run-north-dark-4.png', 'stills/run-north-light-4.png', 'world/run-north-pose-4.png']:
            self.assertIn(name, plan['required_pngs'])
        self.assertNotIn('stills/run-north-dark-5.png', plan['required_pngs'])

    def test_partial_or_other_head_scope_cannot_create_full_native_plan(self):
        for mode in ['partial', 'head']:
            base, head = copy.deepcopy(self.base), copy.deepcopy(self.head)
            if mode == 'partial': base['clips'].pop()
            else: head['head_state'] = 'hat'
            with self.assertRaises(ValueError): native.full_capture_plan(base, head)
