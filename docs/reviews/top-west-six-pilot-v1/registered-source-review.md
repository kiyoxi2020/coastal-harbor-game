# Independent review — registered source preparation

## Scope

Reviewed the supplied brief and implementation report, plus both complete files in `/private/tmp/coastal-registered-source-review-package.txt` against the current workspace copies. No project file was changed. I did not run the full character suite or `check.py`.

## 1. Specification conclusion: conforms for the stated preparation contract

The implementation structurally binds each selected garment frame to exactly one `representation=body` registration entry by pose ID. It binds the actual body PNG and authoring references, derives the target canvas/root and body scale from the registration plan, reads the canonical pose variant/frame, and recomputes the body's nearest affine before accepting that canonical PNG. It also checks the canonical template/action/direction, pose ID, variant geometry and frame duration. Caller fitting offsets/scales are excluded by exact-key validation.

Garment dimensions must exactly satisfy the reduced rational density in both axes. The material root and effective scale are derived with `Fraction`; one affine is applied to both RGBA material and binary `L` ownership. `Image.composite` selects unchanged sampled RGBA rather than multiplying alpha or repainting. The per-pose root trajectory remains tied to the matching body registration. Sparse west-only preparations are supported; the implementation does not invent other directions.

The output is truthfully marked derived and review-only. `source.json` records `prepared-derived-review-only`, `accepted=false`, `runtime_eligible=false`, `complete_hidden_source=false`, source/ownership parents, input closure and derived asset roles. The manifest records the plan, bound inputs, tool/Pillow identity, rational transforms, output bytes/RGBA hashes, and review-only/release-ineligible status. `verify` reconstructs from current parents and compares metadata plus exact output bytes; it checks symlinked paths and extra/missing output entries.

A downstream schema-3 view can reference `materials/<pose>.png`, its matching `ownership/<pose>.png`, and this bundle's `source.json`; the bundle intentionally has no bundle-wide `source_view_pose` claim. This tool does not create the downstream annotation sidecar or strict character recipe. Adult-standard-v2 still needs a real canonical-pose annotation for that integration, as noted in the earlier feasibility report.

## 2. Quality conclusion: strong core checks; two scope limits to preserve

No blocking correctness issue was found for the intended small six-pose preparation. The production transform uses bounded PNG decoding, path traversal/symlink checks, exact input SHA checks, reduced positive Fractions, source-box bounds, binary ownership validation, canonical body pixel equality, no-clipping checks for owned support, fresh exclusive output creation, and complete output inventory verification.

The tool proves consistency with the registration plan supplied to it; it does **not** independently attest that this plan was externally approved or archive-accepted. If that distinction is material, include the approved body archive/acceptance record in the preparation authoring closure and retain its SHA. The output remains review-only either way.

The resource limits are per image and per frame, but output images are accumulated in memory for all frames. With the allowed maximum of 256 frames and 32 megapixels per image, a deliberately oversized plan could require many gigabytes. This is not a practical issue for the six 418×627 source cells, but a future public/general use should consider a total-pixel or total-memory cap, or streamed output generation.

The `authoring_inputs` closure is explicit rather than recursively proven by the strict build contract. The source-prep verifier recomputes the closure listed in the plan; downstream recipes still need to list the preparation manifest and each required parent directly if those files must participate in the strict build digest.

## Reproducible evidence

- Ran five focused temporary-fixture tests:

  `python3 -m unittest tools.characters.tests.test_prepare_registered_source.RegisteredSourceTests.test_sparse_west_build_preserves_source_rgba_and_fractional_registration tools.characters.tests.test_prepare_registered_source.RegisteredSourceTests.test_per_pose_source_root_trajectory_is_copied tools.characters.tests.test_prepare_registered_source.RegisteredSourceTests.test_wrong_raw_body_sha_and_body_authoring_sha_refused tools.characters.tests.test_prepare_registered_source.RegisteredSourceTests.test_verify_detects_forged_output_hashes tools.characters.tests.test_prepare_registered_source.RegisteredSourceTests.test_verify_detects_extra_missing_source_or_symlink`

  Result: **Ran 5 tests in 0.061s — OK**. These use temporary repositories and cover fractional registration, alpha/RGB preservation, per-pose root, parent SHA rejection, forged output hashes and path/output inventory checks.

- Independently reapplied the existing `pack_sources.render` affine from `sources/visible-atlas-body-r001/packing/r001.json` to all six west-walk raw body frames and compared RGBA bytes against the canonical adult-standard-v2 visible body PNGs. All six comparisons returned `True` (`suit_walk_west_0` through `_5`).

- Reviewed code paths for body binding, Fraction density/root math, owner extraction, derived source bundle, complete-input manifest, symlink handling, and output status. No actual worn-source build was run because this review was limited to the supplied implementation and temporary fixtures; mask quality and human ownership approval are outside this check.

The implementation report's **25-test** focused suite result is the author's reported result; this independent review ran only the five listed tests, as requested.
