# 南向 top03 四帧 walk + idle 真实登记

本包完成内部南向衣装资源扩展：一个严格 schema3 基础配方、5个canonical B姿态、15个真实组件、新review-only构建。它是24格统一任务的一部分，不包含发帽、Godot消费者、原生动态或发布认可。

配方 `recipes/top03-south-locomotion/r001.json`，构建 `builds/top03-south-locomotion-r001`。统一 `build.py build` 和 `verify` 均通过，artifact digest `b948a38f804b6bdd74501ec7006a60f320d30519a09baed765da0ddf6c432000`。配方SHA `cc552f470e1705a87f101efb9a9a89667db01f58644b014ec8bd34ebd4ba0236`。

## 实际材料来源

| pose | 有限top材料点 | 实际额外选择 | 原裤材料点 | 原鞋材料点 |
|---|---:|---|---:|---:|
| walk_south_0 B_4 | 29586 | 原已验r005+r007：434点edge选择保持；聚合新revision显式继承canonical alpha | 14093 | 7059 |
| walk_south_1 B_5 | 26450 | r002完整pose为主；r003完整shirt17点；旧r001完整shirt仅2点navy collar | 12886 | 8226 |
| walk_south_2 B_6 | 29484 | r002完整pose为主；r003完整shirt31点 | 13880 | 7142 |
| walk_south_3 B_7 | 27918 | r002完整pose为主；r003完整shirt51点 | 13191 | 8226 |
| idle_south_0 B_0 | 35303 | r002完整pose为主；原B0真实navy knit cuff1696点 | 15791 | 7067 |

新GPT源包 `sources/gpt-top03-south-locomotion-v1` 保存实际使用的7张新完整原图、既有walk1完整shirt原图、提示词、输入参考和各文件SHA，生成器为内置GPT imagegen（工具不暴露精确模型标识）。所有新原图1024×1536，整源NEAREST1/2到512×768，canonical frame root[512,1416]→[256,708]，注册平移[0,0]。原始完整图未按部件挪缩。多源选择为独立二值source-selection，ownership与target coverage角色/文件分开；软alpha不重复相乘。

既有walk1 shirt来源输入：B5为pose约束，southwalk0 collar-repair r004为style，后者库内内容SHA `ba23ed021c5d6cf99a644986761372f9a3c6050d18fbf5a211c3b325d7f47e51`。当时实际使用库内/缓存哪一个同字节路径别名无法独立恢复，source.json已记录此不确定性，没有虚构精确调用路径。它的错位hem/cuffs均不选，只有同坐标两点实际navy collar参与。

新完整pose图生成的脸、手、裤鞋不当body使用。实际body.texture是冻结canonical完整B帧的等RGBA别名，并由schema3同pose body校验绑定。所有生成源皮肤点均从cloth选择中排除或被真实cloth源互补。

## 原navy腕口与原裤鞋的诚实复用

`canonical-b-south-locomotion-reference-v1` 是完整已注册canonical B帧的字节相同copy，明确kind为derived-frame-reference，**不是GPT raw、新身体或隐藏身体**。metadata绑定canonical poses/variant/pose/frame/SHA、原实际layer源/遮挡/SHA与来源包，并追溯379a9bc原始GPT atlas、prompt、旧完整帧registration记录。完整原帧保留，不只保存切片。对应alpha/root/geometry正是该pose真实canonical记录。

idle原腕口下段在y495..518，取实际cloth交集1696点，只含原有navy针织cuff而不含普通蓝袖身。它作为top03有限适配的明确额外材料源，点仍计cloth，不重叫outline、不调色、不平移。原帧1/1整源密度与其真实source_pose注册。`idle-original-navy-cuff-comparison.png` 保留原B0、新r002源、最终混源腕口放大。主代理已目视确认工艺/深蓝trim相容、腕边皮肤正确；这仅是source视觉核查，不是用户或原生认可。

原裤鞋按冻结分层的实际可见lower贡献和人工review的pants/shoes材料界面登记，保留中性轮廓；按真实靴边区域区分裤与鞋，palette仅辅助定位，不以颜色独自声称款式身份。它们各有非空ownership/coverage和完整RGBA纹理，真实mapper从derived full frame复算通过，每帧分别替换时与canonical原身体RGBA完全相同。没有空层，也不把完整参考帧当第二body。该接口只支持列出的5个原canonical B姿态、原版型和真实可见材料，不声称独立可换下身或隐藏腿脚层。

## 边界与alpha

旧粗garment池包含皮肤、裤腰与中性轮廓，不能按名字全当cloth。新姿态的有限材料界面逐区检查原颈口、肩、袖腕、腰线；候选池之外沿的明确中性轮廓/原始fringe逐点记录原RGBA与决定：walk1有11点、walk2有21点、idle有21点；不是通过删除真实袖口蓝布来过关。idle真实袖口仍全部以真实原navy材料覆盖。更早w0的1069点非材料修正和139隐藏sidegap限制不因此升级为完整隐藏衣层。

新的聚合 `south-locomotion-r001` 显式采用 `canonical-surface-alpha-v1` wrapper：RGB来自上述完整真实源及二值选择，alpha仅在owner内取该source annotation绑定的实际canonical frame。source/target同pose，因此无需视觉alpha阈值或重新描边。原始 `south-walk0-r001` source、annotation、view、texture及receipt完全不改；聚合新revision另存纹理/明确alpha来源。wrapper已另做独立只读复查，结论和边界见 `/private/tmp/coastal-canonical-surface-alpha-independent-review.md`。

统一构建5帧实际输出测量：每帧全画布alpha差0；top coverage外RGBA差0；原裤鞋材料内RGBA差0。face/skin/hands/lower原样保留。证据 `actual-output-invariance.json` 与 `five-pose-original-and-build.png`。源512×768、逻辑显示约121×182（display_scale0.2371134），静态实际尺寸与放大接缝都已目视核查；诊断GIF使用canonical80ms，未代替独立runtime rate0.75/native动态验证。

## 文件与复核

- 新定义/适配：`parts/{top03,original-pants,original-shoes}/revisions/south-locomotion-r001` 与各自 `adaptations/adult-standard-v1/review-motion-v1/south-locomotion-r001`。
- 新sidecar：`templates/adult-standard-v1/motions/review-motion-v1/annotations/south-locomotion-r001/poses.json`；不修改共享r001。
- body别名：对应 `body-views/south-locomotion-r001`，完整canonical RGBA。
- 15组件的公开RegisteredAdaptations.component真实准入回执 `component-admission-receipt.json`；实际统一5帧build+verify通过，非fixture。

临时资源登记脚本只是来源/掩码/metadata准入测量，正式构建只调用既有build.py，不新增批次合成器或播放器。失败的shirt r004、idle r005以及整体缩小的idle r006保留在临时源尝试目录，未混入正式source输入。现有早期walk1错trim、walk2缩小候选也未作为整体源接入。

未验证：Godot原生显示、连续运动/进入退出/遮挡/服装切换、发帽、其它方向/动作和用户认可。本包status仍review-only，发布仍关闭；不更新既有baseline、现行catalog或发布manifest/current指针，不提交或推送。


最终门禁：205项人物unittest / 123.008s，全部OK。check.py第一次恰逢共用engine升级后的旧build迁移窗口而报告stale；主代理完成4旧build r004迁移、逐一verify全部7个strict build后，只重跑check一次，结果passed=true：strict_recipes=8、strict_builds=7、frozen_legacy_recipes=9，production_release仍closed。日志：`character-tests.log`、`character-check.log`（迁移窗口失败）、`character-check-after-shared-migration.log`（通过）。没有因该窗口重复205 suite。`git diff --check`通过。已逐一核4个实际关联源包的所有声明assets文件/SHA，结果在`source-assets-verification.json`。
