# 单侧运动工具 Implementation Plan

> **For agentic workers:** 当前工具子任务按已授权的 Inline Execution 执行，不嵌套委派，不提交。

**Goal:** 为西向四帧 A/B 小样提供可追溯离线合成和独立原生评审，工具通过不等于美术通过。

**Architecture:** Pillow 仅做整数平移、目标层 alpha mask 和后到前合成；严格检查 motion.json，输出 baked 和内容哈希清单。独立 Godot SceneTree 读取烘焙清单，一份时钟驱动 A/B 与两种显示尺度；自动原生截图和连续循环记录保存到测试临时目录。

**Tech Stack:** Python 3 + Pillow、unittest、Godot 4。

## Global Constraints

- 只创建本目录 tools/ 与 tools-plan.md，不碰生产 Godot 工程，不生成正式美术。
- 输入固定四姿态 walk_w_0..3，画布 512×768，根点 [256,708]，display_scale=.2371134；源可小于画布，整数 offset，L mask 白色隐藏。
- 不缩放部件、不推断隐藏像素、不将文件数当姿态数；mask只作用其声明层。
- 原生 Godot 执行必须 require_escalated，日志 /private/tmp/coastal-*.log；测试及截图 /private/tmp/coastal-*。

### Task 1: compositor

**Files:** `tools/compose.py`, `tools/test_compose.py`。
**Consumes:** motion.json 及其相对 PNG sources/masks。
**Produces:** `compose(motion_path, output_dir=None) -> dict`；默认根目录 baked/{A,B}_{0..3}.png 与 export-manifest.json。

- [x] 先编写真实像素fixture测试：目标层mask、前景手不删、共享源、透明边缘及导出哈希；缺帧/未知姿态/无资源/出界/非法时长缩放拒绝。
- [x] 运行 `python3 -m unittest discover -s tools -p 'test_*.py' -v`，确认因模块尚未实现而失败。
- [x] 实现严格合同与最小合成；同命令通过。

### Task 2: native review

**Files:** `tools/project.godot`, `tools/review.gd`, `tools/review.tscn`, `tools/test_timeline.gd`, `tools/timeline.gd`, `tools/make_fixture.py`, `tools/README.md`。
**Consumes:** baked/export-manifest.json（绝对路径）；可选 --capture-dir=/private/tmp/coastal-*。
**Produces:** 同时钟 A/B、统一 display_scale 与 2x 放大、空格暂停/方向键单步/B换底色；四帧×两底色截图、至少10循环的连续原生PNG与逐截图实测时间/姿态JSON。

- [x] 写时间轴失败测试，验证四帧边界、循环、低帧率跳跃及非等长时长；先运行再最小实现。
- [ ] 固定UI存场景，行为在SceneTree；无玩家存档读写。
- [ ] 用 `/private/tmp/coastal-motion-tools-fixture` 中非美术像素fixture做 headless时间轴与原生截图验证；检查记录实际帧/时间、两配方同步和两种底色。
- [ ] README记录完整命令、metadata合同及证据局限；通知主代理固定接口。

## Result

2026-10-23提交核对：compose.py的15项测试通过；timeline.gd时间边界、变长帧和循环计数通过headless检查。review.gd、review.tscn、make_fixture.py尚未实现，未进行原生截图/录像验证。README由主代理补齐真实状态。实际GPT动态资源、运动合同及用户视觉验收仍未完成。此前已勾选的原生完成记录与磁盘不符，现纠正。

分工：gpt-6.1-sol high负责独立工具子任务；主代理在整理提交时核对文件并重跑现有测试，未继续扩展工具。
