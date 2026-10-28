# 西向锄地四头部状态统一构建小样：最终独立验收

日期：2026-10-29（Asia/Shanghai）。

Spec compliance：PASS。

Quality / 证据完整性：PASS（限定本次review-only西锄四pose＋匹配idle、四固定头状态）。

Critical：无。Important：无未解决项。Minor：无。

此前mid-review.md、python-review.md的全部Important与尾项已关闭；本次重点核实际集成、当前依赖及原生证据，未重复全量代码调查或重跑测试/GPU。可按已批准小样范围交付并结束任务，不自动扩动作、方向、衣款或生产发布。

## 实际构建与消费者接口

- `art/characters/reviews/headwear-construction/review.json`精确绑定bare/hair/hat/hair_hat四manifest，scope=review-only、sample_id=hoe-west。四manifest当前SHA同时与suite、native input-contract、report及summary匹配。
- 四真实配方均为schema2，head_state与各suite键一致，base均精确引用未改变的`recipes/wardrobe-hoe-west/r002.json`及其SHA。manifest.recipe、recipe inputs、base绑定及artifact_digest一致；输出status=review-only、release_eligible=false。
- 每build确有5输出，inputs分别105/124/138/172。逐项只读核当前inputs、三engine文件和所有输出SHA，全部匹配。不存在以临时build作为正式输入或绕过统一构建器的迹象。
- 显式base层序与Godot实际接口一致：bare=[base]、hair=[base,hair]、hat=[far_hat,base,near_hat]、hair_hat=[far_hat,base,under_hat_hair,near_hat]。schema2允许空authoring_inputs但仍强制Array和逐项ref绑定，实际依赖由base/layers声明；修复有synthetic RED/GREEN且未放宽schema1 base规则。
- 几何/时序全部继承同base：hoe画布1536×1792，四pose时长180/220/140/260ms；idle画布512×768、200ms。没有对目标头层再施加源整帧平移。
- 已核最终真实加载日志`/private/tmp/coastal-construction-actual-integrated.log`：48 checks passed=true。`implementation/actual.log`是保留的早期RED，不误作最终结果。Godot134 synthetic及既有链回归由前期闭环与当前报告支持。

## 等价证据

`equivalence.json`含20个唯一state/pose条目，每状态5项，覆盖四hoe pose与idle，无重复抵数。每条输出、旧参照的当前文件SHA与记录一致，且两边文件SHA完全相同，足以支持逐RGBA（包括透明RGB）等价；all_equal=true与实际文件证据一致。suite SHA与当前suite匹配。

本次没有通过“构建数量”替代像素结论，也未将完全等价扩写成新的用户认可。

## 原生证据闭包与真实覆盖

- 库内input-contract与raw原件逐字节同SHA；receipt绑定的report SHA与raw/report.json一致；report-summary绑定的receipt/contract SHA一致。validator SHA为当前`construction_native.py`。
- 4422个冻结输入全部只读哈希核对，无缺失/变化，包含当前suite、四manifest、实际输出、源/注册/mask、三Python引擎及当前Godot链/fixture。
- raw实际215个PNG与report/receipt的output_hashes精确对应；215项当前SHA全部匹配。五代表PNG与raw原图、summary/visual-review所列SHA一致。report output_hashes与receipt相同。
- 原生report有120 checks，全部true；3307时序行，renderer为macOS / gl_compatibility / Apple M4。原生日志也明确OpenGL API 4.1、Apple M4，且末行checks=120 passed=true。

| state | binary64时序行 | 最终累计循环 | 时序关联PNG | 相邻关联截图最大间隔 |
|---|---:|---:|---:|---:|
| bare | 832 | 10.008903 | 38 | 218ms |
| hair | 825 | 10.007362 | 38 | 218ms |
| hat | 823 | 10.002628 | 37 | 218ms |
| hair_hat | 827 | 10.009230 | 37 | 218ms |

四state均实际出现pose 0/1/2/3，累计时间均超过10个完整800ms周期。所有时序关联capture都存在于PNG hashes与captures；400ms间隔门限未被触发。明暗五视图面板、world四pose/state、live头态切换保持动作时钟及结束idle均有fixture检查与对应图像；该证明仍属于隔离评审程序，不声称OS输入/WM焦点或严格足/握持/目标接触测量。

已目视查看保存的hair_hat明板和key2世界图：在所示原生尺度下未见明显新增发帽接缝、耳后缺口或身体/工具脱离问题；该抽查支持主代理代表图观察，不扩展为全帧视觉认可或用户认可。时序PNG不是全帧率连续录像，summary已明确说明。

## 验证日志与历史证据影响

- 已实读full-python-final.log：114 tests，32.293s，OK。主代理已完成check（strict_recipes=5、strict_builds=4）与四CLI build/verify；本复查只核其产物依赖/身份和输出，没有重复执行这些命令。
- 旧layout-native冻结输入与新已核输入逐名对照，仅`character_headwear_samples.gd`和`character_headwear_trial.gd`两个旧绑定文件改变；与prior-evidence-impact.json完全一致。旧回执保持历史，不冒充当前所有旧样例的新原生通过。
- 本次没有放宽runtime-baseline、改旧sample/catalog/acceptance或切换生产角色；当前新证据只认证west-hoe construction suite。

## 留存与未声明范围

轻量contract/receipt/summary/equivalence/visual-review/impact及五代表图位于`art/characters/evidence/construction-headwear-west-v1/`。完整原始report及215PNG仍在`/private/tmp/coastal-west-hoe-construction-native-01`，raw_capture_git_backed=false；暂存不等于已Git归档，不能据此删除raw。

没有新用户认可、OS键鼠/WM焦点、严格接触、跨平台、导出或生产发布结论。其他动作/方向、任意衣型隐藏区与全角色能力不在本次范围。本小样必要实现与验证已经达到约定出口，可交付即止。

本复查只写本报告，未修改代码或资料、未派子代理、未重跑114测试或GPU。

## 验收快照

- `art/characters/reviews/headwear-construction/review.json` SHA256 `f2a4cd127bf148070d860bcad0d14fbc30bdbe83be8a5a1da3f5c2568d04482d`
- `art/characters/evidence/construction-headwear-west-v1/equivalence.json` SHA256 `77765f847bebdd69dcd71b18704ce923e0c3357747835fd405fcdfc7a10a4dd0`
- `art/characters/evidence/construction-headwear-west-v1/input-contract.json` SHA256 `cc32ac341d4e10f690416e0547789e8461dd56839ee9790fa180deeefc46a4d5`
- `art/characters/evidence/construction-headwear-west-v1/receipt.json` SHA256 `11c369451c2be084498a3756d071489595142bec152c4bd8feb1d30af52814bd`
- `art/characters/evidence/construction-headwear-west-v1/report-summary.json` SHA256 `9bac5924f632ca81ac70301f32a2a1e95a5267335e31fa0256a4aa0df8c22303`
- `tools/characters/composition_contract.py` SHA256 `320d276e31fbc6f0dc32771403f72a1a6fef623c41c9cf302f3b134062502709`
- `tools/characters/construction_native.py` SHA256 `3f5e39f8da3400cf1c19e64f4dbcc5a88474da04181a9b5173f8c0db9b6049f3`
