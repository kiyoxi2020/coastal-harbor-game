# hoe-west实施报告

完成top03海军条纹衫＋原裤鞋的西向4姿态及matching idle，schema1 sample/独立槽布面与mask/完整GPT raw与提示词/失败稿/来源哈希/1×2×板齐。冻结sample SHA256 `99f31cfecc7cdc3c84d4d22fcfa1f1dc9a64e5359ffa7493a867be1b1c7949bd`，inputs共159项，全部目录内相对路径。原blueB姿态与当前原脸手锄裤鞋来自已认可catalog-color-v2；本轮没有改认可母版、全局catalog、Godot、其他组或玩家存档，未提交。

像素方法：新条纹布面的RGB全部来自内置GPT同pose全帧稿；原同pose脸手/锄及未换裤鞋逐字节复用。独立top/pants/shoes的源ownership、当前visible coverage、occlusion和层序分别保存，层都full_frame/offset0/local_scale1。共享层只承担原前景、当前版型的黑轮廓/alpha边缘及原navy接口，不是假称隐藏裸body。源不是一张完整穿衣图直接交付当可组合：各slot可单独查看、当前组合由slot PNG重建，完整衣身与当前遮挡图明确分开。必要隐藏衣身取同pose anchored GPT completion手/锄后布面，不从另一pose贴脸手，不在完整源上永久挖手/柄洞。所有完整raw始终保留。

失败及调整：最初去掉整个人体的unoccluded稿重居中，两次同类证据后停止，保留失败。改为头脚保留作整帧坐标参照，GPT移除手/锄补cloth，再仅导入人工已定位的隐藏 torso；completion不相关的袖型/裤边重画不被导入。ready/lift/contact第一补全仍留手，第二补全定点去手；当前来源及人工目标在source-selection.json、ownership.json和layer.source_references。原裤鞋本轮未改，不把为本样例记录的可见层扩写成任意露体/脱卸能力。

抬锄full1肩外缘213点无GPT alpha；full2肩范围较足但腕口漂移并仍缺125点，未放宽缺源门禁。根据evidence/lift-shoulder-source-diagnostic.png，改做GPT肩缘定点补面full3，尚缺120点；经逐点查明同pose full2在这120点全有真实条纹、0肤色。人工明确肩面panel，仅primary alpha0且属于原cloth的点选full2，0平移/0缩放/0程序新RGB。raw2/raw3、masks/lift-top-visible-supplement-0.png、selected-density、选择规则与工具快照均在inputs；实际验证逐点源RGB与panel/alpha条件成立。1×/2×明暗板没有观察到突兀条纹残边，原生连续审阅仍待主代理。

同版型navy领口/袖腕接口：ready12/lift103/contact5/recovery86个原轮廓点在GPT稿变为新肤色，保留原同pose接口而不让新衣物拥有皮肤；明确人工边界内才可保留，其他位置报错。contact另有5个原深navy/黑轮廓点被GPT画成邻裤颜色，逐点人工归回共享轮廓；它们不是一块旧蓝布补丁。隐藏腰线也按实际GPT衣身/裤边分别ownership，避免把olive裤色归入上衣。未作RGB程序调色或轮廓拉伸。

验证命令：`python3 -m unittest discover -s art/design/character-motion/adult-standard-v1/wardrobe-sampling-v1/hoe-west -p test_build_samples.py`，8项RED→GREEN通过，覆盖非衣RGB/alpha、缺源/slot重叠、整帧越界、缺slot/phase/hash/idle、接口新皮肤越界和同pose补面范围/缺源。`build ... hoe-west`和`validate ... hoe-west`通过：全部hash当前；4+idle source及registered的mask外RGBA0差、alpha完全不变；独立slot重建与baked逐RGBA一致；可见RGB等于声明source，隐藏RGB等于声明同pose GPT completion；selected-density逐RGBA等于声明raw及120点补面；原pose_id/时长/位移/source_box/画布/root/scale/density逐项相同。

时序180/220/140/260ms，总800ms；源1024×1536，整帧注册到1536×1792，root(768,1544)，scale138÷1164/density2。父registration config保留原头框/脚底/握点/landmark，未重新声称关节或精确接触通过。idle1024 GPT源按完整画布统一减半回512×768，原512源的nearest2×图只作坐标参考，未将上采样旧图算新密度。首轮idle重构图的失败源留档。

范围与局限：当前是同版型布面设计适配抽样，支持本配方/方向/4姿态和idle的离线合成。源内部隐藏腰腋的纹理接缝、未露出的精确衣摆轨迹/解剖没有独立动态认可；若更换剪裁、遮挡关系或动作会露出它们，须另适配/验收。原裤鞋与共享轮廓不能被解释为任意三槽兼容或全裸体模板。当前原生十循环/动作结束idle切换及用户新组合认可待主代理；静态板与结构通过不是原生结论。无生产玩法或保存能力。

执行模型gpt-6.1-sol，high，fork_turns=none；内置image_gen.imagegen未返回确切图像模型ID，未推测。无CLI/API回退、无嵌套。harvest-north已按主代理协调独占交接给hoe_long_sleeve，其后未再写该组。
