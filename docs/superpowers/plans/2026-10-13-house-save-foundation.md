# House Save Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在住宅上线前，独立验证 location 场景字段、旧档读取、新档写入与未来版本保护。

**Architecture:** PlayerState 提供唯一校验与内存迁移入口，SaveService 读取时迁移、写入时统一新版；迁移不会改写磁盘。场景碰撞与安全落点由后续住宅模块负责，本任务只校验有限坐标和场景枚举。

**Tech Stack:** Godot 4.7.1 / GDScript / 现有 JSON 原子保存服务。

## Global Constraints

- 关联已批准规格：../specs/2026-10-13-house-interior-door-design.md。
- 不改玩家真实存档；测试目录仅 /private/tmp/coastal-house-save-*。
- 不改变 24/48 格库存、堆叠、采集、姓名等原校验。
- 当前试玩包保持 v0.5.1，本阶段不发布半成品住宅。
- 后续依次为住宅/门素材与碰撞、过门状态机、会话集成与安全落点、实机发布；它们有独立测试门槛，不以本任务通过冒充整体完成。
- 执行在当前会话逐项进行；不自动启动子代理。executing-plans 技能在本环境不可用，采用本计划的红绿测试与检查点流程。

## Task 1: 分场景存档格式与无副作用迁移

**Files:** 全部位于 /Users/wyq/Documents/code/coastal-harbor-game/。
- Modify: godot2d/scripts/player_state.gd
- Modify: godot2d/scripts/save_service.gd
- Create: godot2d/tests/test_house_save.gd
- Regression: godot2d/tests/test_save_state.gd、test_journal.gd

**Interfaces:**
- Consumes: 原 State.valid_data(value)、restore(value)、to_data(position)，Save.read_save()、write_save(value)。
- Produces: State.SAVE_VERSION=2、State.location="harbor"；State.migrate_data(value)->Dictionary，非法数据返回 {}，合法返回独立深拷贝；to_data 的签名不变。
- read_save().data 为已迁移的有效 v2；write_save 接受有效 v1/v2，磁盘统一写 v2。restore 原子恢复场景和库存，失败不改变现有状态。

- [x] **Step 1: Write the failing test**

新增测试内容如下。早期守卫让缺失接口产生明确失败，不出现调用不存在方法的运行错误。

```gdscript
extends SceneTree
var State = load("res://scripts/player_state.gd")
var Save = load("res://scripts/save_service.gd")
var checks: Dictionary = {}
func check(id: String, value: bool) -> void:
	checks[id] = value
	print(("PASS " if value else "FAIL ")+id)
func put(path: String, value: Dictionary) -> void:
	var f := FileAccess.open(path,FileAccess.WRITE)
	f.store_string(JSON.stringify(value))
	f.close()
func finish() -> void:
	DirAccess.make_dir_recursive_absolute("res://verification-house-save")
	var f := FileAccess.open("res://verification-house-save/tests.json",FileAccess.WRITE)
	f.store_string(JSON.stringify({"passed":not checks.values().has(false),"checks":checks},"\t"))
	f.close()
	print("HOUSE_SAVE ",checks.size()," passed=",not checks.values().has(false))
	quit(1 if checks.values().has(false) else 0)
func _initialize() -> void:
	var state = State.new()
	var first: Dictionary = state.to_data(Vector2(330,250))
	check("new_format",first.get("version")==2 and first.get("location")=="harbor")
	check("migration_api",state.has_method("migrate_data"))
	if checks.values().has(false):
		finish()
		return
	state.collect("clam_a","clam")
	state.bag.transfer_to(state.chest,0,1)
	var legacy: Dictionary = state.to_data(Vector2(330,250))
	legacy.version = 1
	legacy.erase("location")
	var original := JSON.stringify(legacy)
	var migrated: Dictionary = State.migrate_data(legacy)
	check("legacy_valid",State.valid_data(legacy))
	check("legacy_migrates",migrated.version==2 and migrated.location=="harbor")
	check("legacy_unchanged",JSON.stringify(legacy)==original)
	migrated.chest[0].amount = 0
	check("migration_deep_copy",legacy.chest[0].amount==1)
	var home: Dictionary = State.migrate_data(legacy)
	home.location = "house"
	home.position = [320,328]
	check("house_valid",State.valid_data(home))
	var loaded = State.new()
	check("house_restore",loaded.restore(home) and loaded.location=="house")
	check("house_snapshot",loaded.to_data(Vector2(320,328)).location=="house")
	check("inventory_preserved",loaded.chest.count_item("clam")==1 and loaded.total_collected==1)
	var invalid: Dictionary = home.duplicate(true)
	invalid.location = "unknown"
	check("unknown_location",not State.valid_data(invalid))
	check("invalid_migration",State.migrate_data(invalid).is_empty())
	check("failed_restore_atomic",not loaded.restore(invalid) and loaded.location=="house" and loaded.chest.count_item("clam")==1)
	invalid = home.duplicate(true)
	invalid.erase("location")
	check("missing_location",not State.valid_data(invalid))
	invalid = home.duplicate(true)
	invalid.location = 1
	check("typed_location",not State.valid_data(invalid))
	invalid = home.duplicate(true)
	invalid.position = [INF,0]
	check("finite_position",not State.valid_data(invalid))
	invalid = legacy.duplicate(true)
	invalid.total_collected = 999
	check("legacy_still_validated",State.migrate_data(invalid).is_empty())
	check("restore_legacy",loaded.restore(legacy) and loaded.location=="harbor")
	var path := "/private/tmp/coastal-house-save-"+str(Time.get_ticks_usec())
	DirAccess.make_dir_recursive_absolute(path)
	var main := path+"/progress.json"
	put(main,legacy)
	var before := FileAccess.get_file_as_string(main)
	var service = Save.new(path)
	var result: Dictionary = service.read_save()
	check("read_legacy",result.ok and result.data.version==2 and result.data.location=="harbor")
	check("read_does_not_write",FileAccess.get_file_as_string(main)==before)
	check("write_house",service.write_save(home))
	check("house_roundtrip",service.read_save().ok and service.read_save().data.location=="house")
	check("legacy_backup_preserved",FileAccess.get_file_as_string(path+"/progress.backup.json")==before)
	invalid = home.duplicate(true)
	invalid.location = "bad"
	put(main,invalid)
	result = service.read_save()
	check("invalid_scene_backup",result.ok and result.recovered and result.data.location=="harbor")
	invalid.version = 99
	put(main,invalid)
	var future_before := FileAccess.get_file_as_string(main)
	check("future_blocks_read",service.read_save().get("future",false))
	check("future_blocks_write",not service.write_save(home))
	check("future_untouched",FileAccess.get_file_as_string(main)==future_before)
	put(main,legacy)
	check("write_legacy",service.write_save(legacy))
	var disk: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(main))
	check("write_normalizes",disk.version==2 and disk.location=="harbor")
	finish()
```

- [x] **Step 2: Run test to verify it fails**

```sh
/Applications/Godot.app/Contents/MacOS/Godot --headless --log-file /private/tmp/house-save-red.log --path godot2d --script res://tests/test_house_save.gd
```

Expected: new_format 与 migration_api FAIL，退出 1。原代码新档仍为 version=1。

- [x] **Step 3: Write minimal implementation**

player_state.gd 常量区新增 SAVE_VERSION，字段区新增 location。替换 to_data 为下列完整函数；valid_data 只替换开头版本判定，后续库存及统计校验不变。在 restore 成功校验后、重建容器前加入 location 赋值。

```gdscript
const SAVE_VERSION := 2
var location := "harbor"

func to_data(position: Vector2) -> Dictionary:
	return {"version":SAVE_VERSION, "location":location, "player_name":player_name,
		"bag":bag.snapshot(), "chest":chest.snapshot(), "collected":collected.duplicate(),
		"discovered":discovered.duplicate(), "total_collected":total_collected,
		"position":[position.x,position.y]}

# valid_data 开头替换为以下条件，后续原校验保持原位：
# if not value is Dictionary or (value.get("version") != 1 and value.get("version") != SAVE_VERSION):
#     return false
# if value.version == SAVE_VERSION and value.get("location") not in ["harbor","house"]:
#     return false

static func migrate_data(value) -> Dictionary:
	if not valid_data(value):
		return {}
	var migrated: Dictionary = value.duplicate(true)
	if migrated.version == 1:
		migrated.location = "harbor"
	migrated.version = SAVE_VERSION
	return migrated

# restore 的校验成功之后新增：
# location = "harbor" if value.version == 1 else value.location
```

save_service.gd 替换 read_save 整个函数如下。write_save 的校验条件改为先执行 `value = State.migrate_data(value)`，再用 `if value.is_empty():` 返回原校验失败提示；其余文件原子写入步骤不变。

```gdscript
func read_save() -> Dictionary:
	var main = _read(directory.path_join("progress.json"))
	if main is Dictionary and main.get("version",1) != 1 and main.get("version",1) != State.SAVE_VERSION:
		return {"ok":false, "future":true, "message":"存档版本不兼容，已保护原文件。"}
	var migrated: Dictionary = State.migrate_data(main)
	if not migrated.is_empty():
		return {"ok":true, "recovered":false, "data":migrated, "message":""}
	var backup = _read(directory.path_join("progress.backup.json"))
	migrated = State.migrate_data(backup)
	if not migrated.is_empty():
		return {"ok":true, "recovered":true, "data":migrated, "message":"主存档异常，已恢复上一份备份。"}
	return {"ok":false, "future":false, "message":"尚无有效存档。" if not has_files() else "存档与备份均无法读取，原文件已保留。"}
```

- [x] **Step 4: Run test to verify it passes**

```sh
/Applications/Godot.app/Contents/MacOS/Godot --headless --log-file /private/tmp/house-save-green.log --path godot2d --script res://tests/test_house_save.gd
/Applications/Godot.app/Contents/MacOS/Godot --headless --log-file /private/tmp/house-save-regression.log --path godot2d --script res://tests/test_save_state.gd
/Applications/Godot.app/Contents/MacOS/Godot --headless --log-file /private/tmp/house-journal-regression.log --path godot2d --script res://tests/test_journal.gd
```

Expected: HOUSE_SAVE passed=true、STATE_SAVE 23 passed=true、JOURNAL 37 passed=true。现有 headless macOS 证书警告与测试有意制造的写入失败不算新回归；任何其他脚本错误都必须先排查。

- [ ] **Step 5: Commit**

```sh
git diff --check
git add godot2d/scripts/player_state.gd godot2d/scripts/save_service.gd godot2d/tests/test_house_save.gd docs/superpowers/plans/2026-10-13-house-save-foundation.md
git commit -m "feat: prepare scene-aware saves for house interiors"
```

## 完成后的执行交接

本计划只完成独立存档基础，不宣布室内、门动画或新试玩完成。下一执行单元为 room_data、house_interior、interactive_door 的素材与碰撞；然后实现 room_transition 和会话集成。必须等实际室内场景存在后才测试坐标安全回退，不能用虚构位置测试冒充场景验收。
