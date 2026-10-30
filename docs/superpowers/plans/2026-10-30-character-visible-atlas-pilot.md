# 人物透明部件 A/B 小样 Implementation Plan

> **For agentic workers:** 按任务逐项执行。本项目默认由主代理直接执行；只有存在独立可交付任务且符合 AGENTS 委派条件时使用 subagent-driven-development，不为本次小样机械拆分代理。

**Goal:** 用现有人物和同一件上衣比较两种制作方法，验证单层透明部件能否以可接受成本适配连续动作，再决定默认制作方法。

**Architecture:** 固定同姿态人体和款式参考，分别制作直接透明部件与穿戴效果后提取部件。合格结果仅在统一坐标下 alpha-over 预览，通过单帧对比后再做单侧连续动作；不先实现完整新构建器。

**Tech Stack:** imagegen、现有图片检查工具、Python/Pillow（仅在用户明确允许用其处理图片后用于处理；否则遵守 imagegen 编辑规则）、现有 Godot 原生评审工具、Paseo Progress。

## Global Constraints

- 设计依据：`docs/superpowers/specs/2026-10-30-character-visible-atlas-design.md`。
- 每个部位一个可见层，每动作一张透明 RGBA 图集；不创建前后层或独立运行/构建 mask。
- north、west、south、east 按行，帧按列。同动作所有部件同画布、同格子、同坐标。
- 不覆盖旧素材、不修改 runtime-baseline，不提交、推送或切换生产。
- 源图、提示词与必要来源保留；不恢复大型历史媒体，不重新生成能直接复用的素材。
- 不用任意部件位移、缩放、复制其他人物脸手修正生成漂移。
- 本计划仅覆盖制作方式验证。完整管线实现以实验结果为输入另写计划，不预先锁定未验证方法。

## Task 1：盘点并固定同一份实验输入

**Files:**
- Read: `art/characters/recipes/adult-top03-full-hair-hat-body/r001.json`
- Read: `art/characters/recipes/adult-top03-full-hair-hat/r001.json`
- Read: 配方实际引用的 `sources/`、`parts/top/top03/` 与 `templates/adult-standard-v1/motions/review-motion-v1/` 文件
- Create: `art/characters/evidence/visible-atlas-pilot/input-inventory.json`
- Create: `art/characters/evidence/visible-atlas-pilot/comparison.md`

**交付接口：** inventory 记录每个选中输入的相对路径、SHA256、用途、尺寸、动作、方向、pose_id、是否可直接复用及理由；comparison 记录使用同一输入的 A/B 结果。

- [ ] 阅读 imagegen 技能并按其入口操作；开启独立 Progress 实验 run，记录制作与复核步骤。
- [ ] 从已有西向行走中选一帧手经过躯干的实际姿态，目视确认遮挡关系，不仅依赖 pose 名字选择。
- [ ] 固定该姿态的原画布、根锚点、top03 款式参考和现有合成帧作对照。
- [ ] 检查所选 body 是否带旧衣服。若带衣服，先基于同母版补齐该姿态的身体底图，目视确认人物身份、姿态、轮廓和锚点；不能用旧衣服遮住缺陷来评判新上衣。
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
- [ ] 检查该侧其余身体姿态，缺少可穿戴底图时按同一身份补齐后再制作上衣。
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
