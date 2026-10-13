# Task 1 report: compact north-entry runtime (2026-10-13)

Status: DONE. Runtime and focused native checks pass. Final furnishing artwork, full legacy suite, exported app and packaging remain parent-owned Task 2/3.

## Changes

- room_data: 288x208 floor at176,112; north door320,128; safe point320,160; exact approved furniture bases and functional points; continuous southern boundary; shelf is wall-mounted, no air collision.
- interactive_door + door_jamb: explicit entrance_normal DOWN; inclusive depth0..56 and lateral24; independently drawn fixed foreground jamb at layer2.
- room_transition: rectangle-shape path preflight checks lateral alignment and forward approach against actual physics, excluding only actor and door; actual automatic walking uses move_and_collide at72units/sec. Alignment preserves initial Y and refuses blocked paths. Player root no longer forced above doors.
- player + doorway_clip shader: sprite-only aperture plane at1 below foreground jamb2, vertex-local frame clipping (correct for AtlasTexture); full character remains visible on floor; concealment starts only after feet cross threshold and completes16units inside before fade. Reverse reveal on arrival. Success/failure/load/reset restore sprite layer0, root0, alpha, clipping and visibility.
- house_session: v2 save format/inventory unchanged. Old320,300 preserved, old320,328 and new doorway/furniture/invalid coordinates safely fall back. North reset/storage point updated.
- house_interior: compact structural drawing and shared y-sort layer. Furniture art rendering untouched for parent.
- Existing house and cottage runtime tests retain coverage with updated geometry; new compact tests add sweeps, obstruction, real shape routes, floor visibility, shader render pixels and reusable five-stage capture helper.

## RED evidence

1. /private/tmp/compact-red.log: failed both57depth x3lateral sweeps, compact floor/north entry, old south/new doorway/new bed migration.
2. /private/tmp/compact-red-behavior.log: failed no-retreat, root layer, fully hidden before fade and progressive clipping.
3. /private/tmp/compact-render-red.log: native north and south actual rendered half-clip tests both failed due to atlas UV. Fixed with frame-local vertex coordinates.
4. /private/tmp/compact-floor-clip-red.log: full_character_until_inside_aperture failed; clipping was visibly removing the head while feet were on floor. Parent visual review plus test drove concealment inside aperture only.
5. Intermediate five-stage screenshots exposed y-sort aperture darkness covering the entire partial actor. Sprite-only opening plane corrected this; root remains0 and fixed jamb stays2. Final captures below supersede earlier recording.

## GREEN commands and results

All commands run at repository root and use isolated /private/tmp save directories.

- /Applications/Godot.app/Contents/MacOS/Godot --log-file /private/tmp/compact-stage-green.log --path godot2d --script res://tests/test_compact_cottage.gd -- --capture-doorways
  Native38checks pass: inclusive sweeps for both doors, near trigger no retreat, full hiding before fade, floor visibility, obstruction rejection/control retained, menu exclusion, five actual swept-character routes (bed/kitchen/chest/photo/chair), load/reset cleanup, native shader alpha-pixel counts north/south, five capture stages in both directions.
- /Applications/Godot.app/Contents/MacOS/Godot --headless --log-file /private/tmp/compact-runtime-final.log --path godot2d --script res://tests/test_cottage_runtime.gd
  18pass after final aperture/layer changes.
- /Applications/Godot.app/Contents/MacOS/Godot --headless --log-file /private/tmp/compact-house-save.log --path godot2d --script res://tests/test_house_save.gd
  29pass.
- /Applications/Godot.app/Contents/MacOS/Godot --log-file /private/tmp/compact-house-gui.log --path godot2d --script res://tests/test_house.gd -- --record-house --output=/private/tmp/compact-house-evidence
  108pass including20cycles/no leaks/inventory, physical bed/wall contacts, held input and menu/reset locks, missing destination rollback and cleanup, saves/migration/explicit failed write. This run preceded final clipping-start/visual-plane refinement; focused native38 and cottage18 were rerun afterward. Parent will run final integrated full regression once after art integration.
- git diff --check passes.

## Visual evidence

Final actual source-scene captures: /private/tmp/compact-door-stages/{harbor,house}-{before,partial,full,emerging,closed}.png.
Inspected house-partial and harbor-emerging after final correction: actor is progressively visible inside actual aperture, not headless on floor; door foreground fixed trim remains above actor.
Native isolated shader evidence: /private/tmp/compact-clip-{north,south}-{0.0,0.5,1.0}.png.
Earlier continuous source recording: /private/tmp/compact-house-evidence/frames/0000.png..0042.png; contact sheet /private/tmp/compact-door-contact.png. Earlier recording is diagnostic and precedes the final visual corrections, not final acceptance evidence.
Reusable --capture-doorways option remains in test_compact_cottage for parent final art/export validation.

## Concerns / environment

Native GUI required approved unsandboxed launch (sandbox exited134). Sandboxed headless emits macOS certificate warning; approved headless save run is clean. Initial save test could not write its existing res://verification-house-save output under sandbox; rerun approved and29pass. House108 includes one expected engine error for deliberate impossible-save-path fixture; test explicitly verifies this failure.
No Windows validation and no exported binary validation in this task. Temporary structural/furniture fallback art is intentionally replaced by parent. No art pipeline or house_furniture edits.

---

## Historical pilot report (preserved)

# Task 1 report: cottage pixel source pilot

Status: **DONE_WITH_CONCERNS**. Four separate built-in generated RGBA PNG candidates and complete prompt/source records are saved under `art/interior/source/`. This task does **not** approve the files for direct runtime import. The user has subsequently authorized programmatic transparency cleanup, pixelation, and common-canvas alignment; that normalization is a separate follow-up task and was not applied here.

## Delivered source files

| File | Native dimensions | Visible bbox (alpha ≥128) | Assessment |
| --- | ---: | --- | --- |
| `art/interior/source/bed.png` | 1024×1536 | `(181,196,843,1231)` | Narrow single bed, intact shell/feet; broad brown semitransparent exterior halo; candidate only. |
| `art/interior/source/door-closed.png` | 1037×1517 | `(239,263,788,1284)` | Front-facing leaf, four panes, brass knob, left hinges; candidate. |
| `art/interior/source/door-half.png` | 1037×1517 | `(238,197,628,1325)` | Narrower pose with similar visible left edge; taller visible range than closed. |
| `art/interior/source/door-open.png` | 1037×1516 | `(236,196,424,1337)` | Narrowest pose, same identity; source canvas one pixel shorter and taller visible range. |

The native images are **not** 48×80 or 30×44. Those are only target logical sizes. All four have an alpha channel, but the alpha≥1 bounds extend far outside the visible shapes, especially for the bed. Alpha channels and transparent corners do not prove crisp transparent sprite silhouettes.

## Source paths and prompts

`art/interior/source/prompts.md` contains the exact prompts and the original built-in output path for every generated candidate, including the rejected first bed attempt and the failed targeted bed halo repair. The chosen originals were copied byte for byte into the source directory; the discarded attempts were not placed in the project.

## Visual review and integration risk

The door leaves appear to swing around a common left edge, but a matching stationary hinge and height across all three poses is **not verified**. Their visible upper and lower bounds shift materially: closed `(263,1284)`, half `(197,1325)`, open `(196,1337)`. Separate independent cropping or centering would move their hinge. The door/source art has not yet been scaled or previewed against the player, so it may not retain its details at 30×44 logical pixels. The bed's glow remained after one focused image edit; that edited result was rejected. The bed also has smooth tonal gradients, which will need review after authorized pixelation.

No runtime scenes, scripts, or tests were changed by this task. Follow-up work should derive cleaned, aligned runtime copies from these originals, preserve the generated sources, and visually inspect the actual in-game scale and common pivot.
