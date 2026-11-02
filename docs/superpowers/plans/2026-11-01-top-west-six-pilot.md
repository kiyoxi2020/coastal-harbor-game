# 现有 body 西向六帧上衣小样 Implementation Plan

> **For agentic workers:** 使用subagent-driven-development；用户明确要求并行，独立核查与源准备工具改动可并行，图像生成和最终集成由主代理完成。保留所有既有未提交修改，不自动提交。

**Goal:** 复用归档adult-standard-v2身体源，优先一次生成西向walk六帧长袖上衣，形成有来源、严格坐标检查和原生动态证据的制作侧小样；失败则记录并转单帧，不把失败稿登记成合格配方。

**Architecture:** imagegen读取六张1024×1536原帧与top04毛衣款式参考，生成3×2格透明衣物图。身体像素始终来自归档；现有统一source-pack及build/verify承担派生和严格合成，不另写人物合成器/播放器。

**Tech Stack:** 内置imagegen、现有Python/Pillow源准备工具、严格构建入口、Godot评审、Paseo。

**执行中用户修订：** 透明上衣六帧直出失败，单帧修订仍只为款式候选；用户要求改为“先按母版生成穿红毛衣的人物，再抠衣物”。本轮切换此方法，仍六帧优先。实际新来源位于art/characters/sources/top04-adult-v2-west-worn-r001/。先检查穿戴表位置/姿势/大小，再用真实衣物归属遮罩保留源RGBA提取，最终叠回原body；不可用生成的人体替换母版，也不能将遮挡后可见片当完整衣身。

## Global Constraints

- 优先六帧同时生成，遇到问题再改单帧；保留合格帧与共同参考。
- 同一母版、整帧注册；禁止部件单独挪缩补错位，不拼其他人物脸手。
- 当前body、108帧姿态、时序和运行基线保持；不得为检查通过刷新runtime-baseline。
- 图像生成不是静态接口或动态兼容认可；完整发布仍关闭，不增加游戏内换装或存档。
- 当前body来源SHA与归档核对；新部件必须有真实来源、mask/层序和声明范围，不造其他方向资源。
- 任何Godot命令使用--log-file /private/tmp/coastal-*.log；测试存档仅/private/tmp/coastal-*。
- 同法同类失败最多两次；有新证据才继续。合格小样交用户视觉评审后才扩量。

### Task 1: 来源与接口核查

**Files:** 只读art/characters/parts/body/adult-v1/archive-r001.json、r001/layout.json、对应六张原帧；报告分别位于/private/tmp/coastal-top-west-six-source-audit.md和/private/tmp/coastal-top-west-six-interface-audit.md。

**Interfaces:** 输出真实六帧路径/SHA、源root(512,1416)、整帧23/194、目标256×224/root(123,201)、时长53/54/53/53/54/53ms及严格接口缺口。

- [x] 并行核对归档与严格配方/原生入口，不假定旧v1上衣兼容v2。
- [x] 确认没有原始高分六帧sheet；同次imagegen以六张已查看的原帧为明确姿态输入。
- [x] 核对来源登记、完整部件和真实前景手/身体层序，生成源本身不绕开严格构建。

### Task 2: 无缩放原像素参考表

**Files:** 新增tools/characters/reference_sheet.py与tools/characters/tests/test_reference_sheet.py，不修改pack_sources.py或build/contract。核查确认这些旧工具均属于身体归档586项冻结依赖，不能直接修改后继承旧认可。

**Interfaces:** imagegen实际最多5张输入，故以通用reference-only工具将六张原图直接RGBA复制为3×2的3072×3072参考表，再与款式图共两张输入。计划kind为coastal-character-reference-sheet-plan-v1，grid/cell_px/按序inputs(file/sha256)固定；输出新目录sheet.png与可重建manifest，不是人物构建或源登记产物。

- [x] 先添加真实半透明与alpha0 RGB保留、错SHA/路径/尺寸/数量、篡改/重算metadata、覆盖输出拒绝测试并确认失败。
- [x] 实现通用build/verify命令；仅原RGBA粘贴，不合成、缩放或裁切人物像素。
- [x] 运行覆盖测试并独立复查：13项通过；两项symlink Important修复后7类攻击拒绝，真实r002六格RGBA全等。最终全量432项和人物check通过。严格body登记、前景手分片和v2评审入口缺口不由此工具冒充解决。

### Task 3: imagegen六帧优先

**Files:** 新来源目录art/characters/sources/top04-adult-v2-west-walk-r001/，保存input-inventory.json、prompts/、originals/及source.json。引用原body和top04款式SHA，不复制旧脸手。

**Interfaces:** 六原帧为姿态，top04仅为砖红绳纹/圆领/袖口风格。要求3×2输出、每格1024×1536、整图3072×3072，实际返回尺寸必须核查；尺寸不符不能假定任意缩放即可贴合。

- [x] 查看所有输入，保存实际完整提示词和来源清单；袖口延至当前body手腕，声明为top04腕长适配候选。
- [x] 执行六帧透明上衣直出：失败（下排漂移），转单帧后按用户修订切换穿戴→提取；不将失败稿认可。
- [x] 检查实际尺寸、alpha、格位、衣物/身体对应与层序；若失败，再以相同输入改单帧验证，不反复六帧同法重试。

### Task 4: 严格合成与原生验收

Q24=A后继续：先以逐像素查看的衣物外轮廓、皮肤排除区和明确的黑线归属重建ownership，保留原穿戴图RGBA，不再重复GPT mask。并行新增通用prepare_registered_source.py及覆盖测试：绑定已批准body packing plan及canonical pose重算原身体RGBA，确认原整帧登记；按相同登记将raw衣物material/ownership准备为256×224 derived source，并保留原图/计划/工具/父级哈希闭包。当前源码允许如实声明的prepared-derived来源，无需修改冻结构建器。该工具不是人物合成器，输出review-only；具体约束见本轮任务brief及实现报告。匹配idle仍须真实源，不能拿walk首帧伪造。

原生入口使用新增通用registered_review预检/样本适配器，接到现有review.py与character_walk_trial/character_motion_review。新场景继承原试玩场景；不新增角色控制或动画时钟，不修改原控制器。仅接有限body+top的idle/walk严格配方，校验source-prep与build来源、capability、原PNG/RGBA及实时输入状态。原生observer只观察实际控制/渲染，不重算人物或伪造idle。

**Files:** 仅合格新源进入新part修订、配方和build；原生优先扩现有通用评审消费者，禁止批次播放器。

**Interfaces:** 同body六pose＋匹配idle，完整源准备清单→coastal-character-construction-v1 build/verify→原生评审；缺资源/前景手接口无法表达时明确拒绝。

- [x] 不凭生成外观创建假mask；静态同姿态检查领肩、袖腕、腰线、灰底衣与前后手。
- [x] 严格build/verify与原生明暗七姿态、10世界循环、位移/停步完成；门/树遮挡和严格接触未覆盖，不扩四向。
- [x] 执行python3 -m unittest discover -s tools/characters/tests及python3 tools/characters/check.py；Godot定点回归仅覆盖实际改动。
- [x] 独立复查实际变更/源和结论；状态及交接记录已完成、失败、未验证与用户视觉待审范围。

## 分工

主代理负责计划、imagegen、集成和原生验收；gpt-6-luna/medium负责六帧源SHA与登记核查；gpt-6.1-sol/high负责严格合同/评审接口核查及必要通用工具实现。源/接口核查可独立交付并与主代理生成准备并行。受派代理不得同时修改同一文件；最终复查复用已空闲代理。

## 完成记录

473全量Python、check56/50/9/1、Godot78、最终GPU600通过；10世界循环/独立idle及原生明暗七姿态已完成，范围见最终小样报告。三项审阅问题修复复验，无生产/基线/默认游戏变更，未提交。后续四向/混搭/严格接触未开始。
