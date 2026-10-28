# Harvest north wardrobe sample

最终配方：**original-blue-long-sleeve + pants02 + original-shoes**，本组只抽样新牛仔裤。红毛衣方案未通过源语义/登记门禁，全部失败稿保留，没有在最终图中采用。

入口 `sample.json`，SHA256 `0c5e81663fed72376e11dcec609c41a95df17adabc0540e8773b6cac599020f9`。4动作 ready/reach/pluck/recovery 为200/250/250/300ms，共1000ms；画布1536×1920、root(768,1600)、display_scale=138/1164、density2，整帧注册平移逐帧继承原candidate。matching idle 为512×768、root(256,708)、scale138/582、density1。

`evidence/comparison-1x-2x.png` 为最终蓝上衣/牛仔裤1×/2×明暗对照；`evidence/independent-slot-sources.png` 为上衣、裤、鞋完整源及共享身体/前景/轮廓。三个槽确实拆出。完整裤源的可见所有权、当前覆盖与遮挡分别保存在 masks；ready/reach 的必要隐藏裤料来自同坐标 anchored GPT donor，不把手/萝卜洞永久挖入完整裤源。黑色轮廓及alpha边缘属于明确的 shared_same_pose_foreground_and_contour，同版型表面适配不代表隐藏裸体或任意剪裁能力。

所有采用的新裤RGB来自内置GPT源的同一坐标；上衣、鞋、脸、手、蔬菜、原alpha和非裤区逐像素保持。没有局部挪缩、调色或跨姿态贴脸。idle新裤源仅从1024×1536整帧统一0.5 nearest到512×768，其他动作保持1024×1536源及原登记。`sources/generation-ledger.json`、`ownership.json`、源图、prompt、mask、工具和原配置均保留，168项inputs全部为目录内相对路径并绑定哈希。

红方案诊断保存在 source-semantics-before、repair-attempt-audit、rejected-red-source-geometry 及 rejected-red-comparison。idle attempt3仍有179个露腕peach像素；pluck孤立collar attempt2明显放大/重居中，拒绝作为同坐标层。后续按主代理明确范围出口停止生图，原蓝上衣由原同pose直接复用。source账本如实区分“含未采用红上衣的整帧裤料donor”和“拒绝的红衣源”。

验证：`python3 test_harvest_sample.py` 7项测试通过；`python3 build_harvest_sample.py validate harvest-north` 验证哈希/登记/时序/独立槽精确重建和源语义门禁。5姿态非裤RGBA变化0、alpha完全相同、原上衣/鞋可见RGB变化0，最终上衣槽新peach计数0。原生GPU连续动作、回idle和用户认可由主代理后续验收；native_checked=false、accepted=false。这里只证明这个单方向固定配方和5姿态，status=sampled-not-exhaustive。
