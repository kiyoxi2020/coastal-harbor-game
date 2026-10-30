# 南向压帽短发完整来源候选

本包保留r004完整GPT原图与提示词，以及直接编辑链r002/r003原图、提示词。只登记真实`water_south_B_ready`投影；生成脸、眉、耳、手、身体均为参考上下文，不能进入角色。

入口为[source.json](source.json)。[归属语义](metadata/ownership-semantics.json)记录人工刘海/发冠/两鬓边界及负向脸眉耳区；色板仅辅助已许可区域，不独立决定归属。[raw ownership](metadata/hair-ownership-raw.png)选中59,493像素。293个耳下探索像素确认为生成脸颊/耳外描边，排除记录与完整原图同时保留，不是删真正发片修错位。

[归一与实测锚](metadata/normalization-and-registration.json)：完整1122×1402源按统一256/187、两轴逆仿射187/256、NEAREST、零offset到1536×1920；raw frame root[561,1168.75]精确映射[768,1600]，不是取生成脚底。normalized耳中点[765,730]到canonical整数登记点[768,729]，一次整源整数平移[3,-1]。实际目标耳中点y=728.5，取整误差和各眼耳残差均保留。

唯一登记候选为`hair-chestnut-short-v1`适配`r002`，独立annotation为`south-headwear-r001`。r004源本身不写配对声明；typed compatibility属于适配目录，分别绑定本发源intrinsic身份与真实全帽身份，不形成共享source bundle哈希环。

当前仅完成同pose组件源重建；未完成新top03衣装接入、其他姿态复用、完整clip/全包、Godot原生连续播放、用户认可或生产发布。r002最初调用的确切输入文件路径未从原调用记录独立重建，source.json明确区分提示词声明与已保存的后续直接输入，不虚构来源精度。
