import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

from tools.prepare_cottage_assets import prepare_assets


class PrepareCottageAssetsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        self.source.mkdir()

    def image(self, name, box, color=(83, 117, 151, 255), stray=False):
        image = Image.new("RGBA", (1000, 1500))
        ImageDraw.Draw(image).rectangle((box[0], box[1], box[2] - 1, box[3] - 1), fill=color)
        if stray:
            image.putpixel((0, 0), (255, 0, 0, 20))
        image.save(self.source / (name + ".png"))

    def valid_sources(self):
        self.image("bed", (250, 250, 750, 1250), stray=True)
        self.image("door-closed", (240, 200, 700, 1200), stray=True)
        self.image("door-half", (240, 150, 550, 1250), stray=True)
        self.image("door-open", (240, 100, 400, 1300), stray=True)

    def run_prepare(self):
        return prepare_assets(self.source, self.root / "assets", self.root / "processed")

    def test_binary_alpha_removes_exterior_halo_and_retains_source_color(self):
        self.valid_sources()
        self.run_prepare()
        bed = Image.open(self.root / "assets" / "bed.png").convert("RGBA")
        self.assertEqual(bed.size, (48, 80))
        self.assertEqual(set(bed.getchannel("A").get_flattened_data()), {0, 255})
        self.assertNotIn((255, 0, 0, 255), set(bed.get_flattened_data()))
        self.assertEqual({pixel[:3] for pixel in bed.get_flattened_data() if pixel[3]}, {(83, 117, 151)})

    def test_rejects_empty_and_opaque_sources(self):
        self.valid_sources()
        Image.new("RGBA", (1000, 1500)).save(self.source / "bed.png")
        with self.assertRaisesRegex(ValueError, "empty"):
            self.run_prepare()
        self.image("bed", (0, 0, 1000, 1500))
        with self.assertRaisesRegex(ValueError, "opaque"):
            self.run_prepare()

    def test_doors_share_registration_and_keep_relative_widths(self):
        self.valid_sources()
        manifest = self.run_prepare()
        entries = [manifest[key] for key in ("door_closed", "door_half", "door_open")]
        self.assertEqual(len({tuple(entry["logical_size"]) for entry in entries}), 1)
        self.assertEqual(len({tuple(entry["pivot"]) for entry in entries}), 1)
        self.assertEqual(len({tuple(entry["registration"]["origin"]) for entry in entries}), 1)
        self.assertEqual(len({entry["registration"]["scale"] for entry in entries}), 1)
        self.assertEqual(len({tuple(entry["floor_anchor"]) for entry in entries}), 1)
        widths = [Image.open(self.root / "assets" / (name + ".png")).getchannel("A").getbbox()[2] - Image.open(self.root / "assets" / (name + ".png")).getchannel("A").getbbox()[0] for name in ("door-closed", "door-half", "door-open")]
        self.assertGreater(widths[0], widths[1])
        self.assertGreater(widths[1], widths[2])
        self.assertEqual(entries[0]["closed_leaf_size"], [widths[0], Image.open(self.root / "assets" / "door-closed.png").getchannel("A").getbbox()[3] - Image.open(self.root / "assets" / "door-closed.png").getchannel("A").getbbox()[1]])

    def test_output_is_deterministic_and_copies_match(self):
        self.valid_sources()
        self.run_prepare()
        before = {path.name: path.read_bytes() for path in (self.root / "assets").iterdir()}
        self.run_prepare()
        self.assertEqual(before, {path.name: path.read_bytes() for path in (self.root / "assets").iterdir()})
        self.assertEqual(before, {path.name: path.read_bytes() for path in (self.root / "processed").iterdir()})


if __name__ == "__main__":
    unittest.main()
