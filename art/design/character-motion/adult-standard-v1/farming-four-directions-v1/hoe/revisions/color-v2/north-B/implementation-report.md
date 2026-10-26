# north B 锄地衣色修订 color-v2

2026-10-26，gpt-6.1-sol/high。仅本目录；未修改旧 hoe、水、采收、共享 compositor/登记器、Godot 或 catalog。无子代理、未提交。候选已冻结，后续仅补不在 inputs 中的说明/诊断。

candidate SHA256：`6bf8e60f1cb6bc4be433aef34da120fd8781a24ba140ec3bcb037e80f1e548b8`。parent SHA256：`a3e4f22b650cd93bbf87d4264e5d2e37cbc6a89bb5a654c6bd0dd22e74762149`。

每帧原源1024×1536；注册1536×1792、root[768,1544]、scale138/1164；180/220/140/260ms，总800ms，与旧组完全相同。源原生显示约121.40×182.10px，注册画布约182.10×212.47px。head/foot/grip/root/时序深拷贝，仅 source 改为合成结果。

内置 GPT imagegen 逐帧完整源编辑。已先 view 原 hoe 和同向已认可 water/harvest 色参考。首轮偏暗；第二轮使用 harvest 中等丹宁蓝参考，保留自然折面，最终全部选 attempt2。共8次调用（4帧×2），所有 raw/prompt/失败色稿保留。原生成路径见 references/generation-ledger.json.txt；精确图像模型 ID 未返回，不推测。

共享 compose_color.py 原样使用、源码快照已入 references。每帧手工声明实际衣身/袖子 polygons，颜色只辅助边界。补齐遗漏肩袖和衣身，再排除腋下/袖下的透明蓝晕光；没有改5%门限或缩 owner 掩盖错位。原合理深色领口/黑描边部分保留。

color_revision 含 parent_candidate_sha256/compositor_sha256，以及 frames[phase,mask,raw_gpt,ownership_polygons,composition_info]。原源/raw/mask/owner/工具快照均绑定 inputs，旧 candidate 为 .json.txt，避免误解旧相对路径。

## 验证

evidence/exact-color-verification.json 绑定最终候选与验证工具 SHA。register_clip.validate_data、所有 inputs/artifact_digest 均通过；4帧源和 registered 的 mask 外 RGBA 差异=0，全 alpha 相同，mask 内非 raw RGB 像素=0，低 alpha 外部晕光 paint=0。非 source 的头/脚/握点/根/时序字段完全相同。没有程序调色、局部缩放、移位、贴脸手或替换工具；raw 中其余变化均未进入最终源。

| phase | 原诊断中位 | 最终诊断中位 | fallback |
|---|---:|---:|---:|
| ready | 115 | 105 | 0.643% |
| lift | 123 | 103 | 0.166% |
| contact | 115 | 105 | 0.121% |
| recovery | 121 | 105 | 0.064% |

诊断为 A>220、B-R>35、B-G>15、R<120、G<150 蓝像素的 uint8 Rec709 亮度中位数，仅参考，不是正式 owner。门限固定5%。部分折面略高于90–100参考区间，未为统计压平合理明暗；新颜色仍待原生/用户看。

[1×/2×明暗与认可 water/harvest 对照](evidence/approved-color-comparison.png) 已更新至最终输入，绑定见 approved-comparison-bindings.json。仅 CPU nearest 静态诊断，不冒称原生。已看源图/细节和对照；本子任务未运行 Godot 原生、世界玩法、导出或玩家档。主代理统一集成/收证。旧非颜色认可范围保留，新颜色 pending，不新增独立可组合/生产迁移认可。

复核（只读验证，不重建冻结输入）：

```sh
python3 art/design/character-motion/adult-standard-v1/farming-four-directions-v1/hoe/revisions/color-v2/south-B/verify_revision.py north-B
```
