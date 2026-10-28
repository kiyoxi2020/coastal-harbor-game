# Run east wardrobe sample

审阅入口：`sample.json`；`evidence/display-1x-2x-light-dark.png` 为实际 display_scale 的 1×/2× 明暗对照；`evidence/independent-slot-board.png` 为共享身体、独立搭扣鞋、原裤、前袖、完整衣身、后袖。

配方 top04 砖红绳纹毛衣 + original-olive-pants-v1 + shoes04 棕色搭扣鞋。四帧 run_east_0..3 各 80ms，循环320ms；matching idle_east_0 一并交付。画布512×768、root=(256,708)、display_scale=138/582、source density=1，与原当前 B 完全一致。

`references/` 保存原同 pose B、原层/覆盖 mask、同源静态设计及整帧 2× 参考，`sources/generation-index.json` 保存每次 GPT 输出路径及 prompt。11 张 GPT 1024×1536 原图全部保留，包含5 outfit、5 complete-torso v1、1 isolated-torso v2。`projected/` 仅完整画布统一0.5 nearest，无任何部件局部拟合、位移或缩放。人物头手身体来自原同 pose，不采用 GPT 改动，也不跨 pose 拼脸。

`ownership.json` 逐帧保存手工鞋口/踝口多边形及折腿包络。原同 pose cloth alpha 提供精确衣身/袖口接口；只有踝口手工窄区域使用原橄榄裤色辅助边界，未对人物自动按色分层。完整 torso 在应用 pose 遮挡前保存，手臂洞不永久挖入衣身。原前后 arm coverage 与层序另行保存；原鞋 source 不充当新款搭扣鞋部件。

`frames[].layers` 的 top/pants/shoes 为实际独立槽，`shared_body` 清除三个可见衣物槽。按 top visible_mask 和裤鞋 mask 选取各部件 RGB，再使用 frame_alpha，即可逐 RGBA 重建 baked。裤槽保持原裤 RGB，身体/手/脸和 mask 外 RGBA、整帧 alpha 均保持原图。

`run_east_3-complete-torso-v1` 下摆缩短，拒绝用于最终 source 并完整保留；v2 改为同坐标孤立 torso 输入后恢复下摆。`run_east_2-shoes-only-input-2x.png` 为定位早期 owner 包络含裤色的诊断，未用于 GPT 输出，也非最终鞋槽；最终 mask 已依实际踝口线精修。原母版的低透明度外缘/游离 halo 原样保留，未以擦除修改原认可 alpha。

验证：`python3 check_sample.py <本目录>` 264项断言通过，包含 inputs 哈希、相对路径限制、三槽与共享身体无重叠、部件精确重建、5帧原非衣 RGBA/alpha 零差、篡改哈希/越界路径拒绝。1×/2×明暗板及独立槽板已目视。原生连续跑动/停步由主代理验收；native_checked=false，user_accepted=false。状态 sampled-not-exhaustive，只证明此固定配方/方向/5姿态，不宣称全部款式、任意裤鞋混搭或其他体型已兼容。
