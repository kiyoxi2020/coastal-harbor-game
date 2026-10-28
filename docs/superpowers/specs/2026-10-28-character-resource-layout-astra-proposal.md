# 人物运动与衣物资源目录设计（Astra，已确认精简留存版）

日期：2026-10-28。设计基线：Git `379a9bc` 及当前工作区。设计者：`gpt-6-astra`，职责为资源组织与扩展设计；主代理独立核对引用、运行入口和冻结证据约束。选择 Astra 是因为本题同时涉及部件复用、动作合同、生产边界和证据迁移。

**用户已确认方案B，并将留存策略收缩为“最终资源＋必要制作输入，历史主要交给Git”。当前正在按此实施；不建立庞大archive副本。** 下文的新目录和字段是建议，不能理解为现有工具已经实现。唯一人体制作与验收规范仍是 [character-art-pipeline.md](../../design/character-art-pipeline.md)；若方案获准，应定点更新该规范第 8 节的目录约定，不能让本草案成为第二份制作合同。

## 1. 目标与本轮完成条件

目标是让维护者能够直接回答：某个体型有哪些动作；某件衣服是哪款、适配了哪些姿态；某张完整帧来自哪些源图；试玩当前使用哪个构建；用户认可究竟绑定哪个结果。增加动作、款式和体型时沿现有统一合同追加资源，不再新建一套 `*-proof-vN` 工具与目录。

本轮完成条件是形成可供用户选择的目录方案、真实旧路径映射、扩展示例和迁移验收边界。验证采用仓库定点核对与设计一致性检查；本轮不运行游戏、不新增原生证据，也不宣称迁移已通过。

## 2. 现状与混乱根因

现有目录记录了真实制作过程，但目录名主要表示“哪次试作”，没有稳定表达资源的归属。

| 已核对的现状 | 维护后果 |
|---|---|
| `character-motion/adult-standard-v1/` 同时有 walk/run 单侧 proof、四向候选、农事、衣物抽样、发帽抽样 | 同一个动作或设计跨多个试验目录，不能仅看目录得知当前选择 |
| `headwear-sampling-v1/catalog.json` 的东跑已指向 `run-east-hat-approved-v5`，西锄已指向 `hoe-west-ear-v3` | “最新目录”“最大的版本号”和实际活动输入不是同一概念 |
| `wardrobe-sampling-v1` 的五组分别组织 source、parts、masks、baked、脚本和证据 | 同款条纹衫的 walk/hoe 适配容易被看成两款衣服；复用边界隐含在脚本中 |
| 农事 `catalog-color-v2.json` 索引 3 动作 × 4 方向 × A/B，共 24 组完整穿衣动画 | A/B 是该批配方标签，不应变成动作 ID 或新的身体；完整帧也不是已拆好的身体模板 |
| 静态六类各 10 候选在 `character-candidates-v2`；没有名为 `character-wardrobe` 的现行目录 | 找衣物时需同时知道静态批次与动态批次；60 候选不等于 60 项运动成品 |
| `.py`、`.gd`、独立 `project.godot`、`.command` 与美术和证据混放；同时存在 `godot2d/dev` 正在使用的试玩代码 | 复制一轮资源可能同时复制一套执行逻辑；入口与源图责任混淆 |
| 一些 README 保留早期“待认可”文字，最新有效状态由独立认可记录和状态文档补充 | 阅读顺序影响理解；重命名文件不能解决证据与状态的区分 |

根因是把**制作批次、设计身份、姿态适配、派生构建与评审记录**放在同一层。解决办法不是简单缩短文件名，而是让它们各有归属，并通过少量显式清单连接。

主代理的定点引用核对还显示：当前 character-motion 约 7,516 个文件、3,200.7 MiB，13 个按试验批次命名的一级子目录；至少 82 个 `.py/.command` 含旧路径、`parents[N]` 或相对层级假设。因此不能将“整理目录”实现为裸 `mv`，也不应为每次评审复制整套库。

## 3. 三种组织方案

| 方案 | 做法 | 优点 | 代价与限制 |
|---|---|---|---|
| A：保留现有批次目录，加总索引 | 继续在 `character-motion` 等目录增量制作，补总 README/catalog | 路径改动最少，适合短期止乱 | 同款衣物和工具仍分散，后续批次继续积累重复；不能根治源、构建和证据混放 |
| **B：按资源身份组织，评审批次另建索引（推荐）** | 统一 `art/characters`；体型、动作、部件款式、配方有稳定位置；构建和证据独立 | 新动作与新款有明确落点，源图可复用，有限范围迁移现有工具即可 | 需要一次路径迁移和证据桥接；目录无法替代缺失美术与适配工作 |
| C：每个动作自带整套身体/衣服/头发/工具 | `actions/hoe/...` 内放齐所有资源 | 打开单动作即可看到完整交付，局部复制方便 | 同一款衣服跨动作重复，修同一源需多处同步；体型与动作乘积放大，不适合本项目 |

推荐 B。保留现有清单和脚本中可用的内容，用统一根路径、显式引用和局部参数化迁移。**不为目录整理建设数据库、内容寻址存储服务、完整编辑器或全新通用播放器。** 现有动作/姿态/衣物字段能直接承载的，不另造语义等价字段。

## 4. 精确目标目录树（全部为拟建）

下列 `<…>` 是具体资源 ID 或修订名，不是必须预先创建的空目录。目录只随实际内容建立。`rNNN` 表示新规范下的不可变内容修订；现有带 `v1` 的稳定 ID 不因目录整理被强制改名。

```text
art/characters/
├── README.md                         # 当前导航、制作入口、明确的未完成范围
├── catalog.json                      # 资源定位与可浏览状态；不是生产发布清单
├── definitions/
│   ├── actions.json                  # idle/walk/run/hoe/water/harvest 等动作语义
│   └── slots.json                    # hair/top/pants/shoes/hat/tool 等槽位定义
├── sources/
│   └── <source-id>/                   # 一次生成/补稿输入输出；跨部件只存一份
│       ├── source.json               # 来源、尺寸、模型、参数、多个引用输入及 SHA
│       ├── prompt.md
│       ├── originals/                # 完整 GPT 原图，不覆盖、不先缩成逻辑像素
│       ├── references.json           # 引用其他源 ID/确切版本，避免复制引用图
│       └── attempts/                 # 同任务失败稿、原因；独立生成也可独立 source-id
├── templates/
│   └── <template-id>/                # 例如 adult-standard-v1；其他体型同一合同
│       ├── template.json             # 身份、已选修订与候选说明
│       ├── revisions/<revision>/
│       │   ├── registration.json     # 母版源引用、画布、根点、关节、显示比例
│       │   ├── body-views/           # 完整身体部件；仅包含实际已制作的隐藏区域
│       │   └── views.json
│       └── motions/<motion-set-id>/
│           ├── motion-set.json       # 精确固定各动作修订；不靠目录扫描取最新版
│           └── actions/<action-id>/<revision>/
│               ├── action.json       # 四向范围、时间轴、事件、进入退出、移动策略
│               └── <direction>/     # south/west/east/north
│                   ├── poses.json    # 有序稳定 pose_id、身体视图、锚点、默认层序
│                   ├── body-views/   # 实际新增的同姿态身体视图；能共享则引用
│                   └── registration.json
├── parts/
│   └── <design-id>/                  # 一款衣服/裤/鞋/发/帽/工具；跨动作身份不变
│       ├── design.json               # 类别、slots、独立款式身份、源引用
│       ├── variants/<variant-id>/
│       │   └── variant.json          # 配色/材质或组合形态；不能冒充独立款式
│       └── adaptations/<template-id>/<motion-set-id>/<revision>/
│           ├── adaptation.json       # 支持的确切姿态/版本、变体、限制
│           ├── views.json            # variant/part/view → 图集区或完整部件图、sources[]
│           ├── views/                # 完整衣身、袖、裤腿、鞋、发帽前后层等
│           ├── pose-map.json         # pose → view；相同投影允许多对一
│           ├── source-ownership/     # 某张源、某姿态的提取归属及掩码
│           ├── coverage/             # 衣物覆盖哪个身体/部件表面及适用姿态
│           └── occlusion/            # 当前前后关系的必要修订；非永久裁源
├── recipes/
│   └── <recipe-id>/<revision>.json    # 体型/动作集/部件适配精确版本、必需能力
├── builds/
│   └── <build-id>/                    # 一次不可变离线输出，可重建但不覆盖旧构建
│       ├── manifest.json             # 输入依赖、工具版本、artifact_digest、范围
│       └── recipes/<recipe-id>/
│           ├── frames/               # 完整 RGBA 烘焙帧/图集，不反过来当通用部件源
│           └── animation.json        # 动作方向索引、时长、根点、事件
├── reviews/
│   └── <suite-id>/
│       ├── review.json               # 指向构建和有限评审范围；可选诊断项显式标记
│       └── review.html               # 派生浏览页；不自带另一套加载规则
├── evidence/
│   └── <review-id>/
│       ├── subject.json              # 构建、纹理、配置、工具/场景及范围的绑定
│       ├── checks/                   # 结构/逻辑/像素/迁移检查
│       ├── native/                   # 原生报告、截图、录像、采集前后回执
│       ├── feedback/                 # 用户原话/截图与问题定位
│       └── acceptance.json           # 独立认可、日期、范围；不存在就不能推定认可
├── releases/
│   └── <release-id>/manifest.json     # 待生产门禁通过才创建的单次正式发布记录
└── migrations/
    └── 2026-10-resource-layout/
        ├── inventory.json            # 实际迁移闭包与旧文件 SHA
        ├── path-map.json             # 旧→新路径，原 ID/新位置，迁移结果 SHA
        └── verification.json         # 路径/字节/输出/运行检查；不冒充原生或用户认可

tools/characters/                      # 现行 Python 制作、校验、烘焙与评审入口代码
├── README.md
├── <现有工具的职责文件名>.py           # 优先移动与参数化，不强制合成一个大脚本
└── tests/                             # 相关 Python 失败反例与回归

godot2d/dev/characters/                 # 现行隔离试玩 .tscn/.gd/.uid、Godot 原生采集脚本
godot2d/tests/characters/               # 现行 Godot 逻辑/实际资源测试
godot2d/assets/characters/
├── active-release.json                # 仅正式切换时引入，指向唯一 release_id
└── releases/<release-id>/              # 仅当前正式发布需要的烘焙资源与运行清单

art/archive/characters/<snapshot-id>/
├── archive.json                       # 原提交、原路径、SHA、复现方式、只读范围
└── （不建立整库副本）                  # 旧布局由Git379a9bc恢复，未入Git资料临时保全
```

`godot2d/assets/characters` 目前已有静态/试作资源；上树描述的是最终边界，不表示现有内容已是正式新版发布。Godot 的 `.uid` 随对应脚本/场景迁移；导入资源按实际引用处理，不能把 `.godot/` 缓存当源资产搬运。对旧冻结 inputs 已明确绑定的特殊元数据文件，先保留原字节与原因，不能按后缀或 ignore 规则直接清除；新清单再单独纠正不必要依赖。

## 5. 各维度如何归属与扩展

### 体型、动作、方向与姿态

`template_id` 表示独立比例与接口的体型，`motion_set_id` 表示该体型采用的动作集合，`action_id` 表示动作语义，`pose_id` 表示稳定姿态身份。方向是动作下的内容维度；帧序和时长在时间轴中，不能让文件字母顺序决定动作。相同 `pose_id` 的内容修订必须被精确版本约束，不在原 ID 下悄悄覆盖旧姿态。

例如给 adult-standard-v1 增加 `wave`：在同一动作定义与模板动作集登记，补真实挥手姿态、所需锚点和袖臂视图；已有衣身/裤鞋仅在投影一致时引用既有 view。增加 5 帧动作不应要求复制四帧小样工具。新增玩法语义需要实际处理器时另改玩法，目录可扩展不等于零代码支持任意行为。

给儿童增加体型：新增一个 template_id，保留儿童完整 GPT 母版和独立比例/锚点，沿同一 motions/parts/recipes 合同适配。不能复制成人坐标后缩小；body09 仍未解决的比例问题保持未冻结，不能因搬入 templates 被标记通过。

### 款式、部件视图和帽下发

`design_id` 表示独立款式。现有 `top03` 等 ID 先保留，通过 `design.json` 写清“海军条纹衫”等名称；需要改 ID 时单列显式映射，而非本次顺手重命名。`original-pants`、A/B 等临时标签先作为有范围的旧配方引用登记，在确认来源与是否为同一设计前，不自动合并成全局同名部件。

同款在 walk/hoe 的图、袖子前后层、各方向、体型适配、换色都不是新增款式。款式数按不同 design_id 的真实设计统计；视图数、姿态数、配方数、烘焙帧数分别统计。为了修帽下头发新出的 source，也不自动增加发型款数。

栗色短发的正常形态与草帽下收发形态属于同一设计的显式 variant；帽下变体声明依赖确切帽设计/适配版本及适用姿态。西锄 key_2 的后发修复落在该发型的**西锄姿态适配修订**，不会把全部动作的帽下发都升级为 v3。东跑 v5 的帽和帽下发保留自己的实际适配与认可范围，不能因同用草帽名字就合并像素或声明互通。

一个 view 允许登记多个源及其选择规则，不能只设计一个 `source` 字段：当前西锄 v3 的发片就是两个真实源与两份 ownership mask 的精确选择。记录每个 source SHA、作用区域/ownership、整帧注册与合成规则，保留原 RGBA；这与按多个动作复制同一 view 是两回事。相同投影的 view 可以被多个 action/direction/pose 显式引用，目录结构不能强制每动作每方向复制 PNG。

例如新增长裙：新增其 design_id、前后摆等真实视图、coverage 与姿态层序；槽位仍可为 pants，名称不限制剪裁。只有新增围巾等新类别才扩 slots 定义，检查锚点/冲突与层序循环；不要为每一条裙子新建渲染器。

### 配方、构建、评审与发布

配方只记录实际组合，不把 `A`、`B` 写进动作名。头部四状态可表示为四个具体配方，或同一配方明确列举四组 slot assignments；迁移优先保留当前 sample 格式，**不在本次强制重构为任意组合衣柜**。16 状态指四方向 × bare/hair/hat/hair_hat；当前有限动作抽样依然只证明其实际覆盖。

一个 build 固定输入后生成完整动画；reviews 只选构建并声明这次查看哪些样例。review 的活动选择不是正式 active_release。evidence 记录实际测试与用户反馈，目录位置不产生“已通过”含义。发布清单必须逐角色覆盖 required_actions 与实际配方，候选/诊断项不能靠 catalog 可见就进入发布。

新增款或动作时，缺失的 view、pose、隐藏身体、coverage 或兼容组合必须精确报出 `recipe/action/direction/pose/part` 并拒绝相应构建/发布，不用旧身体或 standing_0 填补。静态四向完成、完整帧 A/B 完成、五组抽样完成是不同的能力范围。

## 6. 源图、派生图和去重边界

| 内容 | 保存与去重规则 |
|---|---|
| GPT 完整原图、prompt、生成参数、参考与失败稿 | 长期保留，不覆盖；同一实际文件可由多个部件引用一个 source-id，保留所有原始来源别名与路径映射 |
| 手工登记/批准的 source ownership、覆盖轮廓、层序、锚点、姿态映射 | 属于制作输入，长期保存并固定 revision；不能因看起来像中间文件而删除 |
| 提取后的完整衣身/袖/发帽视图 | 保留有用部件库；具备完整输入与确定性工具时可重建，但迁移先逐 SHA/像素验证，不能提前清理 |
| 原生采集 PNG、视频、report、receipt、用户反馈及认可 | 是观测/认可证据，不可由重新运行工具“再生为原证据”；已绑定内容永不覆盖 |
| contact sheet、网页缩略图、未认可的临时烘焙和缓存 | 可在明确依赖与生成命令存在时重建；被证据引用的版本仍需留档 |
| 已认可的烘焙帧与已发布输出 | 保留精确版本以便核验；新构建写新 build-id，不覆盖旧文件 |

不全库按 PNG 哈希盲目合并。相同字节可以共用纹理存储，但源身份、view/pose 引用、时长、覆盖目标和认可范围各自保留；不同来源碰巧同像素也不能丢失 provenance。初期普通文件与 JSON 引用足够，暂不引入 symlink/hardlink 或全局 hash blob 库，以免改变证据防篡改与路径规则。

用户已确认精简留存：旧布局主要保存在Git `379a9bc`，迁移清单固定原路径、原SHA和恢复方式。工作区不额外复制整库archive树；普通失败稿、中间版本、旧工具与重复过程图在现行依赖迁出且Git可恢复后移出。最终采用的原图、prompt、手工mask/注册以及仍被最终稿使用的失败参考必须保留。不能恢复到Git的历史资料先暂存`/private/tmp/coastal-character-layout-untracked-hold`并记录，不能假称已经入Git或静默删除。

认可保留简短的确切版本记录与少量代表图；原生完整过程可留临时采集目录，工作区保留轻量摘要与回执。历史报告原件可从Git原字节恢复，重新执行不冒充原记录。

严格区分三类 mask：source-ownership 属于具体源稿的提取，coverage 属于版型/目标体型/姿态的覆盖，occlusion 属于当前姿态的前后关系。不得把站姿归属 mask 扩用到抬手帧，不把遮挡后的缺口烘入通用衣身，也不靠擦身体修帽发接口。

画布、源密度、根点、合法锚点位移与显示比例全部随注册数据迁移。本次不重新裁切或缩放。当前 walk/run 的 512×768、不同农事的大画布和源密度差异均应显式保存，不能为了目录整齐统一到同一图片尺寸。

## 7. 工具、原生测试与试玩入口

现行制作代码收敛到 `tools/characters`；现行 Godot 试玩与原生采集放 `godot2d/dev/characters`，相关测试分别归 Python/Godot 测试目录。历史证据依赖的旧工具字节在冻结归档保留，标明只供复现，不继续修补为第二套现行工具。

迁移时先保留现有工具职责和样例 schema，仅把写死的根路径/输入 catalog 改为明确参数。成熟逻辑可共享，但不把一次目录整理升级成合成器全面改写；当前完整帧、部件适配和不同证据合同需保留语义差异。

建议未来提供一个明确的评审启动入口（具体参数接口在实施时定点设计），读取 `reviews/<suite-id>/review.json`，进入现有隔离试玩场景。旧 `.command` 可以在过渡期保留为提示或指向新入口的薄跳转，不能内藏旧构建规则；迁移通过后现行 README 只推荐一个入口。评审页可按动作/方向/款式筛选，但只能展示清单声明范围。

美术目录只保留资料、manifest 和派生浏览页；不再在新的美术试作目录建立独立 Godot 工程。正式运行与导出不能隐式扫描 reviews、archive 或源库。现有开发场景确需从仓库外于 `res://` 的美术路径读取时，使用显式仓库根定位并测试启动目录变化，不能依赖终端当前目录巧合。

所有 Godot 验证传 `--log-file /private/tmp/coastal-*.log`；任何测试存档只写 `/private/tmp/coastal-*`。结构检查、真实 GPU 采集、系统 OS 输入/焦点、跨平台、导出测试仍分别标记，不因入口合并合并结论。

## 8. 典型旧→新映射

以下旧路径均相对仓库根；`M/` 仅是本表对 `art/design/character-motion/adult-standard-v1/` 的缩写，`N/` 是拟建 `art/characters/`。映射表示**内容归属**；冻结证据先整体封存，不能直接把其内部路径批量替换后伪装为原文件。

| 真实现有内容 | 拟建归属 | 必须保留的限制 |
|---|---|---|
| `art/design/character-bodies/adult-standard-v1/` 与 `selection.json` 的 directional-brows-v3 | `N/sources/<母版生成ID>/`；`N/templates/adult-standard-v1/revisions/<修订>/` | 原 source 与完整眉毛修订来源保留；选中外观不等于完整隐藏身体 |
| `art/design/character-candidates-v2/{body,hair,top,pants,shoes,hat}/` | 身体归 templates；发衣裤鞋帽归 parts；完整生成源归 sources；六类 gallery 归 reviews/static-candidates | body01 与现有成年母版用引用去重；60 候选及 standing_0 范围不升级为运动适配 |
| `M/locomotion-v1`、`run-west-proof-v1`、`run-four-directions-v1` | 对应 idle/walk/run 动作修订、parts 的实际适配、builds、reviews/locomotion | 先锁真实当前依赖；单侧历史不覆盖四向当前选择；完整源帧与可分层帧仍分别声明 |
| `M/farming-four-directions-v1/catalog-color-v2.json` 及 hoe/water/harvest 的 24 组 | 模板动作目录登记 action/pose/注册；完整穿衣源归 sources；24 组原装参考输出归 builds 的相应配方；review 为 farming-four-directions | A/B 只属该批配方；96 姿态不等于96新款；未有裸身/独立衣物的组不虚构 body-views |
| `M/farming-transitions-v1` | 已实际存在的过渡内容、时间轴分别归对应动作修订或评审构建 | 只迁移实际支持的衔接，不据目录名认定所有动作都有完整过渡 |
| `M/wardrobe-sampling-v1/{walk-west,run-east,hoe-west,water-south,harvest-north}` | 共用设计归 parts；每个姿态适配登记相应动作；五份有限配方归 recipes；烘焙归 builds，评审归 reviews/wardrobe-samples | 五组分别为条纹衫/牛仔裤/原棕鞋、砖红毛衣/原长裤/搭扣鞋、条纹衫/原裤鞋、原蓝长袖/牛仔裤/搭扣鞋、原蓝长袖/牛仔裤/原棕鞋；不推导任意混搭 |
| `M/headwear-sampling-v1/revisions/run-east-hat-approved-v5` | 草帽与栗色短发的东跑/idle 适配归 parts；源和补稿归 sources；现有四状态配方/构建归 recipes/builds；评审归 reviews/headwear-samples | 静态戴法认可与动态认可分开保留；失败 run2/3 源与后续补稿不能丢失 |
| `M/headwear-sampling-v1/revisions/hoe-west-ear-v3` | 栗色短发帽下变体的西锄 key_2 后发适配新修订；帽/其他姿态继续精确引用实际旧输入；新构建归 builds | v3 使用 v2 与原完整短发等外部来源，目录并非自包含；不能仅搬 v3 文件夹；2026-10-28认可只保留实际绑定范围 |
| `M/headwear-sampling-v1/{water-south,harvest-north}` | 对应发帽设计姿态适配、有限配方及构建；与东跑/西锄共用设计身份 | 不能将东跑 v5 或西锄 v3 当作这两组已经换新或重验 |
| 各目录的 `evidence`、`visual-acceptance-*.json`、反馈、冻结 sample/candidate 与 receipt | 原件固定到Git历史；轻量关联与新迁移验证进入 `N/evidence/<迁移评审ID>/`，新索引记录原认可链接 | 保留原 SHA/时间/输入；路径改动后的新 sample 不直接复制 accepted=true |
| `art/design/character-library-v1`、旧 proof、失败批次、退役脚本 | `art/archive/characters/<snapshot-id>/tree/...`，由现行 README 提供追溯链接 | 女性/老人/儿童比例参考仍是参考，不能当成新版已适配体型 |
| `art/design/player-unified-v4`、`godot2d/assets/player-unified-v4` | **本次目录迁移先维持生产原位置**；未来新版完整生产切换后，旧源和必要运行历史转归 archive | 不因新目录建好提前删除在用旧人物；最终导出不得同时包含旧模型与新版人体库 |

现有 design/variant 名在 catalog 与各 sample 之间有不同层次（例如全局发设计 ID 与 `chestnut-short-hoe-key2-posterior-v3` 局部配方标签）。实施清点先建立“原 ID＋原作用域→设计/变体/适配修订”的明确表，逐项确认实际同源关系，不能仅按相似名称合并。

生产引用不只有主角：主代理已确认 `player_unified_frames.tres` 指向旧纹理，餐厅的两位顾客也引用旧生产人物资源。未来退役的完成条件必须覆盖全部实际角色，不能只更新主角场景后删除旧目录。

## 9. 冻结历史、证据与认可如何迁移

保留两类资料的职责：现行库负责后续制作；冻结历史负责解释过去“当时用了什么、看到了什么、认可了什么”。archive 不是第二运行体系，不允许现行生产 loader 从 archive 回退补资源。新制作选中的真实源若仍在历史中，先作为有 provenance 的现行源接纳并固定 SHA；现行构建不得长期依赖 archive 的可执行脚本或旧运行目录。

实际依赖远多于一个候选文件夹：四组发帽 catalog 链到各自 sample、成百上千项 inputs 和父衣装样例；西锄 v3 的原生记录有 1,458 项显式 sample dependencies，并绑定农事、发帽、衣物及 v3 的四份校验工具 SHA。report 和认可还绑定 catalog/sample、原生报告与 receipt。迁移必须按这条闭包逐项处理；当前旧 receipt 对其原路径与原工具有效，不能拿来认证新路径合同。

迁移采用三层记录：

1. **旧记录不变。** 原 sample、report、receipt、acceptance、旧工具与必要输入按确切字节保存在原Git提交，工作区仅保留最终必要输入与轻量认可关联。不修改原 report 中的创建时待认可字段；后续独立认可记录仍单独存在。
2. **新位置与新输入另记。** path-map 保存旧/新路径、SHA、原 ID、目标归属和迁移类型。需要更新路径的 manifest/sample 会产生新字节和新 digest，必须写为新的迁移修订；禁止“改路径后把旧 SHA 也改成新 SHA”覆盖历史。
3. **等价性与认可分开。** 迁移验证可以证明原纹理字节、RGBA 输出、顺序、时长、根点、显示尺度、配方与工具语义保持；新原生冒烟可以证明新入口确实加载目标。它们只给出“技术上保持原结果”的证据，不替用户制造新的认可。当前状态应显示“原版本已认可；迁移版等价已核对/尚待核对”，并链接原范围。若资源、时序、合成规则或画面改变，原认可不能覆盖变化结果，须重新评审受影响范围。

历史路径解析由归档说明与迁移映射处理。需要精确复现旧工具时，在临时独立 checkout 按原仓库布局恢复，不能修改当前活动库去迎合旧绝对路径；外部绝对路径缺失则明确记录复现限制。冻结 JSON 的数字/内容未变也不足以认定 SHA 未变，JSON 序列化和路径字符串都属于字节。

认可不是目录上的一个总布尔值。selected、registered、static_swap_checked、motion_checked、dynamic_swap_checked、native_checked、user_accepted 等仍按现行规范分开，附确切体型/动作/方向/配方范围。未受影响的依赖闭包和输出相同才可以关联原证据；变更共享姿态、mask、工具或场景则重验实际受影响项，不盲目继承，也不要求所有无关动作重新美术验收。

## 10. 分阶段迁移与完成条件

| 阶段 | 授权后的具体工作 | 出口与停止条件 |
|---|---|---|
| 0 本轮设计 | 用户评审本草案，明确目录、历史策略和边界 | 只产出文档；未确认前不迁移、不更新活动入口 |
| 1 清点与冻结 | 以当前 catalog、selection、真实 loader 与构建脚本为入口，追踪实际依赖；登记普通相对路径、res://、绝对路径、跨目录 imports、原认可/receipt | 无漏失依赖；旧基线可定位恢复；外部源无法恢复时先记录阻塞，不删除旧路径 |
| 2 建立最小新库 | 先迁一条完整有限链，建议西锄 v3（含 v2、原发和衣装来源）；源/适配/配方/构建/证据归属落地；旧基线只读保留 | 新路径解析正确，原源/纹理与输出等价，旧失败反例仍可解释；不把该链结果扩写为其他动作已迁完 |
| 3 推广至现有评审范围 | 东跑 v5、南浇/北收发帽、五组衣物、24组农事、四向走跑、静态候选依依赖顺序迁移；现行工具参数化与测试路径同步 | 所有活动 review 显式指新构建；原证据原字节保持；旧脚本退出现行入口，未迁项有明示清单 |
| 4 入口切换与历史封存 | 原生加载/画面对比、必要连续播放与界面选择检查通过后切评审入口；封存剩余旧资料，更新唯一规范目录节与索引 | 无活动开发引用指旧制作路径；无资源丢失/误计款式/认可升级；生产旧人物仍正常，导出边界未扩大 |
| 5 后续制作采用新结构 | 后续补动作/衣物/发帽/体型均新增源、适配修订和构建；只移动现行选择指针 | 不覆盖 GPT 原图、冻结输出或认可证据；修改按实际依赖失效 |
| 6 未来正式人体切换（独立任务） | 完整 required_actions、动态组合、原生世界与角色覆盖通过后形成唯一 release，统一切换所有生产人物 | 同一发布仅一套现行人体体系；旧模型退出运行和导出；验证真实导出支持的入口，不能用源码测试冒充 |

阶段 2 选择西锄 v3 是为了尽早验证最关键的跨目录和冻结证据风险，不要求一开始重做它的美术。若迁移清点发现不可恢复的外部输入，则先补齐来源或选择可完整恢复的另一条小链；不能为了推进先删原件。

目录迁移的最低验收包括：清单项数与字节保全；每个新清单引用可解析；错误/缺资源仍拒绝；活动样例名称、帧序、时间、画布、根点、显示尺度与输出一致；原生入口能选择并播放实际迁移样例；脚本/场景 UID 与必要导入引用正确；旧认可报告不被篡改；生产人物及存档行为不因目录调整改变。变化仅在路径时不机械重做全部美术测试，变化涉及逻辑/共享合成时按风险补失败反例和回归。

最终目录迁移完成只表示“资源组织与入口切换完成”，不表示人体规范阶段 4/5/6 或正式生产迁移完成。系统 OS 输入/WM 焦点、全帧率录像、跨平台和新导出的既有未验证项仍保留。

## 11. 目录迁移完成后如何完善资源覆盖

用户要求后续沿新目录完善覆盖，具体顺序为：

1. 由新库清单生成“体型×动作×方向×实际配方”的覆盖表，分别标记源已具备、适配已具备、烘焙已核对、原生已验证、用户已认可。保留原抽样范围，不重新要求遍历全部衣柜组合。
2. 按首个实际生产角色的固定配方列 required_actions，以现有已认可资源填入明确的姿态映射。只有缺失或不兼容项进入制作队列，已有合格美术不因目录变化返工。
3. 新动作进模板 motions；新款进 parts；动作/体型适配进 adaptations；生成原图与失败稿进 sources；配方与派生分别进入 recipes/builds，所有引用固定修订。配方覆盖表必须区分“有完整穿衣参考帧”和“独立部件可组合”。
4. 对缺口制作先小样、再同批动作，按实际依赖增量验证，完成后生成新构建；共享部件改变只使受影响动作/配方证据失效。原生世界衔接、脚/握点和空间遮挡仍是发布前门禁，目录迁移本身不会解除。
5. 首个配方完整后，再按明确角色需求扩款或体型，并准备统一发布；这些是目录迁移后的独立任务，不在本轮设计或搬迁中混做。

## 12. 用户需确认的核心决策

建议一次确认下面这个完整范围，也可逐项修改：

1. **采用方案 B 和 `art/characters` 新根目录。** 体型/动作/部件/配方按语义组织，批次只作为 reviews/evidence 的范围；现行制作工具与原生试玩移出美术目录。
2. **源图、失败稿和冻结认可保留。** 后续完善“资源覆盖”指补齐所需动作/方向/配方能力；新增或修正素材采用新 revision＋切换活动引用，不能就地覆写已认可原件。历史只供追溯，不进入发布与运行回退。
3. **本次只迁移制作与评审资源，保持现有能力和视觉。** 不同时补新动作、扩体型、重写播放器或把新版替换生产主角；旧 `player-unified-v4` 到完整新版通过时再统一退役。
4. **先完成一条真实依赖链的迁移验证，再推广。** 新入口技术等价与原用户认可分别展示，若发生实际画面变化再提交受影响结果评审。

用户已确认这些决策及精简留存调整，真实实施计划见同日期的character-resource-layout-implementation.md。实施中的逻辑目录不要求一次建立全部文件，更不要求提前制造尚缺的身体/衣物运动资源。

## 13. 本草案查阅依据与限制

- [唯一人体制作规范](../../design/character-art-pipeline.md)：第 4–9 节的完整源、mask、统一合同、有限配方烘焙、单一发布及扩展规则。
- [本轮引用与证据风险核对](2026-10-28-character-resource-layout-reference-audit.md)：主代理独立核对的路径假设、跨目录依赖、SHA 绑定与生产引用；供实施清点使用，不代替迁移后的验证。
- [PROJECT_STATE](../../../PROJECT_STATE.md) 与 [HANDOFF](../../../HANDOFF.md) 最新两节：2026-10-28 西锄耳后 v3 已获认可，相关更早“待认可”文字按历史解释。
- [静态候选](../../../art/design/character-candidates-v2/README.md)、[五组衣物抽样](../../../art/design/character-motion/adult-standard-v1/wardrobe-sampling-v1/README.md)、[24组农事](../../../art/design/character-motion/adult-standard-v1/farming-four-directions-v1/README.md)、[四组发帽](../../../art/design/character-motion/adult-standard-v1/headwear-sampling-v1/README.md) 及各实际 catalog/sample 的有限读取。

本轮没有逐图美术复审、重新运行原生测试、执行全仓迁移闭包或试运行路径替换。以上属于用户确认后的实施验收，不能用本文目录树代替。所有新结构均为提案。
