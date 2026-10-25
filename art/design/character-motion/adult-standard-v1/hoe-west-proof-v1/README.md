当前修订见 [锄地 v2：两轮均未通过，失败源与测量已归档](revisions/v2/acceptance.md)。以下为此前 v1 记录。

# 西向锄地完整帧候选（待返工）

本目录交付同一 `adult-standard-v1` 的西向 `hoe` 四个完整关键帧：举高、挥下、接触、回收。沿用当前奶油短袖、橄榄长裤与棕鞋。**`rework_required`，未获用户批准，不能替换现行角色或宣称母版比例/工具刚性通过。**

入口：[可播放评审页](review.html)、[原生启动器](launch-native-review.command)、[原生明暗停帧](evidence/native-scale-review.png)、[十循环原生录像](evidence/native-ten-cycles.mp4)。HTML 支持播放、暂停、逐帧、速度和明暗背景。原生启动器独立运行9秒后退出，不载入玩法或存档。

## 来源与登记

使用 GPT built-in `image_gen`。三次提示词在 [prompts](prompts)，全部完整原图、哈希及参考来源在 [sources/source-manifest.json](sources/source-manifest.json)。母版来自 `selection.json` 的 `directional-brows-v3`；动作与衣着参照已认可的 `locomotion-v1/registered/walk-west-a-sheet.png`。实际模型精确标识未由工具返回，不臆称具体版本。

- v1 请求6帧超宽稿，输出2172×724、单格362px，人物被缩小，拒绝登记。
- v2 改4帧2048×768，输出尺寸正确，人物约520px高且根点偏右。保留为失败来源。
- v3 以v2为编辑目标，单帧walk为像素密度参考进行定点重画。动作清晰，尺寸2048×768，但头部与密度仍未达标。此次只保留可审查候选，不继续机械重试。

原稿名义每格512×768，但第1、3格的锄头延伸到相邻格约10px，直接切格会裁工具。`register_sources.py` 对每格左右各取24px额外范围，人工检查完整人物＋工具的连通主体后，仅移除相邻人物碎片与独立背景alpha噪点；保留主体原RGBA及2px原alpha边缘。所有帧统一扩为**768×768**、根点**[384,708]**，从原名义格整帧平移**[36,8]**。没有任何缩放、单独挪动衣鞋/手/工具、程序绘画或色彩覆盖。

显示继续使用 `138/582`，原生nearest；768px画布显示182.10px宽高。参考站立人物582px应显示138px，当前候选约570px、实际约135px。完整源/输出/显示尺寸均已如实记录，不用改变显示比例掩盖人物偏小。

## 已检查与遗留问题

已验证4帧尺寸、透明边界和完整人物/工具无画布裁切；每个保留的非零alpha像素均逐点等于原稿RGBA。四帧哈希不同，不用静态冻结冒充动作。`poses.json` 保存可见双手握点、鞋底接触和工具端点的人工近似观察，隐藏关节明确未知。接触帧为2，从350ms开始；900ms循环。该标记仅为视觉评审，不发出玩法事务。

Godot 4.7.1 Compatibility原生1100×650视口，完成30fps、271帧、9.03秒十循环Movie Maker录制，并目视检查同尺度明暗板。录像采用固定时间步；它证明连续原生渲染，不冒充真实时间输入/世界移动/碰撞证据。

仍须返工：

1. 头部约215px高，对照参考236px，约少9%；站立高度约570px，对照582px。姿态自然缩短不能解释整个头部长期偏小，故密度和身份比例检查不通过。
2. 人工观察的柄投影长约293、320、356、326px，明显变化；侧向姿态中工具刚性未建立，不能用独立缩放/移动工具补救。
3. 只有4个关键姿态，回收至举高的切换仍较突兀，当前节拍不是认可的最终动作节奏。
4. 未建立批准轨迹，不能声称脚点/握点误差≤1屏幕像素；尚无分层衣物、隐藏身体、换装、四向、发帽、业务接入或完整运动组合验收。

下一步应以单帧参考的头部真实尺寸及固定工具长度先重做抬锄/接触两帧，确认后再扩完整循环。此目录不改共享规范、状态记录、生产场景或玩家存档，也未导出、提交或推送。

## 复现

```sh
python3 art/design/character-motion/adult-standard-v1/hoe-west-proof-v1/register_sources.py
python3 art/design/character-motion/adult-standard-v1/hoe-west-proof-v1/build_review.py
art/design/character-motion/adult-standard-v1/hoe-west-proof-v1/launch-native-review.command
```

登记与证据绑定见 [registration.json](registered/registration.json)、[validation.json](evidence/validation.json) 和 [artifact-manifest.json](evidence/artifact-manifest.json)。`native_checked`仅覆盖完整帧候选的尺度/明暗及连续渲染观察，`motion_checked`与`user_accepted`均为false。

执行分工：受主代理委派，独立负责本目录完整动作美术与登记，选择理由为中复杂动作来源、坐标及原生证据可独立交付；实际模型标识由主代理按工具调用记录，不从当前上下文臆测。未创建嵌套代理，未返回模型用量，不做成本节省声明。
