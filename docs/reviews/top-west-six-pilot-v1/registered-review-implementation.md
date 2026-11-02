# Generic registered source review adapter

Implemented by gpt-6.1-sol / high. All assigned code is frozen for main-agent integration/native observation.

Files:

- new `tools/characters/registered_review.py`
- minimal registered dispatch addition in `tools/characters/review.py`
- new `tools/characters/tests/test_registered_review.py`
- new `godot2d/dev/characters/character_registered_samples.gd`
- new `godot2d/dev/characters/character_registered_trial.gd`
- new `godot2d/dev/characters/character_registered_trial.tscn`
- new `godot2d/tests/characters/test_registered_review.gd`

No source-preparation script, frozen construction engine, body/template/pose, source art, recipe, production scene, baseline, existing Godot script/scene, or save service was edited. No commits, nested agents, full Python suite, or check.py run by this agent. Main agent owns those coordinated checks and all native visual acceptance.

## Behavior

`registered_review.preflight(repo,suite_path)` validates the exact new suite contract, scope, runtime types/ranges, references, lexical path/symlink safety, actual strict manifest SHA, and invokes existing strict build.verify and source-preparation verify. Scope is schema3 body+top, finite matching idle/walk directions, consistent whole-frame geometry, alpha-over and no further frame registration. Run and farming are explicitly unsupported. Template, motion, direction, design and frame counts are data-driven.

Every selected top view/material, source bundle and ownership is tied to exactly one same-pose preparation frame, whose action/direction/canonical pose document/variant/geometry must match the recipe. All preparation inputs, exact preparation manifest, source.json and selected prepared output references must be direct strict build inputs. Unused decorative source-preparation listings are rejected. Actual canonical body reference identity is required for comparison A, even where strict construction would permit an equal-RGBA copy.

The frozen construction contract requires component textures in parts/. With main-agent confirmation, mapping/layer textures therefore use parts/ copies, whose RGBA and size are checked against the corresponding original prepared textures, and those originals are also direct build inputs. Material, bundle and ownership remain exact prepared-source paths. This reconciles the brief's prepared-output requirement without changing frozen engines.

`review.py registered [--dry-run]` performs preflight, then invokes the shared Godot executable with `character_registered_trial.tscn`, `--registered-suite=<absolute suite>`, and `/private/tmp/coastal-character-registered-review.log`. Existing launcher choices are unchanged.

The Godot loader composes existing resource paths and construction low-level helpers, without invoking head-state/fixed-identity code. It checks actual strict manifest/recipe/code/input SHAs, strict artifact digest, template/action/pose order/durations/geometry, actual canonical body PNG, selected annotation/registered top interfaces, prepared-source manifest/source flags/code/input/output SHA and PNG/RGBA data, same-pose material/ownership/bundle/texture and resolved annotation bindings, and strict output PNG/SHA/RGBA/size. It exposes A/B frames, per-frame metadata, nested clips, geometry and runtime. Every rejection clears all loader state.

The scene inherits `character_walk_trial.tscn`. The script only adapts ready/loading, restricted movement input, controls and status. There is no new `_physics_process`, clock, image compositor, actor or save path. Existing base world movement, actual-distance locomotion phase, idle clock, frame selection, actor.move_and_slide, and shared motion panel provide playback. Unsupported controls are disabled; A/B mean original body/current strict recipe. Failure removes old textures and disables controls. Whole-frame pose/preview placement comes from checked geometry; fixed UI strings/layout remain in the inherited scene overrides. Current geometry yields world pose scale .25/root offset(-123,-201) and source preview 1:1 after the existing CanvasLayer scale2.

## Verification and TDD

Initial focused Python command failed because the new preflight/launcher did not exist (10 tests, 15 assertion failures after correcting a fixture setup error). Later tests observed failure for unsupported composition before the explicit scope rejection was implemented.

Initial Godot test observed `FAIL registered_loader_exists`. Adversarial tests later exposed unsafe malformed clip/action reads; those now return a clear failure with all state cleared. Another observed failing test caught stale enabled controls after a failed trial reload; corrected before final validation.

Final Python:

`python3 -m unittest tools.characters.tests.test_registered_review`

**16 tests passed**, 1.636s. These use a genuine independent synthetic strict schema3 build and genuine registered-source preparations, with generic fixture/east/two-frame walk rather than current west/template/garment IDs. Coverage includes exact scope/runtime, unknown keys, wrong paths/SHAs/symlink ancestors, missing/duplicate preparations, missing direct parent/prepared texture closure, wrong same-pose material despite equal pixels, copied canonical-body reference, scope/capabilities/geometry, unsupported composition and launcher dispatch.

`python3 -m py_compile tools/characters/registered_review.py tools/characters/review.py tools/characters/tests/test_registered_review.py`

Exit 0.

`python3 tools/characters/review.py registered --dry-run`

Exit 0 with the expected registered scene, absolute suite and prescribed log path. This ran complete Python preflight on the actual main-agent strict seven-frame build and its walk/idle source-preparation sources. Actual build artifact at validation: `78d9d30da7363163ebc7f0db8fba890569f5fd7acc5bfd32ab193242272836fa`.

Godot fixture was produced by importing the new test module's `fixture(Path('/private/tmp/coastal-registered-review-fixture-r001'))`; its genuine build/source manifests and exact engine script copies live only under that temporary directory.

`/Applications/Godot.app/Contents/MacOS/Godot --headless --path godot2d --log-file /private/tmp/coastal-registered-review-test.log --script res://tests/characters/test_registered_review.gd -- --fixture-project=/private/tmp/coastal-registered-review-fixture-r001`

**78 checks passed**, exit 0, about 3.43s. Checks cover synthetic canonical and alpha-over RGBA, uneven frame durations, all state-clearing paths, unsupported/duplicate capabilities, changed time, malformed action/frame/clips, wrong pose source, missing closure, tampered output with recomputed byte SHA, missing/duplicate prep references, bad scope/unknown fields/SHA, clean reload, thin scene/controller movement→actual idle, unsupported controls/input, A/B, shared panel stepping and actual seven-frame body/output RGBA plus timing. Current actual suite was present and all 16 real-data assertions ran; if future users run the fixture test without that optional actual suite it still performs the fixture contract checks.

Independent real-data loading/trial smoke script additionally confirmed 7 total frames, west walk indices1..6, west idle index0, canvas256x224/root(123,201), actor(1600,1600), pose scale(.25,.25), offset(-123,-201), and no loading error.

Godot logs have no GDScript parse/runtime error in the final passing run. The local engine emits its existing macOS startup `get_system_ca_certificates` ERROR (`ret != noErr`) before tests; it did not affect scene/resource/test success. Do not classify this as a script or gameplay failure.

## Independent review correction

The independent top-build audit found a valid strict-construction counterexample: keep the walk prepared material and walk mapping target, but set that view's source_pose record to idle. Equal fixture pixels and equal anchors let the generic strict mapper accept this legal cross-pose mapping, while this review adapter is explicitly same-pose. Python originally checked the material/preparation identity without resolving that annotation and accepted it.

Added `test_source_annotation_must_match_actual_prepared_pose_even_with_equal_pixels`; first observed it fail with `ValueError not raised` after a successful real strict rebuild. Python now loads and binds both source and target annotation document/record, requiring unique actual record and matching poses ref, variant, pose_id, actual canonical reference_frame, canvas, root and display scale. It does not rely on selector strings being equal. The Godot `annotation_valid` function already enforced those same resolved semantics; added the same mutated fixture with recomputed recipe/manifest/SHA and confirmed rejection, all state clearing, and successful reload. Final 16 Python/78 Godot counts include this correction and the later consistency/UI clearing corrections below. Source/build art hashes did not change; only adapter code and tests changed. Main agent was explicitly notified that previous full-suite results predate this correction and should be rerun.

## Hidden panel failure clearing correction

A second independent Godot review observed that a hidden motion panel retained its previous reference/motion textures after `load_registered` failed: hidden panels do not process, so world pose clearing alone did not clear both previews. Added three assertions before the fix: immediate clearing of both previews while hidden, stopped playback/zero preview phase, and still clear after two process frames. All three first failed as expected. The failure branch now sets preview phase to zero, calls the existing panel `set_playing(false)`, and clears both preview textures synchronously. No new clock or shared panel changes. Final focused run: **78/78 checks passed**, exit0, about3.43s. Only `character_registered_trial.gd` and `test_registered_review.gd` changed in this correction; Python remained frozen and its ongoing main-agent final suite is unaffected. Main agent was notified to recapture final native evidence after this Godot change.

## Final Python/Godot finite-scope consistency correction

Independent review found a valid strict build with frame layer_order top→body that passed Python review preflight but was outside the Godot adapter's body→top subset. Added a genuine strictly rebuilt reversed-order fixture and a genuine strictly rebuilt identity-normalized source-selection fixture; both initially passed preflight unexpectedly. Added coverage/occlusion scope tests; both also initially lacked explicit rejection. The four failures were observed before correction.

Python now explicitly requires the actual body.id then top.id order, exactly the two body/top layers, alpha-over/null frame registration, null layer coverage/occlusion, binary-rgba-extract-v1 with exactly its kind/density_normalization keys and density None, and null mapping coverage/occlusion. These match the existing Godot finite interface; no feature was added and no GD file changed. Final registered_review Python run: **16/16 passed**, 1.636s; py_compile and actual seven-frame registered launcher dry-run also passed. Only `registered_review.py` and `test_registered_review.py` changed in this correction. Main agent was told to rerun final Python checks and recapture current native evidence, since earlier runs predate this last Python change.

## Boundary and remaining work

Godot JSON parsing turns JSON numbers into floats. Re-serializing a source-prep manifest containing integer rational arrays therefore cannot reproduce Python's typed canonical JSON digest. Godot intentionally binds the source-prep artifact's exact manifest file SHA through strict build inputs and validates all actual parents/code/PNG/RGBA; typed source artifact reconstruction remains the mandatory Python preflight responsibility, matching the existing runtime-consumer convention. The strict build artifact digest (string-only input/engine tree) is independently recomputed in Godot.

This adapter consumes finite same-pose prepared binary garment material with identity/root registration and alpha-over; it does not add alternate composition, moving source landmarks, hidden anatomy, farming or run support. These unsupported interfaces fail rather than being approximated.

Native GPU observation, motion/occlusion/physical appearance acceptance, final coordinated full Python/check and documentation integration remain with the main agent. Headless checks are not visual acceptance or release approval. Main's observer/capture file is independent and was not edited by this agent.
