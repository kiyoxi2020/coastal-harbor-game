# 小屋像素素材首批制作 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 完成床和室内房门的首批生成素材、尺度样张及可运行的素材验证器，为完整小屋替换提供可靠输入。

**Architecture:** 首批先验证床和门，不一次替换全部家具。生图负责造型及透明素材，独立清单负责逻辑尺寸和来源，Godot 校验器负责导入与比例检查；现有住宅继续可玩。首批通过后，沿用同一尺度制作全部物件并接入房间，不能把首批完成称为整屋更新完成。

**Tech Stack:** 当前项目 Godot 4 / GDScript、内置 image_gen、PNG RGBA、Git。

**已批准执行调整：** 原始床含透明外晕，门帧存在画布偏差。用户在执行中明确允许程序整理；因此在原 Task 1 与导入之间增加可重复的 Pillow 清理/像素化/共享门画布步骤及合成图单元测试，并将 Task 2/3 合并给一个实现者完成 RED→GREEN。保持源图不动、门三态共用注册变换、不以独立拉宽消除透视差异。清单区分门扇可见尺寸和含透明边的共同画布尺寸；原例子中的30×44不再被误当作所有门图画布的强制尺寸。独立复核后再接入运行时。

## Global Constraints

- 仓库根：`/Users/wyq/Documents/code/coastal-harbor-game`；下文文件路径均相对该根。
- 规格：`docs/superpowers/specs/2026-10-13-cottage-pixel-art-design.md`，已获用户审阅确认。
- 不改变 1280×720 显示、2 倍镜头或默认半桌面窗口。
- 生成使用用户选定的原有内置生图服务，不切换外部服务。
- 原始生成结果保存在 `art/interior/source/`；游戏采用的精灵放入 `godot2d/assets/house-interior/`。
- 不新增料理、睡眠、装修或经济系统；不用真实玩家存档做测试；不自动推送远端。
- 本计划只负责首批素材质量门槛。完整规格的家具铺开、碰撞、存档落点迁移、动画时长和重新发布必须继续完成，首批结果不得覆盖最新试玩。

## Task 1：生成并审查床与房门素材

**Files:**
- Read: `art/interior/concepts/approved-cottage-pixel.png`
- Create: `art/interior/source/bed.png`
- Create: `art/interior/source/door-closed.png`
- Create: `art/interior/source/door-half.png`
- Create: `art/interior/source/door-open.png`
- Create: `art/interior/source/prompts.md`

**Interfaces:**
- Consumes: 已确认概念图，仅作风格参考，不要求保留原图像素。
- Produces: 四张独立真实透明 PNG；记录提示词、输出原始路径、选用/淘汰原因。门的三个状态不得放在需要程序抠图的共用背景上。

- [x] 先用 view_image 查看确认图，再完整阅读 imagegen 技能；这是生成任务，不用代码画素材替代生图。
- [x] 单独生成床，提示词如下（使用确认图作为 reference，不是整图编辑目标）：

```text
Original top-down front-facing three-quarter pixel-art sprite, ONE single bed only, isolated on genuine transparent background. Match reference cottage: weathered honey wood, restrained shell motif on headboard, cream pillow and sea-teal patched quilt. No rug, wall, floor, cast shadow outside bed, text or other furniture. Not isometric. Chunked hard pixel edges, limited warm palette, no antialiasing, no painterly gradients. Compact readable silhouette intended for 48 x 80 logical pixels, including headboard and feet. Bed length approximately twice the visible standing character height, not a giant double bed. Keep full silhouette with transparent margin. This is an individual game sprite, not a room illustration.
```

- [x] 查看输出，确认无假棋盘背景、截断床脚或双人床比例。把通过的原始输出复制为 bed.png；失败则针对单个问题重生成。
- [x] 生成关闭的门，提示词如下：

```text
Original pixel-art game sprite of ONE upright sea-teal wooden cottage door LEAF ONLY, front-facing, genuine transparent background, no frame, floor, wall, background or text. Match reference style, small four-pane square window and brass handle, worn paint, restrained pixel clusters. Intended visible logical size 30 wide x 44 high, vertical rectangular silhouette, never a floor hatch. Fixed hinge along left edge. No perspective tilt or antialiasing. No external cast shadow. Full uncropped silhouette. This closed leaf is the canonical identity for two subsequent open poses.
```

- [x] 以已通过的关闭门作为参考，分别生成半开和全开门扇；两个调用共享以下提示词，仅替换方括号状态：

```text
Generate the SAME pixel-art cottage door leaf in [HALF OPEN / FULLY OPEN] state on genuine transparent background. Preserve wood color, window, handle, height and left hinge. Keep the hinge vertical and stationary; swing around it, show appropriate narrow edge and back face, do not horizontally squash the closed drawing. Leaf only, no door frame, wall, floor, text or shadow. Same front-facing farming-RPG camera and hard pixel style. Canvas fits a 30 x 44 logical envelope; transparent area remains where closed leaf used to be, do not recenter the narrow open leaf. Keep all visible pixels within the original envelope.
```

- [x] 逐张查看三态，只有身份一致、门高一致且能注册同一铰链的素材才通过。使用生图编辑修正透明边或姿态；没有用户明确授权，不用 Python 改图。
- [x] 在 prompts.md 保存实际提示词、原始输出位置、模型工具、用途和人工观察结果；不得声称模型输出原生 30×44，30×44 是接入的逻辑目标。

## Task 2：先建立会失败的首批资产验证

**Files:**
- Create: `godot2d/tests/test_cottage_assets.gd`
- Create in Task 3: `godot2d/assets/house-interior/pilot.json`

**Interfaces:**
- Consumes: JSON 字典 `{ "bed": {...}, "door_closed": {...}, "door_half": {...}, "door_open": {...} }`；每项有 `path: String`、`logical_size: [int,int]`、`source: String`。
- Produces: 进程退出码 0 为通过、1 为失败；只读文件，不写存档。

- [x] 用 apply_patch 添加如下完整验证脚本：

```gdscript
extends SceneTree

func _initialize() -> void:
	var path := "res://assets/house-interior/pilot.json"
	if not FileAccess.file_exists(path):
		printerr("FAIL missing pilot manifest")
		quit(1)
		return
	var data = JSON.parse_string(FileAccess.get_file_as_string(path))
	if not data is Dictionary:
		printerr("FAIL invalid manifest")
		quit(1)
		return
	for id in ["bed", "door_closed", "door_half", "door_open"]:
		if not data.has(id) or not data[id] is Dictionary:
			printerr("FAIL missing entry: ", id)
			quit(1)
			return
		var entry: Dictionary = data[id]
		var size = entry.get("logical_size", [])
		var expected := [48, 80] if id == "bed" else [30, 44]
		if size != expected or str(entry.get("source", "")).is_empty():
			printerr("FAIL size/source: ", id)
			quit(1)
			return
		var resource = load(str(entry.get("path", "")))
		if not resource is Texture2D:
			printerr("FAIL missing texture: ", id)
			quit(1)
			return
		var bitmap: Image = resource.get_image()
		if bitmap == null or bitmap.is_empty() or not bitmap.detect_alpha():
			printerr("FAIL image/alpha: ", id)
			quit(1)
			return
		var occupied := bitmap.get_used_rect()
		if occupied.size.x == 0 or occupied.size.y == 0:
			printerr("FAIL empty silhouette: ", id)
			quit(1)
			return
	print("PASS cottage pilot assets: 4")
	quit(0)
```

- [x] 在项目根运行，确认因缺清单失败，不是语法错误：

```sh
/Applications/Godot.app/Contents/MacOS/Godot --headless --path godot2d --script res://tests/test_cottage_assets.gd
```

Expected: `FAIL missing pilot manifest`，退出 1。

## Task 3：登记首批候选素材并验证

**Files:**
- Create: `godot2d/assets/house-interior/pilot.json`
- Create: `godot2d/assets/house-interior/bed.png`
- Create: `godot2d/assets/house-interior/door-closed.png`
- Create: `godot2d/assets/house-interior/door-half.png`
- Create: `godot2d/assets/house-interior/door-open.png`

**Interfaces:**
- Consumes: Task 1 审查通过的四张原始 PNG，Task 2 的验证器。
- Produces: 可被 Godot 加载的候选纹理与清单，不更改现有家具绘制代码。

- [x] 复制四张审查通过图片，不覆写旧 atlas：

```sh
mkdir -p godot2d/assets/house-interior
cp art/interior/source/bed.png godot2d/assets/house-interior/bed.png
cp art/interior/source/door-closed.png godot2d/assets/house-interior/door-closed.png
cp art/interior/source/door-half.png godot2d/assets/house-interior/door-half.png
cp art/interior/source/door-open.png godot2d/assets/house-interior/door-open.png
```

- [x] 用 apply_patch 写入清单：

```json
{
  "bed": {"path":"res://assets/house-interior/bed.png","logical_size":[48,80],"source":"art/interior/source/bed.png"},
  "door_closed": {"path":"res://assets/house-interior/door-closed.png","logical_size":[30,44],"source":"art/interior/source/door-closed.png"},
  "door_half": {"path":"res://assets/house-interior/door-half.png","logical_size":[30,44],"source":"art/interior/source/door-half.png"},
  "door_open": {"path":"res://assets/house-interior/door-open.png","logical_size":[30,44],"source":"art/interior/source/door-open.png"}
}
```

- [x] 导入并运行测试：

```sh
/Applications/Godot.app/Contents/MacOS/Godot --headless --path godot2d --editor --import
/Applications/Godot.app/Contents/MacOS/Godot --headless --path godot2d --script res://tests/test_cottage_assets.gd
```

Expected: `PASS cottage pilot assets: 4`，退出 0。这个结果不代表像素质量或门动画视觉合格。

- [x] 在 Godot 预览中按 2 倍显示、最近邻查看床与当前角色，检查床长约为角色高度两倍；以同一门槛叠放门三态，逐帧切换确认无跳帧、铰链不移动。若生成图透明边不同，不把整张画布硬拉伸；下一接入步骤需要按实际包围盒登记区域与锚点。
- [x] 记录观察截图和实际源图尺寸到 `art/interior/source/prompts.md`；未通过的素材保留原始来源但不登记为候选。
- [x] 仅提交本次明确文件，不包含交付历史：

```sh
git add -- art/interior/source godot2d/assets/house-interior godot2d/tests/test_cottage_assets.gd
git commit -m "art: add verified cottage bed and door pilot assets"
```

## 后续完整接入的强制衔接点

此计划刻意停在素材质量关，不假设模型一定一次产出合格游戏资产。首批实际输出决定裁切区域、逻辑锚点和门三态注册数据，然后为整屋接入补全可执行代码计划。不得提前写死未知的源图坐标。

- 首批通过后：同风格生成床头柜/灯、厨房、桌椅、箱子、书架/相框、盆栽、窗帘窗、地毯、墙面地板，补清单与独立纹理验证。
- 接入 `house_furniture.gd` 和 `house_interior.gd`：以脚底锚点组装、最近邻、墙饰独立层，按家具底座更新 `room_data.gd` 碰撞及交互点。
- 接入 `interactive_door.gd`：室内固定门框/暗部/三帧，保持室外路径不变；将 `room_data.gd` SPAWN 改为 (320,300)，同步 `house_session.gd` 旧门前位置的安全回退。
- 接入 `room_transition.gd`：过门时长按实际距离/角色速度计算；验证持键、失败恢复、退出与存档，不能只改动画画面。
- 运行原住宅、存档、库存等全部测试及新增视觉检查；20 次往返、临时存档重启、家具前后遮挡、实际 Mac 导出测试。之后才更新 `交付与预览/2D` 的当前包和报告。

## 自查

本计划覆盖已确认规格中的首批质量验证，不声称覆盖整屋交付。首批整理、验证和床/室内门运行时接入均已完成，独立审查通过；重新发布正在执行。其余物件仍须完成上列衔接工作。实际接口遵循已批准执行调整中的共同门画布和源图整理规则，结果见 `2026-10-13-cottage-pilot-result.md`。
