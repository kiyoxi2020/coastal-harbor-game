# 西向锄地条纹衫抽样

审阅入口：[明暗1×/2×及matching idle](evidence/comparison-1x-2x.png)、[独立槽源/共享前景](evidence/independent-slot-sources.png)、[来源边界诊断](evidence/lift-shoulder-source-diagnostic.png)、[sample.json](sample.json)、[实施报告](implementation-report.md)。

仅top03海军条纹衫＋original-pants＋original-shoes，西向ready/lift/contact/recovery四真实姿态和同配方idle，status=`sampled-not-exhaustive`。原catalog-color-v2西B是姿态/身份母版；本组合的视觉与原生认可另待主代理绑定。

冻结sample SHA256：`99f31cfecc7cdc3c84d4d22fcfa1f1dc9a64e5359ffa7493a867be1b1c7949bd`。动作800ms，1536×1792/root(768,1544)/scale138÷1164/密度2；源1024×1536。idle512×768/root(256,708)/scale138÷582；GPT1024原稿只整帧nearest减半，没有局部衣物缩放。显示画布约182.10×212.45px；idle约121.40×182.10px；2×再统一翻倍。

每姿态parts中top/pants/shoes独立布面，source ownership、当前coverage与occlusion分离；同pose脸手/锄和原版型轮廓在`shared_same_pose_foreground_and_contour`。完整GPT anchored衣身源保留，不在完整源上按当前手/柄挖洞。当前可见源与必要隐藏源分别引用；版型黑线/原navy接口合法保留，未宣称裸身体或任意新剪裁。

抬锄主源第3稿的120个肩缘透明点，用同pose第2稿的真实条纹布面原坐标补齐；两raw/补面mask/选择后的density source都绑定inputs，未程序造色、平移或缩放。

复核：`python3 art/design/character-motion/adult-standard-v1/wardrobe-sampling-v1/hoe-west/build_samples.py validate hoe-west`；测试：同目录`test_build_samples.py`，8项通过。
