# 编辑器 GUI 保存验收

日期：2026-10-15；Godot 4.7.1，Apple M4 / OpenGL Compatibility。

## 结论

已完成代表性场景的实际编辑器修改、保存、独立进程重载与原生渲染验收。此前源码运行合同没有覆盖编辑器保存往返，本轮因此发现并修复三个缺陷；先前“源码收尾完成”不能代替本次验收。当前这三个缺陷均已关闭。

## 修复

- `godot2d/scenes/world/harbor_exterior.tscn`：为11个具有子节点外观覆盖的道具/树实例声明 editable children。此前编辑器保存会丢弃 Sprite2D 贴图和变换覆盖；有效 RED 为11项失败，修复后通过。
- `godot2d/scripts/forage_pickup.gd`：kind 改为导出枚举，并添加 @tool 与重绘 setter，使种类可保存并在编辑器预览。此前保存会让4个 snail/kelp 恢复默认 clam；有效 RED 为4项失败，修复后通过。
- `godot2d/scenes/harbor.tscn`：声明 HarborExterior 可编辑子节点，保留主场景追加的 Returnee。此前打包保存会丢弃玩家；有效 RED 后修复通过。
- 新增 `godot2d/tests/test_editor_save_roundtrip.gd`，覆盖上述保存往返回归。源码正式树位置与 HUD 文案未改，GUI 测试改动仅位于临时副本。

## 实际 GUI 验收

临时工程：`/private/tmp/coastal-editor-gui-acceptance/godot2d`；Save/Settings 在入树前隔离至 `/private/tmp/coastal-editor-gui-acceptance/runtime-save`，不使用玩家真实存档。

| 步骤 | 预期 | 实际 | 结果 |
| --- | --- | --- | --- |
| 编辑器打开室外场景，Inspector 将 CoastalTree0 从(46,128)改为(320,240)，保存 | 位置保存，其他外观和种类保留 | 最终磁盘场景保留新坐标、11个贴图和六个正确种类 | 通过 |
| 编辑器打开 HUD，将 Title.Text 改为 GUI CHECK，保存 | 固定文案重载及运行后保留 | 独立进程加载并启动新游戏后仍显示 GUI CHECK | 通过 |
| 编辑器打开并保存 harbor.tscn | 嵌套玩家保留 | 保存后的主场景包含 Returnee，原生运行显示人物 | 通过 |
| 独立原生进程加载上述文件，检查树位置、底座、阴影与物理查询 | 新处阻挡、旧处清空，底座和阴影随树 | 28/28，已查看 saved-runtime.png，三类拾取物、道具及测试文案正确 | 通过 |

本次操作是 Inspector 数值/文本编辑，不是鼠标拖拽测试；GUI 只手动覆盖上述代表性场景，没有逐个手动编辑所有子场景。

## 自动验证及证据

- 保存往返回归：18项 PASS，failures=0、moved=true、pack=0。
- 场景序列化普通属性审计：4297项、0失败；不包含对象资源的深比较，浮点使用近似相等。贴图另由保存往返合同覆盖。
- 完整场景合同132/132；采集回归49/49；碰撞归属35/35；git diff --check通过。
- 有效 RED/GREEN 与审计：`/private/tmp/coastal-editor-roundtrip/`；最终日志 `entry-green.log`、`audit-final.log`、`contracts-final.log`、`foraging-final.log`。
- GUI 保存文件、差异和原生证据：`/private/tmp/coastal-editor-gui-acceptance/`；最终运行 `runtime-final.log`、`saved-runtime.png`。早期同目录截图/日志可能记录修复前问题，以最终文件为准。临时证据不属于永久发布包。

## 保留边界

历史 test_world 的 house_clear_of_header 44/45，以及 Terrain 的81960个像素单色阶差1（max_delta=1、over_one=0）未在本轮消除或重验。headless仍有macOS系统证书读取提示。本轮没有重新导出、覆盖v0.5.5、提交或推送，也没有Windows/Intel验证。没有自动开始下一阶段。
