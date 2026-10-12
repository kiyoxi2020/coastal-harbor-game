# 潮港旧屋 Godot2D · 当前工程

运行基线v0.3.1，Godot4.7.1。导入project.godot后F5。WASD/方向键移动，E查看，再按E关闭单页提示；R回路口。不使用Esc。

当前树木assets/tree-set-v4，当前地形/水面assets/environment-v2。人物、建筑、地点、碰撞保持最新。当前生产脚本已与v0.3.1发布源码逐字节核对，未回退。

最新交付在项目交付与预览/2D/，历史在archive，不进Git。旧树素材和旧单树测试已归档，环境测试已改为当前树素材。有效检查：test_interaction.gd 36项、test_world.gd 44项、test_tree_set.gd 47项、test_environment.gd 66项。首次导入后可用Godot --headless --path . --script tests/相应脚本运行。

仅漫步原型，无种植、交易、背包或存档。固定640×416、nearest整数缩放。独立包M4实测，未Apple公证、未验证Windows/Intel。素材由生图后整理，并非逐像素手绘；原图和提示词在../art/godot2d/。字体和Godot许可在assets及licenses。
