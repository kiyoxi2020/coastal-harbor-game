# 库存操作规则：执行结果

状态：1B数据层已实现并验证；尚未接入游戏界面。

## 完成功能与接口

所有接口位于godot2d/scripts/inventory/inventory_container.gd。

| 接口 | 行为 |
| --- | --- |
| move_slot(source, destination) -> bool | 移入空格、不同物品交换、同类合并，超过堆叠上限的余数留原格 |
| split_stack(source, destination, amount) -> bool | 拆出部分数量到空格；无效数量、相同格、占用目标拒绝 |
| organize() -> bool | 全容器同类合并、按分类及ID稳定排序，空格排末尾；无变化返回false |
| discard(index, amount, confirmed=false) -> int | 默认拒绝，只有确认且物品允许时移除指定数量；工具和任务类别禁止 |
| transfer_to(target, index, amount) -> int | 按目标剩余容量部分转移，返回实际量；来源余量保留 |
| deposit_matching(target) -> int | 仅存入目标在操作开始时已有的种类，按来源槽位顺序执行 |

跨容器转移使用无通知的内部写入与扣减，在两个容器都完成后通知观察者；一键存同类也完成全批次再通知。无效槽位、空格、自转移、空目标和数量超限不修改库存。

确认参数是未来UI的接入契约，不代表丢弃确认窗口已经完成。移动/拆分选择期间的取消由后续UI处理，数据层只有确认操作才会被调用。

## 测试证据

新增godot2d/tests/test_inventory_operations.gd，先确认六个操作接口缺失导致测试退出1，再实现并重跑至通过。

- 物品目录：8项通过。
- 库存基础：17项通过。
- 库存操作：40项通过，含API检查及1,000次固定种子混合操作的数量守恒、槽位合法性检查。
- 原有赶海回归：49项通过。
- 合计114项检查通过；1,000次操作不另算1,000项独立断言。
- git diff --check通过。

运行命令示例（在项目根目录）：

```bash
/Applications/Godot.app/Contents/MacOS/Godot --headless --log-file /private/tmp/coastal-test_inventory_operations.log --path godot2d --script res://tests/test_inventory_operations.gd
```

Godot受限环境仍打印原有macOS系统证书读取警告，测试正常完成并退出0，无库存脚本解析错误。本次未做新UI实机验证，因为尚未新增UI。

## 交付边界与下一步

现有场景、窗口、镜头、E交互和运行中的旧计数背包均未改动。试玩包仍为v0.4.4；新数据层代码在当前工程中，阶段发布时才重打源码压缩包。

下一阶段为背包与个人手账界面：接入24格显示、详情、鼠标/键盘操作和菜单暂停，再将旧计数替换为唯一库存数据源。存档与标题页仍在后续阶段，不宣称已经实现。
