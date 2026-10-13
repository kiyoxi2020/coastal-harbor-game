# Cottage bed and indoor door runtime pilot

Status: DONE. Only the verified bed and indoor door art has been integrated into the game. Source PNGs and the other furniture remain unchanged.

## Implementation

- The bed uses `bed.png` at its 48×80 logical size and manifest pivot `[24,79]`; its collision rectangle is `Rect2(128,128,48,80)`. The former side area beside x112–122 is walkable, while the bed still blocks at x144.
- The inside door uses the three processed 30×59 PNGs without pose-specific resizing. All poses share the floor anchor `[15,54]`. A fixed 38-pixel frame, tightened to top `-54`, and dark aperture sit behind the leaf. The exterior door keeps its original 22×29 drawing and behavior.
- The room's safe spawn is `(320,300)`. A saved point in the door leaf and foot-clearance region, including the legacy `(320,328)`, normalizes to that spawn. Crossing and arrival now take distance divided by player speed, with the previous approach timing retained.
- The pilot manifest is parsed once by `cottage_art.gd`; missing files show the previous drawing and issue a warning with the missing path. The export include filter explicitly includes `assets/house-interior/*.json` without changing the export path or version.

## Test evidence

- RED: `/private/tmp/cottage-runtime-red.log` — expected failures for the old spawn and bed rectangle, then missing `pilot_texture` before implementation.
- Additional frame RED: `/private/tmp/cottage-frame-red.log` failed at `frame_clears_spawn_feet`. GREEN: `/private/tmp/cottage-runtime-green4.log` — 18 runtime checks, including a real indoor exit whose position progresses during a crossing longer than 0.6 seconds.
- GREEN: `/private/tmp/cottage-house-save-test.log` — 29 save checks. The first sandboxed run completed its assertions but could not write its `res://verification-house-save` report; the rerun with file access passed and wrote the report.
- GREEN: `/private/tmp/cottage-house-test.log` — 99 headless house checks, including the old bed side walkability check.
- GREEN graphical run: `/private/tmp/cottage-house-gui-final.log` and `/private/tmp/cottage-house-gui-final/tests.json` — 106 checks, with real OpenGL/Metal rendering. The intentional save-write-failure case reports its expected directory error and passes its assertion.
- Real GUI captures: `/private/tmp/cottage-house-gui-final/04-interior.png` (final tightened frame, closed door, and new bed), `/private/tmp/cottage-house-gui-final/10-interior-saved.png` (saved room). Earlier real GUI sequence frames `/private/tmp/cottage-house-gui/frames/0015.png` and `/private/tmp/cottage-house-gui/frames/0020.png` show opening and open poses before the static frame was tightened; the registered leaf art is unchanged.

The closed frame, opening poses, bed, spawn visibility, and player layering were inspected at the 1280×720 game viewport. No release package was built in this pilot.
