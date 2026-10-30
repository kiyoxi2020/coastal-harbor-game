# 成年固定配方全动作统一交付：执行方案

> 执行约定：主代理按下列工作包顺序实施；默认直接执行，仅在独立子任务与实际并行工作同时成立时按AGENTS委派。每批有可验证出口，整轮终点是24个能力单元统一交付。当前文件为设计阶段执行方案，未开始代码或美术实施；不自动提交/推送。

**Goal:** 当前成年top03/原裤/原鞋配方支持四向idle、walk/run/hoe/water/harvest及固定hair_hat（栗色短发＋草帽）组合，统一构建、评审与原生验收。

**Architecture:** 扩展现行coastal-character-construction-v1，一份固定hair_hat配方引用全动作基础配方；版本化来源/适配，复用现有Godot加载器和trial权威时钟。西锄是回归基准，西walk是多target接口验证用例，均服务于一个全包交付。

**Tech Stack:** Python3、Pillow、unittest、Godot现有工程及GDScript、GPT同源资源/必要补图、Paseo Progress。

**设计依据：** [全动作统一交付设计](../specs/2026-10-29-character-all-actions-design.md)。用户本轮目标替代[此前西walk单独阶段计划](2026-10-29-walk-west-next-step-analysis.md)的范围和停止出口。

## 全局约束

- 唯一制作规范为`docs/design/character-art-pipeline.md`，目标24动作方向×1个hair_hat组合=24格；当前84pose/84结果不锁死未来必要帧数。
- 不改旧脸手、不靠部件挪缩掩盖缺图；完整穿衣参考不当隐藏身体，三类mask用途分开；新增像素按GPT制作规范保留源/提示词/注册。
- 统一build.py build/verify；旧schema语义保持，新接口显式版本化；缺源/缺view/缺能力必须报到pose与part。
- runtime-baseline.json不刷新、不放宽；生产仍player-unified-v4；本轮完整固定配方动作包不等于8混搭/其他体型/生产发布。
- Godot每条命令都带`--log-file /private/tmp/coastal-*.log`，存档与采集只在`/private/tmp/coastal-*`。
- 逻辑先失败反例再最小实现；每批只跑相关验证，整包交付跑必要完整检查；源码不变不重复GPU采集。

本轮只补齐hair_hat全动作，不为bare、hair-only、hat-only建设新配方、资源或换装功能。既有四状态西锄只保留原范围的历史/兼容回归，不能把四状态工作量继续算入新动作交付。

## 工作包1：冻结全范围来源矩阵与旧构建恢复

**文件：** 新建`art/characters/evidence/all-actions-v1/readiness.json`、`history.json`；读取coverage、2026-10-28覆盖审计JSON、walk准备evidence、具体pose/view/source索引及四旧strict manifest；不全量复制库。

**接口：** readiness为工程规划证据，不是第二份运行权威。每格键是`action_id/direction/head_state`，逐pose记录实际输入file/SHA、配方身份、源/目标坐标、衣装与头部缺口、需登记/重提取/新绘制分类、依赖及阻塞原因。

- [x] 生成24格（head_state固定hair_hat），检查笛卡尔积无漏格/重复，按实际84姿态枚举views，输出新增绘制视图数而非“格数即生图数”。
- [x] 对每个候选来源核父衣装/脸手/比例，复用原款需绑定有限适配身份；不能把pants02/shoes04改名当目标款。
- [x] 记录2742c19中四旧build、三engine文件、配方与原生证据Git对象/SHA，验证恢复原字节及旧Pillow环境可定位；必要非Git输入先保全。
- [x] 形成缺图清单；只对缺失的具体表面/投影准备GPT补图请求，现有可复用来源继续推进。

**出口：** 所有格有真实输入或明确缺口，历史恢复已实测；发现缺口不降低24格目标。不得再次把本工作包当作本轮最终交付。

## 工作包2：扩统一合同及当前构建迁移

**修改：** `tools/characters/build_contract.py`、`composition_contract.py`、`build.py`。
**测试：** `test_build_contract.py`、`test_composition_contract.py`、`test_real_construction.py`、`test_repository_gates.py`。
**资源：** 固定五部件design的`revisions/r002/design.json`和适配`r002/views.json`；旧design/r001不变；输出新西锄回归构建目录及history迁移映射。

**接口：** 保持`construct(repo, recipe, output)`与`verify(repo, directory)`；增加同kind schema3基础配方，schema2头部只允许schema1或schema3一层基础配方。配方显式file/SHA选择设计修订与适配，不再凭隐含latest选择。保留原schema1/2解释。

- [x] 先建立错source_pose、漏target、源/目标坐标混用、未知schema、部件局部缩放、mask用途互换、覆盖错表面、修改锚点/输入哈希和输出覆盖的失败反例。
- [x] 为合法“一个idle source view→多个walk target”建立正例，证明整源保留、实际锚点推导，零缩放、无重复平移；普通alpha与二值RGBA替换分别验证软边。
- [x] 最小扩展合同/渲染，支持真实层序和无必要mask的显式声明；不能把诊断PNG或整套其他衣装作为新身体层。
- [x] 用新engine在全新目录重建西锄四state，20结果对原交付逐RGBA一致；旧配方和原输入继续可验证。
- [x] 原四strict构建在当前engine下过期时如实记录。先迁移评审和证据引用到新build，完成Git恢复/无悬空引用核验后移出被替代strict目录；冻结九legacy和baseline不变。
- [x] 运行`python3 -m unittest discover -s tools/characters/tests`、`python3 tools/characters/check.py`；所有当前strict构建通过，篡改依赖拒绝。

**出口：** 后续所有动作使用同一合同；没有另建每批次构建器；旧回执只认证冻结历史，新引擎输出需新的当前证据。

## 工作包3：一次性扩全包消费者与权威时间轴

**修改：** `tools/characters/review.py`、`construction_native.py`；`godot2d/dev/characters/character_construction_samples.gd`、`character_headwear_trial.gd`、`character_walk_trial.gd`、`character_motion_review.gd`及对应现有`.tscn`。
**测试：** `test_review_construction.py`、`test_construction_native.py`；`test_character_construction_loader.gd`、`test_character_construction_actual.gd`、`test_character_construction_native.gd`。
**新增配置：** `art/characters/reviews/all-actions-construction/review.json`；套件schema2中samples按动作/方向绑定全包一个hair_hat manifest及canonical idle。

**接口：** `load_samples(project, path)`保持；trial从统一clip数据获得pose/timing/geometry/phase映射。新增launcher suite `all-actions-construction`，不另建第二播放器。全包缺任一required clip拒绝打开；内部开发fixture只能明确标partial，不写full状态。

- [ ] 先测试旧hoe suite兼容、不同帧数/时长的合法clip、漏方向/固定hair_hat状态或混入其他交付头状态、manifest错配、SHA篡改、时序不一致、缺canonical idle均拒绝。
- [ ] 移除全包路径中的hoe-west/四pose硬编码，保留旧suite schema1严格边界；动作控件从合同能力显式加载。
- [ ] 让世界角色切动作和面板预览分别清楚，世界角色所有层共用唯一action/direction/elapsed/rate/instance；新数据复用现有trial状态路径。
- [ ] 先为低帧率跨事件、暂停/变速/重播、方向锁定、完成一次及walk-run相位写失败测试，再实现；评审不发业务事务。
- [ ] 原生validator依实际clip/loops枚举证据，记录engine delta、world position/velocity、屏幕变换与接触点，而非只接受fixture布尔值；篡改或缺一组拒绝发回执。

**出口：** 合同和消费者可以一次接全动作，后续批次增加正式资源无需再复制评审/原生工具。

## 工作包4：同配方四向idle与walk

**资源：** `art/characters/recipes/adult-top03-full-base/r001.json`基础配方；`art/characters/recipes/adult-top03-full-hair-hat/r001.json`固定hair_hat配方；五部件新revision适配与所需source包。配方仅在资源齐备时进入活动recipes；临时partial配方放`/private/tmp/coastal-*`验证，不伪装完整。

- [x] 西idle hair_hat精确复用已交付结果；另三向建立同一固定衣装的hair_hat结果，合计四向4个idle，不直接复用灰短裤赤脚的静态身体。
- [x] 西walk先落正式source/target多映射，保留测得delta和实测依据；当前源80ms/rate0.75分开记录，不把离线APNG当runtime证据。
- [x] 继续south/east/north walk；每pose核脸手、领袖腰踝、裤鞋和前后摆层序。按缺口使用GPT定向补源，不任意镜像或复制站姿。
- [ ] 每方向直接在共用trial按真实尺度/速度看连续循环、转向/急停和canonical idle；源分辨率/输出分辨率/实际屏幕大小写入记录。

**出口：** idle/walk四向×固定hair_hat共8格通过内部验证；同一轮直接进入run，不单独结束西walk阶段。

## 工作包5：同配方四向run及运动衔接

**文件：** 同一五部件适配revision及全包配方工作稿，复用现有run来源索引；事件/相位配置属于同一动作合同。

- [x] 逐向核已有run的衣装/身体来源，不能把top04/其他鞋父配方整体接入；补齐top03、原裤鞋和hair_hat的实际动作视图。
- [ ] 登记实际支撑/腾空和walk↔run相位，不把walk加速冒充run，不强制帧号映射。
- [ ] 验证四向转向整套一致、加减速/急停、run→idle和walk↔run；按≤1实际屏幕像素目标核接触/滑步。

**出口：** 新增4格，idle/walk/run共12格成立；必要修复直接回源/映射，不额外启动新跑步体系。

## 工作包6：同配方三农事四向

**文件：** 同一五部件适配与配方；必要工具层/source，motion pose及contact/events精确修订。旧完整农事参考仅作为来源和姿态参考。

- [ ] hoe先复用西向已验20结果，再补其他三向；water和harvest各补四向，每个动作方向hair_hat完整。
- [ ] 保留同母版脸手/比例；弯腰、手臂过胸、工具穿前后、裤腿/鞋及发帽投影按当前pose登记，不能把idle头脸硬贴到不同投影。
- [x] 需要隐藏像素时只补实际露出的表面；工具拆近远层遵循真实握点；不改变业务事务发生时机。
- [ ] 每组验证进入锁方向/移动、接触、恢复、回唯一idle；登记不可取消或实际支持的取消范围，低帧率事件不漏不重。

**出口：** 新增12格，累计24格无缺项。任一格缺源或视觉失败保持rework_required，不能宣称全动作已完成。

## 工作包7：冻结统一制品并完成整包原生验收

**输出：** 新目录`art/characters/builds/adult-top03-full-hair-hat-r001/`一个交付构建；`art/characters/evidence/all-actions-v1/`保存轻量合同/输入闭包/回执/摘要、必要代表图、连续预览和完整采集持久化清单。full-review清单绑定一个hair_hat manifest；coverage按实际范围更新。

- [x] 冻结完整正式配方后用统一build构建hair_hat，输出目录必须全新；执行verify，确认24clip/四idle/全部pose一致。
- [ ] actual加载hair_hat构建，逐帧查看当前84结果及四向4个idle；西锄20图RGBA对照通过，检查所有动作切换不读旧生产纹理。
- [x] 原生采集：walk/run共8组各≥10循环，农事12组各≥10次，24格全部明暗停帧；录制连续渲染帧与精确时序，世界移动不只原地播放。
- [x] 固定hair_hat下测四向idle↔walk/run、walk↔run、各农事开始结束、所有有向转向对、急停、暂停变速/重播；验证发帽组合始终保持一致。
- [ ] 真实尺度核足/握点/目标≤1屏幕像素及滑步，经过树/柜台/门检查真实空间遮挡与碰撞；使用隔离场景/存档。
- [ ] verifier拒绝缺组、少循环、改输入/纹理/输出、错误时钟或接触超界；输出回执后目视代表图和连续动作，失败回具体工作包修复，仅重验受影响依赖并最终核全包闭包。
- [x] 执行人物完整unittest、check.py及Godot消费者synthetic/actual/native检查，明确区分自动与人类验收；保存源/输出/屏幕尺寸与连续记录。

**命令入口（完整资源冻结后执行；snapshot/verify-inputs仅为输入闭包，不是完整回执）：**

```sh
python3 tools/characters/build.py build art/characters/recipes/adult-top03-full-hair-hat/r001.json --output art/characters/builds/adult-top03-full-hair-hat-r001
python3 tools/characters/build.py verify art/characters/builds/adult-top03-full-hair-hat-r001
python3 tools/characters/review.py all-actions-construction --dry-run
python3 -m unittest discover -s tools/characters/tests
python3 tools/characters/check.py
python3 tools/characters/all_actions_capture.py snapshot --suite art/characters/reviews/all-actions-construction/review.json --evidence /private/tmp/coastal-all-actions-native-r001 --observer poses
/Applications/Godot.app/Contents/MacOS/Godot --path godot2d --log-file /private/tmp/coastal-all-actions-native-r001.log --script res://tests/characters/capture_registered_candidate.gd -- --evidence=/private/tmp/coastal-all-actions-native-r001 --construction-suite=<全包review.json绝对路径>
python3 tools/characters/all_actions_capture.py verify-inputs --evidence /private/tmp/coastal-all-actions-native-r001
```

全包suite/schema与输入冻结工具已实现；真实24格84姿态已组为一个strict包并verify。原生验收仍进行，不能宣称全包视觉验收通过。六observer原始证据已完成并独立聚合通过，另8工具点几何侧车通过；355人物测试及全库check通过。严格足底支撑／滑步仍未通过，Progress Q2待选，不能用原始覆盖或栅格0px代替该门槛。输出与evidence路径被占用时用新revision，不覆盖。

## 工作包8：统一交付、用户视觉评审与进度收尾

- [x] 给用户一个入口切换六动作/四方向，头部固定hair_hat且无状态切换按钮，默认打开完整候选；提供连续总览和重点接触/遮挡对照，不要求用户逐个寻找小样。
- [x] 摘要列出24/24格、实际pose数、所有技术检查、来源/新生图数量、历史恢复、未验证平台/OS/导出；任一未完成格不能写全包完成。
- [x] 技术完成、用户视觉待评审分别记录，用户反馈仅重开受影响范围，不拿旧西锄认可替代全动作认可。
- [x] 更新README、coverage、PROJECT_STATE/HANDOFF与Paseo，标明完整固定配方动作包状态；生产发布仍关闭，不自动扩其他体型或玩法。

## Progress执行方式与预计工作量

本次“全动作统一交付：设计执行方案”运行仅跟踪方案设计，设计交付即关闭。开始实施时新建“成年固定配方全动作统一交付”，将上面8工作包作为Ticket01–08按依赖登记；每包Build/Review/Fixes（有修复时）/Verify，done必须满足真实出口。西walk完成只更新工作包4活动，不finish全轮。

主代理负责共同合同、集成、状态与最终验收；来源整理/不同动作适配确有独立文件责任时才委派，最多两个子代理，Godot共享脚本串行修改。需要独立复查时限定来源身份、证据闭包或接触风险，不重复整库调查。

工作量随头部范围收敛而减少：只制作与验收hair_hat，取消其他三状态的新增适配、构建及换装功能。共同合同、完整头发/帽层来源和历史保全仍需完成，不能将原估时简单除以四。此前19–39小时估计作废；工作包1完成后依据实际缺失视图重新估计，额外GPT补图/服务等待与用户评审单列，不以时间到期替代24格目标。

## 本方案自查与当前验证

设计的范围、历史、统一合同、动作资源、时间轴/接触、原生和交付分别落在工作包1–8。不存在“西walk完成就停止”的任务出口，不扩大到生产发布。实施需先读取对应设计并遵守源代码测试门禁；当前仅新增文档，沿用同一会话源码未变的114测试和strict5/build4/legacy9检查，另做文档链接、矩阵计数和diff核验，不以旧结果认证新实现。

## 2026-10-30 最终执行边界

24格84姿态已统一strict构建，所有既定原始观察覆盖缺项0，完整证据与8643个原始PNG路径已无损持久化，见 `art/characters/evidence/all-actions-v1/native-r001/README.md`。正式足底支撑／腾空／滑步门槛仍为rework_required；当前只完成统一评审包，未结项。Paseo Q2由用户选择A继续严格支撑，或B接当前四关键帧评审版、严格支撑后续。Work around设置下未实施任何选项，保留原门槛和失败证据，不擅自打勾或改游戏速度迎合验收。

## 2026-10-30 Q2=B范围决定与结项

用户明确选择B：本轮按当前四关键帧像素步态接收24格84姿态完整统一评审包。严格足底支撑／腾空／滑步从本轮完成门槛转为后续，原规范与失败/未验证证据保留，不冒称物理通过。以上旧checkbox中涉及严格支撑的未勾项按本决定标记为延期；统一入口、完整原生预览、全部既定raw覆盖、355测试、check、无损证据及范围记录均完成。此决定仅适用本轮固定hair_hat评审交付，生产发布仍关闭。
