> 2026-11-02清理说明：所述历史制作媒体和原生过程文件已按用户授权删除，旧数据路径已退役，本文仅保留文字结论；当前数据与验证见[执行报告](2026-11-02-resource-cleanup-executed.md)。

# 默认游戏主角身体接入验收

用户Q22=A批准默认游戏主角先接入当前归档灰色底衣身体；本地开发接入已实现。场景仍为`godot2d/scenes/harbor.tscn`，正常启动即可使用新主角，不需要开发入口或新旧开关。旧餐馆NPC按批准范围暂留，完整统一生产发布关闭。

## 改动与资源身份

来源为`adult-standard-v2-visible-r001`严格构建，24动作方向108帧，农事包含工具。源配方/build及像素未改，仍review-only。新`godot_integration.py`复核严格输出并逐字节复制到`godot2d/assets/characters/integrations/adult-standard-v2-visible-r001/`，生成原生`player_body_frames.tres`及来源/时序/像素摘要清单。

玩家继续使用一个AnimatedSprite2D及原移动控制，支持独立idle、按实际1/4/6帧及时长播放、工具动作锁定与重播/结束；门过渡使用新walk命名和实际根点几何。农事先检查动作能力，再提交业务；缺失、空、错误循环或空纹理不会改土壤、体力、序号或存档，成功动作只提交一次。

Godot默认fix_alpha_border会改变透明边缘：南idle实测1976个透明像素及191个可见像素RGBA不同。关闭后两类差异均为0；生成器现在固定全部像素处理参数并核验导入source/remap，实际Godot加载的108帧RGBA逐一匹配严格构建摘要。另有单像素篡改及导入参数篡改反例。

115项基线文件差异（3改、112增）及引用调整经过独立复查，见[逐项记录](2026-11-01-body-game-baseline-changes.json)。未调用自动基线捕获；旧资产、旧配方与旧构建冻结哈希保持。新增登记是local-development-integration，不创建正式active_release。

## 验证结果

| 验证 | 结果 |
|---|---|
| 人物Python全套 | 419/419，281.133秒 |
| 仓库人物门禁 | 通过55严格配方、49严格构建、9冻结旧配方及1本地接入包；完整发布关闭 |
| 接入专项Python | 18/18，覆盖动作缺失、几何、时序、输出/导入篡改、路径/符号链接、覆盖拒绝 |
| Godot玩家实际资源/行为 | 469/469，含108帧导入RGBA、真实农事提交前拒绝及单次提交 |
| 农田规则／农事表现 | 401/401、32/32 |
| 场景保存往返／紧凑屋 | 15/15、37/37 |
| 南门逻辑／GPU像素回归 | 66/66、132/132，failures=0 |
| 真实海港GPU观察 | 171/171；四向走跑每向至少10循环、12组农事播放、急停/走跑切换、暂停恢复、树/柜台前后、双向进出门 |
| 真实耕种原生流程 | 150/150；真实买种、16格耕地、两种种植、四晚生长、浇水、收获、存档重载 |

仓库门禁及运行包单独verify均已通过。无原生脚本错误或原生ERROR日志。headless工具有既有macOS证书提示，沙箱编辑器导入有全局设置写入提示，不是游戏运行或人物脚本错误。

连续观察按真实渲染快照的记录时间合成为MP4（529个采样），不是逐显示帧录屏或真人操作。走跑时使用真实输入/控制/碰撞，纵向跑道长度有限，北南各两段连续六循环，中途正常反向；没有为了通过验收逐帧挪动身体。树/柜台停帧位置为测试布置，门和农事完整流程为实际运动与交互。

## 画面与尺寸

严格源帧和运行PNG均256×224，根点(123,201)，世界统一scale=0.25，画布世界占地64×56；相机4倍下内部渲染画布256×224。四向idle不透明轮廓为72×151（东）、72×139（北）、77×144（南）、82×149（西）源像素。内部画面2560×1440，本次原生窗口2078×1304，按宽等比适配后纹理画布约208×182屏幕像素，轮廓高度约113–123屏幕像素。保持nearest、原源分辨率和合法整帧缩放，未单独挪缩部位。

已目视检查世界截图、20动作方向连续采样板、树/柜台/门图及收获后画面，未见旧穿衣帧闪回或工具丢失。截图保留原生渲染尺寸：

![默认主角身体](body-game-integration-v1/default-body-world.png)

![四晚耕种与收获后](body-game-integration-v1/farming-complete.png)

## 证据与复现

[轻量摘要](body-game-integration-v1/summary.json)绑定源manifest、运行manifest、基线、输入快照、trace、视频及代表图SHA；[原生检查](body-game-integration-v1/checks.json)保留321项世界/农事结果。

- `/private/tmp/coastal-body-game-native-r001/`：1070项预先冻结输入、trace、529采样、`body-motion.mp4`、原尺寸截图。捕获期间仅无关`test_unified_player.gd`的负例fixture完成修正；实际运行依赖未改，该差异单独记录于input-verification.json。
- `/private/tmp/coastal-body-game-farming-r001/`：隔离存档及四晚农事截图/检查。临时入口`/private/tmp/coastal-body-farming-native.gd`继承既有农事测试，只设置新的证据目录并强制隔离存档参数。
- `/private/tmp/coastal-body-south-door-native.log`：真实GPU门遮挡132项。
- `/private/tmp/coastal-body-integration-final-python.log`、`/private/tmp/coastal-unified-final.log`：全套Python及469项Godot结果。

原生观察入口为`res://tests/test_body_game_native.gd`，需要先在全新的`/private/tmp/coastal-*`目录创建`inputs.json`（工程文件与SHA快照），再传`--body-evidence=<目录>`及`--test-save-directory=<目录>/save`；场景入树前还会设置相同save_directory元数据。所有Godot命令带`--log-file /private/tmp/coastal-*.log`。完整证据临时存放，不承诺永久保全；仓库保留摘要和两张代表图。

## 边界与分工

用户确认的是接入范围，不是本轮新运行视觉的用户认可。精确支撑/滑步、握点/落点、低FPS完整时序、动态衣柜、差异化NPC与全部旧模型退役仍待后续；未修改这些未通过状态。未做导出包、Windows/Intel或真人长时游玩，未提交/推送。

主代理gpt-6-astra负责资源、门禁、实际GPU和交接；gpt-6.1-sol high负责玩家跨文件实现及定点回归；gpt-6-astra high独立复查实现与115项基线差异。两项重要发现均已修复并复查通过，没有模型切换失败。
