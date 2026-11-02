# V5 Other Action Stability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** 延续用户认可的东西向run头部横向稳定效果，检查并修正其他动作。

**Architecture:** 其余四向walk及南北run采用同向idle头中心整帧登记；已认可东西run和idle保持RGBA。农作需区分源漂移与真实弯腰前倾，用户可选择保留前倾或同样锁头，不从位移幅度独自判断错误。不改局部部件、比例、Y弹跳、时序或游戏运行配置。

**Tech Stack:** 现有pack_sources/build/body_review，Godot原生观察器，Pillow诊断。

## Global Constraints

- 新最终图像parts/body/adult-v5/r010，旧r009/归档r006保持冻结。
- 单一统一模型新template-v5-r007、两套recipe/build-r007、独立review suite；仅review，不替换v4。
- 图像所有整帧位移须绑定实测来源、pose和目的；农作保留工具与身体整体关系，不拆头修图。

### Task 1

- [x] 复现其余walk/run横移0–3.5px，农作头位移4–26px与弯腰姿态相关。
- [x] 对照v4脚部稳定位置，确认农作处理方式，保存逐帧诊断。

### Task 2

- [x] 新registration-r005/packing-r005与r010，记录整帧登记依据，确认其他批准图像保持。
- [x] 克隆新模板/配方，严格build+verify，suite preflight。

### Task 3

- [x] 原生姿态/十循环和96切换；实际窗口几何复测与农作前倾、脚底、工具连接目视检查。
- [x] 执行python3 -m unittest discover -s tools/characters/tests与python3 tools/characters/check.py。
- [x] 归档新制品，更新导航和状态，复核旧档及v4SHA；打开新评审窗口供统一验收。
