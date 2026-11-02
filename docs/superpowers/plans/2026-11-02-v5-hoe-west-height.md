# V5 West Hoe Height Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** 修正用户反馈的西向锄地人物变高，同时保持已确认画风。

**Architecture:** 实测r011西锄最高145px、idle137px。两次Imagegen微调膝髋改变蹲姿过大，拒绝。最终以137/145对整组body/visible高分辨率源图统一校准，保持原姿态及内部比例，支撑地标重登记；不是局部缩放或将贴图向下挪。其他152源姿态RGBA保持。

**Tech Stack:** 内置Imagegen、pack_sources、construction-v1、Godot原生观察器。

## Global Constraints

- 不覆r011/archive-r008，新最终图片r012，新template-v5-r009/recipe-build-r009。
- 黑色细线、桃色皮肤、小眼睛、方向/握持/工具/pose IDs/duration保持；只修西向hoe十二源帧。
- 不单独缩头、压腿或将整幅贴图往下挪；头部与完整源表一起按同倍率校准，不声称头部像素大小完全不变。

- [x] 保存idle137px与西锄143–145px失败诊断，并确认头部大小一致。
- [x] Imagegen实验保留为未选记录；同倍率比较后选择完整源表统一密度校准。
- [x] 整帧登记→parts r012，旧152姿态RGBA保持，严格build/verify与suite preflight。
- [x] 原生姿态/十循环、96切换，人物490测试与check.py。
- [x] 新SHA归档及导航/状态，重开评审demo供复验；保留用户验收待定。
