"""Prepare the approved cottage source images for the Godot pilot."""

import argparse
import json
from pathlib import Path

from PIL import Image


NAMES = ("bed", "door-closed", "door-half", "door-open")
ALPHA_THRESHOLD = 128
BED_SIZE = (48, 80)
DOOR_SCALE = 0.048
DOOR_PADDING = 2
HINGE_SOURCE = ((255, 470), (255, 1090))


def clean_source(path):
    image = Image.open(path).convert("RGBA")
    alpha = image.getchannel("A")
    if alpha.getextrema()[0] == 255:
        raise ValueError(f"opaque source: {path}")
    alpha = alpha.point(lambda value: 255 if value >= ALPHA_THRESHOLD else 0)
    box = alpha.getbbox()
    if box is None:
        raise ValueError(f"empty source: {path}")
    image.putalpha(alpha)
    return image, box


def prepare_assets(source_dir, output_dir, duplicate_dir):
    source_dir = Path(source_dir)
    output_dir = Path(output_dir)
    duplicate_dir = Path(duplicate_dir)
    inputs = {name: clean_source(source_dir / f"{name}.png") for name in NAMES}
    output_dir.mkdir(parents=True, exist_ok=True)
    duplicate_dir.mkdir(parents=True, exist_ok=True)
    manifest = {}

    bed_image, bed_box = inputs["bed"]
    bed_crop = bed_image.crop(bed_box)
    ratio = min(BED_SIZE[0] / bed_crop.width, BED_SIZE[1] / bed_crop.height)
    bed_fit = bed_crop.resize((max(1, round(bed_crop.width * ratio)), max(1, round(bed_crop.height * ratio))), Image.Resampling.NEAREST)
    bed_canvas = Image.new("RGBA", BED_SIZE)
    bed_origin = ((BED_SIZE[0] - bed_fit.width) // 2, BED_SIZE[1] - bed_fit.height)
    bed_canvas.paste(bed_fit, bed_origin)
    manifest["bed"] = {
        "path": "res://assets/house-interior/bed.png",
        "logical_size": list(BED_SIZE),
        "source": "art/interior/source/bed.png",
        "source_region": list(bed_box),
        "pivot": [BED_SIZE[0] // 2, BED_SIZE[1] - 1],
        "alpha_threshold": ALPHA_THRESHOLD,
        "fit_size": list(bed_fit.size),
        "registration": {"origin": list(bed_origin), "scale": ratio},
    }
    images = {"bed": bed_canvas}

    doors = [inputs[name] for name in NAMES[1:]]
    left = min(box[0] for _, box in doors)
    top = min(box[1] for _, box in doors)
    right = max(box[2] for _, box in doors)
    bottom = max(box[3] for _, box in doors)
    envelope = (
        max(1, round((right - left) * DOOR_SCALE)) + 2 * DOOR_PADDING,
        max(1, round((bottom - top) * DOOR_SCALE)) + 2 * DOOR_PADDING,
    )
    hinge_points = [[round((x - left) * DOOR_SCALE) + DOOR_PADDING,
                     round((y - top) * DOOR_SCALE) + DOOR_PADDING]
                    for x, y in HINGE_SOURCE]
    for name in NAMES[1:]:
        image, box = inputs[name]
        crop = image.crop((left, top, right, bottom))
        fit = crop.resize((envelope[0] - 2 * DOOR_PADDING, envelope[1] - 2 * DOOR_PADDING), Image.Resampling.NEAREST)
        canvas = Image.new("RGBA", envelope)
        canvas.paste(fit, (DOOR_PADDING, DOOR_PADDING))
        visible = canvas.getchannel("A").getbbox()
        if visible is None:
            raise ValueError(f"empty resized door: {name}")
        leaf = [visible[2] - visible[0], visible[3] - visible[1]]
        manifest[name.replace("-", "_")] = {
            "path": f"res://assets/house-interior/{name}.png",
            "logical_size": list(envelope),
            "source": f"art/interior/source/{name}.png",
            "source_region": list(box),
            "pivot": hinge_points[1],
            "hinge_points": hinge_points,
            "closed_leaf_size": None,
            "visible_leaf_size": leaf,
            "alpha_threshold": ALPHA_THRESHOLD,
            "registration": {"origin": [left, top], "scale": DOOR_SCALE, "padding": DOOR_PADDING},
        }
        images[name] = canvas
    closed_size = manifest["door_closed"]["visible_leaf_size"]
    closed_box = images["door-closed"].getchannel("A").getbbox()
    floor_anchor = [(closed_box[0] + closed_box[2]) // 2, closed_box[3]]
    for name in ("door_closed", "door_half", "door_open"):
        manifest[name]["closed_leaf_size"] = closed_size
        manifest[name]["floor_anchor"] = floor_anchor
    for name, image in images.items():
        for folder in (output_dir, duplicate_dir):
            image.save(folder / f"{name}.png", optimize=False)
    serialized = json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    for folder in (output_dir, duplicate_dir):
        (folder / "pilot.json").write_text(serialized, encoding="utf-8")
    return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, default=Path("art/interior/source"))
    parser.add_argument("--output-dir", type=Path, default=Path("godot2d/assets/house-interior"))
    parser.add_argument("--duplicate-dir", type=Path, default=Path("art/interior/processed"))
    args = parser.parse_args()
    result = prepare_assets(args.source_dir, args.output_dir, args.duplicate_dir)
    print(json.dumps({key: {"logical_size": entry["logical_size"], "visible_leaf_size": entry.get("visible_leaf_size")} for key, entry in result.items()}))


if __name__ == "__main__":
    main()
