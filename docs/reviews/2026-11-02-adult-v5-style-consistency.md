> 历史制作文字记录：所述过程图片、源稿、旧版本与回执已按用户要求清理；现行资源及验证见[独立动画归档](2026-11-02-adult-v5-animation-only.md)。下文路径为历史路径，旧验收结论不作为新闭包回执。

# V5：以认可idle修正walk/run画风一致性

用户指出：idle像素边缘清晰、效果OK，切换walk/run时却变粗、变黄、眼睛变粗。本轮以该idle为唯一风格基准，修正四向walk/run的48个完整姿态。idle PNG保持同一SHA，未重画；六张农事图集原RGBA保留，本轮没有宣称农事已统一。新稿仍待用户视觉验收。

## 结果与查看

**[最终PNG](../../art/characters/parts/body/adult-v5/r007/atlases/)** · [布局](../../art/characters/parts/body/adult-v5/r007/layout.json) · [494项SHA归档](../../art/characters/parts/body/adult-v5/archive-r004.json) · [源图/12次imagegen记录](../../art/characters/sources/adult-v5-style-consistency-r001/generation.json)。最终包仍含164源姿态，两套严格构建各24组108帧，修订模板`adult-standard-v5-r004`沿同一统一模型。

以下是原尺寸1x源帧对照，未额外放大人物；每个方向依次是idle、旧walk、新walk、旧run、新run，RGBA身份另经Godot实际GPU纹理核对：

![原尺寸前后对照](adult-v5-style-consistency-v1/before-after-1x.png)

以下是实际原生面板截图，12张均448×480，以同倍率拼接，未重新缩放。已目视核对四向新稿与idle的轮廓、肤色、眼框及像素阶梯：

![原生同倍率对照](adult-v5-style-consistency-v1/native-panel-comparison.png)

从仓库根打开共享评审器，可实际切换idle/walk/run：

```sh
godot --path godot2d --log-file /private/tmp/coastal-v5-style-review.log res://dev/characters/character_headwear_trial.tscn -- --construction-suite="$PWD/art/characters/reviews/body-pixel-v5-style-r001/review.json"
```

## 修正方法与边界

旧稿分批生成时未锁定最终显示尺度的像素密度和人物大小；旧walk/run头脸偏大、眼框和外沿粗黑，主要肤色由idle约(252,177,118)偏至walk约(250,165,110)、run约(252,165,99)。这些值是局部诊断样本，不是完整色板或人工视觉替代。

新稿先以v4完整姿态为pose-only参考，以认可idle按相同像素倍率作身份/画风参考，内置imagegen重画完整人物，另对walk补一轮色板修正。保留12份原始生成图、提示词及引用SHA，选用4张walk-r002和4张run-r001；没有程序调色、像素化滤镜或把旧脸手贴到新动作。

生成器仍把侧向run的完整人物画大较多。新稿按同朝向idle实际头部皮肤轮廓的像素密度，为每张六帧源表登记一个统一整帧比例；没有单独缩放头、眼、衣裤鞋，没有按总高百分比定位。源表两行各有固定绝对root/pitch网格，中间帧不另拟合位移；完整figure裁区的边界变化只作局部坐标换算。辅助颜色/alpha测量不是ownership mask，也不直接修改像素。最终每帧同为260×228、root(125,201)，运行层offset为0、local_scale为1，不用运行时缩放修画风。

最终切图仍使用现有`tools/characters/pack_sources.py`及[sources内参数](../../art/characters/sources/adult-v5-style-consistency-r001/packing/r002.json)。一次性参数提案助手和未绑定严格配方的r006草稿移到`/private/tmp/coastal-v5-style-density-draft-r001/`作诊断；最终art库不含Python代码，参数足以用现有切图器重建PNG。r007九图集与已独立审阅的草稿逐RGBA一致。

独立审查确认：粗眼、粗边和浓黄肤色突兀程度较旧稿显著改善，未见明显矢量化；48新帧alpha≥128裁边/遗漏为0，pose顺序与时长保持，idle＋六农事图集共7张逐RGBA不变。run仍有轻微暖色/眼黑块残差，未把近似当作严格同一色板或用户认可。

## 验证

| 验证 | 结果 |
|---|---|
| 人物Python全套 | 490/490，265.110秒 |
| 仓库人物门禁 | 67严格配方、61严格构建、9冻结旧配方、2既有本地接入包通过 |
| 最终source pack | verify通过，164姿态完整；idle PNG字节不变 |
| 两套严格构建 | 各108帧通过，仍review-only |
| 原生逐姿态 | 2424项、7321条采样、1109张图；独立证据校验通过 |
| 原生切换 | 96组、595项；独立证据校验通过 |
| 旧依赖保护 | v4归档637项SHA、默认玩家绑定及runtime-baseline保持 |

逐姿态观察包括实际GPU亮/暗背景、面板连续十循环和世界一循环；切换观察绑定真实时钟/姿态/纹理。以上是执行与资源证据，不自动证明画风被用户认可，也不替代严格支撑/滑步、工具接触或动态换装验收。本轮不重复执行旧候选曾失败的十循环农事世界门禁，不将其冒充通过或继承认可。

[轻量摘要及哈希](adult-v5-style-consistency-v1/summary.json) · [逐姿态回执](adult-v5-style-consistency-v1/poses-receipt.json) · [切换回执](adult-v5-style-consistency-v1/transitions-receipt.json) · [独立画风/源完整性审查](adult-v5-style-consistency-v1/independent-style-review.json)。原始快照在`/private/tmp/coastal-v5-style-{poses,transitions}-r001/`，最终输入分别736/742项；最终来源以实际native manifest和纹理摘要绑定。

主代理负责Imagegen、整帧登记、现有严格管线和原生验证；复用`gpt-6.1-sol/high`独立只读检查风格与裁区完整性。没有新增人物合成器/播放器或放宽门禁。当前catalog唯一现行母版及默认游戏仍为已认可v4；本候选未提交/推送、未导出、未授生产或新衣物适配资格。
