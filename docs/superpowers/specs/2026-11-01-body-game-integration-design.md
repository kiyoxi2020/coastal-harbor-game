# Godot默认游戏主角身体资源接入设计

状态：2026-11-01用户明确选择A，Progress Q22=A；实施已授权。

## 目标与本阶段定义

从正常游戏入口进入海港后，主角使用最新归档的成年身体完成四向站立、走、跑、锄地、浇水、收获。这里的“裸人体”指当前已归档的灰色不透明连体底衣身体，不生成或擦除底衣，不增加外搭、发帽或换装界面。

本阶段是默认游戏中的本地开发接入，不是完整可组合人物生产发布。用户认可的身体源归档不自动授予精确接触、动态换装或生产资格。最新配方和构建自身的review-only身份保持原义。

## 已核对的约束

- 当前HEAD：9bb8044c；开始调查时工作树干净。
- 身体归档：`art/characters/parts/body/adult-v1/archive-r001.json`。
- 使用严格构建：`art/characters/builds/adult-standard-v2-visible-r001/`，包含24动作方向、108帧；农事含完整身体和工具。
- `body-reference`构建用于无工具身体参考，不作为游戏农事显示源；两variant不是可随意拆合的图层。
- 当前玩家入口为`godot2d/scenes/actors/player.tscn`，由`player.gd`及`player_tool_action.gd`驱动一个AnimatedSprite2D。
- 当前停步和农事结束均使用走路首帧；`room_transition.gd`直接用方向名播放走路，切换时需同时覆盖。
- 餐馆两位顾客仍引用旧主角纹理，且只有整体调色。完整人物迁移必须另外补有辨识差异的NPC资源，不能用同一个新身体直接冒充两个新NPC。
- `tools/characters/check.py`及`runtime-baseline.json`目前冻结全部生产人物文件和引用，并要求catalog.production_release为空。接入必须评审明确的基线差异，不能自动重采基线以消除报错。

## 方案比较与推荐

| 方案 | 结果 | 成本与边界 |
|---|---|---|
| A：默认游戏主角先接入（推荐） | 正常启动游戏即可操作新身体；现有NPC暂留，明确为迁移中的本地开发阶段 | 实现最符合“先让游戏运行”；需批准本阶段对生产冻结及暂时混用新旧角色的有限例外，不能称完整统一发布 |
| B：真实海港的独立开发入口 | 在真实地图与玩法中操作新身体，默认游戏继续现有角色 | 不触及正式绑定；需要从单独入口启动，不满足默认入口立即切换 |
| C：先完成全部角色统一发布 | 主角、NPC、运行及导出依赖一次切换 | 需补NPC差异化素材、相关合同和最终发布验收，超出本轮先跑身体的最小范围 |

推荐A。批准范围限定于本地默认主角接入、相应运行清单和经审核的精确基线变更；完整发布、NPC替换与外搭制作不包含在内。最终统一发布前必须消除旧人物运行/导出依赖，本阶段不能把该要求标为已完成。

## 资源与数据流

使用既有`build.py verify`复核visible严格构建；新增通用Godot资源接入工具，读取严格构建输出与绑定的模板姿态/时序，生成Godot原生SpriteFrames和本地运行绑定清单。工具放在`tools/characters/`，不在资源批次中另写合成器或播放器。

接入资源放在`godot2d/assets/characters/integrations/adult-standard-v2-visible-r001/`；以校验过的108张构建输出PNG逐字节复制为Godot可导入资源，记录每张源/目标SHA、配方和构建artifact_digest、动作与方向、时长和根点。游戏运行不依赖工程外的`art/`路径。

运行绑定清单标明`local-development-integration`，固定本次唯一主角配方及完整能力；不设置production_release或伪造active_release资格。静态SpriteFrames由清单生成，可复现且可核对，避免在_ready中覆盖Inspector资源。缺动作、错SHA或无法匹配pose时拒绝接入，不回退旧帧。

源画布256×224、根点(123,201)。采用Q20实际世界观察过的统一0.25源像素到世界缩放；相机4倍时源像素到内部渲染像素为1:1。AnimatedSprite2D以非居中方式配合offset=(-123,-201)及场景scale=(0.25,0.25)绑定根点；世界碰撞仍为10×6。不得把旧position=(0,-21.6)和scale=0.15原样套上新画布。记录源图、运行输出、实际窗口/内部画面的显示尺寸，并在原生检查中确认。

## 播放与交互

1. 保留现有CharacterBody2D控制、移动速度72/108、碰撞和单一AnimatedSprite2D；不另建人物控制器。
2. 动画统一采用`idle_<direction>`、`walk_<direction>`、`run_<direction>`、`hoe_<direction>`、`water_<direction>`、`harvest_<direction>`。生成时按清单实际帧数和duration_ms设置时序，不套固定六帧。
3. 停步与工具结束切入独立idle；走跑和转向切换整套身体。房门过渡显式调用walk动画，进入/退出后恢复正确idle。
4. 工具动作锁方向与移动，动画完成只结束当前动作；玩法仍按现有流程提交一次事务。接入不把画面事件变成第二次耕地/浇水/收获。
5. 门遮挡继续使用世界空间shader与真实门轮廓。玩家计算视觉边界时使用实际纹理、centered/offset/scale，覆盖门过渡使用的姿态；工具和身体同一Sprite接受遮挡。
6. Inspector保存与重载保留资源/位置/缩放设置；暂停恢复、输入释放和切场景不能留在错误动作。

## 文件责任范围

- 新增`tools/characters/godot_integration.py`及对应Python测试：校验严格输出、生成运行包/清单/SpriteFrames、确定性复核；不修改构建器的review-only语义。
- 新增上述Godot运行资源目录及`godot2d/resources/player_body_frames.tres`。
- 修改`godot2d/scripts/player.gd`、`player_tool_action.gd`、`room_transition.gd`、`scenes/actors/player.tscn`：动作名称、idle、姿态几何与场景绑定。
- 修改`tools/characters/check.py`与其门禁测试：在明确批准本地接入后核验完整运行包与严格来源，同时继续拒绝未登记变化和虚假生产资格。现有冻结旧配方范围不改。
- `runtime-baseline.json`仅在实施完成、差异与证据审核后更新必要的生产文件/引用项，逐项列明原因；禁止宽泛放行、自动刷新或添加旧格式例外。
- Godot相关回归覆盖玩家、工具动作、门过渡、场景属性保存及实际游戏事务；旧测试中“固定旧贴图/六帧”的断言替换为真实新合同，不削弱业务断言。
- 最后更新`PROJECT_STATE.md`、`HANDOFF.md`和人物导航，注明本地接入范围、尚存的旧NPC依赖及未完成门禁。

## 验收与完成条件

先建立失败测试，覆盖缺动作/错SHA拒绝、可变帧数与时长、独立idle、农事锁定/结束一次、门过渡动画及根点/碰撞保持，再实现最小接入。

必须执行`python3 -m unittest discover -s tools/characters/tests`与`python3 tools/characters/check.py`，另执行受影响Godot逻辑/场景回归。新接入清单与Godot实际加载纹理逐项对应，所有24动作方向可播放。

原生GPU验证从真实海港场景开始：四向走跑各至少十循环、急停/转向/走跑切换、十二组农事开始到结束、树/柜台前后及出入门、暂停恢复、一次完整耕种/浇水/收获事务与存档重载。检查比例、脚点、旧帧闪现、工具缺失、门遮挡和碰撞；保留截图、连续录像与绑定输入摘要。

Godot命令统一带`--log-file /private/tmp/coastal-*.log`，所有测试存档在`/private/tmp/coastal-*`，启动前固定隔离路径。测试不得读取或写入玩家真实存档。未测试导出应用时明确只交付源码运行接入。

只有必要自动检查及本轮原生验收通过，默认游戏主角才能标为接入完成。源图像素不改，不沿用Q20临时观察作为本轮游戏接入回执。精确支撑/滑步/握点/落点与动态混搭未通过的项目继续标为未验证，不由本轮功能验收推导为通过。

## 评审状态

设计已自查目标、数据流、播放、NPC边界、冻结基线及验收范围。用户Q22=A批准默认主角本地接入、精确基线变更及旧NPC暂留。按实施计划执行，不自动提交或推送。
