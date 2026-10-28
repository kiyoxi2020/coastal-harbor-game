# 已认可草帽接入：东向站姿与跑步候选

用户接受右侧 wearing-source-v2 的静态戴法，绑定见 `visual-acceptance-reference.json`。现已提取真实帽层、叠回原人物，补齐东跑四姿态与专用帽下短发，并通过Godot原生验证。当前活动 `headwear-sampling-v1/catalog.json` 仅将东run条目指向本目录 `sample-build/sample.json`；原启动器直接打开新版。新派生发帽与动态效果仍待用户实际认可。

## 资源与实现

- `idle-extraction/`：获准源的整帽、近远面与原身体合成。新戴法不再套旧v4固定接触折线；完整帽冠、帽带和真实黑边保留，生成脸/皮肤/背景排除。
- `motion-extraction/`：采用run0/1；原run2/3帽冠窄的失败证据保留，不用于运行。
- `motion-extraction-v2/`：两份单姿态新GPT源覆盖原上头弧，采用run2/3，runtime零placement。
- `under-hat-hair-extraction/`：四份专用于戴帽组合的栗色刘海/鬓发/耳后及后颈可见视图。原完整hair-only状态不变；不是每列max-y削发，不虚称补齐未画的隐藏裸头发。
- `selected-extractions.json`、`selected-hair-extractions.json` 与 `build_approved.py`：一次性登记已烘焙，按 `far → 原body → 帽下发 → near` 合成；不擦身体、不缩放部件、不采用生成脸。新source/mask/轮廓/登记/源RGBA/提示词均保留。

原bare、hair及四帧80ms/idle200ms时序逐SHA保持；其他三样例目录条目逐字段不变。282项本地inputs和1301项完整依赖闭包已核对。`catalog-before.json` 保留旧目录；不覆盖原源或失败历史，不新增第二套人物体系。

## 验证

6项工具回归、34项Godot加载、90项切换与98项真实资源加载检查通过。两个具体P2已由失败反例修复并独立复核关闭：提取manifest必须匹配pose且明确允许候选（冻结idle仅精确路径+SHA白名单），以及原生快照必须绑定自身与全部实际调用校验工具的SHA。

本轮Apple M4/OpenGL真实GPU原生 **110项全部通过**：东idle与四run姿态、裸头/短发/草帽/短发草帽四状态，明暗停帧、各状态十循环、世界四姿态、动作内切发帽保持时钟及结束匹配idle；1693次时序采样、136张采集PNG、145项原生输出。证据在 `evidence/native/`，严格检查/输出/时序及采集前后依赖门禁 `receipt.json` 通过。136张原PNG完整保留，没有用压缩预览替代。

主代理已查看8张原生明暗五姿态板、帽/发帽时序抽样板及世界四状态板。未见明显贴合透明缝、生成脸缘残条、帽冠穿发或帽檐裁断。原1源像素接触/抗锯齿差异保留，仍待用户在动态试玩中认可；没有通过改alpha、补色或挪移消掉它们。周期截图是抽样，不是逐帧录像；四pose另有独立原生停帧/world采集，时序采样覆盖四pose十循环。

## 试玩与范围

运行上级 `headwear-sampling-v1/launch-game-trial.command`。右上选择东向跑步，右下切换发帽；左侧可暂停/逐帧，方向键在世界中跑动。保持原输入行为与动作时间轴，无玩家存档。

仅此东向样例获本轮新原生验证；其他三组保留旧资源和记录，不扩大为全方向、全动作或完整发帽库通过。原生使用控件信号/handler/逻辑Input，fixture置focused，不宣称OS键鼠/系统焦点恢复通过。未做导出包、跨平台或生产玩法迁移；未提交、推送或导出。

本轮剩余实施和最终只读复核按用户要求使用 `gpt-6.1-sol/high`；此前两运动帽视图完成使用 `gpt-5.6-sol/high`，前期Astra设计/提取记录保留。模型及职责切换见 `implementation-models.json`；未因换模型重做已有合格资源。
