> 2026-10-31 用户追加决定：锄地可见动作直接保留人物＋锄头完整帧，按“把锄头加进去吧”制作；无工具身体源继续保留作换装参考，工具来源及遮挡仍独立记录，不要求先提取独立工具图层。此决定替代本任务原先“可见帧去工具”的做法，不产生严格接触或生产认可。

> 2026-11-01 用户Q21=A明确调整本阶段验收范围：已认可、可重建的像素身体 SOURCE完成归档并允许衣物A/B素材实验；精确支撑/滑步/机械握点/合法地面接触等严格物理项移至后续游戏/穿戴集成独立验证，仍标未通过，不授予生产或完整混搭认可。归档入口为`art/characters/parts/body/adult-v1/archive-r001.json`。此决定覆盖原来将这些严格物理项置于身体源归档之前的门槛，不覆盖后续生产/组合质量门禁。

# 人物全动作裸身体归档与透明部件 A/B 小样 Implementation Plan

> 现行决定（Q4=B）：用户已将身体底图改为完全不透明、无纹理的中性连体底衣，覆盖颈部至手腕/脚踝，手脚外露。下文历史“裸身体”目标由本决定替代；仍先完成身体底图的全动作四向并验收归档，再制作外层衣物。无袖、短裤及其他露肤款式不默认兼容，必须针对底衣覆盖重新验证，不能用局部擦除伪造露肤。
>
> 透明预览纠正：生成预览中的大圈棕灰雾为透明区RGB；抽查alpha=0且Godot浅色背景无可见大圈光晕。Q5已撤回，不清理这些透明像素，也不据此拒收源图。实际边缘仍按原生显示检查。


> **For agentic workers:** 按任务逐项执行。本项目默认由主代理直接执行；只有存在独立可交付任务且符合 AGENTS 委派条件时使用 subagent-driven-development，不为本次小样机械拆分代理。

**Goal:** 先完成同一母版全动作四向裸身体、验收并归档，再用归档人物和同一件上衣比较两种制作方法，验证单层透明部件能否以可接受成本适配连续动作，再决定默认制作方法。

**Architecture:** 全动作裸身体归档是后续部件制作的强制前置条件。归档后固定同姿态人体和款式参考，分别制作直接透明部件与穿戴效果后提取部件。合格结果仅在统一坐标下 alpha-over 预览，通过单帧对比后再做单侧连续动作；不先实现完整新构建器。

**Tech Stack:** imagegen、现有图片检查工具、Python/Pillow（仅在用户明确允许用其处理图片后用于处理；否则遵守 imagegen 编辑规则）、现有 Godot 原生评审工具、Paseo Progress。

## Global Constraints

- 设计依据：`docs/superpowers/specs/2026-10-30-character-visible-atlas-design.md`。
- 每个部位一个可见层，每动作一张透明 RGBA 图集；不创建前后层或独立运行/构建 mask。
- north、west、south、east 按行，帧按列。同动作所有部件同画布、同格子、同坐标。
- 不覆盖旧素材、不修改 runtime-baseline，不提交、推送或切换生产。
- 源图、提示词与必要来源保留；不恢复大型历史媒体，不重新生成能直接复用的素材。
- 不用任意部件位移、缩放、复制其他人物脸手修正生成漂移。
- 本计划覆盖完整裸身体制作/验收/归档，以及之后的部件制作方式验证。完整管线实现以实验结果为输入另写计划，不预先锁定未验证方法。

## Task 0：完成全动作四向裸身体、验收并归档

**Files:**
- Read: `art/characters/recipes/adult-top03-full-hair-hat-body/r001.json` 及其实际母版、姿态和来源引用
- Create: `art/characters/sources/visible-atlas-body-r001/`：采用的完整生成源图、提示词、来源元数据
- Create: `art/characters/parts/body/adult-v1/r001/`：逐帧透明身体及idle/walk/run/hoe/water/harvest六张动作图集
- Create: `art/characters/layouts/adult-v1-r001.json`：公共帧格、方向、时序、根锚点、尺度及必要事件
- Create: `art/characters/parts/body/adult-v1/r001/manifest.json`：合并输入清单、源/输出哈希与最终验收摘要
- Temporary: `/private/tmp/coastal-visible-atlas-body-r001/`：日志、原生连拍/录像、对比图及普通失败候选

**交付接口：** 后续Task 1只能消费归档清单绑定的同一身体版本及layout。以上为拟建路径，尚无资源；不因建目录或登记索引宣称身体完成。

- [ ] 盘点同一母版六动作×四朝向共24格的真实姿态、来源与缺口；当前84姿态为参考，不机械限定帧数。
- [ ] 阅读imagegen技能，先制作西向walk六帧裸身体；与旧四帧保持同72基速、0.75倍率和320ms原始周期，暂以53/54/53/53/54/53ms分配六帧。检查实际身体身份、轮廓、整帧注册、支撑及接缝，通过后再完成全部动作朝向。保留完整源及提示词，不能用旧穿衣body冒充裸身。
- [ ] 身体采用Q4=B中性不透明连体底衣、无发帽，保持同母版脸手与实际动作；工具及其遮挡独立记录，不混入身体像素。禁止任意挪缩部件或拼其他人物脸手。
- [ ] idle先1帧、run先6帧必要时8帧、hoe先6帧、water/harvest先4帧按实际过渡决定是否增至6帧；这只是试验起点，同动作四向按核定阶段保持一致。
- [ ] 固定公共layout；north/west/south/east按行、帧按列。同动作统一画布，记录实际尺寸与解码内存，不擅自缩小源图。
- [ ] 检查全部24格、所有有效帧的身份、身体连续性、alpha、原生尺度、动作/方向衔接与农事握持关系；用实际新身体完成Godot连续预览。若现有入口不支持，先定义最小接口改动和失败测试，不以旧人物试玩代替。
- [ ] 实际人物代码/资源改动须通过人物unittest与check.py；不改冻结基线，不用草稿冒充旧合同。新合同所需变更先明确范围后实现。
- [ ] 将通过的全套身体、来源和layout持久化，在最终manifest中写验收真实范围与未通过项，逐文件绑定路径、SHA256、尺寸、pose、时序及验收依赖，重读文件核验。
- [ ] 只有全部动作朝向完成、实际验收通过且归档可复核，才将Task 0标为done并启动Task 1。身体阶段有未通过项则停留于此，不并行制作上衣A/B或其他穿戴部件。

**验收：** 全部24动作方向裸身体可定位、可复现、可原生连续播放，归档输入输出及证据一致；技术通过、视觉认可与严格接触分别如实记录。既有Q2=B不自动给新身体授予认可，生产仍不切换。Godot日志与测试存档位于`/private/tmp/coastal-*`；临时录像不作为唯一归档。

## Task 1：盘点并固定同一份实验输入

**Files:**
- Read: `art/characters/recipes/adult-top03-full-hair-hat-body/r001.json`
- Read: `art/characters/recipes/adult-top03-full-hair-hat/r001.json`
- Read: 配方实际引用的 `sources/`、`parts/top/top03/` 与 `templates/adult-standard-v1/motions/review-motion-v1/` 文件
- Create: `art/characters/evidence/visible-atlas-pilot/input-inventory.json`
- Create: `art/characters/evidence/visible-atlas-pilot/comparison.md`

**前置条件：** Task 0全套裸身体已经验收归档；禁止只做一帧身体便开始A/B。

**交付接口：** inventory 记录每个选中输入的相对路径、SHA256、用途、尺寸、动作、方向、pose_id、是否可直接复用及理由；comparison 记录使用同一输入的 A/B 结果。

- [ ] 阅读 imagegen 技能并按其入口操作；开启独立 Progress 实验 run，记录制作与复核步骤。
- [ ] 从已有西向行走中选一帧手经过躯干的实际姿态，目视确认遮挡关系，不仅依赖 pose 名字选择。
- [ ] 固定该姿态的原画布、根锚点、top03 款式参考和现有合成帧作对照。
- [ ] 从Task 0归档选择身体并复核SHA、姿态、轮廓和锚点；若仍带旧衣服或归档无效，返回Task 0修订并重新验收归档，不能在A/B阶段临时补一帧后继续。
- [ ] 若身体底图不合格，记录具体问题并先解决，A/B 两组不能使用不同身体。
- [ ] 写输入清单；不把整库重复复制到实验目录。

**验收：** 两组使用完全相同的身体、款式和画布；有效输入可定位且哈希可核对。此任务不承诺现有穿衣底图能直接变成裸身。

## Task 2：同一姿态制作 A/B 两组

**Files:**
- Create: `art/characters/sources/visible-atlas-pilot/` 下的实际生成源图、提示词和返回元数据
- Create: `art/characters/evidence/visible-atlas-pilot/comparison.md` 的 A/B 记录
- 临时叠加图位于 `/private/tmp/coastal-visible-atlas-pilot/`

**交付接口：** 每组得到一张与输入画布同尺寸的可见上衣 RGBA，以及其实际来源和制作记录；失败输出不标记为可用部件。

- [ ] A 组提供固定人体及 top03 参考，要求仅输出当前姿态可见上衣、透明背景、不包含皮肤、脸手、工具，保持原坐标与轮廓。
- [ ] 原位置叠加检查 A；记录每次生成、实际提示词、修整操作、人工操作时间和等待时间。
- [ ] B 组使用相同输入，先生成穿戴 top03 的完整效果，再提取可见上衣。不得用像素相减冒充语义提取。
- [ ] 用与 A 完全相同的条件检查 B，并记录同样的成本数据。
- [ ] 每组遇相同问题连续两次未改善，停止重复同思路，记录原因；不自动无限生成。

**验收：** 原尺寸、同位置下检查肩、领口、袖口、遮挡缺口、透明边缘、皮肤混入、原身体是否被衣服以外像素改变。必须所有关键项合格才比较制作成本；两组都不合格时明确失败，不选一个相对较好但不合格的方案。

## Task 3：暂选方式的连续动作验证

**Files:**
- Create: `art/characters/evidence/visible-atlas-pilot/sequence-review.json`
- 临时图集及原生输出位于 `/private/tmp/coastal-visible-atlas-pilot/`
- Read: `godot2d/dev/characters/README.md`、`godot2d/tests/characters/README.md`

**交付接口：** 西向行走完整帧序列及真实连续预览结论，绑定每帧输入、输出和时序。

- [ ] 对合格候选按实际修整总成本暂选方式，不把单帧结论扩为全部部件通用结论。
- [ ] 使用归档中该侧完整身体姿态；缺帧或身体缺陷意味着Task 0前置条件失效，先回到身体阶段修订、验收并归档，再继续上衣。
- [ ] 补齐连续姿态的上衣，只复用确实同形同坐标的素材；不为保持复用率强行移动或缩放。
- [ ] 按已选动作实际帧数与时间顺序排列，对每帧进行相同固定顺序叠加检查。
- [ ] 使用现有原生评审能力检查循环及进入/退出动作；命令带 `--log-file /private/tmp/coastal-visible-atlas-pilot.log`，不访问玩家存档。现有入口若不能消费小样，先记录缺失接口，再单独定义最小工具改动及测试，不能把旧资源的演示冒充新小样。
- [ ] 检查花纹和袖长是否跳变、接缝是否闪动、手前景缺口是否正确。保持画面原生显示尺寸检查。

**验收：** 单帧质量与连续动画都通过；失败则保留暂选状态，修正原因或回到另一候选，不能批量扩展四向。

## Task 4：记录选型及旧资源迁移范围

**Files:**
- Modify: `docs/superpowers/specs/2026-10-30-character-visible-atlas-design.md`
- Modify: `art/characters/evidence/visible-atlas-pilot/comparison.md`
- Modify: `PROJECT_STATE.md`、`HANDOFF.md` 顶部阶段说明

- [ ] 写明实际 A/B 成本、质量结果、连续动作结果和最终默认方法；不使用估计成功率冒充测量。
- [ ] 分别列出现有可原样复用、需一次提取、需补画、仅作参考的资源；未知项保留为未验证，不先删除。
- [ ] 限定结论到实际测试的部件/姿态。头发等其他类别先做最小代表样本，再扩大适用范围。
- [ ] 根据实际图集尺寸和结果确定后续完整管线实现计划的输入；列明唯一制作规范、构建入口、加载器和门禁的受影响范围，不在本轮顺手重写。
- [ ] 保留必要小样与轻量结论；清理明确不再需要的临时展示，不删除唯一源图。
- [ ] 更新 Progress。成功则以实验选型完成结项；有质量阻塞则如实记录，不宣称新人物已接入生产。

**验证边界：** 本计划编写阶段只检查文档。执行中如修改人物代码或资源，按 AGENTS 完成 `python3 -m unittest discover -s tools/characters/tests` 与 `python3 tools/characters/check.py`；新草稿不能伪装成旧严格配方以绕过门禁。原生与视觉验证按实际修改范围执行，不能由单元测试替代。
