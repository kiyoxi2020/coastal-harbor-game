> 2026-11-02清理说明：所述历史制作媒体和原生过程文件已按用户授权删除，旧数据路径已退役，本文仅保留文字结论；当前数据与验证见[执行报告](2026-11-02-resource-cleanup-executed.md)。

# 西向六帧红毛衣制作小样

## 当前结果

Q24=A 已记录，用户认可六帧红毛衣穿戴外观。此认可绑定 [原稿](../../art/characters/sources/top04-adult-v2-west-worn-r001/originals/worn-six-r001.png)，不扩大为抠图、动态或发布认可。[范围回执](../../art/characters/sources/top04-adult-v2-west-worn-r001/acceptance-q24.json)保留原话与源SHA。

按真实领口、袖口及下摆边界精修六帧归属mask r003，保留87955个源RGBA像素；独立复核的8个残留点已排除。另补真实西向idle穿戴源r002与独立复核的归属mask，未用walk首帧冒充停止姿态。两者均只提取衣物，生成脸手脚不进入结果。

通用 `prepare_registered_source.py` 使用原body登记和整帧统一比例生成256×224材料/二值归属/提取纹理，不进行衣物单独挪缩。六帧源与idle源均build/verify通过；25工具测试与独立反例复核通过。真实配方 [adult-v2-top04-west/r001.json](../../art/characters/recipes/adult-v2-top04-west/r001.json) 已经统一严格入口构建并复核，7帧，artifact `78d9d30da7363163ebc7f0db8fba890569f5fd7acc5bfd32ab193242272836fa`。原body层保持，毛衣普通alpha-over；没有coverage擦除。静态浅深背景目视合理，原生连续动态仍在实施。

## 方法与证据

六张归档body原图均1024×1536，以新增通用`reference_sheet.py`直接RGBA复制为3072×3072的3×2参考表。实际imagegen单次最多5张输入，故使用参考表加款式图共两张，而非向工具提交七张参考图。参考表不缩放、不裁切、不alpha合成，包括alpha0下的RGB也逐格等于原图；它是reference-only，不是人物构建或源登记。

最初透明毛衣直出六帧实际1254×1254，下排领肩上移约169–181原源像素，已拒收。按用户顺序改单帧后，r001袖口覆盖约47%/48%的原手掌肤色采样区域；r002定点修订将辅助统计降为0，可作款式候选，不代表完整衣物兼容。随后五帧并发调用被用户调整方法打断，只发现两张无法可靠映射pose的输出，已保留为未审核中断产物，没有推断身份或认可。

新方法的穿戴六帧同为1254×1254。独立核查只用统一全表209/512比例，没有逐帧拟合：六姿态对应，下排无旧稿大幅漂移，肤色辅助连通块定位的手脚bbox差约0–2表像素。模型仍改动了皮肤RGBA和透明外沿，固定head内部ROI完全相同RGBA仅0–0.31%，所以不能声称母版像素锁定，也不能回贴生成的脸手脚。罗纹领口使露颈短约6–8表像素，需要在原body叠加中继续检查。

抠图使用GPT辅助语义mask研究，以避免重新生成毛衣像素。第一版mask错误保留针织/接缝黑线；第二版虽实心但重画扩大外轮廓，均不能作为正式ownership。诊断预览使用第一版mask阈值128，并在各原格内只填闭合的内部孔洞，再选择穿戴图原RGBA；这是诊断处理，不是已审核部件。

提取预览69641个选中像素与穿戴来源逐RGBA相同，0不匹配，未选区均为RGBA零；没有图像相减、独立位移、缩放或重画衣物。保留源像素只能证明提取不重绘，不能证明mask归属正确。下排颈部肤色混入已经目视确认，袖口、外描边、衣摆和交叉袖层序尚待逐格精修；手遮挡下的隐藏衣身不由可见抠图自动补齐。两轮GPT mask后停止同法重试，下一步应核对真实边界，不能继续用提示词碰运气。

## 代码与验证

新增[通用参考表工具](../../tools/characters/reference_sheet.py)及[13项测试](../../tools/characters/tests/test_reference_sheet.py)。旧pack/build/contract/composition四冻结工具SHA未变；两项独立发现的符号链接门禁问题已修复，7类攻击均拒绝。实际参考表r002构建/verify通过，六格RGBA与原body全等；r001按旧工具身份保留，未覆盖。

前一检查点人物全量432项通过（265.517秒），仓库check通过55严格配方、49严格构建、9冻结旧配方、1本地接入；发布仍关闭。验证摘要见[verification.json](top-west-six-pilot-v1/verification.json)。该检查点尚未构建毛衣；当前7帧严格构建见上，新的全量与原生动态仍待完成，不把Python或诊断叠加图当动态兼容证据。

## 分工与下一步

用户授权并行：主代理负责生成、集成及诊断；gpt-6-luna/medium负责身体源核查、参考表工具和覆盖测试；gpt-6.1-sol/high负责合同核查、代码独立复查及生成图注册评估。任务可独立交付，主代理同时准备图像来源与生图；没有嵌套代理。原身体和游戏依赖未改，未提交/推送。

下一步完成通用registered评审接入：复用既有世界移动/动作时钟，加载实际严格构建，原生检查六帧循环与停止衔接。当前有限长袖姿态无需单独前景手分片，只有真实衣物像素叠在原body；不扩大为其他衣服、全动作混搭或完整隐藏源。

## 七姿态准备与严格构建复核

- 六帧原始穿戴表1254×1254，每格418×627；相对1024×1536 body原帧的统一密度为209/512。idle源r002为1024×1536，密度1。源body根点(512,1416)，整帧23/194登记，输出256×224、根点(123,201)。没有按衣物bbox拟合。
- [准备源独立复核](top-west-six-pilot-v1/registered-source-review.md)、[idle抠图独立复核](top-west-six-pilot-v1/idle-mask-review.md)、[七姿态配方独立复核](top-west-six-pilot-v1/seven-recipe-review.md)均通过有限范围。7张alpha支持mask、top提取/复制、body→top合成均逐RGBA一致；108张canonical body与冻结四工具SHA未变。
- [浅深背景严格输出](top-west-six-pilot-v1/strict-seven-light-dark.png)是静态像素检查图，源文件256×224以1:1排布；不冒充Godot动态。原生世界按统一0.25缩放及镜头4显示，原纹理每像素对应内部屏幕1像素，实际输出尺寸须以原生回执记录。
- 当前部件是同姿态完整可见长袖层；ownership是源衣物归属，coverage/occlusion均null，普通alpha-over不擦除原body。缺失的隐藏面、其他动作、其他款式不继承本轮结果；灰色底衣在未覆盖处仍可能露出。

最终原生与回归结果见下；当前仍为review-only，不接默认游戏、不更新生产发布/基线。

## 最终原生有限验收

[原生七姿态明暗图](top-west-six-pilot-v1/native-r005/panel-seven-light-dark.png)、[完整审阅界面](top-west-six-pilot-v1/native-r005/overview.png)、[原生回执](top-west-six-pilot-v1/native-r005/report.json)及[范围说明](top-west-six-pilot-v1/native-r005/README.md)已归档。macOS/Apple M4/Godot4.7.1实际GPU，600检查通过，10个真实位移驱动的世界循环、256采样、移动230.40625单位、六帧均显示；松键回真实独立idle，停止运动时钟保持。576冻结输入在采样前后SHA一致，日志无ERROR或脚本错误。主代理查看了明暗七姿态、完整界面与实际world/idle图；领袖手裤接口无明显破口或大块残留。

世界统一scale .25、镜头4，纹理到2560×1440视口1:1，原生窗口报告1280×720。截图不透明点的辅助比较存在统一[1,1]栅格采样差；仅用于诊断，不挪缩任何部件、不称零偏移物理注册。来源/输出/实际显示尺度与局限见证据README。

通用审阅器独立复核的三项问题均已修复并复验：源姿态语义错误必须拒绝、隐藏面板失败重载同步清空预览与停止、Python提前拒绝Godot不支持的层序/提取接口。最终16项适配器Python定点与78项Godot检查通过；[复核](top-west-six-pilot-v1/registered-adapter-review.md)及[实现记录](top-west-six-pilot-v1/registered-review-implementation.md)。早期无窗口Godot测试有本机系统证书平台错误，退出0且无脚本错误，不混入最终GPU日志结论。

打开方式：仓库根 `python3 tools/characters/review.py registered`。当前仅body＋top04的西向idle/walk严格配方，不增加游戏衣柜或存档。严格接触、其他方向/动作、其他衣裤鞋/发帽、隐藏面与动态混搭仍未验证；不自动扩量、发布或替换默认角色。Q24不扩大为最终动态用户认可。未提交/推送/导出。

最终全量：`python3 -m unittest discover -s tools/characters/tests` **473项通过，245.281秒**；`check.py`通过56配方/50构建/9冻结旧配方/1本地接入。[最终验证摘要](top-west-six-pilot-v1/final-verification.json)。预期拒绝fixture打印passed:false属于负例断言，完整unittest结果OK，不冒充真实接触通过。
