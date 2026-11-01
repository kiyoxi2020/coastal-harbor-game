# 人物资源库：结构与当前使用逻辑

这是现行人物**制作、构建和评审**的资源库。后续 agent 先读本页，再按任务进入具体文件；不要靠目录名、文件数量或旧日志推断资源已能通用组合。

## 2026-11-01 默认游戏主角身体接入（Q22=A）

正常启动Godot游戏后，主角使用`adult-standard-v2-visible-r001`归档灰色底衣身体，四向六动作共24格108帧；农事保留工具。运行包位于`godot2d/assets/characters/integrations/adult-standard-v2-visible-r001/`，由`godot_integration.py`校验严格构建后生成，SpriteFrames为`godot2d/resources/player_body_frames.tres`。

这是用户批准的本地开发接入阶段：旧餐馆NPC暂留，完整生产发布仍关闭；源配方/build保持review-only，未授予换装或精确接触资格。基线按[具体变更记录](../../docs/reviews/2026-11-01-body-game-baseline-changes.json)精确更新，没有重新采集整份基线。运行接入不改变下文历史发帽评审包的范围。

## 2026-10-30 分类整理后的日常入口

先看 [当前人物与衣物](CURRENT.md)。真实部件路径已按 `parts/<部位>/<款式ID>/` 分类，部位为 top、pants、shoes、hair、hat；共享接口在 shared。每款的体型/动作适配直接位于 `<template>/<motion>/<revision>/`，不再嵌套 adaptations。稳定ID保留，不能仅凭目录存在推断完整动作兼容。

sources保留制作源与提示词，templates保留母版和姿态，recipes定义组合，builds保留加载与重建必需制品。款式内部分review命名文件是实际SHA依赖，仍保留；它们不是可随意删除的展示缓存。

用户已授权精简确认后的验收材料：视频、动图、非必需截图、原始截图压缩包和大型观察快照不再常驻。旧报告中的媒体路径为历史路径，必要时从迁移前提交7ef64b6恢复；旧原生验收不自动变成新路径验收。轻量决定/范围记录保留，迁移清单见 `migrations/2026-10-30-organization.json`。

## 接手时先读什么

1. 仓库根 [AGENTS.md](../../AGENTS.md)：执行约定和强制门禁。
2. [PROJECT_STATE.md](../../PROJECT_STATE.md)、[HANDOFF.md](../../HANDOFF.md) 顶部：当前阶段、已完成和待办；后文是历史。
3. [唯一人物制作规范](../../docs/design/character-art-pipeline.md)：母版、姿态、注册、部件接口、动态验收与发布规则。本页只解释导航和现有实现，不另立制作合同。
4. [catalog.json](catalog.json) 找资源，[coverage.json](coverage.json) 查实际能力和缺口。准备构建时再读[工具说明](../../tools/characters/README.md)与[严格配方示例](recipes/wardrobe-hoe-west/r002.json)。

不要默认全量读取 sources、migrations 或历史原生报告；先由具体配方/动作引用定位必要输入。

## 本轮统一全动作候选

固定 top03 条纹衫、原裤鞋、栗色短发＋草帽的 [统一配方](recipes/adult-top03-full-hair-hat/r001.json) 已完成四向六动作共24格84姿态的严格构建与复核。统一入口为 `python3 tools/characters/review.py all-actions-construction`，配置见 [review.json](reviews/all-actions-construction/review.json)。原生整包既定raw验证已完成；用户Q2=B接收本轮当前四帧像素步态评审交付，严格支撑后续，当前状态见 [readiness](evidence/all-actions-v1/current-delivery-readiness.json)；此入口只展示固定 hair_hat，不扩展其他体型／款式或生产发布。

## 当前有哪几条使用链

| 使用场景 | 实际入口与数据 | 当前边界 |
|---|---|---|
| 默认游戏（本地接入阶段） | `godot2d/scenes/harbor.tscn` → 新身体玩家；餐馆顾客仍用 `godot2d/assets/player-unified-v4/` | Q22=A允许阶段性接入；`catalog.production_release` 为 null，没有新的正式 active_release |
| 现行试玩 | `tools/characters/review.py <suite>` → `reviews/<suite>/review.json` → Godot评审场景/静态HTML → 已登记catalog与build | 展示已完成的有限抽样，不自动遍历所有款式或新配方 |
| 后续严格构建 | `recipes/<recipe-id>/<revision>.json` → `tools/characters/build.py build` → 新build目录 → `verify` | 只产review-only；现有统一固定hair_hat24格84姿态及旧西锄示例，用户Q2=B接收本轮四帧评审版，严格支撑后续，不是完整衣柜或生产发布 |

**新构建成功不会自动替换试玩或正式游戏。** all-actions-construction消费严格manifest与完整suite；其余历史抽样保留sample/candidate格式。需要接入新评审范围时，须另核对消费者、格式和验收，不能只把catalog路径换过去或另建人物播放器。

## 目录结构与职责

```text
art/characters/
├── README.md            # 人读入口；不是资源发布清单
├── catalog.json         # 母版、部件、评审suite和来源索引
├── coverage.json        # 已有配方/动作/方向及验收范围、能力缺口
├── static-index.json    # 静态候选与来源索引
├── definitions/         # 动作与槽位词汇说明
├── templates/           # 母版选择、修订、动作、pose与同姿态身体参考
├── sources/             # 原图、prompt、必要参考及来源元数据
├── parts/               # 款式定义、体型/动作适配、view、pose-map和mask
├── recipes/             # 实际有限组合；新版严格配方也放这里
├── builds/              # 已烘焙输出及清单；不是可随时删除的缓存
├── reviews/             # 试玩/图库配置、抽样catalog
├── evidence/            # 分范围认可、核验回执、摘要与少量代表图
└── migrations/          # 旧新路径/SHA映射、清理和恢复记录
```

| 要查什么 | 从哪里进入 | 关键含义 |
|---|---|---|
| 当前成年母版 | [template.json](templates/adult-standard-v1/template.json)、[selection.json](templates/adult-standard-v1/selection.json) | `active_revision`绑定选定外观；静态母版认可不等于隐藏身体或全动作完成 |
| 动作及四向姿态 | [motion-set.json](templates/adult-standard-v1/motions/review-motion-v1/motion-set.json) → `actions/<action-id>/<revision>/<direction>/poses.json` | 看实际variant、pose顺序、时长、canvas、root和scale；不能把A/B当无差别替换 |
| 同pose身体参考 | `templates/<template-id>/motions/<motion-set-id>/body-views/` | 某些是保留脸/手/工具/衣物轮廓的完整穿衣参考，不是可任意换装的裸身体 |
| 具体衣裤鞋/发帽 | `parts/<category>/<design-id>/design.json` → `<template-id>/<motion-set-id>/<revision>/` | `views.json`列实际适配，`pose-map.json`关联pose/view；只承诺列出的配方范围 |
| 原始来源 | `sources/<source-id>/source.json` → 其assets及prompt/metadata | 保留完整原图与来源身份；originals中也可能含切图或必要中间参考，不能仅凭名字删除 |
| 实际组合 | `recipes/<recipe-id>/<revision>.json` | 区分旧抽样记录与有 `kind: coastal-character-construction-v1` 的严格配方，不能仅按r001/r002判断格式 |
| 当前显示帧 | 配方或评审catalog指向的 `builds/<build-id>/` | 依具体manifest/sample/candidate解析，不按文件名猜哪个是最新版 |
| 静态候选 | [static-index.json](static-index.json)、[静态图库](reviews/static-candidates/gallery.html) | 仍是候选；存在图片不等于动态适配、组合兼容或用户认可 |
| 验收状态 | `coverage.json`与 `evidence/<scope-id>/acceptance.json`、receipt/summary | 技术检查、原生验证和用户认可分别解释；不能从一个布尔值扩大范围 |

款式ID、体型ID、动作集ID、pose_id、view和recipe_id是不同身份。`original-*`保留旧配方作用域，同名不能推断为通用款式；来源包数也不等于独立生图次数。definitions提供词汇导航，修改其JSON不会自动扩展构建器校验、Godot加载器或玩法事件处理器。

## 路径应该怎样理解

- `resource_root: art/characters` 声明资源库根；其纹理、source、mask和inputs通常使用相对于本库的路径，例如 `parts/...`、`sources/...`。
- 现行评审catalog的 `sample`/`candidate` 保留相对于**仓库根**的路径，例如 `art/characters/builds/.../sample.json`，并绑定SHA。
- `res://dev/characters/...` 相对于 **Godot工程根 `godot2d/`**，不是仓库根。
- sources中的opaque历史metadata和migrations可能记录旧路径；追溯字段不是活动加载入口，不做全库字符串替换。
- 缺文件、越界、未知root或SHA不符应先查具体引用链；不要用symlink、另拷一份旧资源或刷新基线掩盖失败。

## 日常操作

以下命令在**仓库根目录**执行。详细参数与依赖见[工具README](../../tools/characters/README.md)。

### 查看已有资源

```sh
python3 tools/characters/review.py headwear
python3 tools/characters/review.py wardrobe
python3 tools/characters/review.py farming
python3 tools/characters/review.py locomotion
python3 tools/characters/review.py static-candidates
```

| suite | 当前内容 |
|---|---|
| headwear（默认） | 东跑/西锄/南浇/北收四组，每组bare/hair/hat/hair_hat；启动默认西锄发帽 |
| wardrobe | 五个代表性衣物配方；不是全部款式通配 |
| farming | 三类农事×四向×长短袖24组 |
| locomotion | 四向站/走/跑及已有两上衣参考 |
| static-candidates | 静态候选HTML图库 |

可加 `--dry-run` 只查看启动命令。也可双击 `tools/characters/review.command`。实际场景和加载器职责见 [Godot试玩README](../../godot2d/dev/characters/README.md)。

### 构建和复核一个新修订

```sh
python3 tools/characters/build.py build art/characters/recipes/wardrobe-hoe-west/r002.json --output /private/tmp/coastal-character-readme-example-r002
python3 tools/characters/build.py verify /private/tmp/coastal-character-readme-example-r002
python3 tools/characters/check.py
python3 -m unittest discover -s tools/characters/tests
```

示例输出路径必须尚不存在；再次构建换一个新路径。正式留存的评审构建可放到全新的 `art/characters/builds/<build-id>`，不得覆盖旧目录。构建器不会自动修改catalog、coverage或认可记录，也没有正式发布命令。

严格配方绑定唯一model、母版/动作集、真实variant、必需动作/方向、同pose部件、源包、mask和完整层序。当前支持完整整帧分层，以及与模板所选variant完全一致的整帧平移注册；不支持构建时裁剪/密度缩放或部件局部挪缩。缺接口时先扩统一合同和测试，不能绕开入口写批次构建脚本。

`alpha-over`与`ownership-replace`显式区分。ownership描述源像素归属，coverage描述覆盖接口，occlusion描述当前前后关系；即使PNG恰好相同也不是同一概念。二值归属替换保留原RGBA软边，不能把诊断mask再乘到源alpha上。

### 修改后需要哪些验证

- 仅README/导航：检查文档链接和所述命令，按AGENTS执行人物工具测试与仓库门禁；不因文档变化重复GPU采集。
- 合同、构建器或路径逻辑：先做能复现误用的失败测试，再跑人物工具测试与 `check.py`；Godot变化再做对应加载/行为回归。
- 实际贴图、pose、mask、时序、层序或组合：按唯一制作规范完成实际显示尺寸、连续动作和原生世界验收；headless或加载成功不能替代。
- 生产切换：完整角色能力、动态/接触/认可与唯一发布清单另行验收；当前仍关闭。

[Godot测试README](../../godot2d/tests/characters/README.md)解释实际加载、合成fixture与原生采集的区别。新build的manifest绑定配方、依赖、构建器/Pillow与输出；依赖改变后 `verify` 会失败，不能手改SHA或通过字段沿用旧证据。原迁移GPU回执只证明当时冻结范围，不给新构建授予认可。

## 后续资源应如何扩展

| 任务 | 修改入口 | 完成前必须确认 |
|---|---|---|
| 新动作 | 当前体型动作集的 `actions/<action-id>/<revision>/`，再补实际配方 | 新pose/时序/事件及进入退出规则；对应衣物/发帽接口齐全 |
| 新款式 | `parts/<category>/<design-id>/`及目标体型/动作集适配 | 同投影可复用view；新形态要真实补源/隐藏区/覆盖与层序 |
| 新体型 | 自身template与动作适配，沿同一model合同 | 不能缩小成人冒充儿童，不能分叉另一套人体管线 |
| 新组合 | `recipes/`中的严格配方新revision，再产新build | 声明实际能力和依赖；先单侧运动小样再扩四向/动态混搭 |

按coverage先补实际生产配方的缺口，不预先穷举整衣柜。固定配方全动作四向发帽评审包已完成；仍欠部分隐藏身体/新衣型接口、严格足/握持/目标接触、其他体型动态适配和正式角色发布。南浇/北收发帽未记录的新用户认可不能由目录迁移补写。

## 维护工具与冻结边界

日常只用 `review.py`、`build.py`、`check.py`及对应测试。以下工具保留用于迁移核验/维护，**不是新增资源的一键初始化步骤**：

| 工具 | 用途与边界 |
|---|---|
| `migrate_layout.py verify`、`import_static.py --verify` | 检查Git基线迁入资源；import/publish不是日常追加资源命令 |
| `index_library.py` | 本次迁移数据的导航生成器；重跑会重写索引/派生数据，不能用来自动登记任意新动作或修复SHA失败 |
| `record_acceptance.py` | 迁移已有分范围认可，不能制造新用户认可 |
| `native_contract.py` | 本次129图等范围的GPU合同校验，不是通用人物正式发布器 |
| `cleanup_legacy.py` | 已批准迁移的清理/保全工具，不是日常资源垃圾回收器 |

[生产与旧构建基线](../../tools/characters/runtime-baseline.json)冻结现行生产依赖、九份旧配方及既有构建文件。不要改旧sample或baseline来“过检查”，不要把builds当缓存清空，也不要在builds根直接放杂项文件（当前门禁按构建子目录检查）。静态门禁不能判断任意新代码的语义或图片中的人体，代码评审与动态视觉验收仍有必要。

PR/push检查见 [character-construction.yml](../../.github/workflows/character-construction.yml)。配置文件存在不等于远端已经运行或分支保护已设置；服务端required check需要另行配置。

## 留存与恢复

保留最终采用资源、可编辑/重建所需原图、prompt、mask、注册和配置，以及轻量认可和代表图。普通失败稿与重复过程资料主要留在Git历史，不额外复制整库archive。

旧布局基线为 `379a9bc`；目录迁移和构建门禁本地提交为 `ad1fb18`。完整旧新路径、SHA及清理记录见 `migrations/2026-10-resource-layout/`。单件历史可用：

```sh
git show 379a9bc:art/design/character-motion/adult-standard-v1/headwear-sampling-v1/catalog.json
```

重跑旧工具用独立历史checkout，不恢复旧制作目录为当前活动入口。未入Git旧过程资料暂存在 `/private/tmp/coastal-character-layout-untracked-hold`，完整迁移原生采集在 `/private/tmp/coastal-character-layout-native`；临时目录不是永久归档，删除前须核实持久保全。库内保留轻量回执、摘要与代表图，不把“临时保全”写成“已入Git可删除”。

## 西锄严格构建四状态小样

统一入口的四份schema2固定配方位于 `recipes/headwear-hoe-west-{bare,hair,hat,hair-hat}/r001.json`。它们引用现有严格衣装配方 `wardrobe-hoe-west/r002.json`，先重建衣装并完成整帧登记，再在目标画布组合已登记头层。四状态仍只覆盖西锄四pose及匹配idle；没有扩全动作或生产发布。

```sh
python3 tools/characters/review.py headwear-construction
```

入口在启动前逐一verify四构建，Godot加载器再次核输入/工具/输出哈希与模板姿态时序。配方和输出仍review-only；不沿用旧用户认可作为新发布资格。准确合成规则和多来源选择见 [小样设计](../../docs/superpowers/specs/2026-10-28-west-hoe-construction-design.md)。
