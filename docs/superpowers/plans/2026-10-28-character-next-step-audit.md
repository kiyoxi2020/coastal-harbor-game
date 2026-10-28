# 人物下一步：单一候选配方覆盖审计 Implementation Plan

> **For agentic workers:** 按任务逐项执行。项目默认主代理直接执行；本任务以只读核查和文档为主，不机械拆分子代理。实施需遵守项目AGENTS.md。

**Goal:** 在现有导航整理收尾后，明确一个候选生产配方的真实覆盖、缺口与首个可验收小样，避免继续整理目录而不推进人物能力。

**Architecture:** 以现有coverage、严格配方、模板姿态与真实部件引用为证据，只新增审计文档。保持当前模型、资源路径、生产角色和冻结基线不变；后续实现按审计发现单独计划。

**Tech Stack:** JSON资源合同、Python现有校验工具、Godot评审入口、Markdown报告、Paseo进度。

## Global Constraints

- 每次只处理一个明确、可验证的任务。本计划的可执行范围止于覆盖审计，不包含生图、全动作制作或生产迁移。
- 新人物配方统一使用coastal-character-construction-v1；不能另建构建器或以旧迁移配方冒充新合同。
- 不自动刷新runtime-baseline.json，不改旧认可，不覆盖源和已冻结输出。
- 保留工作区已有README及分析修改；未获要求不提交或推送。
- 单侧运动小样先于四向扩展，动态组合先于扩体型和扩款。

## 当前事实与优先级

2026-10-28核查时，Paseo“人物目录README与Agent阅读导航”中T02仍在Verify；art/characters、tools/characters及Godot试玩/测试README已有修改。本轮不接管或覆盖该任务，只追加计划分析。

现有coverage有69行有限能力记录。严格示例recipes/wardrobe-hoe-west/r002.json仅声明hoe-west和idle-west，slots为top03及原裤鞋，没有头发/帽子槽。头部四组样例和衣物五组样例不能合并宣称一个固定配方全动作齐全。

建议以成年母版、top03条纹上衣、原裤鞋为候选审计起点，评估栗色短发/草帽接入。这只是复用现有西锄成果的优先候选，不代表用户已经选定正式角色外观。任何生成或正式发布前，需落实实际角色需求。

## Task 1: 收尾依赖确认与审计范围冻结

**Files:**
- Read: art/characters/README.md、tools/characters/README.md。
- Read: godot2d/dev/characters/README.md、godot2d/tests/characters/README.md。
- Read: docs/design/character-art-pipeline.md。
- Create: docs/reviews/character-first-recipe-coverage-audit.md。

**Interfaces:** 输入现有导航与规范；输出审计文档中的候选范围、来源和验收维度，不新增运行API。

- [x] 确认导航任务实际完成状态；记录其链接和命令核验结果，不将本轮计划完成写成导航已验收。
- [x] 在审计文档写明候选衣装、头部四状态、成年母版和“候选、非生产批准”状态。
- [x] 定义24个基础动作/方向单元：idle、walk、run、hoe、water、harvest各四方向。每个单元再核bare/hair/hat/hair_hat；这96个审计单元不是96张图，也不是完整转换测试数。
- [x] 把进入/退出动作、动作中切换头部状态、匹配idle和足/握持/工具目标接触单列；不能用24单元存在代替过渡与接触验收。

**验收:** 候选范围足够具体；未把不同衣装的有限样例混算为完整同配方。

## Task 2: 逐单元核查真实依赖和缺口

**Files:**
- Read: art/characters/coverage.json。
- Read: art/characters/recipes/wardrobe-hoe-west/r002.json。
- Read: art/characters/templates/adult-standard-v1/template.json。
- Read: art/characters/templates/adult-standard-v1/motions/review-motion-v1/motion-set.json。
- Read: art/characters/reviews/wardrobe/catalog.json、art/characters/reviews/headwear/catalog.json。
- Read: 上述清单实际指向的parts、builds、sources和evidence文件；按依赖读取，不遍历所有图片。
- Modify: docs/reviews/character-first-recipe-coverage-audit.md。

**Interfaces:** 输入实际JSON引用及SHA；输出每个单元的证据表和分类型缺口。

- [x] 每行记录动作、方向、pose数量、头部状态、确切配方/manifest路径、来源与修订、输入SHA、匹配idle。
- [x] 分开记录完整穿衣参考、可分层部件、隐藏区、ownership、coverage、occlusion和注册；缺字段不能用相似图推定存在。
- [x] 分开标记源可用、适配可用、严格合同可表达、构建等价、原生验证、用户认可；认可必须追到具体版本及范围。
- [x] 将缺口分为四类：已有资源可复用；缺严格配方描述；缺统一合同接口；缺真实美术/视觉验收。无法判断列“待核实”及缺失证据，不冒充已通过。
- [x] 保留coverage.json原件；审计表只是带证据的报告，不成为第二套运行权威清单。

**验收:** 每个“可复用/已通过”都有确切引用；不能复用的原因明确到配方、动作、方向、pose和部件，审计未完成项显式列出。

## Task 3: 选择一个最小后续实施包并交接

**Files:**
- Modify: docs/reviews/character-first-recipe-coverage-audit.md。
- Modify: PROJECT_STATE.md、HANDOFF.md（仅在无其他任务同时写入时更新简短阶段记录）。

**Interfaces:** 输入缺口表；输出一个后续单任务建议，不在本审计中实施。

- [x] 首选评估“同一西向锄地+idle的四种头部状态进入严格配方”的小样；复用已认可西锄素材，先证明现有接口能否表达。
- [x] 若现有合同可表达，后续仅计划新配方、新输出及与旧样例逐RGBA/时序/注册对比；若不能表达，单独提出最小合同扩展与拒绝错误输入的测试，禁止临时旁路。
- [x] 为该小样明确原生验收：实际纹理、所有pose、连续动作、头部状态切换和返回idle；保留画布/显示尺度及原认可边界。技术等价不自动成为新用户认可。
- [x] 审计若只改文档，运行git diff --check及仓库门禁；人物相关交付按AGENTS执行下列测试，不用纯文档专用测试代替真实合同测试。

```sh
python3 -m unittest discover -s tools/characters/tests
python3 tools/characters/check.py
git diff --check
```

预期：人物单元测试全部通过（本轮之前基线75项），check输出passed=true，diff检查无格式错误。无资源/运行逻辑变化时不重采GPU；报告注明未做新原生/导出验证。

- [x] Paseo登记报告和缺口结论，仅结束本次任务；不自动开始生图、迁移或生产切换。

**验收:** 可据报告直接决定一个明确后续任务；没有“大批重做全部人物”或“先清空旧构建”式不具备边界的工作项。

## 后续阶段路线（不是本轮执行清单）

| 顺序 | 工作 | 进入条件 | 退出条件 |
|---|---|---|---|
| 1 | 当前导航收尾 | 已有文档变更 | 链接、命令、门禁核验完成 |
| 2 | 本计划：固定候选配方覆盖审计 | 明确候选及证据范围 | 完整缺口表和一个小样实施包 |
| 3 | 单侧严格配方/头部小样 | 接口和实际素材已核实 | 统一构建、等价/拒绝测试、动态与原生验收 |
| 4 | 同配方全动作四向补齐 | 单侧小样通过 | 真实适配、过渡、接触、原生和认可满足范围 |
| 5 | 按需求扩款或体型 | 第一配方完整 | 同一模型合同内适配，不开第二管线 |
| 6 | 统一生产发布与旧模型退出 | 发布合同及全部实际角色完成 | 主角和NPC一并切换，导出入口验证，旧依赖退出 |

物理压缩继续延后：重复文件上限仅约9.30MiB。旧输出待实际替代成功、引用迁出并完成评审后逐项退役；不能预先兑现278MiB的删除收益。非Git临时资料的持久保全独立处理，不与人体生产发布混为一项。

## 本轮计划分析的验证边界

本轮已核对当前工作区、Paseo状态、最新README、coverage与r002声明；只新增本计划。未执行覆盖审计本身、未新跑测试、未验证新原生或导出。上一轮75项通过不能作为未来实现的验收结果。既有导航修改由其原任务继续验收。


## 执行结果（2026-10-28）

本计划三项审计任务完成。交付：[覆盖审计报告](../../reviews/character-first-recipe-coverage-audit.md)、[逐格引用与探针](../../reviews/character-first-recipe-coverage-audit.json)、[独立复查](../../reviews/character-first-recipe-coverage-review.md)。衣装24格为2完整/3局部/19未登记；精确同候选的头部范围为8/96能力单元，涉及20个pose/state显示结果。旧语义重建20/20逐RGBA一致，合同表达及消费者接入留作下一独立小样任务。

75项测试、check.py、4369旧原生输入、10项认可绑定与附件760条文件引用记录核验通过；独立复查spec/evidence均PASS。未实施小样、未新采GPU或导出，未提交/推送。执行分工为主代理集成，两位gpt-6.1-sol/high分别核衣装和头部，gpt-6-astra/high独立复查。Paseo四步本轮跟踪，完成后关闭。
