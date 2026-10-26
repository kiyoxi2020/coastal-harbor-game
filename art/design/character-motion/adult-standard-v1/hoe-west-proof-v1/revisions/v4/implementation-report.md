# 锄地v4：四姿态待试看候选

使用imagegen技能的built-in image_gen，完整输入改为用户刚认可的water v3 ready1024×1536；未输入旧小头hoe全身、未贴旧脸、未分件缩头鞋或修柄。所有6次完整输出、提示词、输入关联及哈希保留。精确生图模型ID工具未返回，不臆测。未GUI、存档、提交或下级代理。

首张contact头437×446、柄约800px，已拒绝并留测量；第二张采用左侧紧凑工作锄，头恢复后才扩预备/抬锄/收回。收回第一张柄约640px，第二张改用实际紧凑ready完整源；仍有工具差异，停止同类两次尝试，保留第二张供用户试看，不局部缩柄掩盖。

| 顺序 | 时长ms | 实际头框px | 柄collar→butt px | 柄轴角度 |
|---|---:|---:|---:|---:|
| 预备ready | 180 | 469×476 | 552.76 | -16.50° |
| 抬锄lift | 220 | 464×482 | 545.80 | +15.08° |
| 落锄contact | 140 | 474×487 | 541.90 | -28.55° |
| 收回recovery | 260 | 464×483 | 603.02 | -0.48° |

认可water同口径头框473×488，选用四张均接近该密度；观察点约±8源px，数字小数只是坐标运算，不代表亚像素精度。原图全部1024×1536。头顶随动作在登记坐标y309..379自然变化，没有锁头顶或贴回站姿。实际冠/颏/颈、肩肘腕表面、衣摆、鞋和工具点及投影分段见 poses.json/measurements.json；髋膝踝衣物内关节为null，未按总高百分比猜测。投影段存在动作/衣摆变化，不将总高反算为缩放系数。

整帧整数登记到1536×1792，root[768,1544]，display_scale138/1164、source density2。root依近鞋后缘/鞋底轮廓及母版固定偏移[144,4]登记，完整原图连低alpha像素均保留。近鞋后缘一致是登记定义，不是接触通过；远鞋轮廓x跨度27px、近鞋趾约1px，测量不确定度未达到精确支撑认证。落锄刃最低点可低于鞋底表现入土，未裁掉工具。

工具长度最大/最小差11.28%；lift前手在柄轴约0.238处、contact约0.376，不能声称握点轨迹/刚性冻结。所有手都可见包住木柄，但手指遮挡下精确接触、工具连续性及脚轨迹仍待原生连续播放与用户评审；本轮解决可辨四姿态和头部恢复，不冒称完整动态/换装或生产验收。

candidate.json及registered已冻结：candidate SHA256为697c235907b38a20c6910373d8f5ca41ad134e86a35fe43103188b438644703d，artifact_digest为8f374b4418d922ad6aa0c0faf687bb099b5674bf36e05698a7db95f7268b0a10。总时长800ms，loop=false、events为空，诊断重播不触发世界事务。主代理接入catalog/试玩并负责原生，本子任务未启动GUI。

结构测试先RED（candidate尚未建立），后4项GREEN：四不同姿态/原时序、完整RGBA整数登记、真实源/输入/配置/纹理哈希、头框门槛及未认可范围。复现：

    python3 art/design/character-motion/adult-standard-v1/hoe-west-proof-v1/revisions/v4/register_candidate.py
    python3 art/design/character-motion/adult-standard-v1/hoe-west-proof-v1/revisions/v4/test_candidate.py

来源在 provenance.json/source-manifest.json。evidence/four-poses-2x.png只是静态排版，不是原生证据。未改v3、其他动作、catalog、trial/UI或状态文档。主代理与用户后续实际原生结论单独记录，不改本候选源和冻结哈希。
