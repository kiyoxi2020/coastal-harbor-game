# Implementation report

已完成 run-east top04 砖红绳纹毛衣 + 原橄榄裤 + shoes04 棕搭扣鞋真实三槽小样及 matching idle。sample SHA256 `fa1b11913f8facc8527b8c6c0d76ebb44cfe13b2ae394c1f844fe5dc19fe76d8`。四真实姿态各80ms（320ms循环），512×768/root256,708/scale138/582/density1与原当前B保持一致。

11张 GPT 完整原图及 prompt/输出路径、全部复制参考、整帧投影、ownership、多层完整部件、mask、原 coverage/层序和工具均绑定 inputs。完整衣身不挖手洞；可见 mask 独立。第4帧 torso v1 下摆缩短已拒绝并留存，v2 使用孤立同坐标部件输入修复，没有脚本绘画或局部拟合。鞋口早期包络误含裤色，独立槽板定位后按实际踝线和局部原裤色边界辅助精修；没有通过放宽质量阈值或调色掩盖。

264项结构/能力断言通过，5帧非衣 RGBA和alpha差异均0，独立slots+共享body可逐RGBA重建全部最终图。1×/2×明暗对照、完整 torso 和各部件板已目视。原裤在自己槽内逐RGB保持；原 alpha 的低透明度 halo 如实保留。

未验证：GPU原生连续动作及回待机、用户认可。主代理负责整合/原生。局限：此次只适配同版型的固定抽样配方及单方向5姿态；完整换装GPT源本身不等于动态组合，交付的拆槽也不代表全部库存设计任意混搭可用。没有提交、没有修改旧认可图、共享Godot或catalog。

实际执行模型 gpt-6.1-sol，reasoning_effort=high，fork_turns=none。职责为独占 walk/run 抽样资源，未嵌套代理。
