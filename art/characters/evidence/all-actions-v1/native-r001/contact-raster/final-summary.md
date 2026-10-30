已完成固定栅格对应两组正式观察：

- poses06：70点＋32鞋＝102/102通过，最大meanRGB1.777482。
- world05：5894实际draw全部输入/GPU绑定，适用2980draw产生7034点ROI＋1373鞋面帧＝8407/8407通过，独立预数一致；70点各见于全部10个真实farm实例，全部8走跑clip/32鞋pose覆盖，最大meanRGB1.876773。

全部最优offset[0,0]、无歧义/缺项/未验测量。固定41ROI、原源点/鞋coverage/whole padding/alphaRGB界/min4/所有最优≤1不变；采集前批准固定4ULP数值不确定样本排除，逐项计数明确，不看actual颜色选点。源与原始PNG字节均未改。

实际E为poses06和world05，父目录world04仅历史命名；不接受失败world04。完整receipt/逐pose与instance计数/少量source-native对照/SHA索引在对应目录。旧poses04原mismatch历史保留，6处handle文字标签勘误单列，冻结源70报告不改。

只证明近不透明栅格对应，不证明实际握心/接地、支撑或腾空、滑步、soil/合法target、动态美术或用户认可。全raw官方aggregate由root另行完成。
