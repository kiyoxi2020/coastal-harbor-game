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
