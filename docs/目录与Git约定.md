# 目录与 Git 约定

根目录只维护当前 Godot 2D 项目。工程在 `godot2d/`；`art/` 保留必要源图、提示词与处理脚本，运行资源在工程 `assets/`。不要删除资产名中的 v2/v4：这些是当前引用的素材标识。

Git 跟踪当前源码、资源、测试和必要文档；历史版本依靠正常提交追溯。未经授权不自动提交或推送；未提交及忽略文件不能依靠 Git 恢复。

不保留 archive、Unity/3D 工程、历史发布包、重复处理结果和逐批实施记录。构建输出写入忽略的 `builds/`；测试输出与存档写入 `/private/tmp/coastal-*`，Godot 命令显式传 `--log-file /private/tmp/<name>.log`。`.godot/` 为可再生成的本地缓存。

2026-10-16 清理保留全部既有 Godot 源码改动、美术原图、锚点/碰撞元数据和有效测试。最近验收结论在 `superpowers/plans/2026-10-15-editor-scenes-result.md` 与 `2026-10-15-editor-gui-acceptance.md`，两者记载的旧临时证据路径不保证仍存在。
