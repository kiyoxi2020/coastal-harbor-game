# Lossless reference-sheet utility implementation

## Scope and files

Added only the two assigned files:

- `tools/characters/reference_sheet.py`: reusable 3×2 reference-sheet CLI (`build`, `verify`).
- `tools/characters/tests/test_reference_sheet.py`: real Pillow image and path safety tests.

The tool accepts `coastal-character-reference-sheet-plan-v1` with `grid=[3,2]`, `cell_px`, and exactly six row-major `file`/`sha256` items. Inputs are relative to `art/characters`, under `sources/`, `templates/`, or `parts/`. It rejects absolute/traversal paths, symlink components, duplicate entries, bad SHA, non-RGBA files, inconsistent dimensions, invalid grid/count, existing outputs, and output locations outside `art/characters/sources/<id>/references/<revision>` or `/private/tmp/coastal-*`.

Build creates only `sheet.png` and `manifest.json`. It directly RGBA-pastes cells onto a transparent RGBA canvas, without alpha-over, resize, or crop. The manifest records canonical plan and digest, each cell's source/hash/position, script and Pillow identity, output PNG SHA and raw RGBA SHA, and fixed `reference-only` status. Verify rejects symlinks in every ancestor of the project, plan, source, output directory, sheet, and manifest; reconstructs expected pixels from current inputs; compares exact RGBA and PNG bytes plus all manifest metadata; and rejects extra files.

## TDD and verification evidence

### Initial implementation

1. Wrote tests before implementation.
2. RED: `python3 -m unittest tools.characters.tests.test_reference_sheet` failed to import the missing module, the expected missing-feature failure.
3. GREEN: the focused suite passed 6 tests after correcting one test's pixel coordinate.
4. `python3 -m unittest discover -s tools/characters/tests`: **425 tests passed in 244.194 seconds** before the later symlink-hardening change.
5. The main agent's output `art/characters/sources/top04-adult-v2-west-walk-r001/references/r001` passed the then-current CLI `verify` before hardening.

### Symlink review fix

The main agent found that plan/project ancestor symlinks and verify output ancestor/file symlinks were not all rejected. Added red tests first: the focused run failed on symlinked plan, `art` ancestor and verify output parent as expected. Added component checks without resolving away symlinks for project root, plan path, `art/characters`, source path, output path and verify sheet/manifest.

After the fix:

- `python3 -m unittest tools.characters.tests.test_reference_sheet`: **13 tests passed**.
- `python3 -m py_compile tools/characters/reference_sheet.py tools/characters/tests/test_reference_sheet.py`: passed.
- Final script SHA-256: `6b4b1d9836628744c510c6a2b2c0dda2bc0da3940495e6ee75cb7ed7b0dff299`.

Per main-agent coordination, I did not rerun the full 425-test suite or `check.py` after this fix. The extra `python3 tools/characters/check.py` process started before the review fix was interrupted at the main agent's request; it exited 130 with `KeyboardInterrupt` in existing `tools/characters/build_contract.py` mask verification. That run is not counted as passing. The pre-fix full suite result remains recorded; the main agent will run the full suite plus new tests and `check.py` once after final freeze.

The real r001 directory and manifest were not modified. Its embedded script identity points to the pre-hardening script; do not overwrite or treat it as verification under the final script. Build a fresh r002 with the final CLI before use.
