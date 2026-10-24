# 单侧运动工具 Implementation Plan

> **For agentic workers:** 当前工具子任务按已授权的 Inline Execution 执行，不嵌套委派，不提交。

**Goal:** 为西向四帧 A/B 小样提供可追溯离线合成和独立原生评审，工具通过不等于美术通过。

**Architecture:** Pillow 仅做整数平移、目标层 alpha mask 和后到前合成；严格检查 motion.json，输出 baked 和内容哈希清单。独立 Godot 场景读取烘焙清单，一份时钟驱动 A/B 与两种显示尺度；自动原生截图和连续循环记录保存到测试临时目录。

**Tech Stack:** Python 3 + Pillow、unittest、Godot 4。

## Global Constraints

- 只创建本目录 tools/ 与 tools-plan.md，不碰生产 Godot 工程，不生成正式美术。
- 输入固定四姿态 walk_w_0..3，画布 512×768，根点 [256,708]，display_scale=.2371134；源可小于画布，整数 offset，L mask 白色隐藏。
- 不缩放部件、不推断隐藏像素、不将文件数当姿态数；mask只作用其声明层。
- 原生 Godot 执行必须 require_escalated，日志 /private/tmp/coastal-*.log；测试及截图 /private/tmp/coastal-*。

### Task 1: compositor

**Files:** `tools/compose.py`, `tools/test_compose.py`。
**Consumes:** motion.json 及其相对 PNG sources/masks。
**Produces:** `compose(motion_path, output_dir=None) -> dict`；默认根目录 baked/{A,B}_{0..3}.png 与 export-manifest.json。

- [x] 先编写真实像素fixture测试：目标层mask、前景手不删、共享源、透明边缘及导出哈希；缺帧/未知姿态/无资源/出界/非法时长缩放拒绝。
- [x] 运行 `python3 -m unittest discover -s tools -p 'test_*.py' -v`，确认因模块尚未实现而失败。
- [x] 实现严格合同与最小合成；同命令通过。

### Task 2: native review

**Files:** `tools/project.godot`, `tools/review.gd`, `tools/review.tscn`, `tools/test_timeline.gd`, `tools/timeline.gd`, `tools/make_fixture.py`, `tools/review_data.gd`, `tools/test_review.gd`, `tools/test_review_ui.gd`, `tools/verify_capture.py`, `tools/README.md`。
**Consumes:** baked/export-manifest.json（绝对路径）；可选 --capture-dir=/private/tmp/coastal-*。
**Produces:** 同时钟 A/B、统一 display_scale 与 2x 放大、空格暂停/方向键单步/B换底色；四帧×两底色截图、至少10循环的连续原生PNG与逐截图实测时间/姿态JSON。

- [x] 写时间轴失败测试，验证四帧边界、循环、低帧率跳跃及非等长时长；先运行再最小实现。
- [x] 固定UI存review.tscn，行为在review.gd，清单检查在review_data.gd；无玩家存档读写。
- [x] 用 `/private/tmp/coastal-motion-tools-fixture` 中非美术像素fixture做 headless时间轴、清单/UI与有窗口原生截图验证；记录实际帧/时间、四视图纹理索引、两种底色、源/mask检视与十循环连续PNG。
- [x] README记录真实美术/fixture完整命令、metadata合同及证据局限；通知主代理固定接口。
- [x] 新增source_root兼容字段及重定位失败测试；评审清单未实现、原生证据不存在、小数毫秒未拒绝、深底黑字分别先验证失败再实现/修复。

## Result

2026-10-23本轮工具完成：16项Python合成测试通过；Godot时间轴、真实baked/source读取、损坏哈希/时序/小数时长拒绝、暂停/恢复、首尾单步、换底色、target mask及A/B显示尺度检查通过。原生Godot 4.7.1（`/opt/homebrew/bin/godot`）以有窗口Compatibility/OpenGL在Apple M4运行，日志`/private/tmp/coastal-motion-native-fixture-final.log`无错误。`git diff --check`通过。

最终fixture证据：`/private/tmp/coastal-motion-tools-capture-final/capture.json`，8张四帧×两底色、2张原始源/mask检视、72张连续PNG；真实连续时钟6418.250ms，覆盖10循环，最大采样间隔98.404ms，四姿态全覆盖。`verify_capture.py`通过；已目视检查浅/深底和原始target mask，深底文字对比度问题已修复。artifact_digest=`a1ba61270162ea5b9d5ec8cc29449d415446891ce99821a0541f69c9b5c04884`。该目录是可删除的测试证据，未写入生产工程或美术发布清单。

接口：schema_version仍为1；`source_root`相对manifest目录指向motion目录，旧清单默认`..`。子层沿用frames.layers与inputs.sha256，主视图读取烘焙PNG，检查视图显示未应用coverage的完整源和对应raw mask。README列出真实美术原生启动/捕获命令；原生工具仅原地播放，不证明移动时支撑脚/滑步、世界遮挡、碰撞或完整动作覆盖。真实GPT动态资源未运行，不宣称人物美术或用户动态验收通过。

分工：本轮独立工具代理只负责tools/与本计划，主代理并行制作真实GPT美术。未嵌套委派、未提交。此前计划的原生工具缺失已补齐；真实素材质量、分层合同、原生人物运动及用户视觉验收由主任务继续处理。

### Task 3: travel diagnostic (追加授权)

**Goal:** 固定地面参照下以72 world/s × camera4 = 288 screen px/s向左平移真实烘焙角色，供主代理检查支撑脚/滑步；工具不判定脚点美术通过。

**Files:** `tools/travel_clock.gd`负责绝对时间到相位/根点/完整循环边界重置；`tools/travel_review.tscn/gd`负责固定刻度、A/B两行和原生捕获；`tools/test_travel.gd`与`tools/verify_travel_capture.py`验证位移/同相位/显示参数隔离及证据。沿用review_data清单加载器，不改生产工程。

- [x] 先失败测试：1000ms左移288px，A/B同时间同帧同根x；80ms/帧和非等长时长；manifest.display_scale不乘入轨迹，camera4不再次乘入纹理显示尺度。
- [x] 最小实现固定根点x1100、两个y行，只有完整循环边界可重置；预计算一屏能容纳的完整循环数，过长周期允许暂时移出屏幕并记录，不能中途跳回。
- [x] 自动默认10循环、约30fps连续PNG及逐帧截图元数据，真实elapsed/root x/速度/循环、重置事件、manifest/工具哈希绑定。捕获写入/private/tmp/coastal-*，启动require_escalated。
- [x] fixture headless与原生验证，目视固定刻度/真实平移，写明不能自动证明接触点稳定或美术通过；README交付真实命令与限制。


Task3结果（2026-10-23）：先观察到移动场景/轨迹模块缺失的失败，再实现；`test_travel.gd`通过，覆盖真实1000ms/288px位移、A/B同相位同根点、80ms与非等长时长、manifest显示尺度和移动速度隔离、整循环重置及过长单循环不提前瞬移。

- 640ms非等长fixture：`/private/tmp/coastal-motion-travel-fixture-capture/travel-capture.json`，1张起始图+169张连续PNG，6434.120ms，10循环、2次已声明边界重置，最大采样间隔48.636ms。
- 320ms（80ms/帧）fixture：`/private/tmp/coastal-motion-travel-80-capture/travel-capture.json`，1张起始图+85张连续PNG，3216.806ms，10循环、1次已声明边界重置，最大采样间隔50.165ms。
- 两次均经有窗口Godot 4.7.1 / Apple M4 Compatibility原生捕获；`verify_travel_capture.py --fixture`通过，直接测量PNG色块位置并检查固定地面刻度、288px/s速度、A/B帧/根点同步和边界重置。目视比较起点与中途截图确认两个角色经过固定刻度。日志`/private/tmp/coastal-motion-travel-native.log`及`...-native-80.log`无错误。`git diff --check`通过。

仅诊断工具fixture通过；未运行或判断真实人物接触脚、滑步、动态衣物兼容、世界交互或用户美术认可。原地工具仍独立保留。真实美术命令与限制已写README，使用travel_review.tscn入口，默认10循环自动捕获并退出。未改生产工程、未修改主代理真实素材、未提交。


### Task 4: stationary short-cycle capture sampling（追加授权）

**Scope:** 仅`tools/review.gd`、`tools/verify_capture.py`、新增`tools/test_capture_sampling.gd`及工具文档。不碰真实parts/masks/body归属修复。

- [x] 原记录`/private/tmp/coastal-motion-ab-native`复现37张连续样本导致>=40验证失败；新增缺少采样/停止联合规则失败测试。
- [x] 最小修复：目标间隔`min(1000/24ms, min_frame_duration/2)`；停止条件为至少十循环 AND 至少40连续样本 AND 四姿态全覆盖，不降低验证门槛、不伪造固定fps。
- [x] 回归验证80ms目标40ms、长帧目标1000/24ms、变长帧按最短时长一半；37/39样本、少姿态、未满十循环均不得停止。
- [x] capture.json新增目标间隔、实测fps和实际间隔min/mean/max；verify_capture保留>=40要求并核对四姿态与实测统计。
- [x] 用80ms/帧fixture完成有窗口原生验证，记录结果并通知主代理工具哈希稳定后再烘焙真实素材。


Task4原生结果：`/private/tmp/coastal-motion-capture-80-native/capture.json`，8停帧+2检视+69连续样本，实测3214.856ms覆盖十循环、四姿态均覆盖。目标40ms/25fps；实测21.151855fps，间隔min40.453ms/mean47.277176ms/max58.381ms。verify_capture通过，>=40门槛保持不变。采样/停止联合条件headless回归通过；原生日志`/private/tmp/coastal-motion-capture-80-native.log`无错误，git diff --check通过。只证明工具fixture，真实A/B需主代理修复归属后重新烘焙/捕获。

### 最终真实尺度记录修正

真实138/582在Godot JSON往返后精确浮点相等断言误报；先红测试复现，再仅在travel验证器使用1e-12容差。2项回归绿，1e-7真实差异仍拒绝。主代理按最终工具哈希重新烘焙并原生捕获，真实美术证据见同级README。工具Python共18项；不修改画面尺度或放宽采样门槛。
