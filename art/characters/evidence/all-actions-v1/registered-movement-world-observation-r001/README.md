同一严格走跑包：四向idle/walk/run共12格36姿态。四向walk/run各10连续真实世界循环；原始2054物理tick的距离、相位与GPU姿态已独立重算，见execution-verification.json。本记录绑定采集时72737/de39版本引擎及确切代码快照；之后为农事新增canonical大写姿态和同母版前景分拆，因此本记录不冒充新版本验收。所有输入与PNG重新校验通过。原始完整PNG及运行时代码保全路径见summary.json；仓内保存完整压缩原始报告与代表截图。尚未验证农事、严格支撑/工具接触、港口实际树/柜台/门遮挡、全24格或用户认可。

追加实际鞋部屏幕对应：32运动姿态、412张连续截图全部最佳offset=[0,0]且误差≤1px，RGB均值残差最大1.870（真实alpha≥250，显式背景混合界限）。采用报告中真实render_source_to_screen/实际snap属性，截图裁切源点保持采集时CPU锚；Wrun整帧padding通过sprite offset＋left/top还原canonical鞋坐标，未改身体/鞋/注册。逐张结果见shoe-raster-correspondence.json。仅核对canonical鞋像素与屏幕位置，不等于支撑、腾空、滑步或工具目标批准。
