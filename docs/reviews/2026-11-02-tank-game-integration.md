> 2026-11-02清理说明：所述历史制作媒体和原生过程文件已按用户授权删除，旧数据路径已退役，本文仅保留文字结论；当前数据与验证见[执行报告](2026-11-02-resource-cleanup-executed.md)。

# 男性背心短裤母版接入默认游戏

按用户“把新母版接入游戏”的指令，默认入口`godot2d/scenes/harbor.tscn`的玩家已使用Q27认可的v4母版。四向idle、walk、run、hoe、water、harvest共24组108帧，农事带工具。

## 资源与变更

最终美术保留在`art/characters/parts/body/adult-v4/r001/`，归档637项SHA逐一核对无变化。来源为`art/characters/builds/adult-v4-tank-visible-r001/`严格构建；现有生成器校验后逐字节派生到`godot2d/assets/characters/integrations/adult-v4-tank-visible-r001/`，生成`godot2d/resources/player_body_v4_frames.tres`。

生产场景仅替换`player.tscn`的一条SpriteFrames引用，保留256×224源帧、根点(123,201)、整帧0.25世界缩放、nearest过滤及10×6碰撞。玩家逻辑、动作时序、门遮挡、存档格式均未修改。源图与工具像素保持不变，导入关闭透明边缘修色。

基线精确新增110个文件（108 PNG、manifest、SpriteFrames），修改1个场景哈希，追加新资源保护和本地接入登记，仅更新对应引用；旧冻结文件和配方保留。逐项差异JSON仅作为当时本地审查暂存，不加入Git；本次退役后的现行范围见[清理执行报告](2026-11-02-resource-cleanup-executed.md)。未调用自动基线捕获。旧v2包用于追溯，默认玩家没有旧版切换分支。

## 验证

| 验证 | 结果 |
|---|---|
| 人物Python全套 | 490/490，401.820秒 |
| 仓库人物门禁 | 通过59个严格配方、53个严格构建、9个冻结旧配方、2个本地接入包；正式发布关闭 |
| 运行包独立verify | 24组108帧通过，正式发布关闭 |
| 默认玩家实际纹理/行为 | 469/469 |
| 农田规则/基础入口 | 401/401、6/6 |
| 保存往返/紧凑房屋 | 15/15、37/37 |
| 南门逻辑/GPU像素回归 | 66/66、132/132，failures=0 |
| 真实海港GPU观察 | 171/171 |
| 四晚实际耕种/收获/重载 | 150/150 |

默认玩家回归先更新预期为v4，旧绑定产生`body_frames_bound`与`integration_manifest_exists`失败；生成新包并替换绑定后469项全部通过，覆盖108帧实际Godot导入RGBA与真实农事提交约束。

真实海港GPU观察冻结1495个输入，结束后全部哈希一致。四向walk各至少10循环、run东西各10/南北各12循环；实际输入驱动移动与碰撞，12组农事完整播放、暂停恢复、急停和走跑切换、树/柜台前后、双向门通过。农事播放观察与真实耕种事务分别验证，不混用证据。

已目视检查20组走跑/农事采样及门进出序列、原生世界图，未见灰色长袖长裤旧帧闪回或工具丢失。512张原生人物裁剪采样按实际时间生成临时MP4，属于渲染采样回放，不是逐显示帧录像或真人操作。原生截图2560×1440，窗口记录3620×1994；源画布世界尺寸64×56，相机4倍下内部画布256×224，适配窗口约354×310屏幕像素（按内部画面等比适配估算）。没有单独挪动或缩放身体部位。

![新默认主角](tank-game-integration-v1/default-body-world.png)

![耕种收获](tank-game-integration-v1/farming-complete.png)

## 证据与复现

[检查与来源摘要](tank-game-integration-v1/summary.json)绑定严格构建、运行manifest、基线、冻结输入、trace、检查及代表图SHA。详细临时观察位于`/private/tmp/coastal-tank-game-native-r001/`，实际农事在`/private/tmp/coastal-tank-game-farming-r001/`；存档全部隔离，无真实玩家存档写入。仓库只保留轻量结果和代表图。

复核运行包：`python3 tools/characters/godot_integration.py verify godot2d/assets/characters/integrations/adult-v4-tank-visible-r001/manifest.json`。原生世界入口`res://tests/test_body_game_native.gd`需新的coastal临时证据目录与预先冻结inputs.json，传`--body-evidence=<目录>`和`--test-save-directory=<目录>/save`。实际耕种临时入口继承既有`test_life_farming_native.gd`，只设置新证据目录并强制隔离存档参数。

## 范围

本次为默认玩家本地开发接入；旧餐馆NPC暂留，正式统一人物发布、动态换装和严格接触资格未新增。未导出或验证独立应用/Windows，未提交或推送。

主代理实施接入并做原生验证；复用gpt-6.1-sol/high代理独立只读审查精确基线。审查通过：111项差异精确一致，243个旧运行文件哈希保留，528个旧构建文件及9个旧配方按既有迁移绑定复核通过，运行包绑定Q27严格构建，生成器与门禁未改。
