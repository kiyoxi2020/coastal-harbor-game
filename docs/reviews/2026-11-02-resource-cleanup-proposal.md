> 用户已于本轮批准A组和旧人物链退役，执行结果见[清理报告](2026-11-02-resource-cleanup-executed.md)。下文为删除前的审查快照，不代表文件仍存在；B4室内测试输入、B5其他待确认变体及C缓存未顺带清理。

# 当前资源清理提案（待用户审查，未执行删除）

本次仅盘点并生成文字清单，不删除、移动、解除Git跟踪或提交任何资源。用户本轮要求先审查，优先于默认过程清理规则。建议先审批A组；B组须另做依赖迁移，C组为可选缓存。文件状态与大小为2026-11-02本轮扫描快照，执行前须重新核对SHA及引用，不能按过期目录通配符删除新增文件。

## 盘点与判断依据

- `godot2d/project.godot`主入口为`scenes/harbor.tscn`。递归追踪场景、脚本、资源配置、class_name及JSON内res路径，得到323项保守静态依赖（其中assets文件208项）。主入口内仅供测试参数触发的tests驱动单独标记，不混同正常玩法调用。检查主代码的加载/文件访问，纳入`regions.json`与`house-interior/pilot.json`中的运行路径。
- 分别核对人物runtime-baseline、全部严格build输入/输出，以及当前v4/v5最终归档，共6453项现存构建/冻结依赖。工具与测试代码另做路径检索；例如室内原稿虽不参与运行，却仍被单元测试读取。
- 工作区扫描范围约2.4 GiB（不含.git）；主要是art约2.2 GiB，godot2d约132 MiB，其中Godot缓存磁盘占用约83 MiB。下表大小按文件逻辑字节计算，受文件系统分配影响，实际释放量可能不同。
- 这是静态依赖与引用审查提案，尚未执行删后运行测试。源码、文档、许可文件和现有未提交修改不因“非运行资源”而被当作废旧资源；本次无代码、美术或配置变更，不运行整套人物门禁。

## A：建议首批删除（可逐项批准）

| 编号 | 范围 | 文件数 | 预计空间 | 已跟踪 / 未跟踪 |
|---|---|---:|---:|---:|
| A1 | 历史恢复压缩包 | 2 | 187.30 MiB | 0 / 2 |
| A2 | 设计原稿、概念图及旧展示图 | 136 | 157.42 MiB | 136 / 0 |
| A3 | 环境/树木旧制作原图 | 7 | 6.97 MiB | 7 / 0 |
| A4 | 室内概念图 | 1 | 1.76 MiB | 1 / 0 |
| A5 | 历史评审截图与录像 | 64 | 16.52 MiB | 6 / 58 |
| A6 | Finder目录缓存 | 124 | 1.20 MiB | 0 / 124 |
| A7 | 已替代的旧农事贴图包 | 33 | 0.03 MiB | 33 / 0 |
| 合计 | 去重后实际文件 | 367 | 371.19 MiB | 183 / 184 |

逐文件路径、大小、Git跟踪状态和SHA的CSV曾用于本地审查，属于暂存文件、不加入Git；长期保留本提案与执行报告的文字摘要。表中A1–A7均排除了主入口依赖、已知冻结/构建输入及当前用户修改。只删除CSV列出的文件，不整目录连带删除其他文件；空目录可在批准执行后移除。

- **A1**：`art/archive/2026-10-22-npc-rejected.zip`与`2026-10-23-unused-assets.zip`。仅为此前清理的本机恢复副本，非运行/构建依赖；不另做备份。README和轻量文字记录保留并同步说明恢复ZIP已移除。没有把Git仓库压缩或历史删除算进收益。
- **A2**：`art/design/`下原图、概念图、旧UI稿与展示截图，共136个媒体文件（包含已烘焙进游戏资源的旧人物原稿）。主游戏使用`godot2d/assets/`中的最终切图；未发现A2文件进入当前人物构建/冻结输入或现有工具/测试的实际文件引用。保留文字总结、通用工具代码及尚未单独确认的JSON，避免整目录删除。
- **A3**：`art/godot2d/environment-v2/`、`tree-set-v4/`中的7张制作图，最终游戏贴图保留于`godot2d/assets/`。
- **A4**：`art/interior/concepts/approved-cottage-pixel.png`，室内构思参考；已接入的家具最终贴图/运行manifest保持。
- **A5**：`docs/reviews/`的63张图片与1段录像。保留文字报告，并把附件链接标为历史已清理；不宣称旧原生媒体或回执仍可重新核验。当前v4认可清单及归档绑定的13项报告/回执/输入文件不在此项。
- **A6**：各处`.DS_Store`，不包含Godot缓存目录内文件；它们是Finder目录缓存，不是动画数据。
- **A7**：`godot2d/assets/farming-grid-v2/`全部33个文件，含16张旧贴图和导入侧文件。主脚本已使用`farming-polish-v3`/`flowers-v7`，主入口、全部脚本与测试检索均未发现旧包调用。执行后应验证农事/图标及导出；其余assets目录不得顺带删除。

### A2的具体子目录

| 路径（仅CSV列出的媒体） | 文件数 | 空间 |
|---|---:|---:|
| `art/design/P06-ui` | 3 | 0.97 MiB |
| `art/design/P07-acceptance` | 8 | 7.24 MiB |
| `art/design/P09-art-v1` | 11 | 13.54 MiB |
| `art/design/P09-crafting` | 8 | 5.60 MiB |
| `art/design/P11-restaurant` | 11 | 10.62 MiB |
| `art/design/bag-navigation-v2` | 2 | 2.74 MiB |
| `art/design/bag-ui-v1` | 3 | 3.85 MiB |
| `art/design/farming-grid-v2` | 4 | 5.71 MiB |
| `art/design/farming-polish-v3` | 1 | 1.02 MiB |
| `art/design/fertilizer-badge` | 2 | 2.57 MiB |
| `art/design/flowers-v7` | 3 | 3.76 MiB |
| `art/design/harbor-district-v1` | 3 | 3.23 MiB |
| `art/design/hud-map-button` | 3 | 2.98 MiB |
| `art/design/kitchen-ui-v2` | 15 | 19.56 MiB |
| `art/design/map-expansion-v1` | 7 | 12.48 MiB |
| `art/design/menu-navigation-v1` | 4 | 5.50 MiB |
| `art/design/npc-modular-v2` | 10 | 6.37 MiB |
| `art/design/player-unified-v4` | 5 | 9.43 MiB |
| `art/design/restaurant-concept-v1` | 1 | 2.38 MiB |
| `art/design/seed-keyboard` | 2 | 2.59 MiB |
| `art/design/trade-navigation-v2` | 2 | 2.78 MiB |
| `art/design/trade-ui-v2` | 1 | 2.07 MiB |
| `art/design/trade-ui-v3` | 1 | 1.27 MiB |
| `art/design/trade-ui-v4` | 1 | 1.32 MiB |
| `art/design/trade-ui-v5` | 5 | 6.72 MiB |
| `art/design/visual-polish-v6` | 6 | 7.02 MiB |
| `art/design/world-map-c` | 7 | 5.20 MiB |
| `art/design/world-map-single` | 5 | 2.92 MiB |
| `art/design/world-map-v1` | 2 | 5.97 MiB |

## B：建议后续清退，但本轮不直接批准删除

| 编号 | 路径/范围 | 当前体积或潜在范围 | 暂不能直接删的原因及前置工作 |
|---|---|---:|---|
| B1 | `art/characters/sources/`旧原稿/参考/派生 | 总1118.12 MiB；未绑定媒体1116张、431.89 MiB | 1886个文件仍被构建/当前归档引用。未绑定不等于无catalog、来源或评审消费者；先区分现行独立动画输入、需继续制作的部件和废弃过程链，再按已确认子集删除。保留V4/V5动画必需输入。 |
| B2 | `art/characters/builds/`非现行构建 | 总537.89 MiB、95个构建目录 | 1602文件受严格或旧冻结合同保护；门禁目前要求验证各构建。须先明确要退役的评审/配方/旧冻结范围，完成独立包和依赖迁移；不为删除直接放宽或刷新基线。当前两套V4/V5构建保持。 |
| B3 | `art/characters/templates/`及`parts/`旧模型/适配 | 总231.10 MiB；parts未绑定媒体992张、53.15 MiB | 仍有canonical、mask、姿态映射、catalog和旧运行基线依赖。旧衣物/发帽库是否继续用于后续换装须明确；不能将未接入游戏直接等同于已废弃。当前V4制作母版与V5最终动画包保留。 |
| B4 | `art/interior/source/` | 3.40 MiB媒体，另有布局JSON | `tests/test_prepare_cottage_assets.py:78`实际读取`furnishings-atlas.png`与regions.json，制作工具也使用该目录。先将测试改为独立临时夹具、确认运行pilot.json不读取source字段，再删批次输入，保留最终家具与运行配置。 |
| B5 | 其他`godot2d/assets/`未命中主入口的图片 | 38张、约2.41 MiB（不含A7） | 涉及farming-polish旧变体、flowers尺寸比较、visual-polish和UI旧图。部分存在测试/评审动态拼路径调用，须逐文件核查；不能整包删。运行图对应.import及字体许可必须保留。 |
| B6 | `art/characters/migrations/`大型旧清理清单等 | 总7.17 MiB | 属旧迁移/重建工具资料，非玩法资源；先确认哪些迁移工具仍保留、把过程结论缩为文字，不删统一ID/路径合同所需数据。 |

B组体积相互不能作为可释放总量；总目录包含现行必需文件。审查A不代表批准B的目录删除或基线修改。

## C：可选的可再生缓存

| 编号 | 范围 | 大小 | 建议 |
|---|---|---:|---|
| C1 | `godot2d/.godot/` | 75.92 MiB逻辑字节（du约83 MiB） | 不是废旧美术，是Godot导入缓存。可选，关闭相关Godot进程后清理，之后会重新导入；默认不纳入A。此次仅统计，不读取缓存内容。 |
| C2 | Python `__pycache__`及`.pyc` | 执行前按实际目录重盘点 | 可再生且已忽略，无需为目录整洁频繁清理；不涉及任何源码。默认不纳入A。 |

## 明确保留

- 当前主游戏实际资源（含最终字体与许可、环境/UI/室内/农事贴图、当前主角和顾客）、对应.import配置、运行JSON、场景和脚本；不能按所有“没在某个场景直接引用”的文件判废。
- 当前成年V4母版与游戏接入、已认可V5 r012独立动画包（9图集、164源姿态/108显示帧）及其必要元数据/构建输入。V5未接入主游戏，继续本地忽略，不加入Git；它是后续使用的现行成果，不是废旧过程稿。
- `AGENTS.md`、唯一人物制作规范、PROJECT_STATE/HANDOFF与其他开发文档、工具/测试源码及许可声明；既有用户修改全部保留。
- `.git/`约3.3 GiB：不改写历史、不执行gc/prune或删除Git对象。本提案移除工作区文件不代表相同体积的Git历史会缩小。

## 批准后的执行边界与验证

可按编号批准，例如“只执行A1、A3、A5、A6”或“执行全部A”。当前没有删除授权，不自动执行；B和C需单独指定。

批准后重新比对CSV的路径/SHA、跟踪状态及主入口依赖，文件被修改或新增引用则移出清理集并汇报。执行A时保持文字总结/历史附件说明；不做过程二进制备份、不擅自git add/commit、不自动清退已冻结人物链。A7涉及运行资产删减，须运行对应农事/图标检查、Godot加载/画面检查，并复核导出入口；若最终清理集触及人物代码/数据，则按人物规范执行两项强制门禁及适用验证。

## 补充：旧人物资源库具体包括什么、如何退役

这里的“旧人物资源库”指历史制作/评审链，不是把art/characters整目录判为废旧；上表的目录总量包含当前必需资源，不能当成全部可释放体积。

| 范围 | 具体历史内容 | 目录总量（包含现行数据） |
|---|---|---:|
| sources | 旧motion/newrun/newfarm/GPT原图、参考板、A/B尝试、分层准备稿、静态候选来源包 | 1118.12 MiB |
| builds | 旧农作A/B、top03衣物、栗色短发/草帽组合、西向小样、v1/v2/v3身体等烘焙结果 | 537.89 MiB；95目录中40个为冻结旧构建 |
| templates | adult-standard-v1/v2/v3，以及body02–body10候选；当前v4及v5-r009另行保留 | 113.03 MiB |
| parts | 旧body版本、top01–10、pants01–10、shoes01–10、hair01–10、hat01–10及旧动态适配 | 118.07 MiB；含当前v4/v5，不能整目录删 |
| recipes/reviews/evidence/migrations | 旧组合配方、试玩配置、原生回执、静态候选入口、迁移映射与大型旧清理清单 | 其中migrations为7.17 MiB，其余主要为文字/结构化配置 |

还有关联的Godot旧接入包：`godot2d/assets/characters/integrations/adult-standard-v2-visible-r001/`已不再是当前玩家绑定，但仍登记为本地integration。当前玩家使用v4；NPC仍使用旧烘焙图中的部分纹理，所以不能按“旧人物”把player-unified-v4整包删除。

这些保留原因主要是制作/评审/校验合同，而不是当前动画缺帧。`check.py`逐项核对40个旧构建的528个冻结文件、9个旧配方，并验证所有现存严格配方/构建；删除单个PNG会报缺失或SHA错误。冻结不是永久保留理由，但退役须精确审查，不可通过重采整份基线或禁用检查来完成。

建议退役顺序（当前仅方案，不执行）：

1. 固定保留主游戏实际主角/NPC纹理及运行配置、当前v4母版、已认可v5 r012独立动画数据，以及统一制作/构建/加载工具。旧服饰/体型候选如不继续使用，可整条评审能力退役；不与仅删除原稿混为一项。
2. 将仍要使用的v4/其他最终包改为直接绑定最终完整图集与动画元数据，消除旧生成图、参考板及历史manifest的强制依赖；像v5独立化一样比对PNG/逐帧输出、pose/root/time及必要mask，建立新摘要而不重写旧认可。
3. 同步退役不用的review、recipe、build及catalog/coverage入口，随后删除对应sources/templates/parts的无消费者子集；通用源码不因旧样例退役而删除。过程只保留文字总结。
4. 单独给出runtime-baseline精确变更供审核：仅退役获准的旧构建/配方和不再使用的v2接入登记，保留所有现行主角/NPC文件的SHA与运行绑定。若必要的新独立构建/integration元数据改变，列明确切新旧差异及像素等价证据；不自动刷新整份生产基线、不放宽验证器。
5. 清退后运行人物490项测试所在的测试集、check.py及主游戏实际加载/动作检查，并验证保留的v5评审仍可加载；任何缺引用先修复现行合同，不恢复整批过程资源作为常态解决办法。更新README/CURRENT与文字交接，不擅自git add或提交。

建议将这项作为独立的“历史人物链退役”任务审查；A组清理获准不代表上述合同、能力或基线变更获准。本次没有删除任何人物文件。
