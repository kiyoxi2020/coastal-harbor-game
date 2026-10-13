# Compact cottage Task 2: generated furnishings integration

## Delivered

- Integrated all 13 measured subjects from the existing built-in generated atlas. Preserved the atlas, prompt, bed and three door source images and their existing texture pixels.
- Registered independent furniture, two windows, framed photo, two rugs, floor and wall textures in both processed-art locations. The manifest records source path and region, logical size, foot anchor, alpha rule, physical base and interaction points where applicable.
- Used deterministic alpha threshold 128 and largest connected subject for transparent silhouettes, then nearest-neighbor resizing. Opaque wall/floor tiles come from an inset of the corresponding generated patches. Their alpha is made fully opaque after checking the interior contains no transparent gaps.
- Runtime furniture now draws registered images. No procedural furniture rendering remains. Wall and floor repeat the generated 64×64 textures; rugs draw below the player. Bed and door texture dimensions and placement remain unchanged.
- Furniture blockers now describe physical bases. The lamp and leaves do not add collision, and wall-mounted shelf, photo and windows have no floor blockers.

## RED then GREEN

- New Python real-atlas test initially failed because all 13 atlas subjects were absent from `pilot.json`. It now passes and checks completeness, original provenance, dimensions, binary alpha, duplicate outputs, opaque wall/floor and four interaction points. The four existing fixture tests still pass without an atlas.
- Expanded Godot runtime test initially failed for all new furniture, windows, rugs, wall and floor. It now passes every image-loading assertion.
- Final checks: `python3 -m unittest tests.test_prepare_cottage_assets` (5 passed); Godot `test_cottage_assets.gd`, `test_cottage_runtime.gd`, and `test_compact_cottage.gd` (all passed). Godot prints a macOS certificate-store warning in headless runs; it does not affect these tests.
- GUI capture at 1280×720 with camera 2× was viewed at `/private/tmp/cottage-task2-final.png`. It shows all requested generated art in the compact room, clear north entry and usable paths. This checks the static final room; door-transition visual stages and packaged export remain Task 3/final-release work.

## Scope and remaining work

No new image generation was performed. No door-transition code, release package or full legacy suite was changed or run in this task.
