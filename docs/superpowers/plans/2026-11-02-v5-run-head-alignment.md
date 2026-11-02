# V5 Run Head Alignment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** 用户要求东西向奔跑脑袋横向对齐，消除此前保留的姿态前倾横移。

**Architecture:** 基于r008原源图、同一整帧比例和画布，每姿态记录实测头部中心为完整帧的水平登记基准，与同向idle头中心对齐。每帧仅改变整帧source_root_px.x，身体、颈、头共同登记，不移动局部部件，不改变纵向弹跳。该显式用户要求替代上一轮保留v4头部横移的目标。

**Tech Stack:** 现有pack_sources.py、build.py、body_review.py、Godot原生观察器。

## Global Constraints

- 最终图像新增parts/body/adult-v5/r009；冻结r008及其归档不修改。
- 只改run-west/east十二帧水平登记，其他图像、Y、尺度、时序不变。
- 新模板v5-r006、配方/构建r006、独立review-only suite与archive-r006；不更改v4默认游戏。

### Task 1: 头部登记

- [x] 保存r008六帧头中心失败数据（西5px、东4.5px，要求范围≤0.5px）。
- [x] 新registration-r004/packing-r004逐帧记录源头中心、目标idle中心、整帧登记根点。
- [x] 运行pack_sources.py pack生成r009，检查新结果≤0.5px、无alpha裁切且所有其他帧RGBA保持。
- [x] 克隆template-r006、两套recipe/build-r006，执行build与verify及新suite preflight。

### Task 2: 验证

- [x] 原生poses观察器验证连续十循环、完整逐帧绑定，实际截图测量头部水平范围≤1屏幕px（2倍显示）；检查颈部、身体与循环接缝。
- [x] 原生96组切换验证；不把时钟/绑定通过当作视觉认可。
- [x] 执行python3 -m unittest discover -s tools/characters/tests，以及python3 tools/characters/check.py。

### Task 3: 归档和交付

- [x] 新parts archive、当前导航/PROJECT_STATE/HANDOFF/报告，保持历史回执绑定。
- [x] 验证v4运行与旧r008归档SHA，重开新suite评审窗口，Progress完成；用户视觉验收待定。
