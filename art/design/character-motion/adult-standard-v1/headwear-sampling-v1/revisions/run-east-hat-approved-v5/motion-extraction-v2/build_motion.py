from pathlib import Path
from PIL import Image, ImageChops, ImageDraw
import hashlib
import json
import shutil


P = Path(__file__).resolve().parent
V5 = P.parent
HEADWEAR = V5.parents[1]
SIZE = (512, 768)
VISIBLE_ALPHA_MIN = 32


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def blank() -> Image.Image:
    return Image.new("L", SIZE)


def polygon(points) -> Image.Image:
    mask = blank()
    ImageDraw.Draw(mask).polygon([tuple(point) for point in points], fill=255)
    return mask


def count(mask: Image.Image) -> int:
    return sum(mask.histogram()[1:])


def exact_outside_mask(left: Image.Image, right: Image.Image, mask: Image.Image) -> bool:
    different = ImageChops.difference(left, right)
    if different.getbbox() is None:
        return True
    inverse = ImageChops.invert(mask)
    return all(ImageChops.multiply(channel, inverse).getbbox() is None for channel in different.split())


def selected_rgba_exact(source: Image.Image, plate: Image.Image, ownership: Image.Image) -> bool:
    return all(
        ImageChops.multiply(ImageChops.difference(source_channel, plate_channel), ownership).getbbox() is None
        for source_channel, plate_channel in zip(source.split(), plate.split())
    )


def mask_union(left: Image.Image, right: Image.Image) -> Image.Image:
    return ImageChops.lighter(left, right)


def write_visuals(directory: Path, name: str, image: Image.Image) -> None:
    background = Image.new("RGBA", SIZE, "#d2dce4")
    background.alpha_composite(image)
    background.crop((90, 60, 505, 405)).resize((830, 690), Image.Resampling.NEAREST).convert("RGB").save(
        directory / f"{name}-head-2x.png"
    )
    board = Image.new("RGB", (1024, 768))
    for column, color in enumerate(["#e0e7eb", "#26364b"]):
        background = Image.new("RGBA", SIZE, color)
        background.alpha_composite(image)
        board.paste(background.convert("RGB"), (column * 512, 0))
    board.save(directory / f"{name}-light-dark.png")


def make_manifest(directory: Path, pose_id: str, audit: dict) -> dict:
    files = {
        "source_original": "source-original.png",
        "source_window": "source-window.png",
        "source_full_frame": "source-full-frame.png",
        "source_ownership": "source-ownership.png",
        "source_plate": "source-plate.png",
        "source_near": "source-near.png",
        "source_far": "source-far.png",
        "source_near_ownership": "source-near-ownership.png",
        "source_far_ownership": "source-far-ownership.png",
        "plate": "hat-complete-plate.png",
        "near": "hat-near.png",
        "far": "hat-far.png",
        "ownership": "registered-ownership.png",
        "near_ownership": "near-ownership.png",
        "far_ownership": "far-ownership.png",
        "coverage": "target-coverage.png",
        "contact": "authored-contact.png",
        "opening_profile": "authored-opening-profile.json",
        "coverage_missing": "coverage-missing.png",
        "original_body": "original-body.png",
        "composite": "composite.png",
        "visual_light_dark": "composite-light-dark.png",
        "visual_head_2x": "composite-head-2x.png",
        "visual_hat_light_dark": "hat-light-dark.png",
        "visual_hat_head_2x": "hat-head-2x.png",
        "landmarks_visual": "landmarks-source-target.png",
        "registration_measurements": "registration-measurements.json",
        "source_contours": "contours.json",
        "audit": "audit.json",
    }
    manifest = {
        "schema_version": 1,
        "pose_id": pose_id,
        "status": "candidate-ready-for-main-native-review",
        "runtime_candidate_allowed": True,
        "native_verified": False,
        "user_visual_accepted": False,
        "source_to_target_integer_translation_px": [0, 0],
        "runtime_full_frame_placement_px": [0, 0],
        "canvas_px": list(SIZE),
        "local_scale": [1, 1],
        "files": files,
        "sha256": {name: sha(directory / name) for name in files.values()},
        "counts": audit["counts"],
        "registration_residual_px": audit["registration"]["residuals_px"],
    }
    (directory / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


frame_reports = []
frame_manifests = []
for pose_number in (2, 3):
    pose_id = f"run_east_{pose_number}"
    directory = P / pose_id
    contours = json.loads((directory / "contours.json").read_text())

    raw_source = V5 / "motion-sources" / f"pose-{pose_number}-wearing-v2.png"
    normalized_source = V5 / "motion-sources" / f"pose-{pose_number}-wearing-v2-normalized.png"
    shutil.copyfile(raw_source, directory / "source-original.png")
    shutil.copyfile(normalized_source, directory / "source-window.png")
    window = Image.open(directory / "source-window.png").convert("RGBA")
    normalized_from_raw = Image.open(directory / "source-original.png").convert("RGBA").resize(
        (512, 512), Image.Resampling.NEAREST
    )
    normalized_exact = ImageChops.difference(normalized_from_raw, window).getbbox() is None

    source_full_frame = Image.new("RGBA", SIZE)
    source_full_frame.paste(window, (0, 0))
    source_full_frame.save(directory / "source-full-frame.png")

    original_reference = HEADWEAR / "run-east" / "references" / f"{pose_id}-bare.png"
    shutil.copyfile(original_reference, directory / "original-body.png")
    original_body = Image.open(directory / "original-body.png").convert("RGBA")

    near_edge = contours["near_edge"]
    far_right_x = contours["far_right_x"]
    near_semantic = polygon(
        [(90, 40), (far_right_x - 1, 40)]
        + list(reversed(near_edge))
        + [(near_edge[0][0], 350), (90, 350)]
    )
    left_semantic = polygon(contours["left_semantic"])
    right_semantic = polygon(contours["far_right_semantic"])
    semantic = mask_union(mask_union(near_semantic, left_semantic), right_semantic)

    outer = blank()
    outer_draw = ImageDraw.Draw(outer)
    for y, x0, x1 in contours["outer_spans"]:
        outer_draw.line((x0, y, x1, y), fill=255)
    source_ownership = ImageChops.darker(semantic, outer)
    for coordinate in contours["background_exclusions"]:
        source_ownership.putpixel(tuple(coordinate), 0)

    far_candidate = ImageChops.darker(
        source_ownership,
        mask_union(polygon(contours["far_left_depth"]), polygon(contours["far_right_depth"])),
    )
    # A stored near-edge coordinate is real foreground rim. A depth polygon may meet
    # the rim geometrically, but it cannot take ownership of that shared boundary.
    shared_near_edge = blank()
    shared_draw = ImageDraw.Draw(shared_near_edge)
    shared_draw.line([tuple(coordinate) for coordinate in near_edge], fill=255, width=1)
    # The far-left depth polygon's upper edge follows the same visible dark lip
    # through the sparse first segment of near_edge. Preserve that whole edge in
    # front rather than allowing polygon fill semantics to steal isolated pixels.
    shared_draw.line(
        [tuple(coordinate) for coordinate in contours["far_left_depth"][1:3]],
        fill=255,
        width=1,
    )
    source_far_ownership = ImageChops.subtract(far_candidate, shared_near_edge)
    source_near_ownership = ImageChops.subtract(source_ownership, source_far_ownership)

    source_plate = Image.new("RGBA", SIZE)
    source_plate.paste(source_full_frame, (0, 0), source_ownership)
    source_near = Image.new("RGBA", SIZE)
    source_near.paste(source_full_frame, (0, 0), source_near_ownership)
    source_far = Image.new("RGBA", SIZE)
    source_far.paste(source_full_frame, (0, 0), source_far_ownership)
    for name, image in {
        "source-ownership.png": source_ownership,
        "source-near-ownership.png": source_near_ownership,
        "source-far-ownership.png": source_far_ownership,
        "source-plate.png": source_plate,
        "source-near.png": source_near,
        "source-far.png": source_far,
    }.items():
        image.save(directory / name)

    dx, dy = contours["placement_px"]
    assert [dx, dy] == [0, 0], "v2 sources are zero-registered; do not bake another shift"

    def registered(image: Image.Image) -> Image.Image:
        output = Image.new(image.mode, SIZE)
        output.paste(image, (dx, dy))
        return output

    source_count = count(source_ownership)
    plate, near, far, ownership, near_ownership, far_ownership = [
        registered(image)
        for image in (
            source_plate,
            source_near,
            source_far,
            source_ownership,
            source_near_ownership,
            source_far_ownership,
        )
    ]
    no_registration_clip = count(ownership) == source_count

    composite = original_body.copy()
    body_over_far = Image.alpha_composite(far, original_body)
    composite.paste(body_over_far, (0, 0), far_ownership)
    composite.paste(near, (0, 0), near_ownership)

    opening_profile = {}
    for x in range(SIZE[0]):
        occupied = [y for y in range(SIZE[1]) if near_ownership.getpixel((x, y))]
        if occupied:
            opening_profile[x] = max(occupied)

    target_coverage = blank()
    authored_contact = blank()
    coverage_pixels = target_coverage.load()
    contact_draw = ImageDraw.Draw(authored_contact)
    original_alpha = original_body.getchannel("A")
    for x, maximum_y in opening_profile.items():
        if not 100 <= x < 480:
            continue
        for y in range(100, maximum_y + 1):
            if original_alpha.getpixel((x, y)) >= VISIBLE_ALPHA_MIN:
                coverage_pixels[x, y] = 255
        if maximum_y + 1 < SIZE[1] and original_alpha.getpixel((x, maximum_y + 1)) >= VISIBLE_ALPHA_MIN:
            contact_draw.point((x, maximum_y), fill=255)

    coverage_missing = ImageChops.subtract(target_coverage, near_ownership)
    profile_record = {
        "coordinate_space": "target_full_frame",
        "source_to_target_integer_translation": [0, 0],
        "visible_original_alpha_threshold": VISIBLE_ALPHA_MIN,
        "basis": (
            "Lower border of the reviewed real near-hat surface. Target coverage contains every original-body "
            "pixel with alpha >= 32 above that surface, not a legacy contact line or a small probe set. "
            "The profile is audit-only and does not paint hat pixels or erase the body."
        ),
        "samples_px": [[x, y] for x, y in opening_profile.items()],
    }
    (directory / "authored-opening-profile.json").write_text(json.dumps(profile_record, indent=2) + "\n")

    for name, image in {
        "hat-complete-plate.png": plate,
        "hat-near.png": near,
        "hat-far.png": far,
        "registered-ownership.png": ownership,
        "near-ownership.png": near_ownership,
        "far-ownership.png": far_ownership,
        "target-coverage.png": target_coverage,
        "authored-contact.png": authored_contact,
        "coverage-missing.png": coverage_missing,
        "composite.png": composite,
    }.items():
        image.save(directory / name)
    write_visuals(directory, "hat", plate)
    write_visuals(directory, "composite", composite)

    measurements = json.loads((directory / "registration-measurements.json").read_text())
    residuals = {
        name: record["residual_after_integer_translation_px"]
        for name, record in measurements["features"].items()
    }
    max_residual = max(abs(value) for residual in residuals.values() for value in residual)

    union = mask_union(near_ownership, far_ownership)
    overlap = ImageChops.darker(near_ownership, far_ownership)
    owned_shared_near_edge = ImageChops.darker(shared_near_edge, source_ownership)
    all_near_edge_foreground = (
        ImageChops.subtract(owned_shared_near_edge, source_near_ownership).getbbox() is None
        and ImageChops.darker(owned_shared_near_edge, source_far_ownership).getbbox() is None
    )
    source_perimeter_owned = any(source_ownership.getpixel((x, 0)) for x in range(512)) or any(
        source_ownership.getpixel((x, 511)) for x in range(512)
    ) or any(source_ownership.getpixel((0, y)) for y in range(512)) or any(
        source_ownership.getpixel((511, y)) for y in range(512)
    )
    source_face_probe_owned = [
        coordinate for coordinate in contours["source_face_probes"] if source_ownership.getpixel(tuple(coordinate))
    ]
    neutral_background_owned = []
    for y in range(512):
        for x in range(512):
            if not source_ownership.getpixel((x, y)):
                continue
            red, green, blue, _ = window.getpixel((x, y))
            if min(red, green, blue) > 80 and max(red, green, blue) - min(red, green, blue) < 20:
                neutral_background_owned.append([x, y])

    checks = {
        "raw_1254_nearest_normalization_exact": normalized_exact,
        "selected_hat_rgba_matches_normalized_source": selected_rgba_exact(source_full_frame, source_plate, source_ownership),
        "zero_registration_does_not_clip_hat": no_registration_clip,
        "source_hat_does_not_touch_source_canvas_edge": not source_perimeter_owned,
        "near_far_union_reconstructs_complete_hat": ImageChops.difference(union, ownership).getbbox() is None,
        "near_far_are_disjoint": overlap.getbbox() is None,
        "real_near_rim_not_reclassified_far": all_near_edge_foreground,
        "outside_hat_support_original_rgba_exact": exact_outside_mask(composite, original_body, ownership),
        "source_anatomy_probes_excluded": not source_face_probe_owned,
        "reviewed_gray_background_excluded": not neutral_background_owned,
        "full_visible_original_upper_head_covered": coverage_missing.getbbox() is None,
        "contact_is_real_owned_near_hat": ImageChops.subtract(authored_contact, near_ownership).getbbox() is None,
    }
    assert all(checks.values()), {pose_id: {name: result for name, result in checks.items() if not result}}

    missing_points = [
        [x, y]
        for y in range(SIZE[1])
        for x in range(SIZE[0])
        if coverage_missing.getpixel((x, y))
    ]
    audit = {
        "pose_id": pose_id,
        "status": "candidate-ready-for-main-native-review",
        "runtime_candidate_allowed": True,
        "native_verified": False,
        "user_visual_accepted": False,
        "placement_px": [0, 0],
        "runtime_full_frame_placement_px": [0, 0],
        "counts": {
            "owned": count(ownership),
            "near": count(near_ownership),
            "far": count(far_ownership),
            "target_coverage": count(target_coverage),
            "authored_contact": count(authored_contact),
            "coverage_missing": count(coverage_missing),
            "explicit_background_exclusions": len(contours["background_exclusions"]),
        },
        "coverage_missing_first": missing_points[:20],
        "checks": checks,
        "registration": {
            "operation": (
                "Whole normalized source kept at target coordinates. Ear, eye, and brow independently support "
                "zero integer translation; no local scale, hat-only shift, or generated-body adoption."
            ),
            "translation_px": [0, 0],
            "local_scale": [1, 1],
            "landmark_measurements": "registration-measurements.json",
            "residuals_px": residuals,
            "max_component_residual_px": max_residual,
            "note": "Generated anatomy is not adopted. Residuals are registration evidence; full original-head coverage is checked separately over all visible support pixels above the real near-hat surface.",
        },
        "composition": {
            "order": ["hat_far", "original_body", "hat_near"],
            "body_source_mutated": False,
            "source_rgb_or_alpha_mutated": False,
            "source_anatomy_adopted": False,
            "near_edge_policy": "Stored real near_edge coordinates remain in near ownership even where a far-depth polygon meets the shared boundary.",
        },
        "source_density": {
            "raw_source_px": [1254, 1254],
            "normalized_source_px": [512, 512],
            "normalization": "whole-image nearest",
            "target_fullframe_px": list(SIZE),
        },
        "source_sha256": {
            "raw": sha(directory / "source-original.png"),
            "normalized": sha(directory / "source-window.png"),
            "original_body": sha(directory / "original-body.png"),
        },
        "source_face_probes": contours["source_face_probes"],
        "source_face_probe_owned": source_face_probe_owned,
        "neutral_background_probe_owned": neutral_background_owned,
        "visual_review": [
            "source-contact-grid.png",
            "landmarks-source-target.png",
            "hat-head-2x.png",
            "hat-light-dark.png",
            "composite-head-2x.png",
            "composite-light-dark.png",
        ],
    }
    (directory / "audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    manifest = make_manifest(directory, pose_id, audit)
    frame_reports.append(audit)
    frame_manifests.append(manifest)


(P / "preliminary-audit.json").write_text(
    json.dumps(
        {
            "status": "superseded-partial-audit-retained-at-original-path",
            "replacement": "manifest.json and per-pose audit.json",
            "poses": [
                {
                    "pose_id": report["pose_id"],
                    "runtime_candidate_allowed": report["runtime_candidate_allowed"],
                    "counts": report["counts"],
                    "checks": report["checks"],
                }
                for report in frame_reports
            ],
        },
        indent=2,
    )
    + "\n"
)

root_manifest = {
    "schema_version": 1,
    "status": "two-replacement-motion-poses-ready-for-main-native-review",
    "scope": ["run_east_2", "run_east_3"],
    "runtime_candidate_allowed": {manifest["pose_id"]: True for manifest in frame_manifests},
    "runtime_full_frame_placement_px": [0, 0],
    "native_verified": False,
    "user_visual_accepted": False,
    "source_audit": "source-audit.md",
    "source_audit_sha256": sha(P / "source-audit.md"),
    "pose_manifests": {manifest["pose_id"]: f"{manifest['pose_id']}/manifest.json" for manifest in frame_manifests},
    "pose_manifest_sha256": {
        manifest["pose_id"]: sha(P / manifest["pose_id"] / "manifest.json") for manifest in frame_manifests
    },
    "preserved_rejected_predecessor": {
        "directory": "../motion-extraction",
        "run_east_2_audit_sha256": sha(P.parent / "motion-extraction" / "run_east_2" / "audit.json"),
        "run_east_3_audit_sha256": sha(P.parent / "motion-extraction" / "run_east_3" / "audit.json"),
        "note": "The v1 rejection remains valid for its older sources and measured translations. It was not modified or weakened; v2 uses new pose-specific wearing sources that independently pass the same full-head coverage gate.",
    },
}
(P / "manifest.json").write_text(json.dumps(root_manifest, indent=2) + "\n")
print(json.dumps(root_manifest, indent=2))
