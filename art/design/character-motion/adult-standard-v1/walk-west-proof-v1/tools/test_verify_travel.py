"""Godot JSON scalar precision regression; preserve rejection of real scale changes."""
import unittest
import verify_travel_capture as verifier


class TravelScaleTests(unittest.TestCase):
    def test_godot_json_decimal_roundtrip_preserves_display_scale(self):
        declared = 138 / 582
        recorded = float(format(declared, '.15g'))
        self.assertNotEqual(recorded, declared, 'fixture must reproduce serialization rounding')
        check = getattr(verifier, 'check_display_scale', None)
        self.assertIsNotNone(check, 'display scale verification needs serialization tolerance')
        check(recorded, declared)

    def test_actual_display_scale_change_is_still_rejected(self):
        check = getattr(verifier, 'check_display_scale', None)
        self.assertIsNotNone(check, 'scale comparison must not be removed')
        with self.assertRaises(AssertionError):
            check(138 / 582 + 1e-7, 138 / 582)


if __name__ == '__main__':
    unittest.main()
