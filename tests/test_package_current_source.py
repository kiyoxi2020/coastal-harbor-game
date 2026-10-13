"""The release source package can be verified before replacing the live delivery."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from zipfile import ZipFile


class StagedSourcePackageTest(unittest.TestCase):
    def test_staging_output_preserves_current_delivery(self):
        with tempfile.TemporaryDirectory(prefix="coastal-source-package-") as temporary:
            root = Path(temporary)
            (root / "tools").mkdir()
            tool = root / "tools/package_current_source.py"
            shutil.copy2(Path(__file__).resolve().parents[1] / "tools/package_current_source.py", tool)
            (root / "godot2d/scripts").mkdir(parents=True)
            (root / "godot2d/scripts/harbor.gd").write_text("extends Node\n")
            (root / "godot2d/README.md").write_text("current source\n")
            (root / "godot2d/export_presets.cfg").write_text('application/short_version="0.5.4"\n')
            live = root / "交付与预览/2D"
            live.mkdir(parents=True)
            sentinel = live / "package-verification.json"
            sentinel.write_text('{"version":"previous"}\n')
            staging = root / "builds/staging"
            staging.mkdir(parents=True)
            (staging / "package-verification.json").write_text('{"version":"0.5.4"}\n')
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            subprocess.run([sys.executable, str(tool), "--output-directory", str(staging)], check=True, capture_output=True)
            self.assertEqual(sentinel.read_text(), '{"version":"previous"}\n')
            with ZipFile(staging / "CoastalHarbor2D-v0.5.4-source.zip") as archive:
                self.assertIsNone(archive.testzip())
                self.assertEqual(archive.read("godot2d/scripts/harbor.gd"), b"extends Node\n")
            report = json.loads((staging / "package-verification.json").read_text())
            self.assertGreaterEqual(report["source_files_matched"], 4)
