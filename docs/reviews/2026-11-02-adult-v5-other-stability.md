> 历史制作文字记录：所述过程图片、源稿、旧版本与回执已按用户要求清理；现行资源及验证见[独立动画归档](2026-11-02-adult-v5-animation-only.md)。下文路径为历史路径，旧验收结论不作为新闭包回执。

# V5 其余动作稳定性修正

最新：[最终PNG r010](../../art/characters/parts/body/adult-v5/r010/atlases/) · [评审suite](../../art/characters/reviews/body-pixel-v5-other-stability-r001/review.json) · [475文件SHA归档](../../art/characters/parts/body/adult-v5/archive-r007.json)。待用户统一验收。

用户“ok，继续修正其他动作”延续上一轮头部横向稳定目标。四向walk和南北run按同向idle头中心登记完整人物帧；上一轮用户认可的东西run和idle共16姿态逐RGBA保持。全部walk/run头部横向范围≤0.5贴图px，保留上下弹跳。

农作有真实弯腰、挥锄和伸手，不能仅看头位移大小判断横漂。已提供“保留前倾”与“农作锁头”的可选问题；在未收到相反偏好时按推荐方式保留前倾。逐帧查看无工具与带工具源图，实测脚底皮肤内沿的支撑跨度，与v4同姿态支撑跨度中心对照，移除额外整体横移。身体、手、工具、作物和水流一起整帧登记，未局部拆动。颜色仅辅助已目视确认脚部地标，不生成ownership/mask，不以含工具/水流的总alpha外框定位人物。该测量不证明真实关节、严格接触或动态换装。

|头中心范围（贴图px）|r009|r010|
|---|---:|---:|
|walk北|3.5|0.5|
|walk西|1.5|0.5|
|walk南|0|0|
|walk东|2|0.5|
|run北|1.5|0.5|
|run南|1|0.5|

24个农作方向/显示变体（body及visible）112源姿态，相对同姿态v4支撑中心的最大偏差从最高18.5降至≤0.5贴图px。不是把农作头锁死；头部相对脚部的原始前倾轨迹保持。v4本身合法支撑姿态差异也保留。

[全部诊断数据](adult-v5-other-stability-v1/geometry-before-after.json) · [无工具农作逐帧](adult-v5-other-stability-v1/farm-body-after.png) · [带工具农作逐帧](adult-v5-other-stability-v1/farm-tools-after.png)。图板为原生贴图1倍裁格，单帧260×228；原生评审面板为2倍显示，需结合实际窗口验证。

registration-r005/packing-r005记录所有源根点与实测地标；102帧X登记改变，源图、裁区、统一比例、Y、时序均保持。东walk一帧初次nearest采样产生1px残差，校准实际整帧采样相位后≤0.5px；未归档草稿移至coastal临时诊断，不覆盖旧冻结r009。新source bundle为adult-v5-other-stability-r001，模板/配方/构建r007仍沿同一模型。旧r009归档469项与v4归档637项SHA保持；默认游戏不切换。

## 验证

pack、两套108帧strict build与verify、suite preflight通过。原生逐姿态/十循环2420项、1107张PNG，以及96切换595项通过；两份独立回执通过，分别742/748冻结输入。490人物测试通过（281.807s）；仓库门禁通过73严格配方/67严格构建/9旧配方/2既有接入。v4场景、资源与运行基线SHA保持。无工具身体以完整帧图板逐帧检查，原生观察器绑定visible真实纹理。本轮不修改农作画风、不重新生图、不宣称严格接触或发布通过。未提交、推送或导出。

[实际农作面板](adult-v5-other-stability-v1/native-farm-panels.png) · [验证摘要](adult-v5-other-stability-v1/summary.json) · [原生像素位置匹配](adult-v5-other-stability-v1/native-pixel-registration.json) · [登记地标的屏幕投影](adult-v5-other-stability-v1/native-geometry-verified.json)。原始观察在`/private/tmp/coastal-v5-other-stability-{poses,transitions}-r001/`。

原生几何复核曾发现直接用RGBA源图的皮肤阈值检测扁平化RGB截图，会把背景混合的抗锯齿边缘算入皮肤，改变脚底最低行及头部边界；该方法结果明确标为拒绝，保留在native-rgb-threshold-rejected.json，未当作通过证据。改用实际截图与对应源图全部alpha≥250像素配准：108姿态、624676点全部在同一2倍变换和像素原点[-26,-2]匹配，几何容差0px；每通道颜色容差256−alpha仅容纳理论背景混合和取整，不容纳位移。由实测公共渲染变换投影源地标，walk/run范围与农作支撑登记偏差均≤1屏幕px。该几何/输入证据仍不等于用户认可或物理接触证明。
