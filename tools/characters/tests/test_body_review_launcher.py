"""Public launcher routes body-only suites through strict preflight."""
import contextlib
import io
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import review

class BodyReviewLauncherTests(unittest.TestCase):
    def test_body_launcher_requires_preflight_and_shared_scene(self):
        output = io.StringIO()
        with patch.object(sys, 'argv', ['review.py', 'body-actions', '--dry-run']), patch('body_review.preflight') as checked, contextlib.redirect_stdout(output):
            review.main()
        checked.assert_called_once_with(review.REPO, review.REPO/'art/characters/reviews/body-actions/review.json')
        self.assertIn('character_headwear_trial.tscn', output.getvalue())
        self.assertIn('--construction-suite=', output.getvalue())

    def test_invalid_body_never_launches(self):
        with patch.object(sys, 'argv', ['review.py', 'body-actions']), patch('body_review.preflight', side_effect=ValueError('stale body')), patch('review.subprocess.call') as launch, contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit): review.main()
        launch.assert_not_called()
