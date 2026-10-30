# 南向under-hat组件登记候选

[views.json](views.json)只包含真实源/目标`water_south_B_ready`，设计身份为`hair-chestnut-short-v1`版本`r002`。未覆盖完整南浇clip或其他动作。

源为`gpt-south-underhat-r004-v1`完整GPT原图；normalized binary ownership保留源RGBA软边，未重复乘alpha。冠面、刘海与两鬓在原脸耳上合成；生成脸眉耳手及身体像素不入角色。与真实南帽配对的独立typed声明位于[compatibility](compatibility/south-underhat-r004-real-south-hat.json)。

[实际重建记录](evidence/reconstruction.json)绑定设计、adaptation、annotation、canonical B父底图、源/纹理SHA、decoded RGBA摘要与最终mapper工具SHA。使用`RegisteredAdaptations.component`从完整原图重建，`composition_contract.compose`按`base → under_hat_hair → near_hat`合成；无第二套构建器/播放器、无far占位、无coverage/occlusion擦除。

![actual canonical B parent plus hair and hat](evidence/water_south_B_ready-canonical-body-hair-hat.png)

完整图为1536×1920；canonical display_scale=0.11855670103092783，对应逻辑画布约182.103×227.629。图片仅源坐标诊断，未测物理屏幕尺寸或完成原生视觉验收。耳/刘海历史放大证据文件名前缀`historical-`使用旧蓝长袖衣装；新完整诊断直接使用canonical B父底图，其头部ROI与旧证据相同。

最终核验：两组件真实重建均通过；原帽与旧真实帽逐RGBA相同；真实发帽支撑外父底图RGBA不变。强冠面alpha≥220在真实帽外0像素；43个alpha=1软发缘保留，不能把0强冠越界扩为全源、动态或用户认可。

未执行strict配方construct/verify，因为本次没有创作完整clip配方；新top03底图接口、其他pose、Godot连续动作、接触时序与生产发布均未认可。
