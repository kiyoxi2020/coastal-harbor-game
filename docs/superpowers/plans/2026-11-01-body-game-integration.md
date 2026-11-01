# Godot身体资源运行接入 Implementation Plan

> **For agentic workers:** Use subagent-driven-development for independent Godot implementation and a final review; main agent owns resources, gate integration and native acceptance. No commits or pushes requested.

**Goal:** 默认游戏主角运行归档灰色底衣身体，完整支持24动作方向。

**Architecture:** 既有严格构建 → 校验/逐字节复制 → 确定性SpriteFrames及本地接入清单 → 现有单AnimatedSprite2D玩家。人物配方及构建维持review-only。

**Tech Stack:** Python/Pillow、Godot 4、GDScript、tscn/tres。

## Global Constraints

- Q22=A允许默认主角本地接入及受影响冻结绑定的精确变更；旧餐馆NPC暂留。
- 不自动刷新基线，不改变旧配方冻结范围，不授予production_release资格。
- 256×224、根点(123,201)、整帧scale=0.25；静态设置在场景。
- 动作名称为action_direction；时长来自严格配方，不能假定六帧。
- 测试存档/private/tmp/coastal-*，Godot带--log-file /private/tmp/coastal-*.log。
- 不改生成源像素，不增加合成器/人物播放器，不提交或推送。

## Task 1：严格输出到Godot资源与门禁（主代理）

Files: 新增tools/characters/godot_integration.py、tests/test_godot_integration.py；修改check.py与门禁测试；生成assets/characters/integrations/adult-standard-v2-visible-r001/及resources/player_body_frames.tres。

Interface: create(repo, build_dir, package_dir, frames_file)生成local-development-integration manifest；verify(repo, manifest_path)从严格构建、配方、实际输出和tres重算并比较。角色端只加载生成的SpriteFrames；manifest包含clips数组，每条name/action/direction/loop/frames，每帧texture/pose_id/duration_ms/sha256。

- [x] 先测试缺完整动作拒绝、篡改PNG/时序/tres拒绝、不可覆盖输出、确定性时序与资源闭包；确认失败。
- [x] 调用build.verify与validate；仅接收完整24格、共享几何、单一visible variant的构建。复制输出并设置SpriteFrames speed=1000、frame duration=duration_ms（毫秒转秒由引擎处理）。
- [x] 验证路径均限于受管Godot资源，拒绝路径穿越/符号链接/额外文件（允许Godot.import边车）。源构建和新包SHA一一对应。
- [x] 门禁在原有冻结比较之外验证显式登记的接入清单；保持未登记生产变化反例。基线待最终代码审核后只改批准文件和资源项，记录差异，不运行capture_baseline重采。

## Task 2：Godot玩家与动作接入（子代理，独立文件范围）

Files: scripts/player.gd、player_tool_action.gd、room_transition.gd、scenes/actors/player.tscn；tests/test_unified_player.gd、test_unified_player_native.gd及确实受影响的玩家/门测试。

Interface: player.sprite为唯一AnimatedSprite2D；SpriteFrames加载res://resources/player_body_frames.tres，idle/walk/run/hoe/water/harvest加方向后缀。新增player.play_idle()供工具及门过渡调用。

- [x] 先将真实测试目标设为新SpriteFrames、24格及真实时长、独立idle、缺动作安全拒绝、工具锁定/结束；旧实现上运行应失败。
- [x] 场景：centered=false、offset=(-123,-201)、position=(0,0)、scale=(0.25,0.25)、animation=idle_south。
- [x] player以walk_/run_播放，停步和release-input进入idle；视觉边界计算使用centered/offset/scale，不能按旧384画布推断。
- [x] ToolAction开始前校验动画存在/帧非空，active只在成功时设置；相同动作重播从首帧开始，结束调用play_idle，锁定方向/移动。
- [x] room_transition的walk_to播放walk_方向，停止/碰撞后idle；保留原真实世界遮挡和存档事务。
- [x] 资源就绪后运行headless玩家、南门及直接相关测试；保存往返与业务测试不得削弱断言。

## Task 3：集成审核、基线及原生验收（主代理）

- [x] 审核生产diff，明确登记新资源及4个生产代码/场景的具体SHA变化，原旧资产及冻结配方维持原哈希；接入清单受门禁复核。
- [x] python3 -m unittest discover -s tools/characters/tests；python3 tools/characters/check.py；Godot相关回归，日志保存/private/tmp。
- [x] 新原生fixture使用真实harbor.tscn、隔离save_directory元数据，检查四向走跑各10循环、12农事、暂停恢复、门/树/柜台；实际纹理来源、pose和时序绑定报告。
- [x] 使用真实农事事务及存档重载验证流程，无第二次提交；全动作画面截图及连续采集，目视检查。
- [x] 独立review评审本轮diff及风险，修复重要问题后仅重跑受影响测试。
- [x] 更新PROJECT_STATE/HANDOFF/人物入口与轻量结果报告；记录未测试项、旧NPC暂留及精确接触/动态换装/生产门禁未通过。

## 模型分工

主代理gpt-6-astra负责资源/门禁及原生集成。Godot跨文件实现采用gpt-6.1-sol high；最终独立评审采用gpt-6-astra high。文件责任不重叠，不嵌套派生代理。
