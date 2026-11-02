import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from tools.characters import reference_sheet


class ReferenceSheetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="coastal-reference-sheet-")
        self.output_temp = tempfile.TemporaryDirectory(prefix="coastal-reference-sheet-output-", dir="/private/tmp")
        self.root = Path(self.temp.name).resolve()
        self.characters = self.root / "art" / "characters"
        self.source_dir = self.characters / "sources" / "fixture" / "originals"
        self.source_dir.mkdir(parents=True)
        self.plan_path = self.root / "plan.json"
        self.output = Path(self.output_temp.name) / "coastal-sheet-r001"
        items = []
        for index in range(6):
            image = Image.new("RGBA", (4, 3), (index, 40, 90, 255))
            image.putpixel((1, 1), (200 + index, 80, 20, 127))
            image.putpixel((2, 1), (17, 33, 55, 0))
            path = self.source_dir / f"frame-{index}.png"
            image.save(path)
            items.append({
                "file": f"sources/fixture/originals/frame-{index}.png",
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            })
        self.plan = {
            "kind": "coastal-character-reference-sheet-plan-v1",
            "grid": [3, 2],
            "cell_px": [4, 3],
            "inputs": items,
        }
        self.write_plan()

    def tearDown(self):
        self.temp.cleanup()
        self.output_temp.cleanup()

    def write_plan(self):
        self.plan_path.write_text(json.dumps(self.plan), encoding="utf-8")

    def test_build_pastes_original_rgba_without_alpha_compositing(self):
        reference_sheet.build(self.plan_path, self.output, project_root=self.root)
        with Image.open(self.output / "sheet.png") as sheet:
            self.assertEqual(sheet.mode, "RGBA")
            self.assertEqual(sheet.size, (12, 6))
            self.assertEqual(sheet.getpixel((5, 1)), (201, 80, 20, 127))
            self.assertEqual(sheet.getpixel((6, 1)), (17, 33, 55, 0))
            self.assertEqual(sheet.getpixel((0, 4)), (3, 40, 90, 255))
        manifest = json.loads((self.output / "manifest.json").read_text())
        self.assertEqual(manifest["kind"], "coastal-character-reference-sheet-v1")
        self.assertEqual(manifest["status"], "reference-only")
        reference_sheet.verify(self.output, project_root=self.root)

    def test_verify_rejects_changed_source_even_if_plan_sha_is_updated(self):
        reference_sheet.build(self.plan_path, self.output, project_root=self.root)
        source = self.source_dir / "frame-0.png"
        image = Image.open(source).convert("RGBA")
        image.putpixel((0, 0), (1, 2, 3, 4))
        image.save(source)
        with self.assertRaises(reference_sheet.ReferenceSheetError):
            reference_sheet.verify(self.output, project_root=self.root)

    def test_verify_rejects_output_pixel_tamper_even_when_hashes_are_recomputed(self):
        reference_sheet.build(self.plan_path, self.output, project_root=self.root)
        manifest_path = self.output / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        output_path = self.output / "sheet.png"
        image = Image.open(output_path).convert("RGBA")
        image.putpixel((0, 0), (7, 8, 9, 10))
        image.save(output_path)
        manifest["output"]["sha256"] = hashlib.sha256(output_path.read_bytes()).hexdigest()
        rgba = image.tobytes()
        manifest["output"]["rgba_sha256"] = hashlib.sha256(rgba).hexdigest()
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaises(reference_sheet.ReferenceSheetError):
            reference_sheet.verify(self.output, project_root=self.root)

    def test_build_rejects_bad_plan_paths_counts_dimensions_and_sha(self):
        cases = []
        broken = dict(self.plan)
        broken["inputs"] = self.plan["inputs"][:-1]
        cases.append(broken)
        broken = dict(self.plan)
        broken["inputs"] = [dict(x) for x in self.plan["inputs"]]
        broken["inputs"][1] = dict(broken["inputs"][0])
        cases.append(broken)
        broken = dict(self.plan)
        broken["inputs"] = [dict(x) for x in self.plan["inputs"]]
        broken["inputs"][0]["file"] = "../escape.png"
        cases.append(broken)
        broken = dict(self.plan)
        broken["inputs"] = [dict(x) for x in self.plan["inputs"]]
        broken["inputs"][0]["file"] = str(self.source_dir / "frame-0.png")
        cases.append(broken)
        broken = dict(self.plan)
        broken["cell_px"] = [5, 3]
        cases.append(broken)
        broken = dict(self.plan)
        broken["inputs"] = [dict(x) for x in self.plan["inputs"]]
        broken["inputs"][2]["sha256"] = "0" * 64
        cases.append(broken)
        for case in cases:
            with self.subTest(case=case):
                self.write_plan_value(case)
                with self.assertRaises(reference_sheet.ReferenceSheetError):
                    reference_sheet.build(self.plan_path, self.output, project_root=self.root)
                self.plan_path.write_text(json.dumps(self.plan), encoding="utf-8")

    def write_plan_value(self, value):
        self.plan_path.write_text(json.dumps(value), encoding="utf-8")

    def test_build_rejects_symlink_inputs_and_inconsistent_dimensions(self):
        link = self.source_dir / "linked.png"
        link.symlink_to(self.source_dir / "frame-0.png")
        plan = dict(self.plan)
        plan["inputs"] = [dict(x) for x in self.plan["inputs"]]
        plan["inputs"][0]["file"] = "sources/fixture/originals/linked.png"
        self.write_plan_value(plan)
        with self.assertRaises(reference_sheet.ReferenceSheetError):
            reference_sheet.build(self.plan_path, self.output, project_root=self.root)

        image = Image.new("RGBA", (5, 3), (1, 1, 1, 255))
        image.save(self.source_dir / "frame-1.png")
        plan = dict(self.plan)
        plan["inputs"] = [dict(x) for x in self.plan["inputs"]]
        plan["inputs"][1]["sha256"] = hashlib.sha256((self.source_dir / "frame-1.png").read_bytes()).hexdigest()
        self.write_plan_value(plan)
        with self.assertRaises(reference_sheet.ReferenceSheetError):
            reference_sheet.build(self.plan_path, self.output, project_root=self.root)

    def test_build_requires_fresh_allowed_output_directory(self):
        existing = self.root / "not-allowed"
        existing.mkdir()
        with self.assertRaises(reference_sheet.ReferenceSheetError):
            reference_sheet.build(self.plan_path, existing, project_root=self.root)
        allowed_existing = Path(self.output_temp.name) / "coastal-sample"
        allowed_existing.mkdir()
        with self.assertRaises(reference_sheet.ReferenceSheetError):
            reference_sheet.build(self.plan_path, allowed_existing, project_root=self.root)

    def test_build_rejects_symlinked_plan(self):
        plan_link = self.root / "plan-link.json"
        plan_link.symlink_to(self.plan_path)
        with self.assertRaises(reference_sheet.ReferenceSheetError):
            reference_sheet.build(plan_link, self.output, project_root=self.root)

    def test_build_rejects_symlinked_project_root(self):
        project_link = self.root / "project-link"
        project_link.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(reference_sheet.ReferenceSheetError):
            reference_sheet.build("plan.json", self.output, project_root=project_link)

    def test_build_rejects_symlinked_art_ancestor(self):
        alternate = self.root / "alternate"
        alternate.mkdir()
        (alternate / "art").symlink_to(self.root / "art", target_is_directory=True)
        with self.assertRaises(reference_sheet.ReferenceSheetError):
            reference_sheet.build(self.plan_path, self.output, project_root=alternate)

    def test_build_rejects_symlinked_sources_ancestor(self):
        sources = self.characters / "sources"
        saved_sources = self.characters / "sources-saved"
        sources.rename(saved_sources)
        sources.symlink_to(saved_sources, target_is_directory=True)
        with self.assertRaises(reference_sheet.ReferenceSheetError):
            reference_sheet.build(self.plan_path, self.output, project_root=self.root)

    def test_build_rejects_symlinked_output_parent(self):
        real_parent = Path(self.output_temp.name) / "real-parent"
        real_parent.mkdir()
        alias_parent = Path(self.output_temp.name) / "alias-parent"
        alias_parent.symlink_to(real_parent, target_is_directory=True)
        with self.assertRaises(reference_sheet.ReferenceSheetError):
            reference_sheet.build(self.plan_path, alias_parent / "r001", project_root=self.root)

    def test_verify_rejects_symlinked_output_directory_ancestors_and_files(self):
        reference_sheet.build(self.plan_path, self.output, project_root=self.root)

        alias = Path(self.output_temp.name) / "alias"
        alias.symlink_to(self.output, target_is_directory=True)
        with self.assertRaises(reference_sheet.ReferenceSheetError):
            reference_sheet.verify(alias, project_root=self.root)

        self.output.rename(Path(self.output_temp.name) / "saved")
        self.output.symlink_to(Path(self.output_temp.name) / "saved", target_is_directory=True)
        with self.assertRaises(reference_sheet.ReferenceSheetError):
            reference_sheet.verify(self.output, project_root=self.root)
        self.output.unlink()
        (Path(self.output_temp.name) / "saved").rename(self.output)

        for filename in ("sheet.png", "manifest.json"):
            path = self.output / filename
            saved = Path(self.output_temp.name) / f"{filename}.saved"
            path.rename(saved)
            path.symlink_to(saved.name)
            with self.subTest(filename=filename):
                with self.assertRaises(reference_sheet.ReferenceSheetError):
                    reference_sheet.verify(self.output, project_root=self.root)
            path.unlink()
            saved.rename(path)

    def test_verify_rejects_symlink_in_output_parent(self):
        real_parent = Path(self.output_temp.name) / "real-parent"
        real_parent.mkdir()
        actual_output = real_parent / "r001"
        reference_sheet.build(self.plan_path, actual_output, project_root=self.root)
        alias_parent = Path(self.output_temp.name) / "alias-parent"
        alias_parent.symlink_to(real_parent, target_is_directory=True)
        with self.assertRaises(reference_sheet.ReferenceSheetError):
            reference_sheet.verify(alias_parent / "r001", project_root=self.root)


if __name__ == "__main__":
    unittest.main()
