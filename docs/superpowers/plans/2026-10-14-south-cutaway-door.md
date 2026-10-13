# 下方剖面入口与穿模修正 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将室内出口移至整个房间底部中央，使进入室内方向向上，并消除门框切人、门板前残留头部及实体穿越。

**Architecture:** 保持 RoomData → HouseInterior/HouseSession → InteractiveDoor → RoomTransition 的职责划分。室内外法向独立；关闭门扇与固定门柱分别碰撞；门洞采用空间遮挡而非人物帧擦除。先复现用户截图，再验证方向、实际渲染和发布应用。

**Tech Stack:** Godot 4.7.1、GDScript、CanvasItem shader、既有像素图集、Python打包工具。

## Global Constraints

地板仍为 Rect2(176,112,288,208)，不调整人物、镜头、窗口或家具尺寸。
室内门槛移到整个房间下边缘中央 (320,320)，安全落点为 (320,288)。
室内入口朝房间的方向为 UP，室外门保持 (209,165)、朝地面 DOWN，室外安全落点仍为 (209,194)。
保持 E 开门、查看和关闭提示，B/Tab 手账。
两侧门前范围按各自朝地面的法向计算：深度0..56、横向±24。
存档版本仍为2，库存和进度不变。
验证后更新最新2D试玩包、源码包、截图、录像及报告；旧版可恢复归档且Git忽略，3D不变。不自动推送远程。

批准规格：`docs/superpowers/specs/2026-10-14-south-cutaway-door-design.md`。
实际项目：`/Users/wyq/Documents/code/coastal-harbor-game`，沿用现有 feature branch，保留用户修改。

## 文件职责

- `godot2d/scripts/room_data.gd`：门位、法向、室内墙体。
- `godot2d/scripts/house_interior.gd`：补北墙、下方剖面入口。
- `godot2d/scripts/interactive_door.gd`、`door_jamb.gd`：各向门形、门扇及固定门柱碰撞和绘制。
- `godot2d/scripts/house_exterior.gd`：室外房屋、原门洞切口及遮挡轮廓。
- `godot2d/scripts/room_transition.gd`、`player.gd`、`doorway_clip.gdshader`：沿地面移动、空间遮挡、视觉恢复。
- `godot2d/scripts/house_session.gd`：独立室外法向、安全位置和存档恢复。
- `godot2d/tests/test_south_door.gd`（新增）：方向、物理与实际渲染回归。
- 既有 `test_compact_cottage.gd`、`test_cottage_runtime.gd`、`test_house.gd`、`house_driver.gd`：更新旧北入口假设，保留行为覆盖。

### Task 1: 下方通道、独立法向与实体碰撞

**Files:** Modify room_data.gd, house_interior.gd, house_session.gd, interactive_door.gd, door_jamb.gd；Create tests/test_south_door.gd；更新受门坐标影响的既有测试。

**Interfaces:** 保留 `can_interact(point: Vector2) -> bool`、`set_pose(value: int) -> void`、`safe_position(location: String, point: Vector2) -> Vector2`。`ENTRANCE_NORMAL`仅用于室内，新常量`OUTSIDE_ENTRANCE_NORMAL`用于室外。门扇碰撞仍由 `collision`/`body`暴露；固定门柱不能归属被禁用的门扇形状。

- [ ] 建立隔离存档的SceneTree测试，先运行以下断言观察旧实现失败：

```gdscript
const Room = preload("res://scripts/room_data.gd")
# scene 使用 harbor.tscn，journal_test=true，save_directory=/private/tmp/coastal-south-test。
check("south_edge", Room.DOOR == Vector2(320, Room.FLOOR.end.y))
check("south_spawn", Room.SPAWN == Vector2(320,288))
scene.home.switch_room("house", Vector2.ZERO)
check("inside_up", scene.home.active_door().entrance_normal == Vector2.UP)
scene.home.switch_room("harbor", Vector2.ZERO)
check("outside_down", scene.home.active_door().entrance_normal == Vector2.DOWN)
```

运行 `/Applications/Godot.app/Contents/MacOS/Godot --headless --log-file /private/tmp/south-door-red.log --path godot2d --script res://tests/test_south_door.gd`；预期上述室内断言失败，失败不能来自解析错误。

- [ ] 修改几何，保留 furniture()/locations()：

```gdscript
const SPAWN := Vector2(320,288)
const DOOR := Vector2(320,320)
const ENTRANCE_NORMAL := Vector2.UP
const OUTSIDE_ENTRANCE_NORMAL := Vector2.DOWN
# blockers() 的外围矩形，门柱另由门组件提供：
# Rect2(160,96,320,32) 上墙；左右墙不变。
# Rect2(176,320,124,16)、Rect2(340,320,124,16) 下墙两侧。
# house_session._ready():
exterior_door.entrance_normal = Room.OUTSIDE_ENTRANCE_NORMAL
# house_interior._draw(): 北墙连续，不再留下旧洞。
tile_texture(wall_texture, Rect2(176,64,288,64))
block(Rect2(176,320,124,7), "6b5c44")
block(Rect2(340,320,124,7), "6b5c44")
```

- [ ] 室内门绘制改为低剖面：横向38单位框、30单位净开口、门槛厚3单位；门扇三态闭合跨口、半开沿铰链、全开贴柱。用现有门纹理的注册区域配合低矮结构，不旋转正面高门图铺在地板。固定门柱使用独立StaticBody2D，保留开门后的实体阻挡。两侧门都检查净通行宽度大于人物10单位宽。
- [ ] 为0..56深度及±24横向按 `door.position + door.entrance_normal * depth + Vector2(lateral,0)`采样；后方用负深度拒绝。实际物理沿门两侧推进、贴关闭门按E，再打开门过通道；不是只检查碰撞矩形存在。
- [ ] 验证存档：旧(320,128)回退、(320,240)保留、新门(320,320)回退、新安全点有效。原v1/v2库存迁移仍使用既有 test_house_save.gd，不更改存档版本。
- [ ] 运行 test_south_door、test_house_save、test_cottage_runtime、test_house，更新与北门方向绑定的断言和路线但不删除菜单锁、连续跨门、失败恢复覆盖。记录实际命令、退出码和失败修复，再提交任务1。

### Task 2: 重现截图并修复空间遮挡

**Files:** Modify player.gd, doorway_clip.gdshader, interactive_door.gd, door_jamb.gd, house_exterior.gd, room_transition.gd；Modify tests/test_south_door.gd, test_compact_cottage.gd, house_driver.gd。

**Interfaces:** 保留 `reset_doorway_visual()`、`walk_to(point: Vector2) -> bool`、`update_clip()`及状态机阶段名。遮挡由实际门的几何提供，不从inside布尔值推断运动方向。`doorway_hidden`若保留，仅作为状态/捕获进度，不再驱动从头向下的帧裁切。

- [ ] 在修改视觉前，用真实房屋、门和人物同一画面重现截图位置，保存门前站立、擦左框、室外部分穿门的PNG。检查屋图原门是否真正剔除、门扇pose、人物脚底、shader参数、全局绘制顺序。用截图标出错误，不把上一版“仅独立人物像素数减少”测试视为正确性证据。
- [ ] 新增完整场景渲染失败检查：同一门前地面位置比较正常人物与过门前人物轮廓；固定门框不在躯干中间形成竖切；室外门已开时角色不能叠在关闭门板上。捕获状态可用：

```gdscript
await RenderingServer.frame_post_draw
root.get_texture().get_image().save_png("/private/tmp/coastal-south-before.png")
# 靠门与远离门都必须测试，不能只看安全落点。
for depth in [7.0,12.0,24.0,40.0]:
    scene.player.position = door.position + door.entrance_normal * depth
    await process_frame
    await RenderingServer.frame_post_draw
    root.get_texture().get_image().save_png("/private/tmp/coastal-south-depth-"+str(depth)+".png")
```

- [ ] 依据上述复现记录，分离真实前景轮廓与门洞背景。室外开口使用原图实际开口坐标，确保原图门扇残片不盖人物；门前人物不受高层竖框全局遮挡。室内剖面只保留低门柱和门槛前景，不使用54高的北墙门框。若测得原图切口和新门不一致，先统一几何再改遮挡，禁止盲目调整z值。
- [ ] shader只使用世界坐标空间界限，不使用 `frame_y < hidden_fraction`。采用明确的开启开关，离开跨门阶段即关闭；遮罩边界需来自已测量的门洞/前墙轮廓，不能写成人物高度百分比。人物在地面完整，在真实前景后才被遮挡；不同入口方向不共用一条擦除规则。
- [ ] 保持沿门法向真实行走；越过可见区域再淡出。跨越终点必须结合新遮罩实际完全遮住人物的位置验证，不能无条件复用旧APERTURE_DEPTH=16。缺目标、碰撞中断、读档、R复位全部恢复材质开关、人物透明度和排序。
- [ ] 原生运行 `/Applications/Godot.app/Contents/MacOS/Godot --log-file /private/tmp/south-door-render.log --path godot2d --script res://tests/test_south_door.gd`。双向捕获门前/开门/跨越/目标显露/关闭，检查向上进屋、向下出屋，查看连续帧而非最后一张图。若仍有切身或悬头，不得进入发布。
- [ ] 更新 test_compact_cottage 原有北向假设及旧shader参数断言为新行为验证；补20次跨门后清理检查、失败恢复及库存不变。覆盖测试通过后提交任务2。

### Task 3: 全回归、导出验证与最新交付

**Files:** Modify godot2d/export_presets.cfg, godot2d/README.md；Create docs/superpowers/plans/2026-10-14-south-door-release-result.md；使用 tools/package_current_source.py。

**Interfaces:** 使用既有应用 `--verify-house` / `--verify-journal` 驱动；导出release模板不支持 `--script`，不得再将此作为导出测试。版本更新到0.5.5，先暂存后验包，再替换最新交付。

- [ ] 执行全部原有回归与住宅专项；每个进程保存日志，退出非零或任何断言失败均不得发布。无窗口进程均传 `--log-file /private/tmp/...`，所有游戏测试用独立临时存档，禁止测试用户进度。
- [ ] Python素材处理与打包测试：`/opt/homebrew/bin/python3 -m unittest tests.test_prepare_cottage_assets tests.test_package_current_source -v`，预期全部通过。运行渲染测试并保存PNG；仅headless通过不算视觉验收。
- [ ] 将export_presets.cfg的版本及暂存路径改为0.5.5；导出命令：`/Applications/Godot.app/Contents/MacOS/Godot --headless --log-file /private/tmp/south-door-export.log --path godot2d --export-release macOS ../builds/staging/v0.5.5/CoastalHarbor2D-v0.5.5-macOS.zip`。先创建精确暂存目录，不覆盖当前2D。
- [ ] 解压暂存应用，运行其Contents/MacOS二进制并传 `-- --verify-house --test-save-directory=/private/tmp/coastal-south-app`；随后在另一个临时目录运行 `--verify-journal`。检查退出码、驱动JSON、真实应用图片与录像。补导出应用重启及途中退出验证；不以原生源码测试替代导出测试。
- [ ] 对源工程与Mac应用各检查两个方向的全部五阶段，重点复看用户截图对应位置。记录观察结果、失败修复和未测试平台；录像注明真实采样频率。
- [ ] 在暂存目录初始化package-verification.json后运行 `python3 tools/package_current_source.py --output-directory builds/staging/v0.5.5`。验证ZIP CRC、源码逐文件字节一致及Mac应用签名。将旧最新2D移到明确命名且被Git忽略的archive路径，新版通过后才提升；保留3D与用户存档。
- [ ] 把最新ZIP、截图、录像、自测报告复制到 `/Users/wyq/Documents/Codex/2026-10-08/wo-x/outputs/current-game/`。校验两处文件哈希；更新说明，不在最新目录混入旧版。最终提交并做全分支审查；不推送远程。

## 计划自查与执行记录

- 已覆盖规格的下方门位、独立方向、北墙补齐、低剖面、固定门柱、连续交互、空间遮挡、旧档、安全恢复和最新发布。
- Task 2以实际截图复现为前置，遮罩边界需测量后写入，不能把猜测参数当作完成实现。
- 三任务顺序执行，不并发修改相同Godot脚本。每任务记录基线与结束提交、测试命令及输出，再独立审查。
- 如执行技能缺失，明确报告并使用同等的逐项实施/验证步骤，不假称已调用缺失技能。
