# Run-east headwear sample

Four 80ms motion poses plus exact matching idle, each bare/hair/hat/hair_hat. Candidate for native and user visual review; no user acceptance recorded.

New motion hair uses built-in GPT imagegen hair-only transparent source `sources/hair-only-motion-v2.png`; no face/ear/neck/clothes in that source. The independently generated `sources/hat-only-motion-v2.png` covers the original scalp in all four motion poses. Original exact-pose bare bytes are retained. Static idle uses same-density original cardinal GPT hair/hat view with explicit zero translation; no standing face is copied.

The tool returned 1254×1254 for the requested 1024×1024 atlas. The entire source atlas is uniformly nearest normalized to target atlas density, then individual head views receive only measured integer head-anchor translation. Native frame is 512×768, root (256,708), display scale 0.2371134021 (121.402×182.103 screen px). No part-local scale or body change.

`registration.json` records reviewed, silhouette-tracing source-space polygons, exact cutout and target ear anchors, source-to-full-frame offsets, and rejected v1 sources. Source alpha and the hair palette assist only inside the explicit semantic region. Each full GPT part is retained in `sources/` and its active extracted part in `parts/`. Per-pose target-frame coverage is the registered visible alpha; the separate cap-volume mask tucks only the upper hair layer under the painted hat profile. It never erases the original body. All hands lie below headwear; no tool in run. Four motions and idle use their own original same-pose base.

`build_sample.py` deterministically extracts and composes source pixels, checks external parent and bare hashes, and lists all local and external inputs. `validation.json` binds sample SHA and all 15 changed-state exact-RGBA preservation/reconstruction checks. `review.png` is an overview, `large-head-review.png` is enlarged inspection of all motion states. Failed anatomy-contaminated extraction snapshots are retained under `failed-drafts/extraction-v3` and excluded from active dependencies. Prompts and every original GPT source are retained.

No original body, wardrobe or shared catalog files modified. Native playback and user aesthetic approval remain to the main agent/user.
