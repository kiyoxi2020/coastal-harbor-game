# 农事关键姿态评审加载器

2026-10-26。独立子任务仅新增：
- godot2d/dev/character_farming_review.gd
- godot2d/dev/farming_review_catalog.json
- godot2d/tests/test_character_farming_review.gd

使用已批准的明确接口，按test-driven-development先建立真实失败，再实现。未改review面板、trial、场景、状态文档或任何候选/美术；未启动GUI、存档服务、玩法、提交或下级代理。

## 稳定接口

RefCounted公开clips:Dictionary、error:String、catalog_sha256:String。clips按water/hoe/harvest动作键保存。
load_catalog(project_root:String,catalog_path:String="res://dev/farming_review_catalog.json")->bool。
get_clip(action:String,direction:String,garment:String)->Dictionary，仅west/A；不支持返回{}，不会回退其他动作、方向、衣服。

每clip包含action_id、direction、garment、textures:Array[Texture2D]、durations_ms:Array[int]、canvas_px:Vector2、root_anchor_px:Vector2、display_scale:float、candidate_sha256、pose_ids:Array[String]、note和source_status。note明确“仅关键姿态”“非完整动作”及源失败范围。来源status原样保留，不把可加载当动作通过。

catalog绑定项目相对candidate路径与真实SHA256：
- water v3：157e128cfb1d3f67c5a48b7dde678e30645c303a84504519316acc8ae6e2458e，2姿态。
- hoe v3：ea10e68d145d7581d5a9aaac0fae599b0bba3c649cb244c918d7beb37b3fe49b，1姿态。
- harvest v2：890aac809b31c357d9ad04e30d77166a4ea03d5ce39545602f75f66a6ac0a9c6，2姿态。

## 校验与原子性

候选/输入/纹理路径必须为安全相对路径（拒绝绝对、scheme/冒号、反斜线、空组件、dot/dotdot）；所有输入实际文件和sha全检，包括当前未直接显示的生成参考/配置/规则。每纹理另验实际sha与canvas尺寸，frame source/sha须绑定inputs。候选必须schema1/adult-standard-v1/对应action/west；要求完整有效画布、画布内有限root、2×source density、display_scale=138/1164，无bbox或人物总高拟合。

帧ID非空且唯一；duration必须有限正整数（可安全存入32位整数）。全部候选只在局部pending中加载；全部通过才公开clips并赋catalog_sha256。失败清空clips/catalog_sha256且给中文error；成功重载可恢复。无任何actor引用、事件、事务或玩家存档。

## 测试

先RED：
    /Applications/Godot.app/Contents/MacOS/Godot --headless --path godot2d --log-file /private/tmp/coastal-farming-loader-red.log --script res://tests/test_character_farming_review.gd

预期失败：farming_loader_exists、pinned_catalog_exists；退出1，明确因功能缺失失败，无脚本解析错误。

后GREEN：
    /Applications/Godot.app/Contents/MacOS/Godot --headless --path godot2d --log-file /private/tmp/coastal-farming-loader-green.log --script res://tests/test_character_farming_review.gd

43项全通过，退出0。覆盖真实三候选、纹理/类型/维度/时长、缺方向/B拒绝、隔离真实依赖fixture、第三候选失败后清除旧成功、路径穿越/反斜线/绝对纹理、input/纹理/源依赖哈希、实际画布错配、零/负/小数/字符串时长、体型/动作/方向/密度/scale错误、root越界、重复pose/action、缺hash、无效catalog类型以及错误后重载恢复。

隔离fixture仅在/private/tmp/coastal-farming-loader-fixture。Godot两次启动都有该机器既存的macOS get_system_ca_certificates提示；测试没有加载器错误，GREEN退出0。不将headless结果称为原生画面/交互或视觉认可，UI与原生由主代理完成。没有扩跑无关测试。

## 试看说明更新与面板只读复查

主代理要求将catalog三条note改为中性中文试看说明，已逐字采用：
- water：西向短袖：2个关键姿态（预备/倾倒），尚未补齐完整动作。
- hoe：西向短袖：仅1个落锄关键姿态，先看比例、工具与握持。
- harvest：西向短袖：站立/蹲身2个关键姿态，先看脚位与姿态变化。

source_status与所有candidate/源图均未改。新catalog SHA256为9f57993ca3ecf022bf396f76b9e7699e87c5beb2b4d2cce3631f3b13a457f07f。loader测试相应去除对“非完整动作”固定措辞的硬编码，保留关键姿态说明及source_status要求；此次仅文案/断言措辞同步，按要求未重跑43项或主代理UI测试，前述43 GREEN为此次文案更新前结果。

对character_motion_review.gd农事分支完成只读复查，未修改主代理文件：
- preview_durations直接取clip.durations_ms；advance_preview对农事rate固定1.0，保留原每姿态500ms，不继承walk/run速度倍率。
- motion scale为reference.scale×(clip.display_scale/(138/582))，当前clip固定138/1164，故恰好为参照scale的1/2；位置为reference.position+[256,708]×reference.scale-root_anchor×motion.scale，使登记脚根一致，不按bbox/总高拟合或局部挪部件。
- 扩大静态Slot仅容纳1536×1664/1728完整画布；Sprite自身固定scale不受容器宽高拉伸。
- farming_clip通过loader.get_clip(review_action,review_direction,trial.garment)，只有west/A；缺资源时motion.texture先置null且给出明确指引，未回退其他方向、衣物或旧动作。
- 切回合法idle/walk/run路径显式恢复motion.scale与motion.position为reference值，不残留农事几何。
- current_pose_index/step_frame/advance只修改preview_phase_ms和playing，select_clip只修改面板选项；无actor/facing/世界phase、事件、事务或存档写入。
- 新按钮数组与ACTIONS扩展顺序一致，农事按钮共用动作ButtonGroup，保持单动作选择；closure仍固定当前按钮枚举值并实时取另一维选择。

定点静态结论：未发现农事新分支阻塞级错误。原生显示、交互和用户视觉评审由主代理执行，本次未GUI/重跑UI测试。
