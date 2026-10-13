# 背包界面视觉提案：海岸帆布与潮汐手账

状态：概念预览，待确认；尚未修改游戏代码或试玩包。使用内置 image_gen 生成，参考当前 v0.5.0 背包实机截图。

## 改动方向

- 删除右上固定海产计数条，以可点击的背包图标和B键提示替代；点击直接打开背包页，B/Tab快捷键不变。
- 青绿帆布外框、浅米白内页、克制皮扣与缝线，布质分页和带内凹层次的24格收纳槽。
- 物品详情独立纸签，选中态采用珊瑚色角标与边框，按钮区分主次。
- 不改动容量、存档格式、物品操作、世界地图或桌面窗口大小。

## 接入约束

图中为生图视觉参考，不是已实现界面或可直接使用的完整界面贴图。需将框、分页、槽位与背包图标拆成可缩放素材；纹理降低频率以适应游戏内部1280×720。全部中文、数量、说明、焦点和按钮由Godot动态绘制。保持六列四行，保留键盘与鼠标操作，生成图内不必要装饰文案不直接带入游戏。确认后再实施并重打试玩包。

项目原图：art/godot2d/ui-journal-concept/canvas-journal.png。

## 完整生成提示词

```text
Use case: ui-mockup. Create a production-feasible pixel-art inventory UI redesign for the Chinese cozy modern coastal village game 潮港旧屋. Reference image is the current actual game UI and provides ONLY functional layout, screen aspect ratio, in-game background style and colors. Make a materially more art-directed UI, not a simple recolor of flat boxes.
Output one polished 16:9 front-facing game screenshot mockup. Pixel-art, clean integer-like pixel clusters, crisp stepped contours, limited restrained palette, no blur or realistic cloth photos. Art direction: modern coastal canvas satchel plus tide journal, seafoam/teal canvas outer frame, warm ivory inset pages, subtle stitched edges, tiny restrained brown leather tabs, modest salt-worn texture only near edges. Not medieval fantasy, no gold filigree, no giant ropes, no clutter, no shells scattered over buttons. Visually warm and personal but realistic for a small Godot 2D team using nine-patch frames and sprite icons.
Changes requested:
1. REMOVE the persistent top-right inventory counts line altogether. Show a single clearly legible small canvas backpack pixel icon in a compact framed HUD button at upper right, with a tiny B keycap. Do not display clam/snail/kelp quantities in HUD. Keep it visible above the centered inventory panel.
2. Centered inventory window takes about 85% screen width and 78% height over a subdued coastal game background. Top title reads 海边生活手账; three attractive physical fabric bookmark tabs read 背包 个人 设置, selected 背包. Close button at upper right of panel reads 返回.
3. Left content has five compact category chips 全部 海产 食材 材料 工具. Below EXACTLY 6 columns and 4 rows =24 equal usable item slots, padded orderly layout, stitched recessed light canvas pockets with restrained top highlights and 2-tone depth. Three occupied slots: original small pixel clam, snail, kelp icons, each quantity 2, all other slots empty. Selected clam slot has a warm coral corner marker and distinct border. No decorative props blocking any slots. Need plenty of empty slots, not a fully filled loot screen.
4. Right detail panel a subtly layered paper inventory tag, larger clam icon, heading 蛤蜊 ×2, small category 海产, readable short description 赶海拾得的蛤蜊。 then 当前不可直接使用。 Three real separated buttons 移动 / 合并, 拆分, 丢弃…; don't add actions or currencies or equipment slots. A distinct 整理全部 button at bottom.
5. Bottom left reads 24 格 · 每格最多 99 个. Footer reads E 确认 · B / Tab 返回. Clear readable Chinese type, not decorative handwriting. In actual implementation text remains live rendered; this image is an art-direction preview only.
Strong hierarchy and consistent margins, surface detail concentrated on framing, quiet readable inner spaces, pixel icons with identifiable silhouettes. Keep game background broadly consistent with reference, no new gameplay scenery, no alternate concepts collage, no promotional labels or watermark.
```

