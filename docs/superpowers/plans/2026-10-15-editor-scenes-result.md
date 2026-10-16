# 编辑器场景迁移收尾结果

> 2026-10-15 GUI续验：实际编辑器保存发现并修复贴图覆盖丢失、拾取物种类丢失、嵌套玩家丢失三个缺陷。代表性Inspector编辑/保存与独立原生重载28/28，保存往返18项、普通属性审计4297项、场景合同132项、采集49项通过。详见`docs/superpowers/plans/2026-10-15-editor-gui-acceptance.md`。未重新导出或提交。

日期：2026-10-15。当前分支 `codex/cottage-pixel-assets`，工作树仍有既有混合未提交修改。

## 结论

按交接顺序完成 I1、I2、M1，并由当前主代理对本轮增量做只读复核。最终审查列出的生产阻塞已关闭，编辑器场景迁移源码收尾完成。本轮没有独立子代理复审、提交、推送、导出或覆盖 v0.5.5 交付。

## 修改与复核

- I1：`tree.tscn` 的公共 Base 随每棵树实例移动；Market、GardenA/B、Crates 和 House 的已有底座归属对应实例。`harbor_exterior.gd` 递归读取实际矩形静态碰撞并转换回室外局部坐标。默认22个旧碰撞的中心、尺寸与数量逐项一致；没有给无底座装饰新增碰撞。房屋实际原点 `(174,165)` 保留，门的位置、门柱及8单位过渡未改。只验证当前轴对齐平移合同，不新增任意旋转/缩放地图系统。
- I2：`harbor_exterior.tscn` 明确保存 `world_bounds`、`foraging_area`；StorageCrates 下的 InteractPoint 驱动仓储提示与E打开。Harbor/HouseSession/WorldCamera读取场景配置；Camera的室外节点引用序列化于主场景。默认矩形、24单位采集距离、28单位仓储距离及业务ID不变。更新 journal_driver 使用真实仓储查询；未再引用被移除的 STORAGE_POINT。世界边界配置用于安全落点及镜头，物理边缘形状仍为场景里可编辑的独立碰撞。
- M1：Journal 的标题状态、个人资料、保存失败说明改用三个导出模板，默认文案保持原样。刷新只填入状态数据；不覆盖Inspector模板。占位符分别为 `{status}`、`{name}/{total}/{discovered}`、`{message}`。
- M2：HANDOFF、PROJECT_STATE、README、progress 和 final-review 已统一当前结论，历史报告保留并明确标为被替代状态。

生产修改：`godot2d/scenes/harbor.tscn`、`scenes/world/harbor_exterior.tscn`、`scenes/world/tree.tscn`、`scripts/harbor_exterior.gd`、`harbor.gd`、`house_session.gd`、`world_camera.gd`、`scripts/ui/journal.gd`。
测试修改：新增 `test_editor_collision_ownership.gd`、`test_editor_outdoor_sources.gd`、`test_editor_journal_templates.gd`；更新 `test_editor_scene_contracts.gd` 与 `journal_driver.gd` 的实际节点/交互查询。

## 本轮验证

| 检查 | 结果 |
| --- | --- |
| I1 RED → GREEN | 原场景25/35，10个预期失败；修复后headless及原生各35/35；I2后最终headless仍35/35 |
| I2 RED → GREEN | 原场景4/14，10个预期失败；修复后含2个默认配置断言，headless及原生各16/16 |
| M1 RED → GREEN | 0/7 → 7/7，入树前覆盖模板并验证多次刷新 |
| 最终完整编辑器场景合同 | 132/132 |
| 树 / 环境 / 采集 / 显示 / 手账 | 51/51、67/67、49/49、13/13、47/47 |
| 南门定点回归 | failures=0，包含8单位浅跨、关门再淡出、出屋开门及门柱检查 |
| 本轮补丁格式 | git diff --check 通过 |

原生验证通过获准GUI环境运行，Apple M4 / OpenGL Compatibility。I1只实例化室外场景，不创建持久化服务；其余完整场景在入树前注入独立 `/private/tmp/coastal-*` 存档目录，Settings沿用该隔离目录。

| 原生步骤 | 预期 | 实际 | 结果 |
| --- | --- | --- | --- |
| 入树前将树0移至(320,240)，Crates移至(560,245) | 底座与树影随动，新位置阻挡、旧位置清空 | 物理点查询与安全落点检查通过；已查看default/moved两张原生截图，底座与画面对应 | 通过 |
| 移动StorageCrates，移动采集点并改可采区域，缩小/平移边界 | 新处E打开，旧处不提示；采集及镜头采用新配置 | 原生16项通过，已查看moved截图；小边界的镜头中心为(440,310) | 通过 |

这两组是原生自动化场景/输入检查及截图查看，不是编辑器GUI手动拖拽保存测试。

证据：`/private/tmp/coastal-editor-i1/`、`/private/tmp/coastal-editor-i2/`、`/private/tmp/coastal-editor-m1/`，含起点快照、分任务diff与日志；I1有default.png/moved.png，I2有moved.png。M1测试夹具曾因误用discovered类型中断；确认其为Dictionary并改正夹具后得到有效RED，再修改生产代码得到GREEN。I1第一轮修复的几何断言定位到误用门X209作房屋原点，纠正为实际X174后全部通过；未改原场景布局。I2首轮剩余提示断言由新游戏release_input保护导致，显式释放后通过。

## 保留的边界

- `test_world.gd` 的既有 `house_clear_of_header` 为44/45基线例外；本轮未重跑或更改此断言。
- Terrain此前原生对比为81960个像素单色阶差1，max_delta=1、over_one=0；本轮未重做地形，不能宣称零差分。
- 批次1–6冷启动、住宅录像和场景预览沿用先前已验收证据；本轮只补修复直接相关验证，没有重跑所有历史批次。
- headless日志有macOS系统证书读取错误；原生没有该提示。手账目录创建错误来自刻意的保存失败注入，随后失败对话框与取消检查通过；没有将日志称为完全无错误。
- 本轮没有新导出包验收，也未验证Windows/Intel Mac。正式交付仍是原v0.5.5；发布/提交由后续明确任务决定。
