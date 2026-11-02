## 当前入口（旧人物专项数据已退役）

仅保留V4 body-actions与V5 body-pixel-v5；recipe/build分别r002与r010，唯一构建工具和通用注册/组合/时钟保持。运行包verify-runtime不读取本地制作源；verify仍要求严格源重建，二者不混同。下文旧例用于说明通用接口，涉及旧衣柜/发帽/迁移数据的命令不再可直接运行。CI不再调用已退役数据的迁移/静态导入验收。当前README/CURRENT为导航，制作合同仍以唯一规范为准。[退役范围及验证](../../../docs/reviews/2026-11-02-resource-cleanup-executed.md)。

## 2026-11-02 V5独立动画归档

`body-pixel-v5`仍通过现有统一评审器加载；当前template-v5-r009、两套recipe/build-r010、parts/body/adult-v5/r012、archive-r010，sources/adult-v5-animation-r012仅保存最终动画快照。旧V5制作过程与旧版本已清理，下文相应过程路径为历史。默认游戏/基线保持v4，唯一规范8.2.1约束验收后只留动画必需数据。

## 人物美术归档与试玩输入

最终人物美术实际图片及配套数据必须归入`art/characters/parts/`；当前母版最终PNG为`parts/body/adult-v4/r001/atlases/`。本目录的试玩继续通过严格recipe/build与suite加载，build保留为验证制品，不是最终美术归档根。不得为移动目录改坏冻结输入或绕过加载校验；新归档遵循[唯一制作规范第8节](../../../docs/design/character-art-pipeline.md#8-目录迁移与成本)。

## 背心短裤身体全动作评审

运行 `python3 tools/characters/review.py body-actions`。通用 `character_body_samples.gd` 严格加载body-only 24能力配置，复用headwear trial的动作时钟/世界移动/观察器，隐藏发帽控件。主配置为 `art/characters/reviews/body-actions/review.json`，支持四向idle/walk/run/hoe/water/harvest，108帧，农事带工具。

无工具身体配置 `body-reference.json` 可通过同一场景的 `--construction-suite=<绝对路径>` 指定。两者均review-only；完整能力加载不代表生产发布、接触验证或用户认可。[验收记录](../../../docs/reviews/2026-11-01-tank-all-actions.md)。

# 人物Godot试玩入口

本目录是隔离制作评审的场景和加载代码，资源统一来自 [art/characters](../../../art/characters/README.md)。它不接管正式玩家/顾客，正式入口仍是 `res://scenes/harbor.tscn`。

## 注册body＋top有限审阅

`python3 tools/characters/review.py registered` → `reviews/registered/review.json` → Python严格构建/准备源预检 → `character_registered_trial.tscn` / `character_registered_samples.gd`。场景继承 `character_walk_trial.tscn`，脚本继承既有controller，不新增运动/动画时钟。加载器核实际SHA、PNG/RGBA、canonical body、同pose语义与来源闭包，失败同步清空世界/预览状态。

当前有限样例为成年v2西向walk六帧＋独立idle、top04红毛衣；只启用有资源的方向/动作。1/2是制作侧body/配方比较，不写默认游戏或玩家存档。Python负责typed JSON与原图重建；Godot复核绑定实际字节与加载状态。GPU观察器 `tests/characters/capture_registered_review.gd` 只驱动现有输入并采样原时钟，要求新建 `/private/tmp/coastal-*` 证据目录及预先冻结的input-contract.json，不能以headless测试替代视觉验收。


## 统一固定发帽全动作入口

`python3 tools/characters/review.py all-actions-construction` 加载唯一严格构建，包含成年固定 top03／原裤鞋／栗短发＋草帽的24动作方向、84姿态。沿用同一 headwear trial／motion review，共享世界玩家与权威动作时钟。左侧六动作四方向可暂停和逐帧；方向键行走、Shift跑步、F浇水、G锄地、H收获，C收起对照、R回起点。只有 hair_hat，不提供其他头部状态切换。本轮Q2=B评审交付状态见资源库 readiness；无真实存档和生产切换。

## 启动与调用关系

从仓库根运行 `python3 tools/characters/review.py <suite>`；launcher读取 `art/characters/reviews/<suite>/review.json`，选择本目录场景及参数。默认suite为body-actions，V5使用body-pixel-v5，也可用 `--dry-run` 查看实际命令。静态候选打开HTML，不经过Godot播放器。

| suite/职责 | 文件 | 当前行为 |
|---|---|---|
| locomotion、farming | [character_walk_trial.tscn](character_walk_trial.tscn)、[character_walk_trial.gd](character_walk_trial.gd) | 同一试玩基础；farming增加农事catalog、转换和诊断参数 |
| 衣装抽样 | [character_wardrobe_trial.tscn](character_wardrobe_trial.tscn)、[character_wardrobe_samples.gd](character_wardrobe_samples.gd) | 加载五个实际sample；不是全部衣服自动适配 |
| 发帽抽样 | [character_headwear_trial.tscn](character_headwear_trial.tscn)、[character_headwear_samples.gd](character_headwear_samples.gd) | 四组动作/方向×四头部状态，验证sample/parent/贴图及输入SHA |
| 默认西锄发帽入口 | [character_headwear_hoe_review.tscn](character_headwear_hoe_review.tscn)、[character_headwear_hoe_review.gd](character_headwear_hoe_review.gd) | 原发帽试玩的薄入口，只调整初始选择，不是另一套合成器 |
| 动作/农事面板 | [character_motion_review.gd](character_motion_review.gd)、[character_farming_review.gd](character_farming_review.gd) | 现有动作面板、时间与农事评审辅助逻辑 |
| 路径校验 | [character_resource_paths.gd](character_resource_paths.gd) | 解析显式库根，拒绝非法路径；无root兼容用于已有格式/隔离fixture，不授权新配方绕过合同 |

完整all-actions-construction消费当前严格构建manifest和统一suite；历史suite保留迁移manifest/sample/candidate格式。`build.py`的新严格构建不会自动出现在这些suite中；新增评审范围要明确接入和验证消费者，不能直接替换catalog路径后假定兼容。

## 路径与状态

- `res://`以 `godot2d/` 为根；资源库位于仓库的 `art/characters/`，不是Godot assets目录。
- 评审catalog中 `sample`/`candidate`通常相对仓库根；sample内 `file`/`inputs`等按显式resource_root解析。不要统一加一层目录或批量改成res://路径。
- 父衣装与子发帽有各自root和SHA，必须分别解析。失败应清空无效状态/报错，不回退旧身体或另一帧。
- headwear目前显式限定四组抽样和四种头部状态。给definitions或文件夹增加动作，不会自动解除加载器的能力限制。
- 旧sample内创建时的accepted/native_checked字段可能保留当时状态；当前认可应查资源库evidence和coverage中的确切独立记录，不能只读一个字段。

## 修改与验证

静态场景/UI留在tscn；运行行为和校验放gd。素材、合成和配方沿 [统一构建工具](../../../tools/characters/README.md)，不要在本目录追加每套衣服一个播放器或为错位增加本地缩放。

按改动选择 [人物测试](../../tests/characters/README.md)：路径/加载修改先用合成fixture反例和实际资源测试；画面、动画、遮挡或切换还需真实GPU与原生世界验证。日志统一 `/private/tmp/coastal-*.log`，不使用玩家真实存档，不读取 `.godot/`缓存作常规验收。

## 严格构建小样消费者

`python3 tools/characters/review.py headwear-construction` 在Python逐构建verify后，经 `--construction-suite=<绝对路径>` 进入现有发帽场景。`character_headwear_samples.gd`按新suite kind分派到 [character_construction_samples.gd](character_construction_samples.gd)，返回原样例数据结构并复用原时间轴/世界动作。新suite仅显示西锄按钮；普通旧场景仍默认东跑，原hoe_review薄入口仍选西锄。

消费者验证四manifest、recipe2/head_state/头槽与层序、同一base_recipe、当前三工具文件及全部inputs、真实模板variant几何时序、PNG/SHA/RGBA。完整源重建与多来源选择由Python verify执行；Godot不另建合成器。加载失败清空，不回退旧sample。
