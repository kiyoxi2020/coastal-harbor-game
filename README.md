# 潮港旧屋

Godot 4.7.1 / GDScript 的 2D 像素沿海生活模拟原型。

打开 [godot2d/project.godot](godot2d/project.godot)，按 F5 运行；入口为 `scenes/harbor.tscn`。
WASD/方向键移动，E 交互，B/Tab 打开手账，R 返回安全点。

## 目录

- `godot2d/`：唯一游戏工程，含场景、脚本、运行素材、许可与回归测试。
- `art/`：2D 美术原图、生成提示与处理脚本；运行资源位于工程 assets 中。
- `tools/`、`tests/`：小屋素材处理工具及 Python 测试。
- `docs/`：当前设计约束与最近验收结论。
- `PROJECT_STATE.md`、`HANDOFF.md`：当前状态与交接；`AGENTS.md`：开发约定。
- `沿海小镇复兴-游戏设计简稿.md`：现有游戏设计简稿。

当前源码包含 v0.5.5 后的编辑器场景迁移，尚未重新导出。已知限制见项目状态。
仅维护当前 2D 源码；旧版本由 Git 提交记录追溯，不在仓库内保留历史副本、Unity/3D 工程、试玩包和验证输出。尚未提交的改动不属于 Git 历史。
