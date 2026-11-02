> 历史制作文字记录：所述过程图片、源稿、旧版本与回执已按用户要求清理；现行资源及验证见[独立动画归档](2026-11-02-adult-v5-animation-only.md)。下文路径为历史路径，旧验收结论不作为新闭包回执。

> 后续用户反馈：idle画风认可，walk/run粗边、偏黄、眼睛变粗，当前优先进行idle基准画风一致性修正。本页记录旧r005候选，不代表新稿或用户动作认可。

# Adult-v5 全动作像素风候选

基于当前adult-v4，使用内置`image_gen.imagegen`将全部9张图集转为像素风：108身体姿态＋56农事带工具姿态，共164源姿态。最终选用9次整图转换结果；另有1次body-water定向修源试验未选用。男性身份、灰色背心短裤、四向与毫秒时序保留。v5为独立待验收候选。

## 最终交付

- **[实际最终图片](../../art/characters/parts/body/adult-v5/r005/atlases/)**：body六动作、hoe/water/harvest三张带工具图集。[layout.json](../../art/characters/parts/body/adult-v5/r005/layout.json)与[manifest.json](../../art/characters/parts/body/adult-v5/r005/manifest.json)。
- [目录说明及启动方式](../../art/characters/parts/body/adult-v5/README.md)；[最终候选归档](../../art/characters/parts/body/adult-v5/archive-r003.json)冻结487项文件SHA。旧r001–r004打包提案仅保留诊断。
- [最终模板](../../art/characters/templates/adult-standard-v5-r003/template.json)，同一`unified-composable-character-v1`模型；[带工具build](../../art/characters/builds/adult-v5-pixel-visible-r003/manifest.json)与[身体参考build](../../art/characters/builds/adult-v5-pixel-body-reference-r003/manifest.json)，各24方向动作108帧。
- [imagegen原始输出](../../art/characters/sources/adult-v5-pixel-imagegen-r001/originals/)、[提示词](../../art/characters/sources/adult-v5-pixel-imagegen-r001/prompts/)、[9次选用请求与来源](../../art/characters/sources/adult-v5-pixel-imagegen-r001/generation.json)、[源说明](../../art/characters/sources/adult-v5-pixel-imagegen-r001/README.md)。原图与imagegen默认输出逐字节相同。

## 尺寸、登记和完整性

原生生成图为1341×1173（idle及4列农事）、1642×958（6列运动/锄地）。idle仅为参考排成2×2并整图nearest放大供imagegen观察；其他8次直接以v4最终图集和新idle作目标/风格参考。脚本只登记、整帧提取和打包，没有程序像素化、重画部位或阈值改写alpha；完整原始alpha留存，最终帧按声明裁区采样。

Imagegen实际行距、列距不等于目标画布等分网格。最终[packing/r005.json](../../art/characters/sources/adult-v5-pixel-imagegen-r001/packing/r005.json)与[registration-r005.json](../../art/characters/sources/adult-v5-pixel-imagegen-r001/registration-r005.json)记录实际裁区：每图集一个统一整帧比例，每方向行一个绝对root/pitch网格，首末足部对应点确定固定间距，中间帧保留自身动作。没有对每帧分别拟合位移或按总高百分比定位。

西向锄头超出较窄网格裁区，因此保留完整原source tile；局部root随crop origin作等量坐标换算，`crop_x + local_root_x`保持同一绝对root网格。全部164层offset仍为0。独立复查确认恢复173个遗漏工具像素，164格显著alpha裁边为0，9张源图alpha≥128轮廓无遗漏；颜色/alpha测量仅辅助检查，不构成ownership mask。

统一整帧260×228，根点(125,201)，display_scale=1。相对v4的256×224增加左右各2、底部4像素留白，保留完整工具和边缘，未移动角色世界根点；6列图集1560×912、4列1040×912、idle260×912。Godot共享评审器仍nearest、整帧统一缩放；实际原生显示尺寸由下面证据记录。原始RGB预览可能显示红/黄色透明杂点，其中高饱和红点alpha最大1–3；亮/暗背景检查使用实际合成后的GPU图像。

更正源网格后，10条重点回位轨的首末足部额外偏差≤1.5登记像素，消除原30–40像素累积横移。这是特定回位诊断，不是全动作支撑/滑步或土壤工具接触验收。左右留白造成nearest相邻源像素取样差异，不声明与旧提案逐RGBA等价，也不继承旧提案视觉证据。

## 验证

| 检查 | 结果 |
|---|---|
| 人物Python全套 | 490/490，495.984秒 |
| 最终仓库门禁 | 通过65严格配方、59严格构建、9冻结旧配方、2本地接入包；正式发布关闭 |
| 最终source pack verify | 9张PNG＋layout通过，digest `4f8159b1f0e0dc26d73199b74a4cb5ced39369845f2e683684cb05e0927cb9ab` |
| 两套严格build | 各24组108帧通过，review-only |
| 独立源裁区审查 | 164格轮廓/工具完整，实际原图与imagegen输出一致 |
| 最终带工具原生逐姿态 | 2486项，7600条采样、1140张图；独立回执通过 |
| 最终身体参考原生逐姿态 | 2436项，7327条采样、1115张图；独立回执通过 |
| 最终连续世界动作 | 两轮内部13028/13012项通过，独立校验拒绝时钟不连续；未通过，不继承至新稿 |

主代理负责生图、登记、构建与原生验证；复用`gpt-6.1-sol/high`只读审查源裁区及重点回位。旧v4归档637项SHA、默认玩家场景/资源和runtime-baseline保持；最终v5归档487项SHA另独立核对。

## 原生证据与查看

[轻量摘要](adult-v5-pixel-v1/summary.json)绑定实际最终模板、PNG、build、native输入、原始观察报告和校验回执；[独立源审查](adult-v5-pixel-v1/independent-source-review.json)。

此旧动作风格已被用户要求修订，原始快照仅作诊断；新一致性稿另建实际纹理绑定的验收。

原始观察位于`/private/tmp/coastal-v5-r003-{visible-poses,body-poses,world}-r001/`，使用现有共享评审器和原生GPU，窗口置顶、最高60fps、关闭vsync；无需另写人物播放器。每轮预先冻结实际输入，producer内部检查与独立`all_actions_evidence.py validate`均须通过。最终素材的原生观察不继承旧提案回执。

旧提案曾出现后台渲染停顿、短帧漏采或处理帧缺口；内部计数通过不等于独立证据通过，失败日志保留但未列为最终通过。Finder曾写入.DS_Store导致严格快照拒绝，元数据仅移至coastal临时备份；不可变图集包目录现为只读以阻止再次写入，最终图片仍可查看、后续修订仍新建目录。没有放宽门禁或修改生产基线。

## 范围与待验收

本次完成v5全图像素风候选和统一查看入口，尚无用户对v5的视觉认可。catalog唯一现行母版和默认游戏继续使用已认可v4；Q27、衣物mask、严格接触及动态换装资格不自动迁移。未导出或验证独立游戏包，未提交/推送。
