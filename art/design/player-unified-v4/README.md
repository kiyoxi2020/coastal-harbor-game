# 统一人物逐帧动画 v4

2026-10-19，按用户要求使用内置 GPT imagegen 重新生成整套角色，并已接入游戏。

- 红外套、蓝裤、黄靴角色；walk/run/hoe/water/harvest五组，south/west/east/north四方向，每向六帧，共120帧。
- `*-original.png`：五张GPT原始透明图。走路为母版，其余四组均参考同一母版。`*-prompt.md`保留完整提示词；`sources.json`使用工作区内相对路径。
- `godot2d/assets/player-unified-v4/`：120张384×384统一画布的透明帧与metadata.json。按alpha连通轮廓切图，保留完整工具/水滴；仅做确定性切图、每组六帧一致的nearest尺寸校准和根点注册，不重画角色，不逐帧任意缩放。
- 统一锚点(192,336)，世界缩放0.15；走/跑保留原图步态起伏，工具动作固定脚底。`build_sprites.py`可从五张原图重建帧和SpriteFrames，需Pillow；原始图不覆盖。
- `godot2d/resources/player_unified_frames.tres`：20组动画，走路9fps、跑步12fps循环，工具9fps非循环。保留原north/south/west/east行走命名以兼容门过渡。
- 游戏只用一个AnimatedSprite2D和原门遮挡材质，单姿势Pose节点、形变与交叉淡化均已停用。Shift跑步；工具播放完毕由animation_finished回到待机。
- `native-preview.gif`：120张实际原生引擎渲染帧依次展示，9fps审核预览；不是动作概念图，也不代表每组动画在游戏中的真实速度（跑步为12fps）。顺序为每方向下walk/run/hoe/water/harvest，再进入下一个方向。

验证详情见docs/design/p01-p14/P05-feedback.md。未导出或验证Windows/Intel。
