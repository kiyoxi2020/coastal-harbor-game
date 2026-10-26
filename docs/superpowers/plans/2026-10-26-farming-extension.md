# 农事动作扩展与衔接 Implementation Plan

> **For agentic workers:** 使用 subagent-driven-development；用户要求多个子代理并行，目录责任隔离。现有人体规范与继续执行指令为本轮依据，不重复等待方案确认。

**Goal:** 交付现有西向农事样例的世界角色动作衔接试玩，并独立制作南向浇水、西向长袖锄地少量候选。

**Architecture:** 现有 catalog 只读加载保持；隔离trial新增显式开关，动作使用独立权威时间轴，整帧纹理按源密度显示；不接入真实农事事务。新美术仅写各自目录，不自动覆盖认可catalog。

**Tech Stack:** Godot 4 / GDScript、GPT imagegen、Python/Pillow登记。

## Global Constraints

遵循 docs/design/character-art-pipeline.md。已认可源图/纹理/时序不改。没有新制作的过渡姿态，使用明确的硬切入/结束回idle，视觉衔接仍须用户评审。测试存档和Godot日志仅/private/tmp/coastal-*。不提交、推送、导出或迁移生产人物。

### Task 1: 西向农事衔接（主代理）

Files: godot2d/dev/character_walk_trial.gd、character_walk_trial.tscn、tests/test_character_farming_transitions*.gd、新独立启动器及说明。
- [x] 失败测试：开关、能力拒绝、走跑进入、锁方向/移动、准确时长/帧边界、结束idle/恢复几何、换衣排队、失焦暂停、重置取消、面板独立。
- [x] 最小实现：--trial-farming-transitions，F/G/H进入water/hoe/harvest；仅已加载西A；不得自动转向或换衣伪造支持；动作过程中不重入；完成后idle，下一tick恢复输入。
- [x] 相关逻辑回归、原生键盘输入/截图/连续十循环，记录真实输入哈希。

### Task 2: 南向浇水候选（water_south，gpt-6.1-sol high）

Files: art/design/character-motion/adult-standard-v1/water-south-proof-v1/** only.
- [x] 参考同母版南idle及已认可西water，GPT ready/pour两姿态、源/prompt/登记、candidate、测量与结构验证。
- [x] 独立评审；未通过保持诊断，不扩方向，不冒称用户认可。

### Task 3: 西向长袖锄地候选（hoe_long_sleeve，gpt-6.1-sol high）

Files: art/design/character-motion/adult-standard-v1/hoe-west-long-sleeve-proof-v1/** only.
- [x] 参考认可hoe v4和B衣服，GPT ready/contact两姿态；完整源/提示词/整帧登记与测试。
- [x] 独立评审；完整图候选不等于分层兼容，不覆盖已认可A。

### Task 4: 集成与交接（主代理，子代理窄复查）
- [x] 实际产物和相关证据一致性；更新PROJECT_STATE/HANDOFF与进度记录，列出未验证及阻塞。最终复查P2已补采集后依赖契约/失效门禁：12回归通过、1140保守超集当前验证通过，gpt-6-astra high复审关闭，无剩余P1/P2。
