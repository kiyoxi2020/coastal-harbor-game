# 南向浇水衣物组合抽样

审阅入口：[明暗1×/2×与同配方idle](evidence/comparison-1x-2x.png)、[独立槽源与共享前景](evidence/independent-slot-sources.png)、[sample.json](sample.json)、[实施报告](implementation-report.md)。

配方是原蓝长袖＋pants02深蓝直筒牛仔＋shoes04棕搭扣鞋。仅南向ready/raise/pour/recovery四姿态及matching idle；status=`sampled-not-exhaustive`。原三农事已认可catalog-color-v2的同向B是姿态/身份母版，当前抽样衣物未获用户认可，原生验证由主代理另行绑定。

冻结SHA256：`9b2c74d2755c658545c9b15e86d77d1212d715e167d7c05a7a39d6bef730fc11`。动作1000ms，1536×1920/root(768,1600)/scale138÷1164/源密度2；idle512×768/root(256,708)/scale138÷582。动作源原尺寸1024×1536；idle GPT原稿1024×1536，仅整帧nearest统一减半，不单独缩放衣物。显示画布约182.10×227.63px，idle约121.40×182.10px；2×按上述显示尺寸翻倍。

每姿态的parts目录包含top/pants/shoes独立完整布面源及visible派生PNG，masks分开保留source ownership、当前coverage与occlusion；原同pose脸手、壶、水流和版型黑轮廓在`shared_same_pose_foreground_and_contour`。当前固定版型轮廓合法复用，并非裸身体或任意剪裁能力。完整源不按当前手或壶永久挖洞，相关隐藏布面来自同pose GPT anchored completion；没有把带壶的full稿当作无洞部件。

复核命令（仓库根）：`python3 art/design/character-motion/adult-standard-v1/wardrobe-sampling-v1/hoe-west/build_samples.py validate water-south`。构建器快照已绑定在references/build_samples.py.txt，后续hoe helper变化不影响冻结输入。
