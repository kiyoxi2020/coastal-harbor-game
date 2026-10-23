# 人物运动评审与游戏实现依据

2026-10-23原独立代码评审实际使用`gpt-6-astra high`；后续联网调研与版本2文档整理由主代理完成，未再次调用Astra。本页保留可核查的发现和来源，原建议步骤、资源合同、成本公式及验收清单已合并至[唯一人体制作规范版本2](../character-art-pipeline.md)，不再维护重复执行方案。

用户本轮已要求完成动态人体＋衣服组合设计。采用结论为：统一动作模板、衣身/局部视图复用、衣物覆盖与姿态前后关系分离、单一时钟、有限配方离线烘焙；先单侧四帧，再四向完整动作与动态混搭，最后扩体型及运动适配款数。设计更新不等于动画实现或视觉认可。

## 已核实事实与证据边界

以下为2026-10-23原独立评审读取代码、资源配置与目录得到的快照；本轮规范整合未重跑这些代码或验收。

| 已核实项 | 当前内容及其边界 |
|---|---|
| 静态母版 | 当前成年标准采用已认可面部修订v3；衣物构造要求每方向严格512×768，四向2048×768图。它是穿内搭的站立母版，非完整隐藏身体或动画骨架。 |
| 候选数与兼容 | `catalog.json`当前body/hair/top/pants/shoes/hat各10项；代表项兼容为`standing_0`。除独立身体候选外，配件限定`body01`。目录的`candidate`字段不能推导全部用户认可；body01已有选择记录与候选目录状态也需分别理解。 |
| 静态裁切 | `build_wearable_candidates.py`按方向使用手、颈、头保护域；上衣/裤腰有固定y区间；裤装按款/方向在局部带注册`boundary_y_by_x`，每列边界以下不归裤装；鞋另排除局部小腿皮肤。结果按归属域原位替换，包括透明像素，并检查其他RGBA不变。 |
| 头部裁切 | `build_head_body_candidates.py`使用站立脸/耳/颈多边形、短发/帽体积上限及特定头巾尾部例外；不含弯腰、抬头、转头或运动前后发层序。 |
| 已有主角 | `player.tscn`使用一个`AnimatedSprite2D`和`player_unified_frames.tres`；五组为**walk/run/hoe/water/harvest**，四方向、每向六帧，共120张384×384帧。walk 9fps、run 12fps循环；工具9fps不循环。当前脚本为`player.gd`与`player_tool_action.gd`；未找到指定名称`player_unified_renderer.gd`。 |
| 生产动作语义 | 走路速度72、跑步108；工具期间移动锁定，`animation_finished`结束工具显示。`harbor.gd`先执行成功的农事事务，再播放hoe/water/harvest。野外`collect`是另一业务入口，当前该入口未调用这套工具播放；不能把harvest与collect资源名称互换。 |
| 当前验收边界 | 候选README记载两套衣裤鞋的8种交叉状态×4方向静态预览；不是运动混搭。全部发帽组合、长裙/雨靴跨款接口、新体型适配都没有由这些结果获得保证。 |

证据位置：

- [候选README](../../../art/design/character-candidates-v2/README.md)、[目录](../../../art/design/character-candidates-v2/catalog.json)、[衣物构造](../../../art/design/character-candidates-v2/build_wearable_candidates.py)、[衣物规则](../../../art/design/character-candidates-v2/wearables-mask-policy.json)、[头身构造](../../../art/design/character-candidates-v2/build_head_body_candidates.py)。
- [现主角说明](../../../art/design/player-unified-v4/README.md)、[帧资源](../../../godot2d/resources/player_unified_frames.tres)、[主角场景](../../../godot2d/scenes/actors/player.tscn)、[移动脚本](../../../godot2d/scripts/player.gd)、[工具脚本](../../../godot2d/scripts/player_tool_action.gd)、[动作入口](../../../godot2d/scripts/harbor.gd)。
- [返工原因](NPC-rework-astra-review.md)、[唯一制作规范](../character-art-pipeline.md)。

原评审未逐张重审60项画面，未运行Godot运动小样，也未生成动画资源；这些事实不代表动态制作已通过。


## 静态提取和运行时遮挡解决的是不同问题

**提取遮罩**回答的是：在特定母版、特定姿态、特定源图中，哪一处像素归上衣，哪一处归脸、手、皮肤或背景。它决定把什么像素从完整图取出来，以及替换哪个旧表面。当前`boundary_y_by_x`适合登记该静态源图的裤脚；它不是随腿旋转的骨架，也不是所有姿态通用的裤脚曲线。

**人物内部遮挡**回答的是：这一帧近侧手是否盖住衣身，远侧手臂是否在背后，锄柄是否应穿过握持手的掌心，长发是否有一部分在肩后。需要这一个姿态的实际像素和深度关系。一个部件同时跨越前后关系时，应拆成语义子层，不能给整件永久设置一个z值。

**人物与世界的遮挡**回答的是：人物在树、柜台、门扇的前还是后。它由脚点、世界排序和真实物体轮廓决定。人物身高或挥锄外框不能替代脚点排序；现有门材质也不会自动理解新多层人物。若将来改为多层渲染，全部可见层、工具与阴影必须一致地服从原门过渡合同。离线合成整帧可减少这一接入风险，但仍需实际过门验证。

**接触与事件**回答的是：脚此刻是否承重、工具是否握住、锄头是否到达目标，业务效果何时发生。这些不是透明遮罩能够解决的问题。

| 姿态变化 | 站立规则失效的位置 | 正确资源或约束 |
|---|---|---|
| 走路摆臂、腿交替 | 站立手域会误切袖子或留下源稿手；两条裤腿相交后按每列单一最下缘无法表达所有孔隙和前后腿；鞋留在旧脚位置 | 逐姿态手/袖/左右腿/鞋的完整轮廓；必要的远近子层；脚接触相位 |
| 跑步抬膝与腾空 | 裤脚不再是固定y附近的轮廓；踝口角度、鞋底可见面和两腿深度变；站立脚底基准不能逐帧拉回所有脚 | 明确支撑、离地、腾空、落地；固定角色根点与合理步态起伏；每帧脚部姿态 |
| 挥锄举臂、弯腰 | 原保护框截掉举起的袖子/工具，脸颈域未随头躯干改变；衣摆露腰；两手交叉抓柄，工具穿过身体 | 统一动作母版；袖口—腕—手—握点配套；前后工具段；关键帧与目标接触点 |
| 裙摆/长衣/高靴 | 静态“裤/鞋归属”不能决定运动裙摆开合、膝部遮挡或裤腿是否塞进靴子；普通鞋适配不能推导长靴兼容 | 指定设计的动作适配版、腿部隐藏规则和兼容配方；不强行通配 |
| 发帽跟随低头 | 原短发上限会切断后脑发量；帽檐盖脸的范围发生变化；长发有肩前肩后部分 | 每姿态发帽体积、前后子层；帽下发型适配或明确不兼容 |
| 转向/动作切换 | 各层独立播放会出现身体已换方向但裤鞋还在旧帧；重置到静止帧导致脚点跳动 | 一份动作状态、方向、时间轴与原子配方切换 |

逐帧语义遮罩并非一概禁止。**为实际姿态记录衣袖覆盖手臂、帽檐覆盖头发是合法的真实遮挡；看到穿模后加任意横条擦掉身体则不是。** 应保存真实覆盖源、前后层及被遮挡的身体内容，不能靠结果图看不见就宣称肢体结构正确。

## 游戏实现调研与mask复用

调研日期：2026-10-23。范围为公开的一手开发说明、框架作者文档和开源项目资料；不据游戏画面猜测内部实现，也不将模组框架等同于原版全部实现。当前问题是复用与遮挡的制作方案，尚未实施运行时换装。

### 可核实的实际做法

| 游戏或工具 | 公开资料能确认的机制 | 对当前方案的意义及证据边界 |
|---|---|---|
| 《饥荒》及Klei人物动画管线 | Klei开发者Kevin于2012年说明：人物build由多个身体部件及各部件的多个视图构成；动画记录部件二维变换及当前视图，运行时组合显示。2014年Klei的GDC演讲摘要也明确提到服装/颜色替换及动画复用。 | 可以复用部件与动作，仅在投影改变时换部件视图。不是一张完整静态衣服靠mask完成全部运动。历史开发说明没有公开完整换装层序算法，不据此声称当前DST版本采用某种像素mask或shader。[开发者原答](https://gamedev.stackexchange.com/questions/44319/what-animation-technique-is-used-in-dont-starve)、[GDC演讲摘要](https://gdcvault.com/play/1020949/2D-Animation-at-Klei)、[GDC官方视频](https://www.youtube.com/watch?v=8_KBjd0iaCU)。原答本次搜索返回正文，直接打开曾失败；GDC摘要可检索，直接页面当前维护中；未声称看完视频。 |
| 《Terraria》的tModLoader绘制接口 | `PlayerDrawLayers`区分Skin、Torso、Leggings、Shoes、BackArmShirt、ArmOverItem及Composite变体；装备定义提供`HidesArms`、`HidesHands`、`HidesTopSkin`等身体可见性规则。 | 与“按衣物控制人体是否显示”直接相关，但这里的隐藏标志是身体区域规则，不能冒称逐像素动态mask；衣身、袖臂、持物层仍分别处理。[绘制层](https://docs.tmodloader.net/docs/stable/class_player_draw_layers.html)、[衣物隐藏规则](https://docs.tmodloader.net/docs/stable/class_armor_i_ds_1_1_body_1_1_sets.html)。 |
| 《星露谷物语》的Fashion Sense模组框架 | 上衣、袖子、裤、鞋等独立外观；袖子可以有动画，`AppearanceSyncing`可使鞋随裤子的动画更新，`DrawOrderOverride`控制前后绘制。作者v7.5.0发布说明增加按动画帧覆盖层序。 | 适合借鉴“衣身与袖子分开＋统一动作相位＋需要时变层序”。这是该框架的实现证据，不是原版渲染器的完整说明。[袖子资源](https://github.com/Floogen/FashionSense/wiki/Creating-a-Sleeves-Content-Pack)、[同步](https://github.com/Floogen/FashionSense/wiki/Appearance-Syncing)、[层序](https://github.com/Floogen/FashionSense/wiki/DrawOrderOverride-Property)、[发布记录](https://github.com/Floogen/FashionSense/releases/tag/v7.5.0)。 |
| Flare开源游戏/引擎 | 动画资源定义图集、帧数、时长；`render_layers`按方向指定槽位层序，`animation_slots`给槽位分配动画。 | 提供另一种可核查的分层动画方案；这份文档只证明按方向排序，不能扩述为已支持每帧深度mask。[项目属性文档](https://github.com/flareteam/flare-engine/wiki/Attribute-Reference#statblock-render-layers)。 |
| Spine官方换装示例（工具，不是某款游戏实现） | skin由attachments及可选bones/constraints组成，同一骨架动画可换用不同附件；多个衣物skin可组合。 | 将动作与外观分离的成熟工具路线。仍需制作可绑定部件、关节隐藏区和特殊视图；工具能复用动画不代表现有静态PNG已经可绑定。[Skins说明](https://esotericsoftware.com/spine-skins)、[Mix and Match](https://en.esotericsoftware.com/spine-unity-mix-and-match)。 |

以上证据支持几种并存的路线，不能归纳为“现有游戏全部使用同一方法”。这些资料为版本2的部件复用与局部换帧设计提供依据，不能替代本项目运动小样验收。

特别注意：[Fashion Sense的SkinToneMasks](https://github.com/Floogen/FashionSense/wiki/Skin-Tone-Masks-Property)把指定RGB替换为玩家肤色阴影，是调色规则，并不根据人体自动计算遮挡；不能因名称含mask就作为本方案的直接实现依据。


## Godot接口依据

以下为原主代理核对的官方接口说明，版本2设计仍应在实际接入时验证。

- [Cutout animation](https://docs.godotengine.org/en/stable/tutorials/animation/cutout_animation.html)说明切纸式动画与逐帧动画可混用，手脚等复杂部位可用不同绘制帧。引擎具有骨架工具，不代表站立图片已经具备可绑定接缝和运动姿态；推荐路线是本项目约束下的判断。该教程注明尚未完整更新到4.7，仅用于概念依据。
- [AnimatedSprite2D](https://docs.godotengine.org/en/stable/classes/class_animatedsprite2d.html)明确改变animation或直接设置frame会重置对应进度，提供set_frame_and_progress保持帧相位。它支持同步所需接口，但不会替项目自动维护多部件的公共时钟或生成缺失姿态。
- [CanvasItem](https://docs.godotengine.org/en/stable/classes/class_canvasitem.html)区分绘制层序与Y排序；Y排序只在相同z_index间成立。世界按角色根点排序和角色内部手/袖/工具前后关系应分别设计，再整体服从门、树等世界遮挡。

## 当前状态与制作入口

当前六类各10项是静态候选目录，最终视觉交接尚未结束；body09男童高度接近成人，冻结其动作模板前需修正。现有候选不是隐藏身体齐全的运动库。

后续仅按[统一规范](../character-art-pipeline.md)执行；本页不再保留“先扩静态库后另行动画”“每姿态独立生图”或相互重复的分阶段建议。本次只整合设计，未生成新动画、修改运行时或进行Godot运动验收。
