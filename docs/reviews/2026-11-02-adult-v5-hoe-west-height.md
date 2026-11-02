> 历史制作文字记录：所述过程图片、源稿、旧版本与回执已按用户要求清理；现行资源及验证见[独立动画归档](2026-11-02-adult-v5-animation-only.md)。下文路径为历史路径，旧验收结论不作为新闭包回执。

# V5 西向锄地人物偏高校准

最新：[最终PNG r012](../../art/characters/parts/body/adult-v5/r012/atlases/) · [suite](../../art/characters/reviews/body-pixel-v5-hoe-west-height-r001/review.json) · [477项冻结归档](../../art/characters/parts/body/adult-v5/archive-r009.json)。用户已认可当前效果，默认v4游戏和现行母版不变。

用户指出西向锄地人物略高。对照同一260×228画布/125,201根点，idle头顶皮肤到脚部为137px，r011西锄visible六帧为144/144/145/141/125/143px；工具高于头部的范围不计入人物高度。最初尝试Imagegen稍收膝/髋，两次结果的蹲姿变化过大，未选用；原图、提示词与中断记录保留sources/adult-v5-hoe-west-height-r001。未把这些实验作为最终新姿态。

最终选择更小的改动：原r011高分辨率source美术与姿态不变，整组六帧body和visible使用同一个137/145校准因子，仍走现有pack_sources的单次nearest整帧变换，不二次缩已烘焙PNG。完整人物及工具共同变换，内部比例、握持和黑线颜色不改。根点不往下挪，实际脚部支撑地标重新量取保持占地位置；不是按总高百分比猜部件接口，也没有局部缩脸、压腿或拉伸。头部随整帧缩放约5.5%，不声称它的像素大小完全不变；同倍率静态对照仍保留黑线清晰度和角色识别。

|姿态|r011高度px|r012高度px|
|---|---:|---:|
|0|144|136|
|1|144|136|
|2|145|137|
|3|141|133|
|4弯腰|125|118|
|5|143|136|

[六帧idle/旧/新对照](adult-v5-hoe-west-height-v1/idle-before-after-1x.png) · [完整测量（含body）](adult-v5-hoe-west-height-v1/geometry-before-after.json)。该皮肤地标只作图像高度诊断，不是ownership或物理接触证明。每帧原生源格260×228，正式面板通常2倍显示；原动作曲线和身体比例保持，不要求弯腰帧也与idle总高相等。

只改变西锄12个body/visible源姿态；其余152逐RGBA保持，七图集PNG字节保持；全部164 pose ID和duration保持。最终仍9图集、164源姿态、24方向动作/108显示帧，沿同一统一模型template-v5-r009、construction-v1两套recipe/build-r009。源登记packing/r004、height-calibration-r001和method-selection-r001明确选择理由/引用/尺度，新增source bundle仅绑定新prepared整图集；不建立新播放器或合成管线。

两套108帧严格build/verify、suite preflight通过；原生1788项/791张PNG、96切换595项及两份独立回执通过（734/740输入）；108实际显示姿态615554高alpha像素与源图固定2倍/同原点位置匹配。490人物测试通过（443.110s），门禁77严格配方/71严格构建/9旧配方/2既有接入通过。旧r011归档576项与v4归档637项SHA保持。未改变全局游戏人物选择、生产基线、动作时序/逻辑或存档；未提交、推送或导出。动态换装与严格世界接触不在本轮通过范围。

[原生idle/旧/新对照](adult-v5-hoe-west-height-v1/native-idle-before-after.png) · [验证摘要](adult-v5-hoe-west-height-v1/summary.json) · [像素位置复核](adult-v5-hoe-west-height-v1/native-pixel-registration.json)。原始观察保留/private/tmp/coastal-v5-hoe-west-height-{poses,transitions}-r001。r012评审demo已打开。
