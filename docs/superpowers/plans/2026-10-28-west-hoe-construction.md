# 西锄四状态严格构建与原生小样 Implementation Plan

> **For agentic workers:** 使用subagent-driven-development，按文件责任并行Python合同与Godot消费者；主代理集成/原生/交接。已获用户继续实施授权，不重复确认，不提交/推送。

**Goal:** 通过统一build.py构建四固定头部配方，20帧等价并在现行Godot评审连续播放。

**Architecture:** 同kind schema2引用schema1 base_recipe，先重建衣装后在目标坐标作明确头部合成。保持现行build manifest字段；新review suite复用现有headwear trial/时间轴。

**Tech Stack:** Python/Pillow、严格JSON合同、Godot 4 GDScript、unittest、原生GPU采集、Paseo。

## Global Constraints

- 设计见 `docs/superpowers/specs/2026-10-28-west-hoe-construction-design.md`；仅hoe-west四pose和idle-west一pose、四头状态。
- `coastal-character-construction-v1`唯一新配方入口，旧schema1语义不改；禁止子部件挪缩、另写批次合成器、伪造mask或source。
- 所有来源/注册/ownership、key2多来源选择必须绑定真实SHA；输出始终review-only，不放宽runtime-baseline。
- 保留源、旧sample/catalog/acceptance、已有用户修改；不采纳旧回执作为新native验收。
- Godot日志统一/private/tmp/coastal-*.log；测试存档/采集只在/private/tmp/coastal-*。

## Task 1: 固定schema2及消费者接口

Files: 上述design文档、本计划；读取build.py/build_contract.py/check.py与现有headwear loader/trial。

- [x] 明确四固定配方、base_recipe重建与目标坐标阶段；对比通用DAG及复制成品方案，采用前者的有界父配方组合。
- [x] 固定suite为kind coastal-character-construction-review-v1/schema1/resource_root art/characters/scope review-only/sample_id hoe-west/states四键，每值manifest仓库相对路径+SHA。
- [x] 固定manifest沿用现有字段，消费者读取recipe2.head_state/base_recipe，从父配方clips取得几何/时序。
- [x] 将精确JSON输入合同交给两位实施代理；各自只写分配文件。

## Task 2: 严格组合合同与真实反例（Python代理）

Files: tools/characters/build.py、build_contract.py；可新增composition_contract.py；tools/characters/tests/test_composition_contract.py。

- [x] 写合成小图失败测试：先重建父配方、binary RGBA replace保留软边、supported-alpha-stack在支撑外保留RGBA、key2双来源二值选择；先运行看到当前schema2拒绝/尚无功能的失败。
- [x] 加拒绝例：未知字段、state/槽不符、base循环或schema2嵌套、错base SHA、错pose/时长、不同画布、部件偏移/缩放、缺源/ownership/registration、错选择/派生图、诊断mask伪作覆盖、构建依赖篡改。
- [x] 实现同入口schema2验证与render，base依赖合入manifest inputs，新增代码纳入engine_identity；保持旧验证严格，不新增baseline例外。
- [x] 运行定点测试及旧构建合同回归。报告RED/GREEN命令、结果与字段示例。

## Task 3: 现有评审接入与拒绝例（Godot代理，并行Task 2）

Files: 新character_construction_samples.gd；headwear_samples.gd仅kind分派；headwear_trial.gd仅参数/选择范围；新test_character_construction_loader/actual/native.gd及UID。

- [x] 新合成fixture测试先红；覆盖scope/状态/parent/pose/时长/几何、source/engine/PNG/manifest篡改、路径和symlink；失败清空。
- [x] strict loader核suite、四manifest、recipe2/head_state和同一base_recipe、当前所有inputs/engine、输出PNG/RGBA/SHA、父pose顺序/时长与几何，输出原head样例结构。
- [x] 现有trial支持新suite override并仅显示实际样例，默认西锄；旧四样例不变。
- [x] 实际加载测试使用预定suite路径；native fixture复用现有inspect_head，单样例四state、明暗五pose、每state十面板循环、世界四pose、切换时钟/返回idle，增加原始binary64时序字段。
- [x] 运行新synthetic和旧相关加载回归，记录RED/GREEN；GPU主代理执行。

## Task 4: 配方、构建与统一launcher（主代理）

Files: art/characters/recipes/headwear-hoe-west-{bare,hair,hat,hair-hat}/r001.json；四新build目录；reviews/headwear-construction/review.json；tools/characters/review.py及其必要测试。

- [x] 根据已冻结旧sample生成四份schema2 JSON，明确所有source bundle、registration和ownership，不在美术库放生成脚本；key2从两源归属重建并验证。
- [x] 用统一命令逐一build到全新库内目录（构建ID同配方ID加-r001），逐一verify；任何失败先查原因，不能覆盖旧目录或刷新baseline。
- [x] 对四build的20输出与旧sample逐RGBA、pose顺序、duration、geometry核对，保留完整证据。
- [x] 给review.py增加headwear-construction suite，启动前verify四构建；dry-run也完成输入核验。现行suite入口保持。
- [x] 执行必要人物单元测试、check.py及Godot新actual/loader与相关旧回归。

```sh
python3 -m unittest discover -s tools/characters/tests
python3 tools/characters/check.py
python3 tools/characters/review.py headwear-construction --dry-run
/Applications/Godot.app/Contents/MacOS/Godot --headless --path godot2d --log-file /private/tmp/coastal-construction-actual.log --script res://tests/characters/test_character_construction_actual.gd
```

预期全部通过，20帧完全等价，review-only、生产关闭。输入或engine再变动后只重建本轮新输出，使用新build ID，不覆盖冻结旧资料。

## Task 5: 新原生证据与独立交付（主代理）

Files: tools/characters/construction_native.py及tests/test_construction_native.py；art/characters/evidence/construction-headwear-west-v1/摘要/回执/代表图；相关README、PROJECT_STATE.md、HANDOFF.md。

- [x] 对snapshot/validate先写失败测试：缺循环/pose/state、错时序、错输入/工具/PNG、输出覆盖不足、路径/别名覆盖保护；验证失败不得写通过回执。
- [x] snapshot绑定当前suite/四manifest、source/engine、实际Godot链与fixture；GPU后核对所有冻结输入不变、真实render backend、四state/全部pose、至少十完整循环、原始binary64时序与PNG全覆盖。
- [x] Godot GPU命令使用新的/private/tmp/coastal-* evidence路径，禁止覆盖；画面检查明暗面板与世界第三帧及连续样本。fixture不是OS输入/WM焦点验收。
- [x] 独立审查完整diff、字段合同、真实20等价、依赖失效和native证据；修复重要问题并定点复验。
- [x] 保存轻量证据及必要代表图，报告原始采集位置、scope/未测项；更新文档、交接和Paseo。原认可范围不扩。
- [x] 到小样完成条件停止，不自动扩四向/其他动作/生产切换；不提交或推送。


## 实施完成（2026-10-29）

交付：[西锄统一构建小样与证据](../../../art/characters/evidence/construction-headwear-west-v1/README.md)、[独立验收](../../reviews/2026-10-29-west-hoe-construction-review.md)。schema2及四固定状态配方由唯一build.py入口构建/verify，20/20逐RGBA等价，既有Godot评审已消费真实四build。

114人物Python测试、check.py（strict5/build4/legacy9）、Godot新synthetic134/实际48及旧loader34/actual98/trial90通过。Apple M4/OpenGL原生120检查、3307时序样本、215PNG与4422输入闭包通过；四state各十面板循环、世界四pose、切换时钟/idle通过。主代理目视五张代表图，未扩用户认可。迁移257帧和静态60候选检查通过。

原始采集/private/tmp/coastal-west-hoe-construction-native-01保留，不假称Git已归档；库内留合同/回执/摘要及五图。旧原生合同两份dev脚本受影响已另记，不把新回执扩到其他样例。新试玩已用review.py headwear-construction打开。未做OS输入/WM、严格接触、跨平台/导出或生产切换，未提交/推送。下一独立任务再选同配方能力扩展，不在本轮自动执行。
