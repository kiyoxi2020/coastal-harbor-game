# 采收西向v2：站立/蹲身关键姿态拒绝，未扩序列

2026-10-25，gpt-6.1-sol/high农事子任务；使用imagegen技能/built-in image_gen，精确生图模型ID工具未暴露。未嵌套代理、未启动GUI、未提交、未改旧稿/共享入口。

旧两稿四格法站高644px（目标582），鞋中心漂移约95/135px。本次改为单张站立校准→从同完整源生成蹲身关键姿态，不输入旧采收整身；先两姿态而不先四格。完整母版、批准idle均实际查看；原图、完整prompt、输入角色/生成原文件关联保留。

两源均1024×1536，512×768 idle整画布2×；统一显示scale138/1164，从画布合同确定，不按总高拟合。完整源整数整帧登记1536×1664，不重采样、不挪鞋/拉腿、不覆旧脸。近鞋后缘与母版固定偏移仅用于推定观察根点，不代表认可动作脚根。

| 实际观察（源px；点位约±8px） | 站立持物 | 蹲身握叶 |
|---|---:|---:|
| 头部投影框（2×idle478×484） | 467×474 | 497×502 |
| 冠→下巴 / 下巴→衣摆 / 衣摆→观察根点投影y | 474 / 326 / 353 | 497 / 197 / 257 |
| 萝卜可见球体宽×高 | 144×148 | 155×136 |
| 握叶冠→根尖 | 234.78 | 199.06 |
| 原始近鞋后缘 | [656,1412] | [853,1371] |
| 原始远鞋趾 | [330,1392] | [430,1355] |

倾头/蹲身会改变投影，不能用总高拟合代替头/躯干/腿段检查。即使把整帧近鞋后缘统一登记，远鞋趾仍差[-97,4]px≈11.51屏幕px，远鞋后缘差[-21,3]px≈2.51屏幕px；远鞋轮廓/相对占地改变，非整图简单移位。近鞋后缘一致是登记定义，不拿它当支撑通过。萝卜形状/投影变化，精确握取/地面接触未冻结；蹲身根部亮晕原样保留，不擦除alpha掩盖。

拒绝两姿态作为可用采收动作，没有扩拔起/收回/起身四帧，没有反复同思路生成。肩肘腕可见表面、鞋点、握叶冠和萝卜边界在 poses.json/measurements.json，衣物隐藏髋/膝/踝为null。缺隐藏身体、分层衣服、A/B混搭、四向、完整序列、用户认可，不接入加载器。

review.html提供真实纹理明暗1×/2×和逐帧；evidence/static-review.png仅排版。provenance.json/source-manifest.json绑定原图/prompt/输入/源哈希；candidate.json含实际纹理、配置、规则及姿态依赖哈希，明确拒绝/不可玩法。四项结构测试通过：RGBA完整、依赖/digest、姿态转换/未知、拒绝完整能力，见 evidence/validation.json；不代表动作验收。

    python3 art/design/character-motion/adult-standard-v1/harvest-west-proof-v1/revisions/v2/build_candidate.py
    python3 -m unittest discover -s art/design/character-motion/adult-standard-v1/harvest-west-proof-v1/revisions/v2 -p test_candidate.py

主代理决定测量拒绝稿无需原生录像，未执行GUI。可选诊断：

    godot --path godot2d --log-file /private/tmp/coastal-harvest-v2-native.log --script /Users/wyq/Documents/code/coastal-harbor-game/art/design/character-motion/adult-standard-v1/harvest-west-proof-v1/revisions/v2/native_review.gd

无存档/玩法事件；重复两姿态不能称完整采收循环或自然衔接。artifact_digest：8b224b74267be6f32d4761cf8e86a1e2d62a09b75ee8aabc6fc6a8440540e381。
