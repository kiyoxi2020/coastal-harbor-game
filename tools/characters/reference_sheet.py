#!/usr/bin/env python3
"""Build and verify lossless, reference-only image sheets for image generation."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path, PurePosixPath

from PIL import Image, __version__ as PILLOW_VERSION


PLAN_KIND = "coastal-character-reference-sheet-plan-v1"
MANIFEST_KIND = "coastal-character-reference-sheet-v1"
SCRIPT_PATH = Path(__file__).resolve()
PROJECT_ROOT = SCRIPT_PATH.parents[2]
SHA_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class ReferenceSheetError(ValueError):
    """Invalid plan, source, output, or reference sheet."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_json(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _reject_symlink_components(path: Path, stop_at: Path) -> None:
    """Reject symlinks from path up to stop_at, including the final component."""
    path = Path(_absolute_norm(path))
    stop_at = Path(_absolute_norm(stop_at))
    try:
        relative = path.relative_to(stop_at)
    except ValueError as exc:
        raise ReferenceSheetError(f"path is outside allowed root: {path}") from exc
    _reject_symlink_absolute(stop_at)
    current = stop_at
    for component in relative.parts:
        current = current / component
        if current.is_symlink():
            raise ReferenceSheetError(f"symlink is not allowed: {current}")


def _absolute_norm(path: Path, base: Path | None = None) -> str:
    import os

    path = Path(path).expanduser()
    if not path.is_absolute():
        path = (Path(base) if base is not None else Path.cwd()) / path
    return os.path.abspath(str(path))


def _reject_symlink_absolute(path: Path) -> None:
    """Reject symlinks in every existing path component without resolving them away."""
    path = Path(_absolute_norm(path))
    current = Path(path.anchor)
    if current.is_symlink():
        raise ReferenceSheetError(f"symlink is not allowed: {current}")
    for component in path.parts[1:]:
        current = current / component
        if current.is_symlink():
            raise ReferenceSheetError(f"symlink is not allowed: {current}")


def _read_plan(plan_path: Path) -> dict:
    try:
        plan = json.loads(Path(plan_path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ReferenceSheetError(f"cannot read plan JSON: {plan_path}: {exc}") from exc
    if not isinstance(plan, dict) or plan.get("kind") != PLAN_KIND:
        raise ReferenceSheetError(f"plan kind must be {PLAN_KIND}")
    if plan.get("grid") != [3, 2]:
        raise ReferenceSheetError("grid must be [3, 2]")
    cell = plan.get("cell_px")
    if not isinstance(cell, list) or len(cell) != 2 or any(type(n) is not int or n <= 0 for n in cell):
        raise ReferenceSheetError("cell_px must contain two positive integers")
    inputs = plan.get("inputs")
    if not isinstance(inputs, list) or len(inputs) != 6:
        raise ReferenceSheetError("inputs must contain exactly six row-major entries")
    seen: set[str] = set()
    normalized = []
    for index, item in enumerate(inputs):
        if not isinstance(item, dict) or set(item) != {"file", "sha256"}:
            raise ReferenceSheetError(f"input {index} must contain exactly file and sha256")
        name = item["file"]
        digest = item["sha256"]
        if not isinstance(name, str) or not name:
            raise ReferenceSheetError(f"input {index} file must be a non-empty relative path")
        relative = PurePosixPath(name)
        if relative.is_absolute() or ".." in relative.parts or "\\" in name:
            raise ReferenceSheetError(f"input {index} path must be relative and cannot traverse: {name}")
        if not relative.parts or relative.parts[0] not in {"sources", "templates", "parts"}:
            raise ReferenceSheetError(f"input {index} must be under sources/, templates/, or parts/: {name}")
        canonical_name = relative.as_posix()
        if canonical_name in seen:
            raise ReferenceSheetError(f"duplicate input path: {canonical_name}")
        seen.add(canonical_name)
        if not isinstance(digest, str) or not SHA_PATTERN.fullmatch(digest):
            raise ReferenceSheetError(f"input {index} sha256 must be 64 lowercase hexadecimal characters")
        normalized.append({"file": canonical_name, "sha256": digest})
    return {"kind": PLAN_KIND, "grid": [3, 2], "cell_px": list(cell), "inputs": normalized}


def _resolve_input(characters_root: Path, relative: str) -> Path:
    path = characters_root.joinpath(*PurePosixPath(relative).parts)
    try:
        path.relative_to(characters_root)
    except ValueError as exc:
        raise ReferenceSheetError(f"input escapes art/characters: {relative}") from exc
    _reject_symlink_components(path, characters_root)
    if not path.is_file():
        raise ReferenceSheetError(f"input is not a file: {relative}")
    return path


def _validate_inputs(plan: dict, characters_root: Path) -> list[Image.Image]:
    frames = []
    expected_size = tuple(plan["cell_px"])
    for index, item in enumerate(plan["inputs"]):
        path = _resolve_input(characters_root, item["file"])
        data = path.read_bytes()
        actual_sha = _sha256(data)
        if actual_sha != item["sha256"]:
            raise ReferenceSheetError(f"input SHA-256 mismatch: {item['file']}")
        try:
            with Image.open(path) as opened:
                if opened.size != expected_size:
                    raise ReferenceSheetError(
                        f"input dimensions differ from cell_px at index {index}: "
                        f"{item['file']} is {opened.size}, expected {expected_size}"
                    )
                if opened.mode != "RGBA":
                    raise ReferenceSheetError(f"input must be RGBA without conversion: {item['file']} is {opened.mode}")
                opened.load()
                frames.append(opened.copy())
        except OSError as exc:
            raise ReferenceSheetError(f"cannot decode image: {item['file']}: {exc}") from exc
    return frames


def _output_path(output: Path, project_root: Path) -> Path:
    project_root = Path(_absolute_norm(project_root))
    output = Path(_absolute_norm(output, project_root))
    tmp_root = Path("/private/tmp")
    try:
        tmp_relative = output.relative_to(tmp_root)
        is_tmp = bool(tmp_relative.parts) and tmp_relative.parts[0].startswith("coastal-")
    except ValueError:
        is_tmp = False
    source_root = project_root / "art" / "characters" / "sources"
    try:
        source_relative = output.relative_to(source_root)
        is_source_reference = (
            len(source_relative.parts) == 3
            and source_relative.parts[1] == "references"
            and all(part not in {"", ".", ".."} for part in source_relative.parts)
        )
    except ValueError:
        is_source_reference = False
    if not (is_tmp or is_source_reference):
        raise ReferenceSheetError(
            "output must be /private/tmp/coastal-* or art/characters/sources/<id>/references/<revision>"
        )
    if is_tmp:
        _reject_symlink_components(output, tmp_root)
    else:
        _reject_symlink_components(output, source_root)
    if output.exists() or output.is_symlink():
        raise ReferenceSheetError(f"output directory must be new: {output}")
    return output


def _make_sheet(plan: dict, frames: list[Image.Image]) -> Image.Image:
    width, height = plan["cell_px"]
    sheet = Image.new("RGBA", (width * 3, height * 2), (0, 0, 0, 0))
    for index, frame in enumerate(frames):
        x = (index % 3) * width
        y = (index // 3) * height
        sheet.paste(frame, (x, y))
    return sheet


def _manifest(plan: dict, sheet: Image.Image, sheet_bytes: bytes) -> dict:
    width, height = plan["cell_px"]
    cells = []
    for index, item in enumerate(plan["inputs"]):
        cells.append({
            "index": index,
            "file": item["file"],
            "sha256": item["sha256"],
            "position_px": [(index % 3) * width, (index // 3) * height],
            "size_px": [width, height],
        })
    rgba = sheet.tobytes()
    return {
        "kind": MANIFEST_KIND,
        "status": "reference-only",
        "plan": plan,
        "plan_sha256": _sha256(_canonical_json(plan)),
        "tool": {
            "file": "tools/characters/reference_sheet.py",
            "sha256": _sha256(SCRIPT_PATH.read_bytes()),
            "pillow_version": PILLOW_VERSION,
        },
        "grid": [3, 2],
        "cell_px": [width, height],
        "size_px": list(sheet.size),
        "cells": cells,
        "output": {
            "file": "sheet.png",
            "sha256": _sha256(sheet_bytes),
            "rgba_sha256": _sha256(rgba),
            "mode": "RGBA",
        },
    }


def build(plan_path: Path, output: Path, *, project_root: Path = PROJECT_ROOT) -> Path:
    """Build a new lossless 3x2 reference sheet and its verification manifest."""
    project_root = Path(_absolute_norm(project_root))
    _reject_symlink_absolute(project_root)
    if not project_root.is_dir():
        raise ReferenceSheetError(f"project root is not a directory: {project_root}")
    plan_path = Path(_absolute_norm(plan_path, project_root))
    _reject_symlink_absolute(plan_path)
    plan = _read_plan(plan_path)
    characters_root = project_root / "art" / "characters"
    _reject_symlink_components(characters_root, project_root)
    if not characters_root.is_dir():
        raise ReferenceSheetError(f"art/characters root is not a directory: {characters_root}")
    frames = _validate_inputs(plan, characters_root)
    target = _output_path(output, project_root)
    sheet = _make_sheet(plan, frames)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.mkdir()
    try:
        sheet_path = target / "sheet.png"
        sheet.save(sheet_path, format="PNG", optimize=False)
        manifest = _manifest(plan, sheet, sheet_path.read_bytes())
        (target / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    except Exception:
        for child in target.iterdir():
            child.unlink()
        target.rmdir()
        raise
    return target


def verify(directory: Path, *, project_root: Path = PROJECT_ROOT) -> Path:
    """Rebuild expected pixels and metadata, rejecting any mismatch or extra file."""
    directory = Path(directory).expanduser()
    if not directory.is_absolute():
        directory = Path(project_root) / directory
    project_root = Path(_absolute_norm(project_root))
    directory = Path(_absolute_norm(directory))
    _reject_symlink_absolute(project_root)
    _reject_symlink_absolute(directory)
    characters_root = project_root / "art" / "characters"
    _reject_symlink_components(characters_root, project_root)
    if not characters_root.is_dir():
        raise ReferenceSheetError(f"art/characters root is not a directory: {characters_root}")
    if not directory.is_dir() or directory.is_symlink():
        raise ReferenceSheetError(f"reference sheet directory does not exist or is a symlink: {directory}")
    files = {p.name for p in directory.iterdir()}
    if files != {"sheet.png", "manifest.json"} or any(p.is_dir() for p in directory.iterdir()):
        raise ReferenceSheetError("reference sheet directory must contain exactly sheet.png and manifest.json")
    _reject_symlink_absolute(directory / "sheet.png")
    _reject_symlink_absolute(directory / "manifest.json")
    try:
        manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ReferenceSheetError(f"cannot read manifest: {exc}") from exc
    if not isinstance(manifest, dict) or manifest.get("kind") != MANIFEST_KIND or manifest.get("status") != "reference-only":
        raise ReferenceSheetError("manifest must have reference-only status and the expected kind")
    plan = manifest.get("plan")
    if not isinstance(plan, dict) or manifest.get("plan_sha256") != _sha256(_canonical_json(plan)):
        raise ReferenceSheetError("embedded plan digest mismatch")
    normalized = _read_plan_from_object(plan)
    if normalized != plan:
        raise ReferenceSheetError("embedded plan is not canonical")
    frames = _validate_inputs(normalized, characters_root)
    sheet = _make_sheet(normalized, frames)
    expected_bytes = _encode_png(sheet)
    expected_manifest = _manifest(normalized, sheet, expected_bytes)
    try:
        actual_bytes = (directory / "sheet.png").read_bytes()
        with Image.open(directory / "sheet.png") as actual_image:
            actual_image.load()
            actual_rgba = actual_image.convert("RGBA")
    except OSError as exc:
        raise ReferenceSheetError(f"cannot read output sheet: {exc}") from exc
    if actual_bytes != expected_bytes or actual_rgba.tobytes() != sheet.tobytes():
        raise ReferenceSheetError("sheet output differs from direct RGBA paste reconstruction")
    if manifest != expected_manifest:
        raise ReferenceSheetError("manifest metadata does not match reconstructed inputs, tool, and output")
    return directory


def _read_plan_from_object(plan: dict) -> dict:
    if not isinstance(plan, dict) or plan.get("kind") != PLAN_KIND:
        raise ReferenceSheetError("embedded plan kind is invalid")
    # Reuse the same validator as the JSON entry point without a temporary file.
    if plan.get("grid") != [3, 2]:
        raise ReferenceSheetError("embedded plan grid must be [3, 2]")
    cell = plan.get("cell_px")
    if not isinstance(cell, list) or len(cell) != 2 or any(type(n) is not int or n <= 0 for n in cell):
        raise ReferenceSheetError("embedded plan cell_px is invalid")
    inputs = plan.get("inputs")
    if not isinstance(inputs, list) or len(inputs) != 6:
        raise ReferenceSheetError("embedded plan must have six inputs")
    # Canonicalize through a temporary-independent check.
    seen = set()
    normalized = []
    for index, item in enumerate(inputs):
        if not isinstance(item, dict) or set(item) != {"file", "sha256"}:
            raise ReferenceSheetError(f"embedded input {index} is invalid")
        name, digest = item["file"], item["sha256"]
        if not isinstance(name, str) or not name:
            raise ReferenceSheetError(f"embedded input {index} path is invalid")
        relative = PurePosixPath(name)
        if relative.is_absolute() or ".." in relative.parts or "\\" in name or not relative.parts:
            raise ReferenceSheetError(f"embedded input {index} path is invalid")
        if relative.parts[0] not in {"sources", "templates", "parts"}:
            raise ReferenceSheetError(f"embedded input {index} is outside allowed roots")
        name = relative.as_posix()
        if name in seen:
            raise ReferenceSheetError(f"duplicate embedded input: {name}")
        seen.add(name)
        if not isinstance(digest, str) or not SHA_PATTERN.fullmatch(digest):
            raise ReferenceSheetError(f"embedded input {index} SHA is invalid")
        normalized.append({"file": name, "sha256": digest})
    return {"kind": PLAN_KIND, "grid": [3, 2], "cell_px": list(cell), "inputs": normalized}


def _encode_png(image: Image.Image) -> bytes:
    from io import BytesIO

    buffer = BytesIO()
    image.save(buffer, format="PNG", optimize=False)
    return buffer.getvalue()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    build_parser = subparsers.add_parser("build", help="build a new reference sheet")
    build_parser.add_argument("plan", type=Path)
    build_parser.add_argument("--output", required=True, type=Path)
    verify_parser = subparsers.add_parser("verify", help="verify a reference sheet")
    verify_parser.add_argument("directory", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "build":
            result = build(args.plan, args.output)
        else:
            result = verify(args.directory)
    except ReferenceSheetError as exc:
        print(f"reference_sheet: error: {exc}", file=sys.stderr)
        return 2
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
