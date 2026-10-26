# Harvest north-B 完整源交付

2026-10-26。只追加north-B的4张完整GPT源、提示词/来源/观测，不修改A、共享登记器或Godot；water八组此前已冻结，未再改candidate。执行gpt-6.1-sol/high/fork_turns=none，无子代理。

每张分别以对应north-A完整姿态为编辑目标，已认可B_3背向长袖为设计参考，调用前已逐张view_image。仅将奶油短袖改为到腕蓝长袖/深色袖口，完整新穿衣图；保留背头/耳/裤鞋/萝卜及前后关系。没有眼脸画在后脑，没有把手或白萝卜穿到蓝色后背。已看4姿态源诊断板source-review.png。新源实际均1024×1536 RGBA，真正透明负空间；4唯一文件。未脚本补色、缩放、镜像或贴旧脸手。

| 姿态 | 完整源 | SHA-256 | 可见鞋底参考中点（源px） |
|---|---|---|---|
| ready | [sources/ready.png](sources/ready.png) | `30abac7019fdc2923d0ca55cea08fc5ebdfb3b447fe690f6d275bc551a143b27` | [553, 1408] |
| reach | [sources/reach.png](sources/reach.png) | `d8a2eb8e1b613247c8f6a3e20f6f7cbd45f4a77464855d9034ae57b6077c7e49` | [549, 1385] |
| pluck | [sources/pluck.png](sources/pluck.png) | `0ed022b592487c30d8e6148cf3eac54961e11efacf6cd2b2b67075d2c2109c16` | [560, 1423] |
| recovery | [sources/recovery.png](sources/recovery.png) | `7938b256b9ef3d9a0accdcca22c7fe17f4a9512811a9d1d9fdebd2881bf7bfd4` | [524, 1456] |

[source-manifest.json](source-manifest.json)绑定源/提示词/参考/实际量测/量测工具；generation-provenance.json保存原生成路径及内置GPT调用来源。4次首轮调用均完成，没有丢弃稿；所有原图完整保留。精确图像模型ID未由工具返回，不猜测。

手动选鞋ROI后，measure-sources.py只读取真实alpha≥128的最低可见鞋底行，保留每只鞋各自y、端点及A/B差；没有按总高百分比定位，也没有挪动鞋像素。manual-foot-measurements.json中的参考中点仅为源图观测，**不是世界根或批准支撑轨迹**。ready右鞋最后一行的中心较A差28源px，末行轮廓对1px边界变化敏感，不能据此直接认定整鞋移动28px；主代理应按全鞋轮廓独立确定root，其余鞋底中心差0–2源px/y差0–1源px。隐藏髋膝踝未推断。

验证：执行measure-sources.py成功；读取source-manifest逐项核对全部实际SHA，4帧原生尺寸/模式/alpha/唯一SHA均通过，结果source-validation.json。未创建或修改harvest注册candidate，未执行世界/原生十循环、衣物独立分层、精确接触或用户认可；主代理统一登记与24组试玩收证。完整蓝衣源不等于动态可组合衣物。
