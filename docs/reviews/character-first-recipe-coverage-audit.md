# 首个候选人物配方：覆盖审计与后续小样

日期：2026-10-28。对应计划：[固定候选配方覆盖审计](../superpowers/plans/2026-10-28-character-next-step-audit.md)。

## 结论与范围

首个后续任务建议为：**让统一严格构建合同准确表达现有西向锄地＋匹配待机的四种头部状态，并通过统一评审入口验证。** 这一小样已有实际可用图层；按确切旧构建规则，r002衣装重建加现有注册头层可复现20/20张旧输出，逐RGBA完全一致。它主要缺严格合同表达与消费者接入，不应先重画或批量扩四向。

本次候选为adult-standard-v1 / review-motion-v1、top03条纹上衣、original-pants与original-shoes，评估栗色短发和藏蓝缎带草帽。候选用于工程审计，尚不是正式生产外观或发布批准。body:null在现行合同中引用同pose参考，不表示具备可换任意衣型的隐藏裸身体。

审计覆盖idle、walk、run、hoe、water、harvest各四向，共24个动作方向单元；每单元核bare/hair/hat/hair_hat，共96个能力单元。动作pose数、图像数、转换数与能力单元数分别统计。现行模板每向idle一pose、其余动作四pose只是当前数据，不升级为所有未来动作都必须四帧。

本轮只新增审计资料并更新计划/交接，未制作或变更资源、合同、加载器、冻结基线及认可。开始时已有的AGENTS、README、状态及精简分析修改保留。

## 候选衣装的24格真实登记覆盖

“完整登记”仅指候选三衣装槽在该动作方向有现行接口；“局部”是可追溯的部分槽线索；“未登记”表示当前引用未登记同配方适配，**不是断言没有可复用源图，更不等于必须重新生图**。

| 动作 | south | west | east | north |
|---|---|---|---|---|
| idle | 未登记 | 完整登记 | 未登记 | 局部：同名旧鞋线索 |
| walk | 未登记 | 局部：top03 | 未登记 | 未登记 |
| run | 未登记 | 未登记 | 未登记 | 未登记 |
| hoe | 未登记 | 完整登记 | 未登记 | 未登记 |
| water | 未登记 | 未登记 | 未登记 | 未登记 |
| harvest | 未登记 | 未登记 | 未登记 | 局部：同名旧鞋线索 |

合计完整登记2、局部3、未登记19。严格候选配方[r002](../../art/characters/recipes/wardrobe-hoe-west/r002.json)仅有hoe-west、idle-west两个clip，共4+1 pose、209项file/SHA引用（含重复），校验全部匹配。check.py当前计严格配方1、库内严格build 0；临时构建示例不能计为正式角色发布。

| 槽 | 实际适配范围 | 不能扩大解释的边界 |
|---|---|---|
| top03 | 西走四pose＋idle；西锄四pose＋idle | 西走父配方为pants02与original-brown-shoes-v1，不是本候选原裤原鞋 |
| original-pants | 西锄四pose＋idle | legacy-scoped-baseline-label，不能把其他完整参考的裤子凭外观或名称认作同一已验款 |
| original-shoes | 西锄与北收各四pose＋idle | 北收属于原蓝长袖＋pants02配方；复用到本候选仍需身份、注册与兼容证据 |

top03静态四向完整源确实存在（2048×768，四列south/west/east/north）；它有灰短裤和赤脚的参考身体。静态source及standing_0候选可供后续登记核查，不证明original-pants/original-shoes在各向idle已兼容，也不证明运动投影可用。完整路径、SHA与逐格接口见伴随审计数据。

## 头部四状态与父衣装绑定

| 发帽样例 | 父衣装 | 对本候选的证据价值 |
|---|---|---|
| 西锄＋西待机 | top03 / original-pants / original-shoes | 唯一精确同候选衣装的头部小链，5pose×4state=20显示状态 |
| 东跑＋东待机 | top04 / original-olive-pants-v1 / shoes04 | 头部源/投影线索；不是本候选整套能力 |
| 南浇＋南待机 | original-blue-long-sleeve / pants02 / shoes04 | 其他父衣装的有限抽样，尚无新用户认可记录 |
| 北收＋北待机 | original-blue-long-sleeve / pants02 / original-shoes | 其他父衣装的有限抽样，尚无新用户认可记录 |

因此96个候选能力单元中，现行旧样例可定位的精确同衣装单元只有西锄和西待机的8个；它们涉及20个pose/state显示结果。这不是新严格合同已支持8格，也不是8格已获用户逐状态真人操作认可。其余88格需要分别核源、投影、候选衣装与接口，不能将已有静态头部16状态或其他三组样例拼接补齐。

西锄第三帧帽下发v3是紧凑前发和同pose原完整短发后片的二值来源选择，有两个source_views及各自ownership；不能只登记一个source。保留原脸、手、身体与已登记整帧位置，所有runtime部件offset仍为零、scale为一。

## 真实合成语义与20状态可行性核对

先以r002现有render重建bare，再读当前头层；不写PNG、不创建新配方/build，只比较内存像素。两种探针均保留结果：

1. 把所有头部层直接套标准alpha-over，只得到7/20逐RGBA相等；其余13张不同。这证明改变操作不等价，不能据此判源图缺失或旧资源错误。
2. 定点查Git基线379a9bc的真实builder后：hair-only以纹理alpha>0的二值支撑直接替换RGBA；hat/hair_hat先按far_hat→body→可选帽下发→near_hat做alpha合成，再仅在真实部件二值支撑内贴回原body。按这套规则，20/20逐RGBA完全相同，透明RGB也纳入比较。

标准alpha-over探针首动作hair不同122260像素，idle hair不同31877像素，均涉及可见alpha；不能用透明RGB解释hair-only差异。帽子组合的支撑外原RGBA保全则是另一条明确语义。两类差异不能合并归因。

旧共享compositor：`art/design/character-motion/adult-standard-v1/headwear-sampling-v1/revisions/run-east-hat-approved-v5/build_approved.py`，Git379a9bc，SHA `42e4b0542cdba5834add6705084fef7451c10fbe8b1dc9bcae1e9b531e203950`。旧西锄builder的hair-only二值paste与后续v2/v3保留该状态的路径，详见头部核查资料。

探针仅证明当前已注册图层可重现这条小链；不证明从GPT原图重新提取的完整流程、严格合同支持、原生播放、新视觉认可或生产发布。没有新图，因此本轮不产生新的源图/原生显示尺寸视觉验收。

## 严格合同与Godot接入的确切缺口

| 缺口 | 当前实现依据 | 对下一小样的约束 |
|---|---|---|
| 四状态表示 | build_contract.py能力键为action/direction并拒绝重复；build.py输出键为action/direction/pose | 优先四份固定配方，不为此建设运行时自由衣柜；不可重复clip覆盖输出 |
| 混合合成操作 | build.py每frame仅选alpha-over或ownership-replace；后者body必须第一层且使用二值coverage | 不能把衣装二值替换与发帽alpha合成全塞进一种操作；需显式有界的合成步骤及支撑区保全 |
| 源坐标与目标坐标 | r002四动作先在1024×1536源画布组合，再整体平移到1536×1792；头层已注册到目标画布 | 不得对头层重复平移；需要经过验证的衣装结果在目标画布组合，或先做可追溯整帧登记 |
| 多来源帽下发 | 现行layer只接单source+source_bundle；key2帽下发有两个source_views | 必须逐源绑定ownership及先后/选择规则；不能随便挑一个源或伪造source |
| mask与操作区别 | 所有非body layer强制三mask；render实际只在ownership-replace使用coverage | 不能为凑字段虚造mask，也不能把诊断visible/occluded mask乘回源alpha；已有mask绑定不等于渲染器执行其语义 |
| 新严格输出的评审 | 现行headwear loader固定四旧sample，并验证parent/SHA/四pose/四state | 新manifest不会自动进入suite；新增能力应在同一评审入口明确消费新合同并做拒绝与实际加载回归 |

完整穿衣参考与shared_same_pose_foreground_and_contour并非裸身体。农事motion-set明确body_views_available:false；缺口区域不能靠mask从没有的像素中恢复。后续隐藏区只按实际衣型/动作会露出的表面定向补，不先造无用全裸库。

## 动作衔接、接触与认可范围

| 项目 | 现有证据 | 尚需完成 |
|---|---|---|
| pose/时长/整帧登记 | 西锄4pose为180/220/140/260ms；idle 200ms；根点、源框、平移与显示比例均有记录 | 新严格小样必须逐项保持，不能因整理改节拍/锚点 |
| 头部动作中切换 | 迁移fixture有动作/状态切换与返回idle报告 | 属于隔离评审功能；生产换装按规范在idle原子替换，不从fixture推导生产任意时刻换装 |
| 入动作/出动作 | 已有匹配idle与旧试玩路径 | 同候选全动作四向进入/退出、急停/转向和允许取消范围仍未完整证明 |
| 足/握持/工具落点 | pose/相位与完整穿衣参考可观察 | 缺严格轨迹、点位与目标合同；未达到实际屏幕误差目标≤1像素的统一验收 |
| 隐藏身体/新衣型 | 只有现有有限衣装的表面及部分保留隐藏衣片 | 新衣型或组合需要的裸身体/衣片隐藏区尚未证明 |
| 视觉认可 | wardrobe五抽样、东跑v5及西锄key2 v3有分范围独立记录 | 南浇/北收未记录新认可；旧认可不扩至新配方或全动作/全状态操作 |

原生迁移input-contract绑定的4369个文件本轮逐SHA全部匹配。receipt范围为129张PNG、65个面板各一循环、16次世界报告；旧证据未变，不表示新小样已经原生通过。西锄、东跑及衣装三类acceptance涉及的旧Git原件与迁移subject共10项，逐SHA全部匹配。创建时sample的false字段保留为历史，不覆盖独立认可的限定范围。

## 首个小样实施包与停止条件

**建议任务名：统一合同支持西锄既有衣装构建与四头部状态组合。** 范围为hoe-west四pose＋idle-west一pose，不包含其他方向、其他动作、扩款或生产切换。

1. 先对本报告发现的合同限制建立失败反例：重复能力/覆盖输出、错pose或时长、重复整帧位移、缺少或篡改子构建依赖、缺多源ownership、诊断mask误作coverage、支撑外RGBA改变。将已有20张结果作为真实集成参照，不写只镜像实现的测试。
2. 在统一build_contract/build中选择最小表达：四份固定状态配方；显式已验证衣装合成结果与目标坐标阶段；声明二值RGBA替换、alpha合成及支撑区保全；明确多源注册/二值选择。设计需先说明版本与消费者约束，不能临时写批次构建器、复制成品为“裸身体”或放宽基线。
3. 构建四份新review-only输出并逐一verify，绑定全部实际源/注册/mask/工具依赖。20/20逐RGBA、pose顺序、时长、源框/根点/比例保持；修改实际依赖应使相关构建失效，新增无关源不应影响。
4. 明确接入现有隔离评审入口，增加对新manifest的实际资源加载及拒绝反例。不得直接替换旧catalog后假定格式兼容；旧样例与认可保持可追溯。
5. 新原生采集覆盖实际尺寸、明暗停帧、连续动作、四头状态、动作中评审切换及返回匹配idle；绑定实际纹理/pose/mask/时序/配置hash。若改变美术/显示结果，则单独提交受影响视觉范围，不以像素测试代替用户认可。没有OS输入、跨平台或导出测试就明确不声明。

**完成条件：** 统一入口可构建/复核四固定状态，缺依赖明确拒绝；20输出技术等价，现有评审可实际加载连续播放，必要原生证据完整；冻结基线与生产发布未被自动放开。

**停止条件：** 发现实际源/注册/多来源选择不足时先明确报到pose/part/source，不借旧脸手、任意挪缩或擦身体填补；同一方法两次失败后先分析证据。达到小样完成条件即交付，不自动开始四向扩展。

## 本轮验证、交付与分工

- Task 1导航依赖已确认完成：PROJECT_STATE.md与HANDOFF.md的“人物目录README与Agent导航完善”节记录四份README的47个本地链接、五种suite dry-run、75测试与check通过；上轮Paseo“人物目录README与Agent阅读导航”T01/T02为Done。本轮读取新导航并核查实际调用代码，沿用上述导航链接/启动验证，不声称本轮重跑47链接或五suite。
- 本轮Paseo任务为“固定候选人物配方覆盖审计”，四步依次覆盖范围、并行核查、汇总实施包、独立复查与交接；审计报告与JSON作为D1/D2登记。子代理在沙箱内连接失败一次后由主代理统一在沙箱外同步，审计未受阻。
- 75项人物Python测试通过，check.py通过（strict_recipes=1、strict_builds=0、frozen_legacy_recipes=9）。
- 4369项迁移原生输入SHA与10项认可原件/subject SHA通过；20张现有层语义重建逐RGBA一致。
- 本轮没有新Godot GPU采集、OS输入、连续录像、严格接触或导出测试；未对未登记范围完成全库像素可复用性证明。
- 主代理负责范围、严格合同/消费者、探针、证据复核与集成；两位gpt-6.1-sol/high子代理分别核衣装与头部（跨清单引用与历史来源）；独立gpt-6-astra/high复查审计完整性和关键推断。模型按跨源一致性风险选择，不宣称用量节省。
- 数据清单见[逐格审计JSON](character-first-recipe-coverage-audit.json)；含24行衣装、24行头部四状态、关键输入SHA、两次探针和认可核查。各JSON为审计附件，不是第二套运行时权威清单；原coverage不改。
