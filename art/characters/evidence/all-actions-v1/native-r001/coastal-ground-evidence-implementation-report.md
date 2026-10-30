# Bounded native target geometry verifier

New files only: `tools/characters/ground_evidence.py` and `tools/characters/tests/test_ground_evidence.py`. Existing evidence/capture/contact/core/source modules were not edited.

Frozen SHA:

- ground_evidence.py: `63d63b28e5d1cc3aa3ac4ef9b67e7efc705796ccf571bdf02e4c4426febe9b0f`
- test_ground_evidence.py: `8de288e95a83f213628bbae5be8af2b347c0a868a06ae31279f9a8094258e681`

12 tests PASS68.290s, no errors/warnings: `/private/tmp/coastal-ground-evidence-final-tests-r002.log`. Missing implementation, missing CLI, exact-completion and real32 crop-boundary cases were established RED first. Initial complete scope11 tests also passed; the12th adds the narrowly bounded real32 crop reconstruction case. Synthetic fixture pixels and reports prove the tool only, never actual art/native/soil acceptance.

The verifier consumes the independent sibling `E-ground/input-contract.json` and `report.json`, with kind `coastal-native-ground-target-alignment-observation-v1`. It reuses the complete spatial input-closure and actual loaded-library binding helpers. It does not add a seventh observer or alter the existing six-scope receipt/aggregate.

It verifies the frozen candidate JSON SHA and artifact pin, eight unique Hoe/Water direction cases, canonical pose/source image/SHA and actual material RGBA at the exact canonical point, final composed PNG at its whole-frame padded point, actual GPU pose/hash, and source flags unchanged. The actual frozen GardenA scene and farm grid rules determine the cell center and16×16 half-open bounds. Standing offset is center-minus-actor; direction ties use Y like the game. It checks <=24 distance, false ray hit, and independent forward12 keyboard probe inside the same declared cell.

Each case must use a unique actual player instance, strictly ordered/consecutive stationary physics ticks, correct actual clock/GPU frames and completion. Completion uses exact `elapsed>=duration`, without prematurely rounding a value below the boundary. A captured row is bound to the same actual physics tick/state/instance/actor position/clock.

The source-to-world matrix is checked against the frozen scene registration density, actual actor/pose scale and canonical root offset. Source pixel centers use `source+.5+sprite_offset`. Real32 world and screen projection must agree with recorded binary64 values and the actual camera scale. The actual PNG SHA/dimensions, crop origin and point-in-crop are bound. A2ULP native-float truncation interval handles a reconstructed render origin straddling an integer; arbitrary+2px crop displacement remains rejected. No world point, part, standing position or target bounds are fitted or moved.

Returned receipt scope is `native-geometric-target-alignment-only`. `source_ground_contact_proven`, `physical_soil_impact_proven`, `soil_deformation_proven`, `hidden_grip_proven`, `gameplay_transaction_proven`, `native_raster_correspondence_proven`, `user_approval` and `release_eligible` remain false. Eight-source-pixel material uncertainty is recorded, never used to relax projection or target bounds. Source70 fingerprint is retained as lineage; source material semantics and soil mechanics are not upgraded.

CLI:

```sh
python3 tools/characters/ground_evidence.py validate --evidence /private/tmp/coastal-...-ground --receipt /private/tmp/coastal-...-ground/native-target-geometry.json
```

For an isolated fixture use `--repo /private/tmp/<fixture>` before `validate`. Receipt must be fresh and beside the raw report; it cannot overwrite input/report. Python API: `ground_evidence.validate(repo,evidence)` and `write_receipt(repo,evidence,output)`.

Root owns actual full24 native collection and final whole-project unittest/check. No actual ground capture was claimed or regenerated in this implementation task. No nested agent or commit.
