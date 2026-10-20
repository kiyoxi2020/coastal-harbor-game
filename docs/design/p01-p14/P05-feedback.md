# P05用户反馈修订与统一人物重制

2026-10-19。用户要求提高素材清晰度、图标Tab底栏、人物动作、草地限制、删除屋右箱子；随后明确要求用GPT重做完整走/跑/锄/浇/采集动作以解决素材脱节。本记录覆盖本轮最终状态，P05旧验收仅作历史基线。修改未提交、未推送、未导出，P06未开始。

## 已完成

1. 土/菜/花/石从同一原始GPT图集提取8倍纹理采样，保持世界大小；去掉土壤shader按16像素硬量化。资源assets/farming-polish-v3，原图/逻辑尺寸/根点元数据保留。
2. 底部奶油色四图标栏，GPT锄头/蓝水壶/种子袋/手。Tab循环，1–4直选，B打开手账；面板内Tab仍关闭面板。种子小选择条只在选择种子时显示，不增加工具获取系统。
3. 最终人物使用GPT新生成的统一套装：走路、跑步、锄地、浇水、采集各四向六帧，共120帧。五张原图/提示词/可复现切图脚本/原生预览位于art/design/player-unified-v4。一个AnimatedSprite2D共用20组SpriteFrames和门遮挡材质；停止使用旧走路+新单Pose、身体shader变形和透明交叉淡化。所有图像注册到384画布、相同世界缩放与地面根点；工具动作锁移动/重复请求，结束信号恢复待机，保存失败不播放成功动作。
4. Shift跑步108单位/秒，普通走路72；真实门过渡仍按原72速度和原遮挡顺序，不被跑步修改。
5. 实际GrassField/StonePaths整格检测，石路和部分跨路格拒绝。发现原右菜地有6格覆盖门前石路后，将两区放回完整草地：GardenA(84,224)、GardenB(164,224)，仍各4×2、16格，cell ID和存档不变；两区边界x52..116、132..196，保留16单位草间通道，相邻花石同步移到边缘。本轮未扩展全地图无限耕作。
6. 删除截图所指屋右StorageCrates美术与室外操作点，返回无效室外storage_point防止隐形箱子；仓储仍在屋内原有箱子。鱼摊右侧箱子不属于用户截图对象，保留。

## 关键文件

`scenes/actors/player.tscn`、`scripts/player.gd`、`player_tool_action.gd`、`resources/player_unified_frames.tres`、`assets/player-unified-v4/`负责统一角色。

`farm_plot.gd`、`farm_region.tscn`、`harbor_exterior.tscn`、`farm_soil.gdshader`、`farm_tools.tscn/gd`、`harbor_exterior.gd`、`harbor.gd`及`house_session.gd`负责高清环境、底栏、土地和仓储变更。原素材和历史试验保留，不再作为运行时角色来源。

## 验证

- RED：最初高清土/图标/Tab/箱子/地面API/动作API七项失败；草地检查进一步发现原右区六格压路；新整套SpriteFrames不存在时失败。先复现再实现。
- test_unified_player.gd：206/206，20组×6帧、画布、循环/非循环、真实图像差异，12次动作完整结束并恢复待机。
- test_action_registration.gd：22/22，120帧共享画布/锚点，组内不逐帧缩放。
- test_unified_player_native.gd：136/136，120帧原生渲染、Shift实际72→108速度/动画、12次工具动作均实际播放0..5帧，碰撞脚底不动并正常回待机。证据/private/tmp/coastal-unified-native，日志/private/tmp/coastal-unified-native.log；长期预览[原生动画GIF](../../../art/design/player-unified-v4/native-preview.gif)。正面五动作接触表已查看，非只看生成概念图。
- 相关七组回归455项通过：polish32、grid_scene16、transactions121、day75、journal47、scene_contracts132（batch=6）、house_save32。日志/private/tmp/coastal-unified-test_*.log。
- test_life_farming_native.gd：159/159；真实走遍16格、Tab图标底栏、只许草地、动作帧变化/固定脚底、4晚进屋睡眠、两作物收获与存档重载全部通过。日志/private/tmp/coastal-unified-farming-native.log，存档/private/tmp/coastal-unified-farming-save。原生走路/跑步/工具序列与真实门扇过渡均已覆盖，不沿用旧角色117项报告。

边界：以上为真实引擎渲染与键鼠事件注入，未做人类物理键鼠长时间试玩；GPT逐帧仍可能需要进一步美术润色，不宣称达到手工商业动画质量。P06正式买种/售货、P07完整7日经济与16格劳动量仍待开发；未重导出、未验证Windows/Intel。
