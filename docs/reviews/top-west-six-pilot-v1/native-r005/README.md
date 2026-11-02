# 原生有限小样证据

最终r005：macOS / Apple M4 / Godot 4.7.1 / gl_compatibility。`report.json`绑定冻结输入、24张实际GPU裁图与全视口overview；`input-contract.json`冻结576实际输入。600检查通过，256世界采样，10实际位移驱动循环，西向移动230.40625单位，六walk姿态均出现；松键使用真实idle_west_0，停止时运动phase不推进，A/B比较不改位置。全部冻结输入在采样结束保持SHA。

实际视口2560×1440，DisplayServer报告窗口1280×720（macOS窗口单位）。源与严格输出256×224；整帧world scale .25、镜头4，texture→viewport密度1:1。panel截图同为256×224、密度1:1。未将窗口单位或截图分辨率冒充实测物理显示器像素。

`panel-seven-light-dark.png`仅无缩放排列14张GPU原图，第一列idle，后续六列walk0…5。`overview.png`为标准主题完整审阅界面，world截图来自原控制器真实运动。输入由Godot Input动作注入，未测试操作系统键鼠/窗口焦点。没有新人物播放器或动作时钟。

附加不透明像素诊断见`opaque-raster-check.json`：直接零偏移比较不一致；全部14裁图使用统一[1,1]截图采样位移时，不透明RGB在逐通道≤1范围内一致。这只是整体栅格/裁图采样观察，没有挪缩衣物，不是零偏移注册、透明边或物理接触证明。正式本轮动态结论来自原控制/时序/实际纹理与视觉，不能用这项诊断补足接触验收。

范围不包含精确支撑/滑步、门和树遮挡、低FPS矩阵、其他动作/方向/体型、动态混搭、最终用户动态认可、生产发布或导出。Q24=A仍只对应六帧穿戴源外观。完整临时运行目录为`/private/tmp/coastal-top-registered-native-r005`；本目录保留本轮全部观察制品及最终日志。
