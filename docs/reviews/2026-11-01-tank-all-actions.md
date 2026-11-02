> 2026-11-02清理说明：所述历史制作媒体和原生过程文件已按用户授权删除，旧数据路径已退役，本文仅保留文字结论；当前数据与验证见[执行报告](2026-11-02-resource-cleanup-executed.md)。

# 男性背心短裤母版：全动作统一验收

2026-11-02 用户选择 **Q27=A**，本轮四向六动作外观与动作验收通过。[认可记录及构建哈希](tank-actions-v1/acceptance-q27.json)。原始自验回执保持采集时状态，本决定单独追加，不修改冻结输入。

本轮承接 Q26 已认可的四向 idle：平直侧胸、自然宽腰腹、灰色背心短裤、光头赤脚。walk、run、hoe、water、harvest 四向源已全部更新；保留独立 idle4、walk24、run24、hoe24、water16、harvest16，共108身体姿态，另有56农事带工具显示姿态。原图、生成提示词和输入SHA均保留。

## 统一查看

[61秒原生动作视频](tank-actions-v1/native-actions.mp4)（20组方向动作、实际GPU截图按采样时间编码，人物未重绘或缩放）；[最终界面](tank-actions-v1/native-r002/overview.png)。

`python3 tools/characters/review.py body-actions` 打开共享 Godot 动作评审器。此入口展示带工具版本，四向六动作可切换。无工具完整配方另行构建，供后续静态衣裤鞋与工具接口研究；这次不授予动态换装认可。

[走路](tank-actions-v1/walk-native-board.png) · [跑步](tank-actions-v1/run-native-board.png) · [锄地](tank-actions-v1/hoe-native-board.png) · [浇水](tank-actions-v1/water-native-board.png) · [收获](tank-actions-v1/harvest-native-board.png) · [idle](tank-actions-v1/idle-native-board.png)

这些静态对照图按真实输出像素1:1排列，保留完整256×224画布，没有各帧单独对齐、缩放或截去工具。浏览器可缩放显示，验收细节请查看原尺寸。

## 实际交付

| 内容 | 路径/结果 |
|---|---|
| 不变的认可idle | `sources/adult-v2-idle-tank-shorts-r001/originals/four-idle-r002.png`、`parts/body/adult-v3/idle-r001` |
| 走跑48帧 | `sources/adult-v3-locomotion-tank-r001/derived/r003` |
| 无工具农事56帧 | `sources/adult-v3-farm-body-tank-r001/derived/r001` |
| 带工具农事56帧 | `sources/adult-v3-farm-visible-tank-r001/derived/r001` |
| 完整模板版本 | `templates/adult-standard-v4`，同一统一模型的候选后继版本 |
| 身体严格配方/构建 | `recipes/adult-v4-tank-body-reference/r001.json` → `builds/adult-v4-tank-body-reference-r001` |
| 带工具严格配方/构建 | `recipes/adult-v4-tank-visible/r001.json` → `builds/adult-v4-tank-visible-r001` |
| 评审配置 | `reviews/body-actions/review.json`、`body-reference.json` |

表内路径均相对 `art/characters/`。身体artifact为 `0de60c28c3fdc5a2ac6194236e1264201af9d049b521fe69037a7759a3b05532`；带工具artifact为 `50514fd34548460cfc63d09f2972cfe90d4ca8ed2e4834bcca0a7bb278b4b060`。两个严格build及preflight均为24能力/108帧。

版本化完整模板用于保留已交付idle快照，未修改其motion依赖；仍使用唯一 `unified-composable-character-v1` 和现有严格构建合同，没有分叉第二套生产人物体系。新通用body评审消费者复用既有Godot运动时钟、动作事件与原生观察器。

## 自验与修订

- 南向run原表第1帧在底中、第4帧在顶中，已保留真实非行序映射；最早错误登记计划已退役，最终用r003。
- 北向walk及西向hoe身体源各返修一次。头手脚与源姿态诊断保留，不通过粘旧脸手或单部件挪缩消除差异。
- 主代理检查六动作原尺寸图，独立代理检查12张带工具原表与原生alpha图集，未见旧长袖/长裤残留、明显女性胸型、错序或完全重复帧。
- 两条配方所有pose/clock与原动作轨一致；四向idle输出RGBA与Q26登记图完全一致。所有新atlas与canonical逐姿态RGBA检查通过。
- [源与集成独立检查](tank-actions-v1/locomotion/integration-independent-review.json)、[走跑诊断](tank-actions-v1/locomotion/source-self-review.md)、[农事身体说明](tank-actions-v1/farm-body/summary.md)、[带工具独立审阅](tank-actions-v1/farm-visible-independent.md)。

## 验证记录

- Godot通用body加载/反例：带工具与无工具配置各156项检查通过；旧headwear34项、旧construction48项及observation binding回归通过。最终身体UI文案/速度显示修订另各141项定点检查通过，未改运动值或时钟。
- [适配层独立复查](tank-actions-v1/body-adapter-independent.md)：工具representation、motion动作注册两处缺口已修复，绑定最终代码SHA。
- 最终完整Python测试490项通过（316.205s）；check通过59严格配方、53构建、9冻结旧配方、1既有接入。新消费者、证据分派与既有证据定点回归通过。
- 首轮带工具原生观察6112检查、23964采样、2953张PNG及216明暗pose均通过raw复核；目视发现旧发帽说明和速度显示残留，正在修正后采集最终r002。该r001为修正前记录，不作为最终代码快照。最终带工具r002通过2154项检查、6071采样、974 PNG、216个明暗姿态与20组各10次面板循环，raw复核通过。

最终r002实际世界观察已通过11352项检查：8组走跑各至少10循环（最小10.00027），12组农事各10次；5414渲染采样、2056走跑物理采样、6840农事物理采样、5415 PNG均绑定真实输出。96状态切换通过595检查，raw复核包含1069物理采样与8种稳定idle过渡。实际Renderer为macOS Apple M4 OpenGL/Metal兼容模式。

完整raw PNG与JSON在 `/private/tmp/coastal-tank-*-r002`，仓库 `tank-actions-v1/native-r002/` 保存输入合同、复核回执、压缩raw报告及代表截图；视频溯源记录见 `native-video-provenance.json`。视频尺寸280×332，其中280×300为原生actor裁图，额外32px仅放方向动作标签，时长60.917秒。源图尺寸、整帧倍率及256×224输出见各源自验；验收静态板保留1:1，Godot对照面板标注2倍，实际世界变换记录在raw报告。

无工具身体r002通过2148项检查、6074采样、971 PNG、216个明暗姿态与20组各10次面板循环；raw复核通过。主代理目视检查无工具农事的侧胸/腰腹、裸露四肢及工作姿态。四套最终输入前后SHA复核均通过（872/876/878/872项），[验证总表](tank-actions-v1/native-r002/summary.json)记录实际artifact及报告哈希。

## 仍有的限制

源图匹配发现北walk三处拳头约1.16–1.20登记像素、西walk0脚约1.197像素差；北walk3被遮挡拳头匹配不确定，西hoe第三帧头顶外框约1.32像素差。这些是图像匹配诊断，不能作为精确关节或脚接触认证。

工具握持与轮廓已目视，严格脚接触/滑步、工具物理接触及北向遮挡后的水流尚无完整证据。发帽16状态、衣裤鞋混搭、其他体型和正式发布未验证。全部新构建保持review-only，统一外观/动作已获Q27=A认可；默认游戏仍使用原v2人物，生产清单与冻结基线未变。未提交、推送或导出。

本轮主代理负责工具图、集成与验收；两个并行子代理实际均为gpt-6.1-sol/high，分别负责走跑源及农事身体源，随后负责通用评审校验与Godot加载适配。独立审阅聚焦原始帧序、裁格、男性轮廓和工具握持风险。
