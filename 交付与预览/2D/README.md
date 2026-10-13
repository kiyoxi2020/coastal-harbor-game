# 潮港旧屋 v0.5.3 · 室内床与门扇像素试玩

这是最新的 Mac 试玩版及其对应源码。打开「潮港旧屋 · 低潮赶海.app」，选择新游戏或继续进度。本次只更新了室内床与门扇的像素美术；厨房、桌椅、书架、箱子等仍沿用原画面，整间屋子的美术翻新尚未完成。

从旧屋门前按 E 进入；在室内走近床按 E 查看，在下方门前按 E 离开。室内外箱子共享 48 格仓储。在屋内保存并重新启动后可回到屋内。WASD 或方向键移动，B / Tab 打开手账，R 回当前场景安全入口。

源码包 `CoastalHarbor2D-v0.5.3-source.zip` 包含 Godot 工程、室内原图与处理图、生成工具及其测试。运行工程需要 Godot 4.7.1。`04-interior.png` 是本版导出应用的实际画面；核验结果见 `verification-summary.json`、`package-verification.json` 和各测试 JSON。

Mac 存档目录通常为 `~/Library/Application Support/Godot/app_userdata/潮港旧屋 · 低潮赶海/coastal-progress/`。本轮自验全部使用 `/private/tmp` 下的专用目录，没有写入玩家存档。Mac Apple M4 已验证，应用未 Apple 公证；Windows 与 Intel Mac 未验证。种植、交易、睡觉、潮汐计时与每日刷新尚未实现。

上一版完整保存在项目根目录 `archive/2026-10-13-before-v0.5.3/2D/`。
