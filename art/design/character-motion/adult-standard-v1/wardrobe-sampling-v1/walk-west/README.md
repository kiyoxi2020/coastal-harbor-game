# Walk west wardrobe sample

审阅入口：`sample.json`；`evidence/display-1x-2x-light-dark.png` 为实际 display_scale 的 1×/2× 明暗对照，`evidence/independent-slot-board.png` 为共享身体、独立鞋、裤、前袖、完整衣身、后袖。

配方 top03 海军条纹长袖 + pants02 深蓝牛仔 + original-brown-shoes-v1。四帧 walk_west_0..3 各 80ms，循环 320ms；matching idle_west_0 一并交付。画布 512×768，root=(256,708)，display_scale=138/582，source density=1。

`references/` 包含原同 pose B、原部件/覆盖 mask、静态同源设计及 2× 完整参考；`sources/` 保留 GPT 1024×1536 原图；`projected/` 仅整画布统一 0.5 nearest，所有槽位原坐标提取，未单独移动或缩放。头、手、身体来自原同 pose，非跨 pose 贴脸。`ownership.json` 记录手工包络和鞋口多边形；原衣物 alpha 负责精确同 pose 接口，鞋口经独立部件板复核后以实际踝口线划分，未以颜色自动划分整个人物。覆盖与前后层序独立记录。

完整衣身采用额外无臂 GPT 源，隐藏衣料不挖手洞。动作四帧共用同一原坐标完整 torso 衣身源，袖子按原姿态独立；待机有独立完整衣身。`frames[].layers` 为真正可拆的 top/pants/shoes 槽；`shared_body` 清除三个槽的可见所有权。按 `visible_mask`/裤鞋 mask 选取各槽 RGB，并保留原整帧 alpha，即可逐 RGBA 重建 baked。前袖遮衣身由独立 pose mask 表达。

验证：`python3 check_sample.py <本目录>`，236 项断言通过，包括 inputs 完整哈希、路径限制、三槽与共享身体无重叠、按独立部件精确重建、每帧非衣 RGBA/alpha 零差、篡改哈希/越界路径拒绝。原生试玩由主代理执行，native_checked=false，user_accepted=false。这里只覆盖该固定抽样配方、方向、四姿态及待机，不代表款式全部组合或其他动作已兼容。
