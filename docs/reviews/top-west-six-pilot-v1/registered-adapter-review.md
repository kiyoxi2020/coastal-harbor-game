# registered评审适配器：定向独立复核

范围：`tools/characters/registered_review.py`、`review.py`新增dispatch及`tests/test_registered_review.py`；收到Godot首轮冻结通知后，追加查看`character_registered_samples.gd`、`character_registered_trial.gd/.tscn`及对应测试，并按需读取共用trial/面板接口。未重复美术、source-prep工具实现或七帧配方像素审计，未修改项目文件/跑全量测试。

最终结论：**本次定向复核通过，三项已报告问题均已修复并独立关闭，没有本审查遗留的阻塞项。** 下文1–3节保留发现/处理过程；末节记录最终冻结后的定向复验。未重复全量测试、美术或准备源审计。

## 1. Python source annotation同姿态漏洞：已关闭

初次独立真实fixture复现：在全新`/private/tmp/coastal-registered-adapter-audit-*`调用项目已有真实strict+prep小fixture，只把walk_east_0的view.source_pose.record改成idle_east_0；实际prepared materials仍walk、mapping.target_pose仍walk，更新真实adaptation/recipe SHA并严格重新build。旧adapter preflight成功返回。

原因：旧逻辑校验prepared文件与当前目标pose，却没有核source_pose的实际annotation记录；严格schema3本身允许合法跨source pose登记，不能自动提供本有限同姿态consumer的额外限制。

作者补充真实先失败反例后修复。当前preflight的`same_pose_annotation`分别解析source_pose、target_pose，通过直接bound文档验证实际poses/variant/pose_id/reference_frame/canvas/root/display均匹配当前canonical；不机械要求selector字符串相同，因此仍允许同语义的明确注册记录。

独立重新运行原攻击，在新`/private/tmp/coastal-registered-source-fix-check-*`真实严格fixture中明确拒绝，错误：`Prepared source annotation must match actual canonical pose`。该Important已关闭。

## 2. Godot失败重载的预览纹理残留：已修复（最终复验见末节）

位置：`character_registered_trial.gd::load_registered`失败分支。它同步清空世界pose.texture、frames/clips/metadata及运动状态，但没有同步清空`review_panel.reference_view.texture`和`motion_view.texture`。

实际最小逻辑复现保存在：

- fixture与脚本：`/private/tmp/coastal-registered-ui-review-cuvtwe2i/probe.gd`。
- 日志：`/private/tmp/coastal-registered-ui-probe.log`。

使用真正的2帧east strict+prep fixture，先成功加载再隐藏面板，随后加载坏suite。Godot headless逻辑输出：

```text
READY_OK true previews true true
FAIL_RESULT false body_clear true ref_clear false motion_clear false
HIDDEN_AFTER_FRAMES ref_clear false motion_clear false
```

共用面板仅在可见时_process，因此隐藏后旧预览纹理会一直留存；可见时也需等下一refresh才清。未发现错误回退旧身体数据，但不符合失败立即清除所有评审显示状态的预期。

建议失败分支同步清两个Sprite纹理或刷新空预览，必要时停止预览播放；补隐藏面板失败重载断言。作者已收到复现，主代理已暂停正式采集并安排修复/重采。此处是逻辑状态复现，不充当GPU美术证据。

## 3. Python/Godot scope一致性：已补齐（最终复验见末节）

另一个全新`/private/tmp/coastal-registered-order-review-*`fixture把所有frame.layer_order改为`['top','body']`，实际严格重新构建并更新suite：Python preflight仍接受。Godot显式只收`[body.id,top.id]`并拒绝。

这不会造成Godot错误显示或绕过其门禁，但会出现“Python预检通过，启动后拒绝”的不一致。建议Python提前校验相同层序，补实际strict fixture反例；其它Godot明确限定的prepared二值提取子接口可一并对齐范围说明。该项属于流程一致性，不是任意文件加载或原body替换漏洞。

## 已核实正确的Python链

- registered dispatch先preflight，再打开单一共享scene，传`--registered-suite=`，没有新人物合成器/动作时钟或生产接入。
- suite/runtime类型与范围、lexical路径/symlink、规范build根、manifest SHA明确校验；在旧verifier处理前先遍历strict inputs路径。
- **真实suite实际执行preflight通过**；只作调用计数包装、不mock返回值，确认调用原`build.verify`1次、原`prep.verify`2次。因此是实际重建校验，不是只信manifest标记。
- prep manifest、全部prep inputs、source.json以及materials/ownership/textures均要求直接在strict inputs闭包绑定当前SHA；缺原准备纹理、缺原登记计划、重复/未实际使用的prepared绑定都被拒。
- body要求引用真实canonical file+SHA，拒绝仅像素相同的替代PNG；prepared与clip实际pose/action/direction/variant/canonical_poses及几何逐项绑定。
- copied parts texture逐RGBA等于对应prepared texture；同pose annotation修复后补齐语义约束。能力只收idle/walk及匹配方向，缺资源没有回退。
- 测试使用真实strict+prep fixture及不均匀70/90ms时序，而不只mock“通过”标记。原wrong prepared material与新wrong source annotation是两种不同失败场景，后者确有必要。

## 已核实正确的Godot链

- loader在开始先reject清空，随后只往pending dictionaries/arrays装数据，所有通过后一次提交；具体失败均reject，frames/metadata/clips/geometry/runtime/prepared/artifact不残留。
- 严格输入实际SHA、构建engine代码SHA、strict artifact digest、输出PNG文件SHA与解码RGBA SHA均校验，原body通过真实canonical引用加载；不使用旧资源回退。
- source-prep Godot侧校验绑定的真实manifest/input/engine/output SHA、PNG格式/尺寸、ownership二值及RGBA摘要；明确不在Godot另做raw source compositor，实际重建由Python preflight承担。
- source/target annotation均解析实际同canonical姿态，不只看字符串pose token；prepared文件/closure和parts纹理与prepared输出的RGBA一致。
- trial直接extends现`character_walk_trial.gd`，没有重写_physics_process/current_frame等时钟；走路phase仍按实际位移/世界速度推进，松开回匹配idle，阻挡不继续走相位。预览沿现`character_motion_review.gd`的播放/逐帧逻辑，不另建批次播放器。
- unsupported方向在输入投影和按钮层过滤；run/farming不在当前clips内，相关控件禁用。
- world尺度来自suite统一整帧scale，root来自真实geometry；scene使用nearest继承设置，固定布局在tscn。面板0.5 Sprite scale叠加共用CanvasLayer2倍transform，标题源纹理1:1并非单独放大衣物。
- 除第2项UI纹理残状态外，未发现新的Godot加载/动作时钟阻塞问题。

## 冻结边界与验证限制

`runtime-baseline.json`的git diff为空。body归档冻结的pack_sources.py、build.py、build_contract.py、composition_contract.py live SHA均保持原值。共用walk_trial/motion_review并非该586文件body归档的冻结文件；其新增薄初始化/控件接入仍需对应既有回归，不把历史原生回执变成本轮通过。

同pose修复后复核快照：

- registered_review.py：`ae35856473f0d81b6bf57a193456e429c102963e291e4a7c79bd6b23f0079255`。
- review.py：`d0617a55f64f49093b0ed0449e14b40ba77410837529d21fed5f3fcce386e93d`。
- test_registered_review.py：`99668131694ae10c502fafb06d799e764e0f7900a770e994d6d20edd41729d95`。
- registered_samples.gd：`ebbe932333afa6c39f02e6ff70a47429ee29409842f8d8833a8ea7a677d64997`。
- registered_trial.gd：`1e48c53210b6d3fec24f04575defd7a3fdddb25efae99eee0a3e9d741c1a2b92`（UI残状态修复前）。
- registered_trial.tscn：`4a09e73739069367a9ff7092ff5d468042a0c7203c806ddecf0ef828d3d62777`。

作者报告13项Python定点及75项Godot检查通过；本独立复核没有重复这些整套检查或主代理正在运行的全量/check，只执行上述独立攻击/修复反例、真实preflight及UI逻辑probe。最终采集必须在待修代码再次冻结后复核，不沿用修复前证据。


## 最终冻结后的定向复验：三项全部关闭

严格按主代理要求只复验已报②③，无新调查/全测。①source annotation修复此前已独立复验拒绝原攻击，本轮未重复。

### ②隐藏面板失败重载

复用原真实strict+prep fixture及原Godot probe，只在失败前明确置预览playing=true、preview_phase_ms=73，写新的临时probe与日志，未改项目：

- 脚本：`/private/tmp/coastal-registered-ui-review-cuvtwe2i/probe-final.gd`。
- 日志：`/private/tmp/coastal-registered-ui-final-probe.log`。

headless逻辑输出：

```text
READY_OK true previews true true
FAIL_RESULT false body_clear true ref_clear true motion_clear true
FAIL_PREVIEW_STOP true phase_zero true
HIDDEN_AFTER_FRAMES ref_clear true motion_clear true
```

所以坏suite返回时世界及两预览纹理已同步清空，预览停止/相位归零，隐藏面板再过两帧也保持清空。源代码失败分支与此行为一致。进程exit0；该次probe另打印一条macOS系统CA证书`get_system_ca_certificates`错误，非脚本/加载断言错误，本轮未扩大调查，亦不据此声称该日志完全无ERROR。它不是主代理r005 GPU采集的日志。

### ③Python/Godot范围一致

新`/private/tmp/coastal-registered-order-final-*`真实fixture：原合法body/top同姿态preflight仍成功；将layer_order全部改为top→body后重新严格构建，现Python明确拒绝：

`Registered frame layer order must be body then top`

只读确认最终Python同时显式限定alpha-over、registration null、实际body→top层序、layer/mapping coverage与occlusion null、binary-rgba-extract-v1及density_normalization None，和当前Godot有限consumer范围一致。没有为通过而放宽strict/prep验证。

### 最终本次复核身份

- registered_review.py：`5674f70e4aafb4f34c1ee7a0f884b3aa5a4784eaa57c7c9c7a65105449486c63`。
- test_registered_review.py：`ea31340f072097dbe923c35d54ce9f35a905b35bd84447d8b0b1a248930ae57a`。
- registered_trial.gd：`bc818839aacaaa37f6fb1da28e3a076e5ce67a58abd050b9a3f53796d3049d21`。
- test_registered_review.gd：`037878f097bdde268f6ccd479581c4d89095bed0cd23e35ac72b05698f986b76`。

作者报告最终16项Python定点、78项Godot断言通过；主代理正在执行最终全量与r005 GPU采集。本独立复验只证明旧反例关闭，未冒充这些全量或原生证据完成。
