# Water 四向长短袖八组完整动作候选

2026-10-26。完成water south/west/east/north × A/B共8组、32张真实不同完整姿态，ready/raise/pour/recovery，每组200/200/350/250=1000ms。只写water目录；未改共享Godot/catalog/docs、旧认可图或其他动作，未提交/嵌套代理。主代理后续负责24组试玩加载与原生收证。

## 审阅与冻结候选

每组README和static-review.png提供明暗1×查看；[来源结构摘要](validation-summary.json)、[源与生成记录](generation-ledger.json)、[实际脚/握点汇总](measurements-summary.json)。内置GPT imagegen生成；工具没有返回精确图像模型ID，不推测。执行代理gpt-6.1-sol/high/fork_turns=none。

所有候选schema1，template=adult-standard-v1、action=water、真实direction/garment；canvas1536×1920、root[768,1600]、source_density_scale_vs_idle=2、display_scale=138/1164≈0.1185567010。源每张1024×1536，原生统一显示121.40×182.10px；注册画布原生182.10×227.63px。保持nearest，不按人物总高拟合缩放。

| 组 | candidate路径 | SHA-256 |
|---|---|---|
| south-A | [south-A/candidate.json](south-A/candidate.json) | `b9ef11ac2f347d02670e702e55201755e29a4e5584a7fbf20e9f15f352d2fcaf` |
| south-B | [south-B/candidate.json](south-B/candidate.json) | `85301bc65711e8f7ead3b1873d5dae6cc1125edcbc24b9508ca2e7c82b2301c0` |
| west-A | [west-A/candidate.json](west-A/candidate.json) | `98d3f792287c444da2ef3ec4a208510c3d21064a5db497ab234bbafeadc9d036` |
| west-B | [west-B/candidate.json](west-B/candidate.json) | `0a2bc560d1f03043326adcb509d5f42474b47b0b8fb240002237574fd7d4e2da` |
| east-A | [east-A/candidate.json](east-A/candidate.json) | `96be4ee91391c8f73f3c2c2fddb84b78a21f490117985c04d29c28d4aa2a1e35` |
| east-B | [east-B/candidate.json](east-B/candidate.json) | `2bac17d97437f0439e56edbe86e4b25a05a3d536e54acf99a770d09d6c462f26` |
| north-A | [north-A/candidate.json](north-A/candidate.json) | `db290733732d711f9aea45c4b6493d345037e1d1e1118f816d701aed8f8cbd46` |
| north-B | [north-B/candidate.json](north-B/candidate.json) | `389f75b4a266401881af91ec98fbea3c14efe5e84075c9f238a26a17d93e52db` |

以上最终哈希取代制作过程中发送的中间哈希；所有源/config/measurements/登记工具快照及实际纹理哈希由各candidate.inputs绑定。accepted/geometry_checked/motion_checked/native_checked/modular/gameplay_available均false，原生证据另绑最终candidate，不能据结构通过提升外观/动态认可。

## 来源、动作与策略变更

西A的ready/pour完整源RGBA从已认可water v3无损复用，新增raise/recovery；南A的ready/pour完整源从water-south-proof-v1原帧无损复用，新增raise/recovery。其余28个必要姿态全部独立GPT生成；B是完整穿衣帧重新生成，仅固定蓝长袖外观，不是拆层/换装兼容。四方向均独立绘制，没有脚本镜像。母版三向眉v3及方向对应已认可idle作为参考，源脸/手不由脚本替换。

第一张2048×3072请求的2×2图实际仅1024×1536，每cell密度不足，整图保留sources/rejected-four-grid-west-A.png与prompt，未切入candidate、未上采样。立即改所有姿态单帧1024×1536。共35次新GPT调用：28个必要新姿态、6次针对性修订和1张失败四格；4张既有真实源复用不计新生成。

部分完整生图会拉高头/身：west-B/east-A ready重试保留v1、选用较收敛v2；south-A raise/recovery双参考约束连续两次仍漂移，分析发现错误高身概念图可能干扰几何，改成**单一完整ready目标的简短精确编辑**，保留v1/v2失败稿，采用v3。南recovery明显回到原密度，raise仍有投影差异，未按总高缩放掩盖。没有以重试次数代替验收。

北向严格背头/双耳，无后脑眼脸；手臂和壶在身体前方按空间自然遮挡，能看见的手/柄接点登记，不可见握点保留null，没有把手掌画到后背。pour均保留完整壶嘴至落点的水流与水花；recovery停止连续水流、降壶、舒展手臂并留末滴，四姿态不是重复PNG凑数。

## 登记和真实测量

只进行完整1024×1536源的整数整帧平移到共同画布，无局部缩放/挪脸手鞋、拉腿、镜像或补画。源全部RGBA包括低alpha外晕保留，registered逐RGBA与源整帧置入结果一致。源图/失败稿/提示词/登记配置/源图副本与哈希均保留。

observe_clip.py仅用色彩辅助定位已经目视确认的鞋ROI，再测真实alpha轮廓（包括原始深色边缘），不把棕色填充内缩当鞋底，不决定正式部件所有权。根点使用实际鞋部占地及固定同向参考偏移，不用总高百分比。南pour邻鞋水流污染自动矩形时，先失败回归复现，再依据原源可见鞋底1324与轮廓行1320改用人工观测root[512,1320]；没有修改图像或局部鞋位置。

每帧真实脚轮廓、可见颈/肩/肘/腕表面、握把交叉面、壶嘴与落点见manual-observations/registration-config/measurements。被衣物挡住的髋/膝/踝为null；握柄表面手工粗测不假定精确手指接触，轮廓±8源px、握点可达±24源px，不足以证明既定≤1显示px目标。脚根注册带来的点相等不是接触测试通过。正背/倾斜投影也不能以2D长度证明3D壶刚性。

冠至根投影各组跨度如下（真实数据，姿态变化与生成漂移尚未分离；不是纯比例证明或认可）：

| 组 | 四帧冠根投影源px | 显示跨度px |
|---|---|---|
| south-A | 1164, 1199, 1159, 1170 | 4.742 |
| south-B | 1178, 1218, 1160, 1178 | 6.876 |
| west-A | 1169, 1166, 1159, 1172 | 1.541 |
| west-B | 1231, 1166, 1163, 1177 | 8.062 |
| east-A | 1222, 1150, 1180, 1151 | 8.536 |
| east-B | 1224, 1148, 1178, 1151 | 9.010 |
| north-A | 1164, 1162, 1092, 1108 | 8.536 |
| north-B | 1164, 1163, 1093, 1109 | 8.418 |

这些偏差按原样进入**待视觉验收试玩候选**，不冒称比例、脚点、握点、工具刚性或动态兼容已过。没有冻结该新动作批准目标轨迹；精确接触需要后续原生与用户逐组评审。

## 验证与局限

先运行结构测试：候选缺失时4项失败；来源/能力门禁缺失时先失败，再实现validate_water.py；南pour误把邻水当鞋底先失败，再修测量。最终：

```sh
python3 art/design/character-motion/adult-standard-v1/farming-four-directions-v1/water/test_water_candidates.py
python3 art/design/character-motion/adult-standard-v1/farming-four-directions-v1/water/validate_water.py
```

10项测试通过，8组/32帧来源和完整RGBA登记全部通过；含缺phase、未知方向/衣服、重复纹理、实际源哈希篡改的in-memory拒绝，真实源未篡改。各组明暗1×已目视。对这些新候选未在本子任务运行Godot、世界遮挡碰撞、十次连续动作、实际键盘/换衣/取消/失焦、导出或玩家存档测试；由主代理统一完成24组原生试玩验证。完整穿衣图不等于独立可组合人体/衣物/裤鞋/发帽，也不是生产角色迁移或用户认可。
