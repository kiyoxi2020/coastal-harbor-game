# Worn six-frame sweater extraction audit

## Asset and read-only inspection

Viewed `art/characters/sources/top04-adult-v2-west-worn-r001/originals/worn-six-r001.png` only. It is an RGBA PNG, 1254×1254, with transparent background (corner alpha 0) and opaque figure pixels. The 3×2 row-major cells are 418×627 each: columns x=[0,418), [418,836), [836,1254); rows y=[0,627), [627,1254). No mask was authored and no pixels were changed.

The six cells show complete left-facing walking figures already wearing the red cable-knit sweater. All six retain the gray body/pants, skin, face, hands and black outline, so segmentation must distinguish the top from adjacent body parts; the sheet itself does not encode a clean garment alpha channel.

## Per-cell silhouette and ownership risks

|Cell|Visible sweater shape|Manual ownership decisions still needed|
|---|---|---|
|0, top-left|High rib collar, short torso with ribbed hem, one forward/down sleeve and one sleeve angled back to the right hand.|Trace both shoulder/collar joins against neck skin. Keep the collar/hem and sweater outline; exclude neck, hands and gray lower body. Both wrist/black-cuff transitions need pixel review.|
|1, top-middle|Same collar/torso; arms are closer to a passing pose, with one sleeve reaching the forward left hand and the other ending above the right hand.|Cuff-to-hand boundary on each arm; gray waistband begins directly below the ribbed hem. Sleeve/side seam lines approach the torso contour.|
|2, top-right|One bent forearm swings across the torso; the opposite sleeve falls behind toward the right hand. The crossed legs make the lower body contour busy.|Most ambiguous overlap: the black diagonal from shoulder/underarm through the bent sleeve is garment linework, but the contact with the torso edge must be reviewed pixel by pixel. Keep only visible sweater surfaces; exclude hand, neck and gray pants.|
|3, bottom-left|Forward arm extends left from the torso, the rear sleeve reaches down/right; the torso hem is nearly horizontal.|The curved black underarm/elbow boundary separates sleeve from torso. Decide which shared black edge pixels belong to the sweater. The right cuff, hand outline and waistband touch closely.|
|4, bottom-middle|Compact passing pose; both hands sit near waist height and sleeves converge visually around the torso sides.|High risk of merging a cuff, skin hand and waist hem into one region. Preserve ribbed cuffs/hem, exclude orange hand and gray pants; inspect the near/far sleeve boundary where black strokes meet.|
|5, bottom-right|Return stride; forward sleeve reaches down/left and rear sleeve extends to the right hand, with the same collar and ribbed hem.|The forward sleeve's diagonal seam meets the torso side; the rear cuff is close to the hand and the hem to the gray pants. Review black boundary pixels individually.|

Across all frames, include the knit fabric, ribbed collar/cuffs/hem, and black contour/seam pixels that visibly belong to the sweater. Exclude head/neck, orange skin/hands, gray undersuit/pants, and transparent background. Black pixels can be an outer garment outline, an internal sweater seam, or the boundary of skin/body; color alone cannot assign that ownership. The sheet also has thin colored fringe around some hard outlines, so any fringe must be resolved through the binary mask and visual review rather than painted into the clothing source.

## Extraction path and staging recommendation

Start with **one cell, pose 0**, to author and inspect a binary ownership mask before committing six masks. Verify that every retained RGBA value comes directly from that pose in the original worn atlas, the collar/cuffs/hem look clean at the target scale, and no skin/gray body pixels were included. If pose 0 has acceptable edge assignment and scale, author the remaining five masks with the same rules. A full-table mask pass before proving one cell would multiply the ambiguous black-line and hand-boundary decisions without validating the extraction/registration path.

The existing schema-3 source-view interface supports exact binary extraction of a source frame with:

```json
{
  "extraction": {
    "kind": "binary-rgba-extract-v1",
    "density_normalization": null
  },
  "source_ownership": {
    "role": "source-ownership",
    "mask": {"file": "...binary-L-mask.png", "sha256": "..."}
  }
}
```

The source view also binds `source`, canonical `source_bundle`, `source_pose`, `canvas_px`, and `root_anchor_px`; its ownership mask is binary `L` (0 or 255). This form is appropriate only when the source PNG is already a single full frame matching the registered source-pose canvas. With the current 1254×1254 atlas, the existing atlas route is `registered-source-atlas-v1`: bind the original sheet and bundle, store a binary `source-atlas-ownership` mask in atlas coordinates, and register the owned pose region to the canonical pose anchor. That route uses the declared whole-atlas nearest-neighbor density normalization. Nearest sampling keeps output colors drawn from source pixels, but it can duplicate/drop pixels; it does not provide a one-to-one native-resolution mapping. If strict one-input-pixel-to-one-output-pixel preservation is required, the binary full-frame route needs a source already at the registered frame size, and this larger atlas cannot be passed to it as-is.

Do not use a red-color threshold as formal ownership: it can find candidate sweater areas for human review, but it cannot reliably resolve dark red knit, black outlines, red antialias fringe, collar/neck, wrist/hand, and sweater/pants boundaries. Do not subtract the original body image from the worn image; that would mix pose/color alignment differences into the extracted garment and cannot recover ownership at black/shared contours.

Keep three concepts separate: source ownership says which pixels in this worn source belong to the sweater; target coverage says which registered body surface the sweater replaces; occlusion says which front layers hide it. They need not be the same mask. A zero/one mask is an annotation claim, not visual proof.

## Evidence boundary

This review establishes only that the six poses contain a visually identifiable red sweater and that its seams, wrists and waist can be traced for manual masks. It does not establish completed masks, extracted-pixel integrity, scale/registration fit, six-frame visual acceptance, continuous animation, complete layering, native Godot display or user acceptance.
