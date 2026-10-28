# 人物测试与原生采集导航

这里保存人物Godot回归和采集入口。先读 [人物库README](../../../art/characters/README.md)理解当前资源范围，再按实际改动选择测试；不要按文件数量或名字相似判定可以删除。

## 测试分组

| 类型 | 代表入口 | 能证明什么 |
|---|---|---|
| 实际资源加载 | [test_character_layout_actual.gd](test_character_layout_actual.gd)、[test_character_headwear_actual.gd](test_character_headwear_actual.gd)、[test_character_wardrobe_actual.gd](test_character_wardrobe_actual.gd)、[test_character_farming_catalog_actual.gd](test_character_farming_catalog_actual.gd) | 当前真实纹理/配置/哈希及已实现范围能加载；不等于视觉或动态组合认可 |
| 路径和拒绝反例 | [test_character_layout_roots.gd](test_character_layout_roots.gd)、[test_character_layout_headwear.gd](test_character_layout_headwear.gd)、[test_character_layout_farming.gd](test_character_layout_farming.gd) | 非法root、越界、错SHA、独立parent路径及失败恢复 |
| 隔离合成fixture | [character_fixture_library.gd](character_fixture_library.gd)、各walk/run/farming/wardrobe/headwear逻辑测试 | 用临时程序生成测试小图和清单验证逻辑；不是正式美术或新的模型体系 |
| 时钟与交互逻辑 | 各trial、review、transitions、diagnostics测试 | 动作时序、状态切换及面板合同，按对应脚本的明确断言解释 |
| 迁移整库GPU核验 | [test_character_layout_native.gd](test_character_layout_native.gd) | 固定迁移范围的真实GPU板图、循环与世界报告，需配合Python原生合同 |
| 专项原生/采集 | 各 `*_native.gd`、`capture_character_*.gd` | 各自特定修订/动作的采集与断言；旧范围不自动适用于新修订 |

代码中的旧路径/无root/破坏数据可能是故意构造的失败反例，不是活动资源引用。部分专项采集依赖历史合同或前置输入，不能把全部脚本无参数串行启动当“完整验收”。

## 常用命令

从仓库根运行基础实际资源回归：

```sh
/Applications/Godot.app/Contents/MacOS/Godot --headless --path godot2d --log-file /private/tmp/coastal-character-layout-actual.log --script res://tests/characters/test_character_layout_actual.gd
```

Python构建合同、仓库门禁和真实RGBA重建测试位于 [tools/characters/tests](../../../tools/characters/tests/)，日常检查为：

```sh
python3 -m unittest discover -s tools/characters/tests
python3 tools/characters/check.py
```

Godot命令始终传 `/private/tmp/coastal-*.log`；测试存档/fixture只用 `/private/tmp/coastal-*`，不读写玩家真实存档。不为文档变化机械重跑整套GPU测试。

## 原生证据的前置条件

原生采集必须使用图形环境；headless不能作为GPU画面验收。先核对具体fixture需要的输入、输出目录及参数，再用 [native_contract.py](../../../tools/characters/native_contract.py)建立输入快照，采集后严格验证覆盖、时序和输出。不要覆盖已有回执或重写旧原生报告。

现有layout-native回执只覆盖当时冻结的迁移输入、129张PNG、65个面板各一轮与16次世界报告。它不证明新构建、十循环、OS输入/WM焦点、严格接触、导出或用户认可。其他专项脚本有自己的范围；不能把各报告数字相加当统一发布通过。

改纹理、pose、mask、时长、层序、配方或合成器时，按实际依赖判断旧证据是否失效；需要新原生验证时建立新证据目录。用户认可另按确切版本与范围登记，技术测试不能代签。

## 严格构建四状态小样测试

- `test_character_construction_loader.gd`：临时合成fixture验证strict suite、槽/层/模板、工具和来源/output篡改、路径以及原生采集目录保护。
- `test_character_construction_actual.gd`：读取真实四build/suite，检查实际加载、状态切换时钟/位置、所有姿态和匹配idle；依赖缺失明确失败。
- `test_character_construction_native.gd`：复用现有headwear inspect_head执行四state明暗五pose、每state十面板循环、世界四pose与live评审切换及结束idle。运行前须由Python construction_native.py生成全新input-contract；已有任何输出或链接目录拒绝。

该fixture保存binary64时序与逐PNG哈希，配合专用Pythonvalidator核闭包、覆盖与采样PNG关联。它使用fixture信号/逻辑输入，不是系统键鼠/WM焦点或生产换装验收；新证据不覆盖旧回执。
