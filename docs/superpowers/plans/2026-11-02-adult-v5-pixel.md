# Adult v5 pixel style conversion

Goal: convert all nine adult-v4 final atlases using the built-in imagegen tool into an independent adult-v5 review candidate. Preserve the male identity, tank and shorts, pose ordering, four directions, tools, original timing and whole-frame registration. Pixel art uses crisp clustered square pixels, a limited warm palette, no gradients or antialiasing.

- [x] Freeze v4 inputs and establish four-direction idle style with imagegen.
- [x] Convert all nine atlas images with the same style reference; inspect all poses and tools.
- [ ] Keep prompts, original generated outputs and mapping; final actual PNGs belong under parts/body/adult-v5/r001. Use only extraction/whole-frame registration scripts, no algorithmic substitute for imagegen art.
- [ ] Register complete v5 via the existing template/recipe/build pipeline where geometry and alpha pass; run mandatory Python tests and check, native review, preserve candidacy until user visual acceptance. Do not switch current game or catalog automatically.

Completion requires all 164 source poses accounted for; each converted image reviewed, metadata and hashes saved. If imagegen changes poses or grid, repair the generated source with imagegen rather than arbitrary per-part offsets.
