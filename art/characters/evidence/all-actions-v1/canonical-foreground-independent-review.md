# Independent review — canonical foreground / canonical pose tokens

Result after the authority fix: PASS for this bounded delta. Critical0, remaining Important0, Minor0. One Important defect was reproduced and fixed during review. This is an independent review of root-authored foreground/token/consumer changes; it does not certify the older mapper code authored by this reviewer or any native character/source acceptance.

Reviewed snapshot:
- `tools/characters/build_contract.py` SHA `733f8a921a392b379078d5ec94215e96af0eb90c5607b3e5dc63a48a76e40794`
- `tools/characters/composition_contract.py` SHA `20987dc1ca89ff2e8e26ad1ea57a8270e514d392dad63836ca317d58cdc6c2a0`
- `godot2d/dev/characters/character_construction_samples.gd` SHA `89a862e79b320583e45387d61bac21dc7ec393e686117e7cd412fb74261af40e`

## Important I1 — conflicting same-pose head authority (fixed)

Before the fix, canonical_foreground trusted only the foreground binding's separately selected annotation head mask. A second annotation could name the same frozen canonical pose/frame/geometry but remove an actual selected-head pixel from its own head mask, then label it as hand/tool foreground. The actual hair/hat mappings and their existing visible-head surface stayed unchanged. Including one genuine hand pixel supplied the required real head-material overlap, so the forged mask passed strict validate53dependencies.

Independent reproduction is retained in `/private/tmp/coastal-canonical-foreground-independent-probe.py`. The probe preserves actual mapped-head surfaces, then gives foreground an alternate same-canonical-pose sidecar. Actual head surface at face pixel(0,1)=255; forged foreground-sidecar head surface=0. Initial result was accepted. This was an existing registered-authority contradiction, not an attempt to infer anatomy from colors.

Root added a RED→GREEN regression and now checks every selected hair/hat mapping.target_pose equals foreground.target_pose, including far_hat. Native foreground_targets_valid independently resolves each actual selected mapping from bound adaptations and enforces the same selector. Re-running the unchanged attack after this fix rejects with `Canonical foreground annotation differs from actual head mapping`; the JSON result is `/private/tmp/coastal-canonical-foreground-independent-probe-result.json`. The valid baseline fixture still validates before the attack.

## Verified behavior and limits

The owner mask partitions the one already validated schema3 base into disjoint complete RGBA fragments; there is no second body PNG. Source fragment alpha is retained once. An independent direct witness used baseRGBA[220,120,80,253] over real far/hair/near alpha, giving[219,120,81,255], exactly the expected one-base alpha stack. Duplicating the base would instead give[220,120,80,255]. An owner pixel without head support retained[90,50,20,173] exactly. This also confirms that natural final alpha255 over a hat does not mean the pre-compose mother fragment was duplicated or altered.

Independent padding witness[2,1,1,3] retained the complete unpadded result byte-for-byte at the one shifted position; transparent margins had no support. Code inspection confirms head textures, base and the owner use the same whole-frame offset, and canonical root/geometry remain unchanged until output-envelope derivation.

Foreground is bound by the strict annotation loader to the selected canonical action/direction/variant/pose/reference-frame SHA and geometry. It must be a nonempty binary L mask, inside actual canonical alpha support, disjoint from the shared actual visible-head surface and all validated clothing coverage (or actual alpha for uncovered alpha-over layers). It also needs a real hair/near-hat intersection; foreground appears once at the final permitted depth. Caller-supplied foreground textures, wrong order, wrong mask binding and wrong pose are rejected by the inspected contracts.

The source label hands-tools remains an authored, source-reviewed semantic surface. Binding and pixel reconstruction do not independently recognize anatomy, prove every contact depth in48actual frames, or confer user/native approval. Source mask/annotation changes invalidate their bound inputs and require normal visual review. No new clipping or player behavior is introduced here.

Canonical uppercase pose support is confined to schema3 frame.pose_id, permits only safe ASCII letters/digits/underscore/hyphen, and is immediately compared case-sensitively with the frozen actual variant frame. Other identifiers and schema1/2 paths retain the original lowercase identifier validator. Actual12newfarm source/mapping validation passes, including real water/harvest `_B_` canonical names. No canonical pose file was renamed.

For frames without base_foreground, composition follows the previous branch and selection semantics; legacy schema2 does not admit the new field. Root's27current-build PNG/RGBA equality preview and new regression runs were reviewed as supplied evidence, not re-run or represented as this reviewer's independent full/native test. This reviewer ran the concrete counterexample and focused alpha/padding witness only; no production files were modified.
