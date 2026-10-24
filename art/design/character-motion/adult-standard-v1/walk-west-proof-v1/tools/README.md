# 西向四帧合成与原生评审工具

`compose.py`读取`motion.json`，仅做整数平移、目标层mask和alpha合成。`review.tscn`为独立固定UI，`review.gd`驱动同一时钟下的A/B原尺寸和2×视图；`review_data.gd`直接读取真实烘焙PNG、原始子层和mask，不依赖Godot资源导入。默认nearest过滤，不访问生产场景、玩家存档或`user://`。

本机Godot：`/opt/homebrew/bin/godot`（验证版本4.7.1，原生OpenGL Compatibility / Apple M4）。所有Godot启动按项目约定使用`require_escalated`，日志位于`/private/tmp/coastal-*`。Godot自身可能初始化独立工具项目的数据目录；本工具不读写玩家数据。

## 真实美术运行

在仓库根目录执行，替换`MOTION`为实际文件绝对路径；尚未合格的失败稿也可用于诊断。无需复制素材到tools目录。

```sh
TOOLS="$PWD/art/design/character-motion/adult-standard-v1/walk-west-proof-v1/tools"
MOTION="/absolute/path/to/motion.json"
python3 "$TOOLS/compose.py" --motion "$MOTION"
/opt/homebrew/bin/godot --path "$TOOLS" --log-file /private/tmp/coastal-motion-art-review.log -- --manifest="$(dirname "$MOTION")/baked/export-manifest.json"
```

自动捕获并退出：

```sh
/opt/homebrew/bin/godot --path "$TOOLS" --log-file /private/tmp/coastal-motion-art-capture.log -- --manifest="$(dirname "$MOTION")/baked/export-manifest.json" --capture-dir=/private/tmp/coastal-motion-art-capture
python3 "$TOOLS/verify_capture.py" /private/tmp/coastal-motion-art-capture
```

真实资源的默认位置若为本试验目录`motion.json`，可直接设置`MOTION="$PWD/art/design/character-motion/adult-standard-v1/walk-west-proof-v1/motion.json"`。工具不要求这一位置。重烘焙后再捕获，避免沿用旧输入证据；不同评审批次使用新的捕获目录。

空格或按钮暂停/恢复；左右键/按钮单步并暂停，首尾循环；B/按钮切换浅深底。右侧选择A/B、子层及Source/Mask查看原始源或其目标mask，保持当前姿态和整帧注册。原始源展示不应用hide_mask，便于检查隐藏区是否实际存在；未声明mask则为空。主视图始终播放烘焙图。该工具只有固定A/B配方，不是任意换装编辑器。

## 输入与兼容接口

`compose(motion_path, output_dir=None) -> dict`；CLI默认写入`motion.json`同目录`baked/`，支持`--output-dir`。

- `schema_version=1`，`canvas_px=[512,768]`、`root_anchor_px=[256,708]`，统一`display_scale=.2371134`为本小样约定。
- `frames`为`walk_w_0..3`，每帧正整数`duration_ms`；`recipes`恰为A/B，各含四帧`layers`，按后到前排列。
- 子层`id/source/offset_px`，可选`hide_mask`；源可小于画布，只允许整数平移。PNG路径相对motion目录；mask必须整画布L模式，白色只隐藏其声明目标子层。
- 输出保留每帧`layers`，记录输入/工具/烘焙图SHA-256与`artifact_digest`。schema 1新增兼容字段`source_root`：**相对export-manifest.json所在目录**指向motion目录，自定义输出目录也可解析。旧清单缺省按`..`解析，即传统`motion目录/baked/`结构。
- 评审器检查A/B姿态时长一致及实际烘焙、源、mask文件哈希，源按offset注册到512×768供查看。仅有烘焙帧的旧清单仍可播放，右侧不显示缺失的子层；本合成器始终输出子层引用。测试覆盖指定非法输入，不能代替完整生产数据合同校验。

`capture.json`绑定manifest绝对路径/文件SHA-256、artifact_digest、当前review脚本/场景/项目哈希、显示尺度、UTC记录时间。每张记录PNG文件名、实际动画elapsed_ms、单调wall_usec/captured_usec、pose_id/frame/loop、底色、四个实际Sprite纹理索引、源配方/子层/模式和PNG保存错误码。

自动流程输出8张四帧×两底色停帧，2张Source/Mask检视，以及覆盖至少10循环、至少40张且覆盖四姿态的连续PNG。连续时钟来自真实monotonic ticks，包含PNG保存耗时；目标采样间隔为`min(1000/24 ms, 最短姿态duration_ms/2)`，80ms姿态对应40ms（目标25fps）。实际频率由渲染/PNG保存耗时决定，`capture_actual_fps`和`capture_interval_stats_ms`保存实测平均频率、最小/平均/最大间隔，不伪装为固定帧率录像。十循环到达但数量或姿态不足时继续采样，不能提前退出或降低验证门槛。静态停帧的elapsed_ms是该姿态起点，wall_usec是实测时间。捕获过程中禁用交互改变时钟；全程1280×900，目录限制为规范化的`/private/tmp/coastal-*`。

## 工具fixture与测试

fixture是诊断色块，不是人物美术；所有fixture和截图均在临时目录。

```sh
TOOLS="$PWD/art/design/character-motion/adult-standard-v1/walk-west-proof-v1/tools"
python3 -m unittest discover -s "$TOOLS" -p 'test_*.py' -v
python3 "$TOOLS/make_fixture.py" --output /private/tmp/coastal-motion-tools-fixture
/opt/homebrew/bin/godot --headless --path "$TOOLS" --log-file /private/tmp/coastal-motion-timeline.log --script res://test_timeline.gd
/opt/homebrew/bin/godot --headless --path "$TOOLS" --log-file /private/tmp/coastal-motion-capture-sampling.log --script res://test_capture_sampling.gd
/opt/homebrew/bin/godot --headless --path "$TOOLS" --log-file /private/tmp/coastal-motion-review-data.log --script res://test_review.gd -- /private/tmp/coastal-motion-tools-fixture/baked/export-manifest.json
/opt/homebrew/bin/godot --headless --path "$TOOLS" --log-file /private/tmp/coastal-motion-ui.log --script res://test_review_ui.gd -- --manifest=/private/tmp/coastal-motion-tools-fixture/baked/export-manifest.json
/opt/homebrew/bin/godot --path "$TOOLS" --log-file /private/tmp/coastal-motion-native-fixture.log -- --manifest=/private/tmp/coastal-motion-tools-fixture/baked/export-manifest.json --capture-dir=/private/tmp/coastal-motion-tools-capture-final
python3 "$TOOLS/verify_capture.py" /private/tmp/coastal-motion-tools-capture-final
```

`test_review.gd`只接受`/private/tmp/coastal-*`的fixture，因为会在同目录短暂创建损坏清单测试拒绝行为。headless只验证清单、时间轴和场景行为；原生PNG才是本次渲染证据。

## 证据范围

2026-10-23：16项Python合成测试通过；Godot时间轴、清单哈希/时长与UI交互检查通过。有窗口Godot已捕获四帧两底色和原始源/mask检视、连续十循环；目视检查了浅/深底及mask图。具体本次数量与时间见`tools-plan.md`，临时证据`/private/tmp/coastal-motion-tools-capture-final/`不作为正式美术发布。

**review.tscn是原地播放工具。**不证明移动时支撑脚稳定、滑步、世界遮挡、碰撞、旧版动作覆盖、四方向/五类动作、隐藏像素完整或用户视觉认可。本节记录工具fixture；主任务现已使用真实人物运行，最终来源、视频与验收边界见[小样README](../README.md)。fixture通过、数量齐全或加载成功均不等于动态人物/衣物验收通过。


## 固定地面移动诊断（travel_review）

新增独立`travel_review.tscn`，不改变原地评审入口或生产工程。A/B位于两行固定地面（根点y350/y730），从屏幕x1100出发，共用同一monotonic时钟，以72 world/s × camera4 = **288 screen px/s向左真实平移**。Sprite仅使用manifest.display_scale，不再次乘camera4；不移动脚、改姿态、移动刻度或修补像素。

真实美术运行（所有Godot启动须require_escalated）：

```sh
TOOLS="$PWD/art/design/character-motion/adult-standard-v1/walk-west-proof-v1/tools"
/opt/homebrew/bin/godot --path "$TOOLS" --log-file /private/tmp/coastal-motion-art-travel.log res://travel_review.tscn -- --manifest=/absolute/path/to/baked/export-manifest.json --capture-dir=/private/tmp/coastal-motion-art-travel
python3 "$TOOLS/verify_travel_capture.py" /private/tmp/coastal-motion-art-travel
```

默认自动运行10个实际完整循环、保存起始截图和约30fps连续PNG，随后退出；未指定capture-dir时自动使用`/private/tmp/coastal-motion-travel-<ticks>`。截图采样包含PNG保存耗时，实际间隔和相位写入`travel-capture.json`，不把目标fps当实测fps。80ms/帧与其他合法manifest时长均按实际合同播放。

角色只在**完整循环边界**重置到x1100。每次横穿预留root x128：`loops_per_pass=max(1,floor((1100-128)/(288*cycle_seconds)))`。320ms周期为10循环/次，640ms周期为5循环/次；每次重置记录边界时间、实测观测时间、循环号、跳前/跳后根点和原因。单循环本身过长时允许角色暂时出屏，仍不在循环中途跳回。界面显示pass与已发生的重置，序列跨重置处明确不属于无跳连续运动。

记录绑定manifest路径/哈希、artifact_digest、当前移动场景/脚本/时间轴/加载器/项目哈希；逐图保存实测时间、frame/pose/loop/pass、A/B真实根点屏幕坐标与实际纹理索引、世界速度/camera4/屏幕速度、出屏与PNG错误状态。固定刻度每72屏幕像素（18 world单位），仅为诊断UI，不是正式游戏美术。

工具测试：

```sh
python3 "$TOOLS/make_fixture.py" --output /private/tmp/coastal-motion-travel-fixture
/opt/homebrew/bin/godot --headless --path "$TOOLS" --log-file /private/tmp/coastal-travel-headless.log --script res://test_travel.gd -- --manifest=/private/tmp/coastal-motion-travel-fixture/baked/export-manifest.json --test-no-capture
/opt/homebrew/bin/godot --path "$TOOLS" --log-file /private/tmp/coastal-motion-travel-native.log res://travel_review.tscn -- --manifest=/private/tmp/coastal-motion-travel-fixture/baked/export-manifest.json --capture-dir=/private/tmp/coastal-motion-travel-fixture-capture
python3 "$TOOLS/verify_travel_capture.py" /private/tmp/coastal-motion-travel-fixture-capture --fixture
```

`--test-no-capture`仅供场景测试使用，禁用自动捕获和退出。`verify_travel_capture.py --fixture`会直接测量诊断色块在原生PNG中的位置，并检查固定刻度，证明实际图像跟随288px/s根点移动；真实人物素材运行时不要传`--fixture`。

该入口补充移动参照，但**不自动宣称脚点稳定或滑步合格**；主代理需按真实接触事件/像素跟踪支撑脚。它也不证明四向五类动作、世界遮挡/碰撞、动态换装或用户认可。本节为工具fixture记录；真实美术最终验证见[小样README](../README.md)。具体实测结果见tools-plan Task3。


2026-10-23原地短周期采样修复：真实80ms×4记录`/private/tmp/coastal-motion-ab-native`只有37张连续样本，原有>=40检查正确报错。已先复现并新增采样/联合停止条件失败测试，再提高目标频率并保留>=40门槛；另显式校验连续序列四姿态覆盖。修复后的80ms色块fixture原生结果见tools-plan Task4，不替代真实人物重烘焙后的证据。

2026-10-23真实显示尺度138/582经Godot JSON舍入会有约1e-16误差。travel验证器现以rel/abs_tol=1e-12比较，新增2项回归证明序列化舍入可接受、1e-7真实尺度差仍拒绝；Python工具测试现18项。
