# Godot 2D v1 美术来源

内置图像生成工具，未使用 CLI；实际模型版本未由工具返回。A 风格图是样式参考，不作为地图背景。环境和人物 PNG 保留生成文件，不做离线抠图或重画。Godot 使用 AtlasTexture 按元数据取区域，并以 nearest 过滤缩放；地面、水纹、岸墙和码头由可重复的引擎绘制模块构成。

环境首版因物件间距不足未采用；二版已分离。人物帧尺寸实际为 1254 × 1254，不等于提示词指定尺寸，运行时根据实际尺寸划分 4 × 4。

## 环境首次生成

```text
Use case: stylized-concept. Asset type: transparent environment sprite atlas for a Godot 2D top-down pixel game. Image 1 is approved art-direction reference ONLY. Retain its clear sea-salt palette, original repaired house, teal boards, coral tiles, patched indigo canvas and restrained detailed pixel treatment.
Create one 1536x1024 TRANSPARENT PNG sprite sheet in exactly THREE equal columns by TWO equal rows; each cell is 512x512, each containing ONE complete isolated prop with 35px empty margin from its cell borders. No visible grid, no text, no labels, no ground/background or ground shadows, no checkerboard drawn into image; actual transparent alpha outside objects. Objects do not overlap cells.
Top left: complete cream plaster cottage with coral tiled roof and short chimney, front south-facing facade, green shutters, small asymmetrical teal-plank side porch, bench and hanging rain chain. All parts fit in this one cell. Top middle: complete seafood stall with indigo patched sail canopy on four wooden poles, cream stitched repair patch, fish-shaped sign and neat fish trays, teal wood counter and a small weighing scale. Top right: ONE windswept green coastal tree, asymmetric layered foliage with visible brown trunk extending to bottom.
Bottom left: small teal fishing boat with cream cabin, coral roof, ochre gunwale and black tire fenders, port-side/three-quarter top-down view matching reference boat, NO water. Bottom middle: one rectangular raised wooden vegetable bed of leafy lettuces and a few tomatoes, clearly square aligned edges, NO surrounding grass. Bottom right: small compact grouping of two wooden fish crates with a cream enamel pail and coiled rope.
Camera for ALL: classic orthogonal top-down RPG oblique view, front facades visible, horizontal and vertical alignment, NOT isometric diamond perspective. Original game art, no copied assets. Crisp square pixel clusters and hard edges, about 96x96 logical pixels per large object enlarged in cell, consistent light from upper left, 3-4 discrete shades per material, no gradients or painterly blur. Reduce tiny texture noise compared with reference but KEEP personality and dimensional color clusters. No people. Genuine transparency required.
```

## 环境排布修正

```text
Edit target image1: the six-object game sprite atlas. Preserve the exact art style, object identities and colors. FIX ONLY sprite sheet packing: arrange the six objects into THREE equal-width columns and TWO equal-height rows with substantial genuinely transparent gutters so every object can be cropped as a clean rectangle without any neighboring object. Currently house and stall are too large and overlap the intended cells. Make ALL objects smaller as necessary. Top row house, stall, tree; bottom row boat, vegetable bed, crates/pail. Every complete object stays within its own cell with at least 40 pixels transparent gap to each border. The house including all roof, porch, vines and rain chain must fit in top left cell; whole stall including fish sign must fit top middle; tree only top right. No object touches another. Output a landscape 3:2 transparent PNG, actual alpha zero in gaps, NO color background, NO halos/shadow backdrop, NO printed checkerboard. No labels, lines or captions. Do not add objects. Pixel artwork must remain crisp and original.
```

## 人物帧动画

```text
Use case: stylized-concept. Asset type: 4 direction walking sprite animation atlas with genuine transparent background for Godot 2D farming-life game.
Image 1: approved reference for character identity and pixel art style. Retain the young adult with short dark brown hair, coral-orange open work jacket and cream shirt, teal long trousers and yellow ankle boots. Not a large-head baby, not B-style chibi: readable young-adult 3.5 head proportions. Original character.
Output ONE SQUARE 1024x1024 PNG with actual transparent alpha, exactly FOUR equal columns and FOUR equal rows, 16 frames total, each frame cell 256x256. No lines or drawn grids, no labels or text, no ground shadows or scenery.
Each identical-scale figure is centered horizontally at cell center, feet resting at same local y=224 and top at local y=32 (about 192 source pixels tall). Pixel grid simulates 24x32 logical sprite enlarged: chunky crisp square pixel clusters, about 6 source pixels per logical pixel. Each figure has transparent padding on all sides. Never cross cell boundaries.
ROW 1 (top): four frames looking SOUTH, face toward viewer. Frame1 standing neutral arms by sides and feet together; frame2 left foot steps forward and opposite arm swings; frame3 standing passing pose; frame4 right foot forward and opposite arm swings.
ROW 2: same four phases facing WEST, full left profile with nose pointing left.
ROW 3: same four phases facing EAST, full right profile with nose pointing right.
ROW 4 (bottom): same four phases facing NORTH, BACK OF HEAD AND JACKET visible, no face.
All frames keep exact clothing, body size and top-down RPG camera. Color clusters, no blur, no smooth gradients, no painterly stroke, no antialiasing, no checkerboard printed in background. Real transparency. Large blank gutters separating cells. This is production sprite artwork, not a character showcase or illustration.
```

