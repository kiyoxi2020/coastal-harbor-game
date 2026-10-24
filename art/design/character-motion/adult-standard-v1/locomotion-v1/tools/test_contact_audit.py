import unittest
import contact_audit as audit


def sample(t, foot, ground=(0,0), pose='walk_east_1', side='right'):
    return {'elapsed_ms':t,'pose_id':pose,'direction':'east','support':side,'foot_screen_px':list(foot),'ground_screen_px':list(ground)}


class ContactAuditTests(unittest.TestCase):
    def test_stationary_foot(self):
        r=audit.assess([sample(0,(10,10)),sample(60,(10,10))],required={('east','right')})
        self.assertTrue(r['passed'])
    def test_camera_translation_cancels(self):
        r=audit.assess([sample(0,(10,10)),sample(60,(110,-20),(100,-30))],required={('east','right')})
        self.assertTrue(r['passed'])
    def test_moving_foot_fails(self):
        r=audit.assess([sample(0,(10,10)),sample(60,(23,10))],required={('east','right')})
        self.assertFalse(r['passed'])
        self.assertEqual(r['max_observed_drift_px'],13)
    def test_pose_change_breaks_interval(self):
        r=audit.assess([sample(0,(10,10)),sample(60,(10,10)),sample(90,(30,10),pose='walk_east_2',side=''),sample(120,(50,10)),sample(180,(50,10))],required={('east','right')})
        self.assertTrue(r['passed'])
    def test_gap_is_not_contact_evidence(self):
        r=audit.assess([sample(0,(10,10)),sample(400,(10,10))],required={('east','right')})
        self.assertFalse(r['passed'])
        self.assertTrue(r['missing_supports'])
    def test_incomplete_directions_not_pass(self):
        self.assertFalse(audit.assess([sample(0,(10,10)),sample(60,(10,10))])['passed'])
    def test_time_must_increase(self):
        with self.assertRaises(ValueError): audit.assess([sample(20,(10,10)),sample(10,(10,10))])

if __name__=='__main__':unittest.main()
