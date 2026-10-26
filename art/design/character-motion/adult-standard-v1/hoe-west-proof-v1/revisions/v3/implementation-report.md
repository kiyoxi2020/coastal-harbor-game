# 锄地西向v3：单接触姿态拒绝，未扩序列

2026-10-25，gpt-6.1-sol/high独立农事子任务；使用imagegen技能/built-in image_gen，精确生图模型ID未暴露。未创建下级代理、未启动GUI、未提交或改共享入口。

旧v2两次四格法头缩小约8–10%，柄长316–403px且跨格。本次不输入旧整身动作，改为先单张contact校准，只用实际查看的批准idle作完整身份/比例输入，1024×1536整画布2×源密度，明确600px图像平面柄、可见collar/butt与双手接触。只有contact通过才做backswing；当前失败，没有继续生成或扩量。

完整源为 sources/single-contact.png，完整prompt及关联在 prompts/single-contact.txt、provenance.json。只作整数整帧登记到1536×1728；最初1664画布不足，检查拒绝后根据源1536+位移144=1680的证据扩大画布，未裁边/改美术。显示scale固定138/1164，未按当前人物总高拟合。

| 实际观察（源px，点位约±8px） | 数值/结果 |
|---|---|
| 源 / 母版画布 | 1024×1536 / 512×768，画布2× |
| 头部投影框 | 406×436，对照2×idle478×484；倾头会改变投影，不仅凭bbox证明3D缩放，但密度未确认 |
| 冠→下巴 / 下巴→衣摆 / 衣摆→观察根点投影y | 429 / 180 / 373；不拿弯腰总高当比例 |
| 柄collar→butt | [228,1216]→[935,826]，807.43px；合同600px，超207.43px/34.57% |
| 双手可见柄接触间距 | 354.83px，柄轴投影比例见measurements.json |
| 鞋/支撑 | 单姿态可见鞋底，无跨帧轨迹；刃落点/鞋底接触未冻结 |
| 源完整性 | 无多格交叉，全部原RGBA保留；不改变动作拒绝 |

明确合同要求图像平面长度、无透视缩短，且端点可见，807对600的差异足以拒绝。不能称真实三维刚性已证明。没有挪手/缩柄/补丁改头掩盖失败。隐藏髋/膝/踝为null。没有第二次机械重试，转做独立采收。

review.html为真实纹理明暗1×/2×单停帧，candidate.json明确拒绝且不可玩法/不可组合。poses.json记录源点、整数整帧转换和未知；measurements.json保留完整测量；source-manifest.json绑定实际纹理、配置、prompt、参考及规则哈希。四项结构测试通过：完整RGBA、依赖/digest、姿态转换/未知、拒绝完整能力，见 evidence/validation.json。结构通过不等于动作通过。

    python3 art/design/character-motion/adult-standard-v1/hoe-west-proof-v1/revisions/v3/build_candidate.py
    python3 -m unittest discover -s art/design/character-motion/adult-standard-v1/hoe-west-proof-v1/revisions/v3 -p test_candidate.py

主代理决定测量拒绝稿无需原生录像，未执行GUI。可选诊断显示调用：

    godot --path godot2d --log-file /private/tmp/coastal-hoe-v3-native.log --script /Users/wyq/Documents/code/coastal-harbor-game/art/design/character-motion/adult-standard-v1/hoe-west-proof-v1/revisions/v3/native_review.gd

无存档或玩法事件。仍缺比例确认、合法工具/握点、支撑、backswing/strike/recovery、隐藏身体、衣物、四向及用户认可；未接入加载器。artifact_digest：ab297b1caa40b362d68770bb37d2985d3b6ff1ea946aa5bf16b809c50331da71。
