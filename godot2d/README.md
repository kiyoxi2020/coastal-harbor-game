# 潮港旧屋 Godot2D · 当前工程

运行基线v0.4.0，Godot4.7.1。导入project.godot后F5。WASD/方向键移动，E拾取或查看，再按E关闭单页提示；R回路口且保留收获。不使用Esc。

当前树木assets/tree-set-v4，当前地形/水面assets/environment-v2。新增台阶下低潮沙滩，六个固定拾取点，蛤蜊/海螺/海带各二；右上方显示背包。人物、建筑与树木风格沿用原版，碰撞围绕可通行沙滩更新。

最新交付在项目交付与预览/2D/，历史在archive，不进Git。有效检查：test_interaction.gd 36项、test_world.gd 44项、test_tree_set.gd 51项、test_environment.gd 67项、test_foraging.gd 49项，共247项。首次导入后可用Godot --headless --log-file /private/tmp/coastal-test.log --path . --script tests/相应脚本运行。

当前仅赶海与轻量背包，无种植、交易、睡觉、潮汐计时或存档；退出重开会重置收获。固定640×416、nearest整数缩放。Mac未Apple公证、未验证Windows/Intel。原有素材由生图后整理，新拾取物和沙滩以像素图形绘制；原图和提示词在../art/godot2d/。字体和Godot许可在assets及licenses。
