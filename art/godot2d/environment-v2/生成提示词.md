# 环境精修 v0.2 生图来源

2026-10-12。使用内置 image_gen 工具，未指定API/CLI后端，工具未返回可核实的模型版本，因此不宣称特定模型名。

参考为已确认提案（不是替换背景）。源图存于项目 art/godot2d/environment-v2/：trees-source.png、materials-source.png、materials-water-refined.png，均为1254×1254。首版水材质出现交叉纹理，最终仅使用修订图的水面象限；草地/石板仍取初版。原稿保留。

运行PNG经Godot离线裁切、nearest降采样、4px平铺边缘配对、透明alpha阈值整理；这些是素材准备，不是逐像素人工精修或整张概念背景。树画布96×96，根锚点(48,94)，实际冠高约68–84px；地形64×64，石板分16×16读取。岸墙/码头/礁影/草簇/动态泡沫仍由代码绘制。

## 树木图集完整提示词

```text
Use case: stylized-concept. Asset type: production 2D pixel game tree sprite atlas. The reference is STYLE ONLY: adopt its sunny sea-salt coastal village palette, top-left lighting and orthogonal overhead RPG view. Generate a NEW square 1024x1024 sprite sheet with TRUE transparent alpha background, NO checkerboard painted in. Exactly four fully separated full trees in a strict 2x2 grid of equal 512x512 cells, each tree entirely inside its cell with at least 40px transparent padding, tree trunk root centered horizontally. NO scenery, grass, ground patches, shadows detached from roots, labels, text or UI. Top left: broad rounded layered camphor-like green broadleaf with warm branching trunk. Top right: upright somewhat narrower irregular coastal broadleaf, different branching and foliage silhouette. Bottom left: windswept Japanese-black-pine-like coastal tree, asymmetrical horizontal needle masses and bent trunk whose ROOT is centered, not tropical palm. Bottom right: smaller rounded yellow-fruit tree with only 7 scattered golden fruit, compact canopy. All four trees have visible roots at cell y=450 and crown starts near y=60. Strong chunky pixel clusters appropriate to eventual 72-80px sprite height, green/teal shadows, olive/lime highlights, warm brown wood. Sharply pixelated not painterly, no antialiasing or blurred brushwork, no black outlines. Each is unique silhouette, no duplicates. These will be cut as individual game sprites, not used as concept backdrop. Preserve alpha.
```

## 地形材质完整提示词

```text
Use case: stylized-concept. Asset type: 2D pixel-game MATERIAL atlas. Reference image is ONLY palette/material language, DO NOT reproduce scene, objects or interface. Create a square 1024x1024 atlas comprising EXACTLY FOUR edge-to-edge flat top-down square material swatches arranged in a strict 2x2 grid with boundaries at x=512 and y=512, no margins, no frames, no text, no labels. TOP LEFT: low-contrast sage green grass ground texture, restrained broad pixel patches and tiny leaf marks, not individual tall blades, not a grassy sphere. TOP RIGHT: turquoise shallow coastal water, subdued broken horizontal water shapes, no white foam, no objects or shore. BOTTOM LEFT: deeper teal blue water, subtle coherent horizontal ripples, no white foam, no objects. BOTTOM RIGHT: cream weathered sandstone paving, a regular 4x4 square stone tile grid across this quadrant, thin muted gray-green mortar, very subtle chips and occasional faint cracks, no grass or objects. Each quadrant has consistent value at all its edges and is intended to tile seamlessly independently; no vignette, no lighting gradient, no edge shadow, no checkerboard bands. Palette grass #8eb876-ish water #319cad / #277e99 cream #d8d8b9, shade variation subtle and harmonious rather than noisy. Crisp large pixel clusters, intended to downsample each 512px quadrant to 64px square pixel texture. NO 3D, photo texture, dramatic highlights, speckles or microtexture. Same sunny clear coastal pixel RPG mood as reference. Opaque atlas.
```

## 水面修订完整提示词

```text
Use case: precise-object-edit. Edit this 2x2 pixel-game material atlas. STRICTLY preserve top-left grass and bottom-right cream stone quadrants, grid boundaries at exact halfway points, square canvas and flat top-down view. Change ONLY TOP RIGHT shallow water and BOTTOM LEFT deep water. Replace their diagonal diamond lattice with MUCH quieter low-contrast pixel water: coherent flat turquoise/teal fields with scattered SHORT HORIZONTAL broken ripple clusters and irregular wide horizontal softly stepped color patches. No connected diagonal lines, no X, no diamond shapes, no fishnet, no bright glitter, no white foam, no shore. About 70 percent visually calm flat base with sparse nonperiodic horizontal accents. Shallow remains light blue-green, deep remains deeper teal blue but not dark. Each water quadrant intended as seamlessly repeating square material with no vignette, no borders, no directional lighting. Keep crunchy small pixel clusters, no blur and no realistic rendering. No new text or objects. These will be downsampled to64px tiles; avoid tiny noise.
```

