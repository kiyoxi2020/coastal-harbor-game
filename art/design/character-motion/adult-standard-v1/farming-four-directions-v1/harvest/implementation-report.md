# 采收四方向与两上衣

8组32个真实关键姿态，ready/reach/pluck/recovery，200/250/250/300ms。原西向v2蹲身/持物两源完整RGBA复用为reach/recovery，另外两阶段GPT新制；其他方向独立完整GPT姿态，不镜像冒充。南B/东B由主代理GPT同姿态换蓝长袖；复用hoe_long_sleeve(gpt-6.1-sol high)独立制作西B，water_south同模型独立制作北B。无嵌套。

所有正式源1024×1536，两倍idle源密度；共同1536×1920画布/root[768,1600]、scale138/1164。source→output只整帧整数平移，输出未裁掉源像素；每组registration-config登记真实可见鞋/支撑参考与人工头框，未知或被遮挡的关节/握点明确null，不按总高比例推算。Root是美术注册参考，不能把它当作已批准支撑轨迹；完整姿态生成仍有投影变化，保持待用户视觉评审，不局部缩头脚。采收北向手与白萝卜在身体远侧，保留自然遮挡与两侧可见叶片。

最初四格源仅1024×1536、格内密度不足，作为失败稿存南A，不正式使用；所有后续正式源均逐帧GPT。南B pluck一角alpha1/255（其他角0），是不可见的低alpha量化，未程序擦除或强制不透明；结构门禁容许≤1/255并在测量明示，原生明暗图另检查可见矩形噪声。其他正式源四角0。

4项结构/来源/完整范围/缺phase与改hash拒绝测试在8组上通过；32源与registered crop逐RGBA一致。build_candidate.py为纯登记工具，原源/prompt/references/失败稿保留；固定穿衣图未分层，modular/geometry_approved/accepted/gameplay_available均false。原生完整24组由主代理统一采集，不能据本4项结构测试宣称动态接触或用户认可。
