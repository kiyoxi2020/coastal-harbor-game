# water-south实施报告

已完成固定配方原蓝长袖＋pants02＋shoes04的4真实姿态及同配方idle，交付schema1 sample、独立槽布面、完整GPT原稿/提示词/失败稿、人工逐姿态归属与遮挡配置、来源哈希和1×/2×对照。冻结sample SHA256 `9b2c74d2755c658545c9b15e86d77d1212d715e167d7c05a7a39d6bef730fc11`，inputs共152项，全部sample目录内相对路径。没有改全局catalog、Godot、原认可素材、其他动作组或玩家存档；未提交。

可见新牛仔/搭扣RGB逐像素来自GPT full稿同坐标；未换的上衣可见表面精确引用同pose原图。手、壶与水流原像素位于共享前景，原alpha完全保留。人工ownership先声明姿态表面，颜色只辅助原有布料边界；金搭扣与肤色可能同RGB，未以颜色独立决定owner。相关隐藏布面分别从同pose GPT completion按人工目标多边形提取，覆盖与当前前后关系另存；源未被当前手/工具永久挖空。ready上衣隐藏布面用completion1、裤腰用completion2，二者都是同pose原坐标GPT像素，无局部挪缩/补色。source-selection.json、ownership.json与各layer.source_references记录确切来源。

首轮只去人体的unoccluded稿重居中，按同类两次失败规则停止该方式，全部留档且不作为登记层。改为保留头脚作整帧参照，仅导入必要隐藏表面，不导入completion重画的袖形/外轮廓。recovery原补全仍留手，定点第二稿去手；ready原补全多出蓝色罗纹下摆，第二稿单独补裤腰，人工源边界分槽。完整raw始终保留。首轮idle从512参考直接输出1024时重构图，拒用；第二轮以整帧nearest2×原图仅作坐标参考，GPT实画1024源后整帧减半，未用上采样旧图冒充新密度。

验证：7项隔离单测RED→GREEN（原先缺实现/接口，新增对应最小实现）：非衣RGB与alpha、slot重叠/缺源、整帧越界、缺slot/phase/hash/idle、上衣新皮肤越过人工接口拒绝。实际`build ... water-south`及`validate ... water-south`通过：4姿态+idle的全部inputs当前，source/registered mask外RGBA改变0，全部alpha逐字节不变，独立槽PNG重建与baked逐RGBA一致，槽内可见RGB逐像素等于声明来源，原pose_id/时长/整帧位移/source_box/画布/根点/scale/密度精确相同。checks.json为结构/像素证据；未跑Godot，未把静态板当十循环原生或用户认可。

原脚底/握点/头部和注册信息保存在references/parent-registration-config.json.txt，未局部移动/缩放；鞋只改RGB、alpha/鞋廓/脚点不变。没有新增精确接触或关节轨迹通过结论。原ready/raise/pour/recovery时长200/200/350/250ms，sum1000ms。参考原生范围不自动迁移为本组合已通过。

局限：完整布面源通过可见面＋必要隐藏面构造，并依赖共享原版型黑轮廓/alpha边缘；这证明当前配方和五个姿态的离线槽合成，不证明独立任意剪裁、全裸隐藏体、其他动作/方向或其他配方能力。隐藏腰/腋面的GPT纹理接缝与未露出的准确解剖没有独立动态认可；当前coverage不暴露它们，若新动作或剪裁会露出须重新适配/验收。动作到idle仍用原已认可模板的硬切，没有新增工具收放过渡姿态。原生连续播放与当前新外观待主代理/用户评审。

实际执行模型：gpt-6.1-sol，high，fork_turns=none。生图只用内置image_gen.imagegen；该工具未返回确切图像模型ID，未推测。无CLI/API回退、无嵌套代理。
