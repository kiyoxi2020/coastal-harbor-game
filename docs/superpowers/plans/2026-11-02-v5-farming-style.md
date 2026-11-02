# V5 Farming Style Consistency Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** 补齐原请求的农作画风统一：锄地、浇水、采收与已认可idle同倍率下的线宽、像素颗粒、眼部尺寸及中性桃色皮肤一致。

**Architecture:** 沿已批准的idle画风合同，由内置imagegen重绘完整姿态；先西向锄地小样，再四向农作body/visible共112源姿态。保持r010已确认前倾、脚部占地关系、pose顺序、时序与工具动作。整帧注册仅校正生图源网格与统一密度，禁止拼旧脸手、局部挪缩或程序调色。制作规范单侧小样门禁先自验后扩量；用户已授权全套并要求先自验后统一验收，无须重复审批原设计。

**Tech Stack:** 内置image_gen、现有reference_sheet/pack_sources/build/body_review和Godot原生观察器。

## Global Constraints

- idle/walk/run认可候选RGBA保持，不再扩大为位置修正任务。
- 农作保留正常前倾，仅整帧注册；画风修正不锁死农作头部。
- 新原图、提示词、引用SHA与元数据留sources；最终图片实际放parts/body/adult-v5新revision；旧冻结依赖不变。
- 新严格模板、配方、build及review-only suite；默认游戏v4和生产基线保持。

### Task 1

- [x] 绑定idle master及同倍率工具姿态参考，生成西向锄地风格小样。
- [x] 对比边缘线宽、眼黑块、肤色、像素粒度和运动结构，必要时只改失败项后重验。

### Task 2

- [x] Imagegen四向hoe/water/harvest工具表；依其同姿态生成无工具完整身体表。
- [x] 逐表确认帧数量、动作方向、脸手体型、工具握持、透明alpha与画风。

### Task 3

- [x] 全身统一密度和真实姿态/源网格注册，新typed packing计划→新parts实际PNG。
- [x] 新统一模型模板、construction-v1两套配方与build/verify，suite preflight。

### Task 4

- [x] 原生动态/像素与切换自验，确认idle风格对比及工具运动；必要时退回源图。
- [x] 执行python3 -m unittest discover -s tools/characters/tests及python3 tools/characters/check.py。
- [x] SHA归档与文档状态纠正，启动新评审窗口，用户统一验收待定。
