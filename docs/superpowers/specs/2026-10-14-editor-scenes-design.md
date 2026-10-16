# 编辑器可维护场景迁移设计

日期：2026-10-14。状态：设计完成，尚未实施或验证迁移效果。本稿以当前工作树为基线，不以旧提交替换已完成的门修复。

## 目标、边界与备份

让主菜单、HUD、暂停中的手账、关卡、角色和复用 UI 在 Godot 编辑器中拥有实际节点和可编辑资源；运行时仅绑定数据、处理输入、更新状态。保留现有中文、布局、像素素材、交互、存档、碰撞和门过渡；不添加独立 Esc 暂停菜单、任务、交易等新功能。现有暂停界面就是 B/Tab 手账及其设置页，`pause_menu.tscn` 承载这个已有行为，不新增一种玩法状态。

已阅读 AGENTS.md、PROJECT_STATE.md、HANDOFF.md、南门规格和库存手账规格。当前有用户未提交的门遮挡、导出和交付修改，禁止 reset、覆盖或重建旧提交。主代理已创建 `/private/tmp/coastal-editor-scenes-backup-20261014-220123/workspace.tar.gz`，附 working-tree.patch、git-status.txt、head.txt；备份须在实施前验证可列出目标脚本及未跟踪文件。不要覆盖 `交付与预览/2D/`，本任务默认只交付源码；导出验证若需要，输出到新的临时目录。

审计范围为 `rg --files -g '*.gd' -g '*.tscn' -g '!**/.godot/**'` 返回的工作项目文件：56 个，55 个脚本、1 个场景；其中生产脚本27个、测试26个、美术工具2个。忽略规则中的 work、archive、builds 历史复制不属于当前工程，不迁移这些旧快照，也不读取缓存和二进制。下面逐文件列明处理方式。

## 可选路径

| 路径 | 成本与结果 | 判断 |
| --- | --- | --- |
| A：按场景逐批迁移，保留状态与公开接口 | 先序列化现有外观，测试后删除对应构造器；每批可回退，保持已有驱动可用 | 推荐 |
| B：一次重写为全新控制器、信号总线与关卡框架 | 会同时改变节点、生命周期和状态接口，难以定位视觉与门修复回归 | 不采用 |
| C：仅添加 `@tool` 让原构造器在编辑器执行 | 改动较少，但编辑器仍无可靠静态源，重复生成与覆盖 Inspector 的问题继续存在 | 不满足目标 |

## 主要发现

目前 `harbor.tscn` 只有 Harbor 根节点。`harbor.gd` 创建地面、树、道具、碰撞、角色、镜头、HUD 和手账；`house_session.gd` 随后重组层级、替换房屋脚本并手动调用 `_ready()`。`journal.gd` 每次 render 删除整棵 UI，重新创建按钮和布局。HUD 的 layout 在窗口变化时重写位置尺寸。人物帧、主题和门碰撞也在启动时创建。因此仅拆几个空场景或把 new 换为 instantiate 仍不能满足可编辑性。

高风险点包括：孩子先于父节点 ready；手账旧测试依赖按钮名和公共字段；存档安全位置仍用数据脚本中的矩形；房屋排序点在 ready 中从 Y190 改为 Y165；室外只跨门槛8单位并关门遮挡后淡出。迁移必须保留这些最终行为，不可重新采用废弃的深走门洞方案。

## 目标场景边界

所有路径以下列 `godot2d/` 为根。

| 场景/资源 | 固定内容 | 脚本职责 |
| --- | --- | --- |
| `scenes/harbor.tscn` | HarborExterior、HouseInterior、WorldCamera、HUD、Journal、HouseSession（含 RoomTransition）实例 | harbor.gd 保留启动、交互协调和验证入口；通过节点引用获取对象 |
| `scenes/world/harbor_exterior.tscn` | Terrain、WaterDetail、DepthSortedObjects、5棵树、固定道具、6个拾取点、室外门、全部静态碰撞、出生及交互 Marker2D；初始单一玩家实例放在排序层 | 运行时采集点显隐；不重建树和碰撞 |
| `scenes/world/house_interior.tscn` | 地板、墙、边缘、地毯、11件家具、家具底座及墙碰撞、室内门、出生及交互点 | 室内引用与数据读取；布局不在 ready 中计算 |
| `scenes/actors/player.tscn` | CharacterBody2D、CollisionShape2D（10×6）、AnimatedSprite2D、脚底阴影 | 移动、朝向、动画和真实门洞遮挡；保持单一玩家跨场景 reparent |
| `scenes/world/house_exterior_art.tscn` | 已开门洞的四片 AtlasTexture/Sprite2D、固定图像偏移、排序原点 | 无需启动改 Y；最终原点 Y165，保留原画世界位置 |
| `scenes/world/interactive_door.tscn` 及 indoor/outdoor 两个变体 | DoorCollision、JambCollision 两个柱碰撞、门框、门槛、室外暗部、门扇视觉 | set_pose 只切门扇状态与通道碰撞；不生成节点；入口方向/接近点可编辑 |
| `scenes/world/furniture.tscn`、`tree.tscn`、`prop.tscn`、`forage_pickup.tscn` | Sprite/图标、实际锚点与必要底座碰撞；各关卡序列化实例 | 仅采集高亮及状态更新；家具等优先无行为脚本 |
| `scenes/ui/hud.tscn` | 全屏 Control、顶部/底部条、标题、区域、背包按钮、提示、Toast、地点面板 | 更新动态文字、显隐、倒计时；锚点替换 layout 的尺寸重写 |
| `scenes/ui/journal.tscn` | 常驻 CanvasLayer，主菜单、pause_menu、storage、弹窗容器实例 | 现有 journal.gd 管理 mode、暂停、焦点、库存请求、保存失败；不删除整棵界面 |
| `scenes/ui/main_menu.tscn` | 标题、继续、新游戏、设置、退出、人物预览、状态文案 | 动态启用继续/新游戏与读取错误信息；按钮行为保持 |
| `scenes/ui/pause_menu.tscn` | 原手账边框、背包/个人/设置页签、返回、底部说明、三个固定分页实例 | 显示当前分页，不新增独立暂停入口 |
| `scenes/ui/pages/bag_page.tscn`、`profile_page.tscn`、`settings_page.tscn`、`storage_page.tscn` | 五个筛选按钮、24个背包槽；个人头像与资料；三音量条和已有按钮；仓储24+48格及滚动区 | 状态数据刷新、按钮禁用与信号；不重写手工偏移 |
| `scenes/ui/components/inventory_slot.tscn`、`item_details.tscn`、`backpack_button.tscn`、`portrait.tscn` | 可复用槽图标/数量/焦点、详情控件、背包按钮、头像 | 更新内容；空槽复用已有图标节点并隐藏 |
| `scenes/ui/dialogs/name_dialog.tscn`、`quantity_dialog.tscn`、`confirm_dialog.tscn`、`save_error_dialog.tscn` | 各弹窗固定遮罩、面板、输入框和按钮 | 显示动态标题/数量上限，默认取消，管理 Callable；关闭时隐藏并清空操作 |
| `scenes/ui/transition_overlay.tscn` | CanvasLayer 40、全屏 Fade，默认 alpha 0、鼠标忽略 | 现有 transition 状态机只 tween alpha |
| `resources/ui/pixel_theme.tres`、像素 StyleBox `.tres`、`resources/player_frames.tres`、人物遮罩材质 `.tres` | 当前字体、大小、颜色、边框，四方向各4帧7FPS及现有着色器 | 资源本地化，运行时不替换 Inspector 指定资源 |

可复用场景只有内容重复或本身独立时拆出，不为每个 Label 创建一个脚本。保留 `scene.player`、`scene.hud`、`scene.sort_layer`、`home.interior`、`journal.mode` 等现有公开接口，避免借此重写全部测试。节点明确命名，按钮 `continue`、`close`、`bag_0` 等既有测试 ID 保留。

## Inspector 与数据的唯一来源

1. 固定位置、尺寸、文字、字体和主题直接序列化到场景/资源。HUD 使用 full-rect 根、顶部和底部锚点以及固定 offsets；手账保持现有 Rect2(80,48,1120,624)，不趁机重新设计响应式布局。容器只用于原来确实规则排列的区域；需要单独编辑偏移的布局不用容器强制回写。
2. 动态文字是姓名、数量、物品详情、提示、存档结果和区域名等状态字段。固定标题与按钮文本不在 refresh 中重新赋常量。需要格式拼接的固定前后缀作为导出模板维护；运行时刷新数据并不意味着禁止动态内容变化。
3. 现有 harbor_data/room_data 中的布局不能长期作为第二份真值。每批迁移将对应数据读取改为场景中的 Marker2D、实际碰撞与家具实例；纯校验函数可从 PackedScene 的未入树实例读取配置，避免加载时触发 ready、读写玩家存档。初期可用一致性断言对照旧常量，批次完成后旧布局构造不再驱动场景。库存 ID、容量、存档版本等业务常量仍留在数据脚本。
4. 安全落点检测、门前范围、拾取最近距离与实际场景同源；移动一个家具及其子碰撞后，保存位置检查读取新的碰撞。边界、出生点、门接近点、入口方向必须可编辑且不在 ready 还原。相互依赖的美术与碰撞归同一场景实例。
5. 只移动到场景的节点在 instantiate 后、进入树前就存在。测试要验证这一点，不能仅检查 ready 后 Remote Tree。`@tool` 只允许必要的编辑器自绘预览，不执行游戏启动、持久化或任意子节点构建。
6. 孩子 `_ready()` 不读取尚未配置的 world/home。Harbor 父节点 ready 完成引用绑定后显式初始化游戏依赖；视觉初始化与业务初始化分开。门与人物引用按固定子节点绑定。禁止手动调用 `_ready()`、运行时 set_script 替换房屋、再次 new 同一静态子树。
7. 角色恢复行为仍可恢复被过渡临时改变的状态，但应恢复场景初始值（modulate、z_index等），不能一律 White/0 覆盖用户设定。每个玩家遮罩 ShaderMaterial 设为 local_to_scene，防止预览和实例相互污染。

## `_draw()` 的逐项决策

| 文件 | 决策及等价性边界 |
| --- | --- |
| terrain.gd | 固定土地/海面/石路/海堤/沙滩/台阶/码头迁入 `terrain.tscn` 的具名静态层；重复贴图可用 TileMapLayer，细小装饰可烘焙为保留来源的透明层。优先逐层可选择，不把整个地图烘焙成一张不可调图片；需像素对照验证纹理边缘裁切 |
| house_interior.gd | 地板、墙、地毯与边缘改 Sprite2D/Polygon2D/平铺层，保持最后一格裁切，移除固定绘制 |
| house_exterior.gd | 四片非重叠 AtlasTexture 精确复现挖掉旧门扇的画面；保留 atlas 原图和坐标，禁止重叠 alpha 接缝 |
| house_furniture.gd | 单张贴图改 Sprite2D，centered=false，offset=-pivot；元数据仍保留且校验一致 |
| door_jamb.gd | 三块固定门框改 Polygon2D，尺寸/颜色可编辑；与固定碰撞一起归门实例 |
| interactive_door.gd | 固定框、门槛序列化；三态门扇允许状态驱动切纹理/宽度，三态目标矩形与帧作为导出资源。保留室内裁剪条 Rect2(0,29,30,8)，不能换成完整高门图 |
| player.gd | 阴影可序列化 Polygon2D，仅过渡控制显隐；人物帧和材质资源化，保留真实空间遮罩 |
| forage_pickup.gd | 三种像素小图和高亮可保留轻量自绘，kind、颜色和尺寸导出并在编辑器预览；静态拾取点仍必须是场景实例 |
| water_detail.gd | 动态4相位水纹保留，静态节点在 Terrain 子树中；剪裁区域从关卡配置读取，时间变化不序列化 |
| ui/backpack_icon.gd | 保留小型尺寸适应自绘，启用安全编辑器预览；颜色可导出，mouse_filter 在场景设置 |
| ui/pixel_style.gd | 保留现有像素 StyleBox 绘制算法，kind 和调色参数资源化；去掉初始化覆盖 Inspector 边距；Theme 引用实际 .tres |

不把物理查询、存档对象、库存对象、InputEvent、测试驱动、Timer/Tween 等 `.new()` 误判成静态场景。现有24/48槽容量固定，直接序列化槽实例；未来容量变化才允许按容量差实例化 inventory_slot 场景，不能每次选择格子重建整个页面。

## 分批迁移与验收

每一批开始前保存当前 diff 与新文件清单，先加能在旧工程失败的“节点入树前存在、Inspector 覆盖可保留”测试，再做最小迁移。若同一错误两轮修复仍失败，停止该批并报告。每批同时检查原生渲染，未通过不推进下一批。

| 批次 | 修改范围 | 相关回归与原生验收 |
| --- | --- | --- |
| 0 基线 | 只备份与建立场景合同测试 | 记录标题、HUD、手账三页、仓储、四弹窗、室内外及双向门录像；确认默认窗口、调整窗口、全屏三种状态 |
| 1 HUD/主题 | hud.tscn、主题、背包按钮 | test_display、test_interaction；按E开关提示、B按钮；调整位置/主题/文字保存后运行验证仍生效 |
| 2 菜单与手账 | journal、main_menu、pause_menu、分页/槽/弹窗 | test_journal、journal_driver、库存两测试、test_save_state；取消优先、E焦点、B/Tab、滚动、满包/空包、数量守恒、失败保存；连续开关后无重复信号或残留节点 |
| 3 角色与镜头 | player.tscn、SpriteFrames、材质、camera | test_world、test_display；四向移动、受阻待机、镜头边界；保持48逻辑画布、速度72、2倍镜头；镜头导出参数不能被 ready 覆盖 |
| 4 室外关卡 | exterior、terrain、树/道具/拾取点/碰撞 | test_tree_set、test_environment、test_foraging、test_world、verify_environment_render；沙滩通路、水面阻挡、树后遮挡、6点拾取、静态层逐像素对照 |
| 5 小屋与门 | interior、家具、门、session、transition_overlay | test_cottage_assets、test_cottage_runtime、test_compact_cottage、test_south_door、test_house、test_house_save；双向20次、门柱擦边、长按E、通道阻挡、目标缺失、途中退出、读旧档、R复位并原生录像 |
| 6 收尾 | 移除已迁移构造器，文档交接 | 全部相关测试一次；从完整冷启动串联标题→新游戏→采集→背包→仓储→进出屋→保存重开；验证场景打开无空白/丢资源 |

所有 Godot 命令带 `--log-file /private/tmp/coastal-editor-<batch>.log`；涉及持久化的脚本明确隔离到 `/private/tmp/coastal-*`。源码脚本测试用 `godot --headless --path godot2d --log-file ... --script res://tests/<test>.gd`；原生渲染检查去掉 headless。不能直接启动默认存档入口做有写入风险的测试。若构建新的导出包，必须运行其 `--verify-house`、`--verify-journal` 等现有入口并指定 `--test-save-directory=/private/tmp/coastal-...`，不能引用源码测试冒充导出验证。

Inspector 验收至少覆盖：HUD固定标题/偏移/颜色、菜单按钮文本/主题、人物贴图/偏移、一个家具及其碰撞位置、树实例位置、室内门接近点。测试以内存中场景覆盖或临时副本执行，不污染正式布局。开始、切页、关开菜单、切室内外和改变窗口尺寸后都保留设置；动态状态字段按功能变化。静态图像同尺寸比较，水纹冻结在同相位，人物动画同帧；视频检查门顺序和真实遮挡，不能用像素总量代替观看。

## 风险与错误边界

- 节点初始化顺序：避免子节点过早访问 world；测试场景独立打开不报空引用。
- 数据双源：家具或门在编辑器移动却只改视觉最危险；实体与安全位置读取必须随迁移同步改造，并测试改动生效。
- 字体/StyleBox：自定义资源反序列化需要默认构造，导出属性与默认值正确；主题不能因 `_init` 覆盖掉序列化边距。
- 焦点：保留场景后隐藏页面会留住焦点，必须每次显隐后转交到有效按钮；确认框只允许其内部焦点，默认取消。
- 排序与门修复：房屋 Y165 排序、原图偏移、门扇/门柱分离、室外8单位跨入、室内下方入口均为冻结合同。不得为场景可编辑性改变像素比例或过渡时序。
- 文件与交付：任何迁移只改相应批次，测试夹具使用场景实例替代裸脚本 new 时必须保留行为断言，不能仅删除原测试。最新版交付和已有源码包不覆盖。

## 完整文件审计

下表每行对应一次工作项目文件清单；“保留”表示不属于静态界面或布局迁移，不代表可以删除相关测试。

| 文件 | 行数 | 发现与处理 |
| --- | ---: | --- |
| `art/godot2d/environment-v2/prepare_assets.gd` | 72 | 离线资源预处理工具；不迁生产场景。 |
| `art/godot2d/tree-set-v4/prepare_trees.gd` | 102 | 离线树素材处理；保留锚点/原图，不修改。 |
| `godot2d/scenes/harbor.tscn` | 7 | 唯一现有场景，只有根节点；改为静态子场景实例的入口。 |
| `godot2d/scripts/atlas.gd` | 32 | 动态创建 AtlasTexture/SpriteFrames；固定 atlas 区域和角色帧迁 .tres，工具接口可暂留兼容。 |
| `godot2d/scripts/cottage_art.gd` | 26 | 素材 manifest 读取/校验；保留，改为验证序列化贴图与锚点，不在 ready 覆盖。 |
| `godot2d/scripts/door_jamb.gd` | 9 | 固定门框自绘；迁门场景三块可编辑图形。 |
| `godot2d/scripts/forage_pickup.gd` | 32 | 三类像素图/高亮自绘；场景化节点，保留动态绘制和可编辑参数。 |
| `godot2d/scripts/foraging_state.gd` | 2 | 玩家状态兼容继承；保留。 |
| `godot2d/scripts/harbor.gd` | 326 | 主要静态创建入口；移至 Harbor 子场景，保留交互和验证驱动动态装载。 |
| `godot2d/scripts/harbor_data.gd` | 44 | 室外固定点/碰撞/文案；迁场景实例和标记，同步查询与校验，保留业务ID。 |
| `godot2d/scripts/house_exterior.gd` | 24 | 启动改排序坐标和固定分块自绘；序列化最终位置与四片图像。 |
| `godot2d/scripts/house_furniture.gd` | 21 | 启动取贴图/pivot并自绘；迁家具 Sprite2D 和实际底座。 |
| `godot2d/scripts/house_interior.gd` | 70 | 创建11家具/墙/碰撞/门、固定背景自绘；完整迁室内场景。 |
| `godot2d/scripts/house_session.gd` | 86 | 创建室内外、reparent并手动 ready；移除静态构造，保留单玩家换房和恢复。 |
| `godot2d/scripts/hud.gd` | 124 | 固定UI构造和layout覆盖；场景锚点，保留状态文字及Toast倒计时。 |
| `godot2d/scripts/interactive_door.gd` | 107 | 门/门柱碰撞及暗部构造；迁门变体，保留三态和交互查询。 |
| `godot2d/scripts/inventory/inventory_container.gd` | 175 | 纯库存数据与操作；保留。 |
| `godot2d/scripts/inventory/item_catalog.gd` | 13 | 纯物品定义；保留。 |
| `godot2d/scripts/player.gd` | 80 | 碰撞/AnimatedSprite/材质启动创建；迁角色场景，保留移动/遮罩计算。 |
| `godot2d/scripts/player_state.gd` | 126 | 库存、统计、存档迁移/校验；保留业务，位置校验需与关卡同源。 |
| `godot2d/scripts/room_data.gd` | 38 | 固定房间/家具/门参数；场景来源统一，保留ID和格式兼容边界。 |
| `godot2d/scripts/room_transition.gd` | 172 | 仅淡出层为固定创建；迁overlay，物理查询/Tween与已修正门顺序保留。 |
| `godot2d/scripts/save_service.gd` | 63 | 持久化服务；保留，不读写真实存档。 |
| `godot2d/scripts/settings_service.gd` | 27 | 音量设置服务；保留。 |
| `godot2d/scripts/terrain.gd` | 101 | 全部为固定地形绘制；迁具名静态层及可编辑地形资源。 |
| `godot2d/scripts/ui/backpack_icon.gd` | 18 | 小型可缩放图标；保留自绘、编辑器预览，mouse_filter场景化。 |
| `godot2d/scripts/ui/journal.gd` | 474 | 整棵UI反复构造；拆标题/暂停手账/分页/弹窗，改刷新常驻节点，保留原业务接口。 |
| `godot2d/scripts/ui/pixel_style.gd` | 63 | 程序 StyleBox；保留绘制，kind/颜色导出并以 .tres 配置。 |
| `godot2d/scripts/water_detail.gd` | 57 | 时间驱动水纹；保留动态绘制，固定节点场景化。 |
| `godot2d/scripts/world_camera.gd` | 31 | ready覆盖zoom与平滑；移入Inspector，保留目标跟随/室内定位。 |
| `godot2d/tests/capture.gd` | 97 | 原生截图/路线工具；保留，必要时更新节点路径。 |
| `godot2d/tests/cottage_asset_preview.gd` | 53 | 测试用动态预览台；保留工具生成，生产场景测试使用真实实例。 |
| `godot2d/tests/credits.gd` | 6 | 工具入口；保留。 |
| `godot2d/tests/foraging_driver.gd` | 143 | 采集及导出回归；保持数量/输入/可达行为断言。 |
| `godot2d/tests/house_driver.gd` | 258 | 住宅集成及导出回归；保留单玩家、过渡、退出与稳定存档断言。 |
| `godot2d/tests/interaction_driver.gd` | 88 | E交互回归；保留。 |
| `godot2d/tests/journal_driver.gd` | 157 | 菜单/焦点/仓储回归；保留按钮ID与公共接口，增加常驻节点切换覆盖。 |
| `godot2d/tests/route_driver.gd` | 83 | 通行路线；保持实际碰撞验证。 |
| `godot2d/tests/test_compact_cottage.gd` | 173 | 相关行为/资源回归；保留断言，只按场景实例化或节点路径调整测试夹具。 |
| `godot2d/tests/test_cottage_assets.gd` | 135 | 相关行为/资源回归；保留断言，只按场景实例化或节点路径调整测试夹具。 |
| `godot2d/tests/test_cottage_runtime.gd` | 65 | 相关行为/资源回归；保留断言，只按场景实例化或节点路径调整测试夹具。 |
| `godot2d/tests/test_display.gd` | 44 | 相关行为/资源回归；保留断言，只按场景实例化或节点路径调整测试夹具。 |
| `godot2d/tests/test_environment.gd` | 94 | 相关行为/资源回归；保留断言，只按场景实例化或节点路径调整测试夹具。 |
| `godot2d/tests/test_foraging.gd` | 11 | 相关行为/资源回归；保留断言，只按场景实例化或节点路径调整测试夹具。 |
| `godot2d/tests/test_house.gd` | 16 | 相关行为/资源回归；保留断言，只按场景实例化或节点路径调整测试夹具。 |
| `godot2d/tests/test_house_save.gd` | 92 | 相关行为/资源回归；保留断言，只按场景实例化或节点路径调整测试夹具。 |
| `godot2d/tests/test_interaction.gd` | 9 | 相关行为/资源回归；保留断言，只按场景实例化或节点路径调整测试夹具。 |
| `godot2d/tests/test_inventory_container.gd` | 46 | 相关行为/资源回归；保留断言，只按场景实例化或节点路径调整测试夹具。 |
| `godot2d/tests/test_inventory_operations.gd` | 103 | 相关行为/资源回归；保留断言，只按场景实例化或节点路径调整测试夹具。 |
| `godot2d/tests/test_item_catalog.gd` | 23 | 相关行为/资源回归；保留断言，只按场景实例化或节点路径调整测试夹具。 |
| `godot2d/tests/test_journal.gd` | 15 | 相关行为/资源回归；保留断言，只按场景实例化或节点路径调整测试夹具。 |
| `godot2d/tests/test_save_state.gd` | 67 | 相关行为/资源回归；保留断言，只按场景实例化或节点路径调整测试夹具。 |
| `godot2d/tests/test_south_door.gd` | 244 | 相关行为/资源回归；保留断言，只按场景实例化或节点路径调整测试夹具。 |
| `godot2d/tests/test_tree_set.gd` | 53 | 相关行为/资源回归；保留断言，只按场景实例化或节点路径调整测试夹具。 |
| `godot2d/tests/test_world.gd` | 108 | 相关行为/资源回归；保留断言，只按场景实例化或节点路径调整测试夹具。 |
| `godot2d/tests/verify_environment_render.gd` | 52 | 原生环境渲染；保留作为静态地形迁移对照。 |

## 交接与自查

已完成：56文件分类审计、现有动态构造与自绘评估、目标场景边界、Inspector唯一来源规则、逐批验证策略。未完成：生产迁移、失败测试与实际渲染对照；本设计不宣称游戏验证通过。自查确认：不新增菜单功能、不调整美术布局、不替换现有门方案、不触碰真实存档、不覆盖最新交付。后续实施者先核对备份与工作树差异，按单批执行并记录修改文件、验证结果和遗留问题。
