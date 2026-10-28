# Character build gates implementation plan

**Goal:** Make future character construction use one strict, testable entry point.

**Architecture:** Validated recipe -> registered full-frame layer compositor -> immutable review build -> dependency/output verification. Repository checks detect disallowed production/resource changes. Existing migrated samples remain read-only references.

**Tech Stack:** Python3, unittest, Pillow, existing Godot review resources.

## Constraints

No production character switch, no artwork changes, no overwrite of frozen migrated inputs, no automatic commit/push. No second runtime model. First contract supports full-frame layers, alpha-over or binary ownership composition, and whole-source registration exactly matching the selected template variant; local transforms/cropping/density resize fail explicitly.

### Task 1: Contract and tests

- [x] Create tools/characters/tests/test_build_contract.py with isolated /private/tmp/coastal-* fixtures.
- [x] Exercise valid 3-frame recipe plus idle, missing capability, SHA/pose/timing/mask/identity/root failures and overwrite refusal.
- [x] Run `python3 -m unittest discover -s tools/characters/tests -p test_build_contract.py`; confirm failure because build entry is missing.

### Task 2: Unified builder

- [x] Create build_contract.py for strict keys/references/identity/pose/interface/dependency validation.
- [x] Create build.py exposing `build <recipe> --output <dir>` and `verify <build-dir>`; reject existing outputs and stale inputs, produce review-only manifest, never active-release.
- [x] Add one strict revision adapted from the current wardrobe west-hoe sample. Rebuild to /private/tmp and compare all five RGBA frames to existing accepted outputs.

### Task 3: Repository gates

- [x] Write failing tests for new old-root, old references, extra production character dependency and tampered builds.
- [x] Add check.py plus explicit production dependency baseline, scan strict recipes/builds and Godot references.
- [x] Add GitHub Actions workflow and pinned Pillow requirement; invoke unittest and check.py. Do not claim branch protection was configured.

### Task 4: Verify and handoff

- [x] Run all character Python tests, check.py, real-art rebuild/equivalence, existing migrated layout Godot regression and unchanged native input receipt validation.
- [x] Update AGENTS, character tool/library READMEs, PROJECT_STATE/HANDOFF/development plan with entry commands, supported scope and remaining release gates.
- [x] Mark Paseo steps complete and close run; report no commit/push.

Completed: 75 Python tests, 13 Godot checks, 5 exact real-art RGBA frames, migration/native-input preservation checks. Remote CI and branch protection were not executed/configured. No commit or push.
