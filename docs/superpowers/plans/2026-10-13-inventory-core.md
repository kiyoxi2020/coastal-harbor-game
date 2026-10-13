# Inventory Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立独立于场景的物品目录和有容量的库存核心，验证堆叠、全量入包、满包拒绝和容器隔离。

**Architecture:** 物品目录只保存定义；容器持有私有槽位并返回防修改快照。先补满同类再使用空格，全量加入先检查容量，不发出中途状态通知。此计划不接入现有foraging_state，避免未完成库存操作时改变正式游戏。

**Tech Stack:** 项目现有Godot 4.7.1、GDScript、SceneTree无头测试，无外部依赖。

## Global Constraints

- 初始24格，6列×4行；普通材料每格99个，工具每格1个。
- 初始48格，6列×8行，箱内滚动查看；与24格背包并列操作。
- 保留1280×720内部渲染、2倍镜头、640×416地图、默认居中且面积约占可用桌面50%的窗口。
- 不在第一阶段实现重量、耐久、品质、食材腐败、随机刷新、日循环、联机、装备属性或换装。
- 本子计划只覆盖规格第3节的目录、容量和堆叠基础；其他要求由inventory-roadmap分配，完成本计划不得声称完整背包已发布。
- 以下文件路径相对/Users/wyq/Documents/code/coastal-harbor-game；命令均在该目录执行。

---

## 文件结构

- godot2d/scripts/inventory/item_catalog.gd：现有三种海产定义与查询。
- godot2d/scripts/inventory/inventory_container.gd：固定容量槽位、快照、数量查询、剩余容量、加入。
- godot2d/tests/test_item_catalog.gd：定义校验与防外部修改。
- godot2d/tests/test_inventory_container.gd：满包、堆叠、无效请求、通知、快照隔离。

### Task 1: 物品目录

**Files:** Create godot2d/scripts/inventory/item_catalog.gd; Test godot2d/tests/test_item_catalog.gd。

**Interfaces:** Produces `get_item(id: String) -> Dictionary`，未知ID返回空字典；`stack_limit(id: String) -> int`，未知ID返回0。定义为独立副本。

- [ ] **Step 1: 写失败测试**，test_item_catalog.gd完整内容：

```gdscript
extends SceneTree

func _initialize() -> void:
    var script = load("res://scripts/inventory/item_catalog.gd")
    if script == null:
        push_error("Missing item catalog")
        quit(1)
        return
    var catalog = script.new()
    var checks := [
        catalog.stack_limit("clam") == 99,
        catalog.stack_limit("snail") == 99,
        catalog.stack_limit("kelp") == 99,
        catalog.stack_limit("unknown") == 0,
        catalog.get_item("unknown").is_empty()
    ]
    var item: Dictionary = catalog.get_item("clam")
    checks.append(item.name == "蛤蜊" and item.category == "seafood")
    checks.append(item.discardable and item.use_action == "")
    item["max_stack"] = 1
    checks.append(catalog.stack_limit("clam") == 99)
    print("CATALOG checks=", checks.size(), " passed=", not checks.has(false))
    quit(1 if checks.has(false) else 0)
```

- [ ] **Step 2: 确认缺少实现导致失败**：

```bash
/Applications/Godot.app/Contents/MacOS/Godot --headless --log-file /private/tmp/coastal-catalog-test.log --path godot2d --script res://tests/test_item_catalog.gd
```

预期退出1并出现Missing item catalog；若是测试语法错误，先修测试，不算有效红灯。

- [ ] **Step 3: 新建目录实现**，item_catalog.gd完整内容：

```gdscript
extends RefCounted

const ITEMS := {
    "clam": {"name":"蛤蜊", "icon_key":"clam", "category":"seafood", "description":"赶海拾得的蛤蜊。", "max_stack":99, "discardable":true, "use_action":""},
    "snail": {"name":"海螺", "icon_key":"snail", "category":"seafood", "description":"赶海拾得的海螺。", "max_stack":99, "discardable":true, "use_action":""},
    "kelp": {"name":"海带", "icon_key":"kelp", "category":"seafood", "description":"赶海拾得的海带。", "max_stack":99, "discardable":true, "use_action":""}
}

func get_item(id: String) -> Dictionary:
    return ITEMS.get(id, {}).duplicate(true)

func stack_limit(id: String) -> int:
    return int(ITEMS.get(id, {}).get("max_stack", 0))
```

icon_key对应现有forage_pickup.gd的三个绘制分支，不伪造不存在的贴图路径；UI接入时复用图形语义。

- [ ] **Step 4: 重跑同一命令**，预期CATALOG checks=8 passed=true，退出0。
- [ ] **Step 5: 仅提交本任务文件**：

```bash
git add -- godot2d/scripts/inventory/item_catalog.gd godot2d/tests/test_item_catalog.gd
git commit --only -m "feat: define coastal inventory items" -- godot2d/scripts/inventory/item_catalog.gd godot2d/tests/test_item_catalog.gd
```

### Task 2: 容量与原子加入

**Files:** Create godot2d/scripts/inventory/inventory_container.gd; Test godot2d/tests/test_inventory_container.gd。

**Interfaces:** Consumes catalog.stack_limit(id). Produces `new(capacity: int = 24, catalog = null)`、`snapshot() -> Array`、`count_item(id: String) -> int`、`space_for(id: String) -> int`、`add(id: String, amount: int, require_all: bool = true) -> int`及无参changed信号。add返回实际接收量，0表示无变化；require_all=false为未来仓储部分接收提供基础，但跨容器扣减不在本任务实现。

- [ ] **Step 1: 写失败测试**，test_inventory_container.gd完整内容：

```gdscript
extends SceneTree

class ToolCatalog:
    extends RefCounted
    func stack_limit(id: String) -> int:
        return 1 if id == "tool" else 0

var checks: Array[bool] = []
var notifications := 0

func _initialize() -> void:
    var script = load("res://scripts/inventory/inventory_container.gd")
    if script == null:
        push_error("Missing inventory container")
        quit(1)
        return
    var bag = script.new(2)
    bag.changed.connect(func(): notifications += 1)
    checks.append(bag.add("clam", 98) == 98)
    checks.append(bag.add("clam", 2) == 2)
    checks.append(bag.snapshot() == [{"id":"clam", "amount":99}, {"id":"clam", "amount":1}])
    var before: Array = bag.snapshot()
    checks.append(bag.add("snail", 1) == 0)
    checks.append(bag.add("clam", 99) == 0)
    checks.append(bag.snapshot() == before)
    checks.append(bag.add("clam", 99, false) == 98)
    checks.append(bag.count_item("clam") == 198 and bag.space_for("clam") == 0)
    checks.append(bag.add("unknown", 1) == 0)
    checks.append(bag.add("clam", 0) == 0 and bag.add("clam", -1) == 0)
    checks.append(notifications == 3)
    before[0]["amount"] = 0
    checks.append(bag.count_item("clam") == 198)
    var fresh = script.new()
    checks.append(fresh.snapshot().size() == 24 and fresh.count_item("clam") == 0)
    var chest = script.new(48)
    checks.append(chest.space_for("clam") == 4752)
    checks.append(chest.add("kelp", 100) == 100 and fresh.count_item("kelp") == 0)
    var tool_bag = script.new(2, ToolCatalog.new())
    checks.append(tool_bag.add("tool", 2) == 2)
    checks.append(tool_bag.snapshot()[0].amount == 1 and tool_bag.snapshot()[1].amount == 1)
    print("INVENTORY checks=", checks.size(), " passed=", not checks.has(false))
    quit(1 if checks.has(false) else 0)
```

- [ ] **Step 2: 运行并观察缺少模块失败**：

```bash
/Applications/Godot.app/Contents/MacOS/Godot --headless --log-file /private/tmp/coastal-inventory-test.log --path godot2d --script res://tests/test_inventory_container.gd
```

预期退出1，Missing inventory container。

- [ ] **Step 3: 新建最小实现**，inventory_container.gd完整内容：

```gdscript
extends RefCounted

signal changed
const Catalog = preload("res://scripts/inventory/item_catalog.gd")
var _catalog: RefCounted
var _slots: Array = []

func _init(capacity: int = 24, catalog: RefCounted = null) -> void:
    assert(capacity > 0)
    _catalog = Catalog.new() if catalog == null else catalog
    for i in range(capacity):
        _slots.append({"id":"", "amount":0})

func snapshot() -> Array:
    return _slots.duplicate(true)

func count_item(id: String) -> int:
    var result := 0
    for slot in _slots:
        if slot.id == id:
            result += slot.amount
    return result

func space_for(id: String) -> int:
    var limit: int = _catalog.stack_limit(id)
    if limit <= 0:
        return 0
    var result := 0
    for slot in _slots:
        if slot.id == "":
            result += limit
        elif slot.id == id:
            result += limit-int(slot.amount)
    return result

func add(id: String, amount: int, require_all: bool = true) -> int:
    if amount <= 0:
        return 0
    var available := space_for(id)
    if available == 0 or (require_all and available < amount):
        return 0
    var accepted := mini(amount, available)
    var remaining := accepted
    var limit: int = _catalog.stack_limit(id)
    for slot in _slots:
        if slot.id == id:
            var moved := mini(remaining, limit-int(slot.amount))
            slot.amount += moved
            remaining -= moved
    for slot in _slots:
        if remaining == 0:
            break
        if slot.id == "":
            var moved := mini(remaining, limit)
            slot.id = id
            slot.amount = moved
            remaining -= moved
    changed.emit()
    return accepted
```

- [ ] **Step 4: 重跑库存与目录测试**，预期分别17项、8项全通过且退出0；再运行现有赶海回归，证明未接入模块不改变现有玩法：

```bash
/Applications/Godot.app/Contents/MacOS/Godot --headless --log-file /private/tmp/coastal-existing-foraging.log --path godot2d --script res://tests/test_foraging.gd
```

预期现有赶海测试全部通过。若出现系统证书环境警告，独立记录，不能将其当作游戏通过或失败的唯一依据。当前测试执行只是计划，本文不声称已跑过以上新代码。

- [ ] **Step 5: 审查数量与通知只发生一次，仅提交任务文件**：

```bash
git add -- godot2d/scripts/inventory/inventory_container.gd godot2d/tests/test_inventory_container.gd
git commit --only -m "feat: add bounded inventory stacking" -- godot2d/scripts/inventory/inventory_container.gd godot2d/tests/test_inventory_container.gd
```

## 自审与交接

- 文件职责、目录接口和容器接口一致；工具堆叠用注入测试目录验证，不新增正式工具。
- 测试覆盖不足容量不变、部分加入、两个容器独立、快照防外部修改、未知物品、非法数量和变更通知。
- 不修改旧库存计数，不同时维护两套游戏内库存；正式接入由路线第3项统一替换。
- 此单元没有发布动作、不更新版本号、不更新试玩包。下一单元为1B库存操作规则，必须先落实数量守恒测试再实现。
