# 全镇示意图与区域详情 Implementation Plan

> 最新任务：用户已要求移除右侧，以下原C方案执行清单为历史；单栏修订见文末。

> **For agentic workers:** REQUIRED SUB-SKILL: Use subagent-driven-development to implement this plan task-by-task. 用户已指定子代理执行，无需再次选择执行方式。

**Goal:** 以连续海湾示意图和独立实景详情替换旧版拼贴总览。

**Architecture:** region_catalog保存区域元数据；world_map负责选择、焦点和实景详情；独立world_map_overview场景只负责总览静态美术。静态UI在tscn，状态与投影在gd；保留隔离SubViewport快照。

**Tech Stack:** Godot 4.7.1 / GDScript / 场景与现有像素素材。

## Global Constraints

- 规格以docs/superpowers/specs/2026-10-20-world-map-art-design.md顶部C方案为准。
- 不改变SAVE_VERSION=5、区域旅行、经济、建筑尺度、真实世界布局。
- 测试存档仅/private/tmp/coastal-*，Godot统一--log-file /private/tmp/<name>.log。
- 不提交、推送或导出。最多两个子代理同时工作，不嵌套委派；不得同时修改同一文件。
- UI逻辑1280×720，overview局部640×520，详情640×416实景统一0.6倍。

## Task 1：地图状态、双栏与交互

负责文件：scripts/ui/world_map.gd、scenes/ui/world_map.tscn、scripts/region_catalog.gd（均在godot2d/），相关test_region_map.gd、test_world_map_projection.gd、test_region_map_native.gd及新增test_world_map_c.gd。

接口：world_map保留open()/close()/render()/snapshot_scene(source)，新增selected_region:String、selected_point:String、select_region(id:String)、select_point(id:String)。scene_views仅包含当前详情区域，markers仅当前区域；未来区均为空。详情节点Root/Panel/Detail/Preview；开关保留Root/Panel/Resources，关闭保留Root/Panel/Close。总览Root/Panel/Overview为640×520；实例化独立world_map_overview.tscn为其美术子节点，交互标记由world_map创建。美术场景不处理输入。

- [x] 新增测试，先断言新行为并运行得到预期失败；不把旧“两份同时显示”断言当新规格。
- [x] 实现区域登记、双栏、按需单个快照、区域/地点选择与输入隔离。
- [x] 测试如下行为：打开默认harbor；select_region("harbor_district")只显示街区且相同0.6比例；select_region("hillside")无scene_views和markers；select_point后Esc仅清除地点，再Esc关闭；资源筛选与采集状态同步；house默认harbor。
- [x] 更新旧测试中的UI合同，保持原旅行/存档断言。执行test_world_map_c、test_world_map_projection、test_region_map。

命令模板：
```sh
/Applications/Godot.app/Contents/MacOS/Godot --headless --path godot2d --log-file /private/tmp/coastal-map-c-test.log --script res://tests/test_world_map_c.gd
```

## Task 2：连续总览美术（与Task 1并行，文件独立）

负责文件：godot2d/scenes/ui/world_map_overview.tscn，必要的新godot2d/assets/ui/world-map-c/资源，art/design/world-map-c/美术来源说明。不得修改Task 1文件。

接口：根Control为640×520，所有子节点mouse_filter=IGNORE，nearest过滤；仅地形、道路、建筑地标和装饰，无运行脚本、文字、动态状态或实景方框。地区中心使用规格坐标。父UI负责区域按钮、文本和选中态。

- [x] 检查现有海岸底图和建筑资源，优先复用同源地标；确定连续海湾、地标分离的构图。
- [x] 制作独立场景，地形降低对比度，旧屋下方、餐馆中上、北住宅/西北山林/东岬角明确。
- [x] 原生渲染独立场景，检查640×520构图、地标与道路连接，归档来源和截图。美术不机械编写逻辑测试。

## Task 3：主代理集成与验收

负责文件：新增godot2d/tests/test_world_map_c_native.gd、本计划、规格结果、HANDOFF.md、PROJECT_STATE.md、art/design/world-map-c/验收证据。

- [x] 构建独立临时档原生夹具，键鼠覆盖所有区域、屋内、地点/返回、焦点正反循环、开关与暂停隔离；捕获三种区域和地点状态。
- [x] 集成后运行原生夹具与原地图旅行夹具，查看截图而非只检查进程退出。
- [x] 子代理独立检查规格符合度和代码质量；修复重要问题后重跑受影响验证。
- [x] 运行相关地图、投影、显示、场景合同与菜单回归，记录实际通过数量和未验证边界。
- [x] git diff --check，更新交接，不提交。

## 分工与进度

- 实现：gpt-6.1-sol high，承担UI状态、焦点、快照与回归，涉及多文件集成。
- 美术：gpt-6.1-sol medium，承担独立总览美术，不与实现代理重叠。
- 主代理：设计、计划、原生验收、集成与交接。
- 独立复查在实现完成后复用空闲代理；记录真实结果，不推算用量节省。

## 完成记录

2026-10-20完成。主代理先落盘方案/计划并建立原生失败入口，再并行执行Task1/Task2。最终独立代码复查采用gpt-6-astra high（新增复查代理，与实现职责隔离）；复现并修复echo绕过焦点导航、屋内定位针拦截旧屋点击。固定UI仍在tscn，美术资源不覆盖旧图，未修改真实世界/存档合同。

回归C61＋投影25＋区域28＋显示18＋菜单20＋场景合同132＝284项通过；原生55与跨区/存档29通过。画面已查看并归档art/design/world-map-c，包含步骤/预期/实际/结果。所有测试使用隔离存档。

无代码阻塞；最终用户美术验收、真人长时、Windows/Intel、新导出未执行。设计与代码未提交/推送/导出，P09未启动。后续新增可玩区域须同时登记区域元数据、场景来源映射和美术地标。


## 单栏修订任务（2026-10-20）

- [x] 先用失败检查复现右侧Detail/Resources/Divider/SubViewport仍存在。
- [x] 删除右侧静态节点、快照/地点逻辑及相关主题样式；居中保留640×520总览。
- [x] Tab焦点收敛为总览/关闭，Esc/B直接关闭，保留重复键门禁。
- [x] 更新地图逻辑/布局及原生测试，保留区域旅行/存档断言；检查实际渲染。
- [x] 归档单栏截图、同步状态和最终验证结果。

单栏最终结果：地图25/布局16/区域28/显示18，共87项；原生键鼠44/跨区29均通过。实际截图已检查，见art/design/world-map-single。

本修订由主代理直接执行，修改范围集中于地图UI与受影响测试；未重做总览美术，未提交/推送/导出。


## 提交交接（2026-10-20）

用户授权提交累计地图工作与进度记录，最终版本为单栏总览。基线866cbeb，实际哈希以Git记录为准。本次没有源码变化，沿用最终回归87项/原生44＋29证据。未推送/导出；P09待开发。
