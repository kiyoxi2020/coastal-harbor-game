# 潮港旧屋 v0.4.0 · 低潮赶海

本目录仅保留最新2D试玩。解压`CoastalHarbor2D-v0.4.0-macOS.zip`，或直接打开旁边的`潮港旧屋 · 低潮赶海.app`。

## 试玩路线

1. WASD/方向键移动，从路口走到中央偏左的潮汐台阶，继续向下进入沙滩。
2. 靠近物品会高亮并提示E拾取。蛤蜊、海螺、海带各两个，右上背包实时计数。
3. 集齐六个物品后出现完成提示。可返回小镇继续查看旧屋、市集和码头。

E查看地点，再按E关闭；关窗不会同时拾取。长按不会重复领取。R回路口，不清空收获。

这是单轮赶海原型，**尚无存档，退出重开会重置**；无交易、种植、潮汐计时和睡觉系统。集齐后不会自动刷新。

## 验证与限制

从Git跟踪文件建立无缓存副本，五组247项检查通过；独立Mac试玩另做赶海与渲染检查。详见verification-summary.json、export-foraging-tests.json和各专项报告。

截图09-foraging-before.png、10-foraging-complete.png展示拾取前后；11/12-export图片来自最终独立试玩验证。沙滩与物品为本阶段的简洁像素实现，未重新制作树木和建筑。

本机Apple M4验证；未验证Intel、Windows，未Apple公证。若系统阻止打开，请通过系统正常的安全确认流程操作，不要关闭全局安全保护。

源码包`CoastalHarbor2D-v0.4.0-source.zip`内含当前godot2d工程，用Godot4.7.1导入project.godot。旧v0.3.1交付移至项目archive/2026-10-13-before-v0.4.0/2D，不进入Git。
