# V5 Motion Drift Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修正 v5 walk/run 相对人物根点的异常横漂，交付原生窗口复验候选。

**Architecture:** 原始3列×2行源图按真实源网格登记。每行仅使用一个横向根点和固定列距，保持整帧、统一缩放、纵向登记、动作时序与原像素。利用 v4 同姿态的合法头部倾斜作为参考，独立检查躯干残差；不逐帧移部件或修改运行时偏移。

**Tech Stack:** 既有 pack_sources.py、construction-v1、Godot 原生观察器、Pillow 只读诊断。

## Global Constraints

- 冻结历史候选，新增 parts/body/adult-v5/r008、template-r005、recipes/builds-r005 与 review-only suite。
- 不更换游戏 v4，不改 idle 和六张农作图，不继承用户认可。
- 美术结果归档 parts；临时脚本仅在 /private/tmp。

### Task 1: 复现与根因

- [x] 测量旧候选四组异常横移；西walk17.5、东run38、南walk14、南run9 px。
- [x] 独立源图躯干检查确认足部摆动误导了固定列距；保持合法运动。
- [x] 保存旧候选失败诊断及统一行网格的新登记 r003。

### Task 2: 新候选

- [x] 使用 `python3 tools/characters/pack_sources.py pack art/characters/sources/adult-v5-style-consistency-r001/packing/r003.json --output art/characters/parts/body/adult-v5/r008` 生成新图集。
- [x] 克隆新模板和两套配方；使用 `python3 tools/characters/build.py build <r005.json> --output <new-r005>`，然后 verify。
- [x] 新 review suite 绑定实际构建及打包哈希。

### Task 3: 验证与交付

- [x] 固定根点逐帧测量，独立躯干观察与原生 poses/transitions 连续播放验证。
- [x] 执行 `python3 -m unittest discover -s tools/characters/tests` 与 `python3 tools/characters/check.py`。
- [x] 新归档、更新导航/PROJECT_STATE/HANDOFF，重开评审窗口；保留用户验收待定。
