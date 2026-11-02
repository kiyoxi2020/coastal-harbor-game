"""Retained body suites remain reachable after historical reviews retire."""
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import review


class RetainedReviewEntriesTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='coastal-review-entries-', dir='/private/tmp')
        self.addCleanup(temp.cleanup)
        self.repo = Path(temp.name)
        library = self.repo/'art/characters'
        self.v5_suite = 'reviews/body-pixel-v5-fixture/review.json'
        path = library/self.v5_suite
        path.parent.mkdir(parents=True)
        path.write_text('{}')
        (library/'catalog.json').write_text(json.dumps({'reviews': {'body-pixel-v5': self.v5_suite}}))

    def launch(self, args):
        out = io.StringIO()
        with patch.object(review, 'REPO', self.repo), patch.object(sys, 'argv', ['review.py', *args, '--dry-run']), patch('body_review.preflight') as preflight, contextlib.redirect_stdout(out):
            review.main()
        return preflight, out.getvalue()

    def test_default_launches_current_body_suite(self):
        checked, output = self.launch([])
        checked.assert_called_once_with(self.repo, self.repo/'art/characters/reviews/body-actions/review.json')
        self.assertIn('--construction-suite=', output)

    def test_v5_alias_uses_catalog_suite_and_strict_preflight(self):
        checked, output = self.launch(['body-pixel-v5'])
        checked.assert_called_once_with(self.repo, self.repo/'art/characters'/self.v5_suite)
        self.assertIn('character_headwear_trial.tscn', output)
