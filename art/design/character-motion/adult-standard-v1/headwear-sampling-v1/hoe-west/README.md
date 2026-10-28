# Hoe-west headwear sample

Four same-pose hoe motion keys (180, 220, 140, 260 ms) plus matching idle, each bare/hair/hat/hair_hat. Candidate for native and user visual review; no user acceptance recorded.

The active west-facing hair is `sources/hair-only-motion-v3.png` for keys 0 and 2, plus single-pose `sources/hair-only-key-1-v4.png` and `sources/hair-only-key-3-v4.png`. The two v3 atlas views for keys 1 and 3 faced east and were rejected. The earlier v2 had an excessively low fringe at measured ear registration. The active hat is the independent transparent `sources/hat-only-motion-v2.png`; the old hat source exposed original scalp and contained generated skin. All original GPT sources, prompts, and failed candidates are retained. A clipped single-pose draft is in `failed-drafts/` and excluded from active inputs.

The source sheets are uniformly nearest normalized to the recorded atlas or single-pose density before reviewed integer head-anchor translation. `registration.json` records each source crop, target ear/head anchor, translation and silhouette-tracing source-space semantic polygons. The key 1 source has an explicit small generated-skin exclusion polygon. Source alpha and hair palette assist only inside the semantic regions; generated face, ear, brow, skin and neck pixels are excluded. There is no part-local scaling, mirrored projection, or change to the original body, hands or tool.

The native motion canvas is 1536×1792, root (768,1544), display scale 0.11855670103092783. Per-pose target-frame coverage records registered painted alpha; a separate cap-volume mask tucks only the hair layer under the painted hat profile. Complete active GPT parts remain in `sources/` and extracted `parts/`. Four motions and idle preserve their own exact parent bare texture bytes and timing.

`build_sample.py` checks parent and bare hashes, lists all local and external dependencies, and writes `sample.json` plus 15 exact-RGBA non-edit and reconstruction checks in `validation.json`. `review.png` is the overview; `large-head-review.png` is an enlarged all-state motion inspection. Native playback and user aesthetic acceptance remain for the main agent and user.
