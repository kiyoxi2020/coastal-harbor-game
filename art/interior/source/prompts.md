# Cottage pixel pilot source record

Tool: Codex built-in `image_gen` (`image_gen__imagegen`). The approved image at `art/interior/concepts/approved-cottage-pixel.png` was viewed first and used only as a style reference for the bed and closed door. The closed door candidate was the identity reference for both open poses. The four PNGs here are unaltered copies of built-in outputs; no pixel processing or cutout was applied. All have an RGBA alpha channel, but alpha presence alone is not a quality pass.

The 48×80 bed and 30×44 door sizes below are intended *logical integration targets*, not native generation dimensions. `bbox128` is the bounding box of pixels with alpha ≥128, in `(left, top, right, bottom)` source-image coordinates.

## Bed

- Selected source: `/Users/wyq/.codex/generated_images/01a13567-3afd-7ab2-89ca-ef017728b6cb/exec-d4fced54-3d27-45cc-b8b8-2a715a59b62c.png` → `bed.png`
- Native size: 1024×1536; `bbox128`: `(181, 196, 843, 1231)`.
- Prompt:

  > Use case: stylized-concept. Asset type: independent transparent pixel-art game sprite. Image 1 is a STYLE REFERENCE only, not an edit target. Original top-down front-facing three-quarter pixel-art sprite, ONE single bed only, isolated on genuine transparent background. Match reference cottage: weathered honey wood, restrained shell motif on headboard, cream pillow and sea-teal patched quilt. No rug, wall, floor, cast shadow outside bed, text or other furniture. Not isometric. Chunked hard pixel edges, limited warm palette, no antialiasing, no painterly gradients. Compact readable silhouette intended for 48 x 80 logical pixels, including headboard and feet. Bed length approximately twice the visible standing character height, not a giant double bed. Keep full silhouette with transparent margin. This is an individual game sprite, not a room illustration.

- Observation: The narrow bed, shell headboard, cream pillow, quilt, and full feet are visually readable. It is **not approved for direct runtime use**: a broad brown semi-transparent glow remains outside the hard silhouette. The alpha≥1 bounding box extends almost to the entire canvas `(0, 19, 1014, 1510)`; the corners are transparent, which is insufficient. The pillow and quilt also have soft gradients inconsistent with a strict pixel sprite.
- Rejected generation: `/Users/wyq/.codex/generated_images/01a13567-3afd-7ab2-89ca-ef017728b6cb/exec-11527e06-3ec8-40f0-bbd0-8cc526199f36.png`. It used the same bed prompt above; it was not selected. Its tool reply was accidentally truncated before visual inspection, so no quality claim is made about it.
- Rejected targeted repair: `/Users/wyq/.codex/generated_images/01a13567-3afd-7ab2-89ca-ef017728b6cb/exec-cff0501c-b8c0-4fac-a29d-bfcf4f981a40.png`, 1024×1536. Prompt:

  > Use case: background-extraction. Asset type: transparent pixel-art game sprite cleanup. Image 1 is the EDIT TARGET. Keep the bed silhouette, wood, shell headboard, cream pillow, teal patchwork quilt, framing, dimensions, and hard pixel details unchanged. Remove ONLY the exterior brown glow, vignette, shadow and all semi-transparent pixels outside the bed's visible hard outline. The outside background must be genuinely 100% transparent with alpha zero, including the full margin. Preserve a crisp pixel edge without antialiasing or feathering. Do not crop, resize, rotate, recolor, invent details, or add any other object. This is a targeted transparency repair of the same single bed.

  The repaired result still has a wide glow; alpha≥1 bbox `(0, 3, 1015, 1536)`. It was not copied over `bed.png`.

## Door, closed

- Selected source: `/Users/wyq/.codex/generated_images/01a13567-3afd-7ab2-89ca-ef017728b6cb/exec-2fda0c7a-defc-4a21-a83f-d8c651df471a.png` → `door-closed.png`
- Native size: 1037×1517; `bbox128`: `(239, 263, 788, 1284)`.
- Prompt:

  > Use case: stylized-concept. Asset type: independent transparent pixel-art game sprite. Image 1 is a STYLE REFERENCE only, not an edit target. Original pixel-art game sprite of ONE upright sea-teal wooden cottage door LEAF ONLY, front-facing, genuine transparent background, no frame, floor, wall, background or text. Match reference style, small four-pane square window and brass handle, worn paint, restrained pixel clusters. Intended visible logical size 30 wide x 44 high, vertical rectangular silhouette, never a floor hatch. Fixed hinge along left edge. No perspective tilt or antialiasing. No external cast shadow. Full uncropped silhouette. This closed leaf is the canonical identity for two subsequent open poses.

- Observation: Distinct upright door leaf, four-pane window, brass handle, and left hinge. No obvious broad visible halo. It still contains very low-alpha pixels outside the visible shape (`alpha≥1` bbox `(0, 36, 999, 1492)`); exact clean alpha and a 30×44 game-ready crop are unverified.

## Door, half open

- Selected source: `/Users/wyq/.codex/generated_images/01a13567-3afd-7ab2-89ca-ef017728b6cb/exec-e1a8cefa-0449-44f5-880b-15c85fc05f1f.png` → `door-half.png`
- Native size: 1037×1517; `bbox128`: `(238, 197, 628, 1325)`.
- Prompt:

  > Use case: stylized-concept. Asset type: independent transparent pixel-art animation sprite. Image 1 is the canonical CLOSED door identity reference, not an edit target. Generate the SAME pixel-art cottage door leaf in HALF OPEN state on genuine transparent background. Preserve sea-teal wood color, four-pane window, right-side brass handle, height and left hinge. Keep the hinge vertical and stationary at the left side of the canvas; swing around it, show appropriate narrow edge and back face, do not horizontally squash the closed drawing. Leaf only, no door frame, wall, floor, text or shadow. Same front-facing farming-RPG camera and hard pixel style. Canvas fits a 30 x 44 logical envelope; transparent area remains where closed leaf used to be, do not recenter the narrow open leaf. Keep all visible pixels within the original envelope. Clear view of a door leaf swung roughly halfway open.

- Observation: Narrower perspective and identity details survive; left visible edge is approximately aligned to the closed pose. Top is 66 native pixels higher and bottom 41 pixels lower than the closed pose, so common height and hinge registration are **not verified**.

## Door, fully open

- Selected source: `/Users/wyq/.codex/generated_images/01a13567-3afd-7ab2-89ca-ef017728b6cb/exec-6c532612-2dac-4ce3-8d0a-5cb432baf3f4.png` → `door-open.png`
- Native size: 1037×1516; `bbox128`: `(236, 196, 424, 1337)`.
- Prompt:

  > Use case: stylized-concept. Asset type: independent transparent pixel-art animation sprite. Image 1 is the canonical CLOSED door identity reference, not an edit target. Generate the SAME pixel-art cottage door leaf in FULLY OPEN state on genuine transparent background. Preserve sea-teal wood color, four-pane window identity, right-side brass handle, height and left hinge. Keep the hinge vertical and stationary at the left side of the canvas; swing around it so the leaf is seen mostly edge-on with a narrow strip of back face, not a horizontally squashed closed drawing. Leaf only, no door frame, wall, floor, text or shadow. Same front-facing farming-RPG camera and hard pixel style. Canvas fits a 30 x 44 logical envelope; transparent area remains where closed leaf used to be, do not recenter the narrow open leaf. Keep all visible pixels within the original envelope. Full height remains equal to the closed door.

- Observation: Narrowest profile and same visible left hinge/handle vocabulary. Its native canvas is one pixel shorter, its top 67 pixels higher and bottom 53 pixels lower than closed. The door poses are therefore **candidates, not a verified aligned animation strip**. Do not independently crop and center each pose; a shared pivot and scale need visual validation before use.

## Selection and remaining work

All four files are separate PNGs with alpha and no shared illustrated room background. The bed is rejected for direct use due to glow. The doors are useful source candidates but need common-envelope alignment and a scale test against the player. The model did not deliver native logical pixel dimensions; direct downscaling may blur detail, so inspect a nearest-neighbor in-game preview before promoting these to runtime art. No runtime assets or scene code were changed in this task.
