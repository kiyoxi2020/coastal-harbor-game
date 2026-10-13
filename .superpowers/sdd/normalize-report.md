# Cottage pilot asset normalization report

Status: DONE_WITH_CONCERNS. This prepares and validates the four pilot assets only. No room scene, door behavior, or game package was changed.

## Method and registration

- Source files remain immutable in `art/interior/source`. Run from repo root: `/opt/homebrew/bin/python3 tools/prepare_cottage_assets.py`.
- Alpha threshold is 128: source alpha values below 128 become transparent, all remaining pixels become fully opaque. RGB is sampled from the source with nearest-neighbor resize; no colors are painted. The source bed has zero pixels at alpha 255, so using 255 as the threshold would erase it.
- Bed threshold silhouette is tightly cropped and fit without stretching in a 48×80 canvas. Actual occupied region is 48×75, centered horizontally and bottom aligned with 5 transparent pixels above.
- Doors use one source registration: threshold union region `[236,196,788,1337]`, one nearest resize to a 26×55 inner region, and 2 pixels of transparent padding on all sides. All three frames share a 30×59 canvas. `registration.scale` is the nominal 0.048; integer rounding gives effective factors 26/552 and 55/1141 for every pose. No pose has its own crop or scale. Source hinge marks `(255,470)` and `(255,1090)` map to `[3,15]` and `[3,45]`. `pivot` is the lower hinge `[3,45]`. The independent closed-leaf floor anchor is `[15,54]` and is shared in the manifest for all poses.
- Closed/half/open visible leaves are 26×49, 18×54, and 9×55. The open poses extend beyond the closed leaf vertically; the common envelope retains all of them. `logical_size` is the envelope, while `closed_leaf_size` and `visible_leaf_size` record silhouette dimensions separately.

## Source and output measurements

| Image | Source dimensions | Source threshold bbox | Source alpha 0 / 1–127 / 128–254 / 255 | Output dimensions | Output alpha 0 / 255 | Output bbox |
|---|---:|---:|---:|---:|---:|---:|
| bed | 1024×1536 | 181,196,843,1231 | 952010 / 18135 / 602719 / 0 | 48×80 | 668 / 3172 | 0,5,48,80 |
| door-closed | 1037×1517 | 239,263,788,1284 | 1008101 / 13349 / 550977 / 702 | 30×59 | 536 / 1234 | 2,5,28,54 |
| door-half | 1037×1517 | 238,197,628,1325 | 1168362 / 8276 / 395666 / 825 | 30×59 | 899 / 871 | 2,2,20,56 |
| door-open | 1037×1516 | 236,196,424,1337 | 1370450 / 7706 / 192486 / 1450 | 30×59 | 1303 / 467 | 2,2,11,57 |

Every output has binary alpha only. The four PNGs and `pilot.json` are byte-identical between `godot2d/assets/house-interior` and `art/interior/processed`.

## RED / GREEN evidence

- Python RED: `/opt/homebrew/bin/python3 -m unittest discover -s tests -p test_prepare_cottage_assets.py -v` failed with `ModuleNotFoundError: No module named 'tools.prepare_cottage_assets'` before implementation. After adding floor-anchor coverage, it failed with `KeyError: 'floor_anchor'` before that metadata was implemented.
- Python GREEN: same command passed 4 tests (halo removal/source color, empty and opaque rejection, shared door registration and narrowing, deterministic copied outputs).
- Godot missing-manifest RED: `/Applications/Godot.app/Contents/MacOS/Godot --headless --log-file /private/tmp/cottage-test-red.log --path godot2d --script res://tests/test_cottage_assets.gd -- --manifest res://assets/house-interior/absent.json` exited 1 with `FAIL missing pilot manifest`.
- Godot import GREEN: `... --headless --log-file /private/tmp/cottage-import.log --path godot2d --editor --import` exited 0 and imported the four PNGs. It reported the known macOS certificate warning and an editor settings save error outside the sandbox; neither blocked import.
- Godot validator GREEN: `... --headless --log-file /private/tmp/cottage-test.log --path godot2d --script res://tests/test_cottage_assets.gd` exited 0 with `PASS cottage pilot assets: 4`. The macOS certificate warning remains.
- Graphical preview: `/Applications/Godot.app/Contents/MacOS/Godot --log-file /private/tmp/cottage-preview-gui.log --path godot2d --script res://tests/cottage_asset_preview.gd -- --output /private/tmp/cottage-asset-preview.png` exited 0. Screenshot: `/private/tmp/cottage-asset-preview.png`. Godot's headless dummy renderer cannot produce a viewport image, so graphical execution was used.

## Review concern and plan deviation

At 2× world scale, the current `atlas.gd` player frame is approximately 313×313 source pixels, visually much larger than the 48×80 bed and 30×59 door. The screenshot makes this clear. Runtime integration should choose placement and player scaling deliberately. The closed visible leaf is 26×49 rather than the approximate 30×44 target; preserving aspect and using one transform for all door poses kept their shapes and relative widths intact.

The initial source-only pilot plan was amended with user-authorized alpha cleanup, nearest pixel reduction, shared door canvas registration, mirrored processed copies, richer manifest metadata, and a rendering preview. This report covers the pilot only.
