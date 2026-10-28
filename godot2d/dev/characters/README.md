# 人物Godot试玩入口

本目录是隔离制作评审的场景和加载代码，资源统一来自 [art/characters](../../../art/characters/README.md)。它不接管正式玩家/顾客，正式入口仍是 `res://scenes/harbor.tscn`。

## 启动与调用关系

从仓库根运行 `python3 tools/characters/review.py <suite>`；launcher读取 `art/characters/reviews/<suite>/review.json`，选择本目录场景及参数。默认suite为headwear，也可用 `--dry-run` 查看实际命令。静态候选打开HTML，不经过Godot播放器。

| suite/职责 | 文件 | 当前行为 |
|---|---|---|
| locomotion、farming | [character_walk_trial.tscn](character_walk_trial.tscn)、[character_walk_trial.gd](character_walk_trial.gd) | 同一试玩基础；farming增加农事catalog、转换和诊断参数 |
| 衣装抽样 | [character_wardrobe_trial.tscn](character_wardrobe_trial.tscn)、[character_wardrobe_samples.gd](character_wardrobe_samples.gd) | 加载五个实际sample；不是全部衣服自动适配 |
| 发帽抽样 | [character_headwear_trial.tscn](character_headwear_trial.tscn)、[character_headwear_samples.gd](character_headwear_samples.gd) | 四组动作/方向×四头部状态，验证sample/parent/贴图及输入SHA |
| 默认西锄发帽入口 | [character_headwear_hoe_review.tscn](character_headwear_hoe_review.tscn)、[character_headwear_hoe_review.gd](character_headwear_hoe_review.gd) | 原发帽试玩的薄入口，只调整初始选择，不是另一套合成器 |
| 动作/农事面板 | [character_motion_review.gd](character_motion_review.gd)、[character_farming_review.gd](character_farming_review.gd) | 现有动作面板、时间与农事评审辅助逻辑 |
| 路径校验 | [character_resource_paths.gd](character_resource_paths.gd) | 解析显式库根，拒绝非法路径；无root兼容用于已有格式/隔离fixture，不授权新配方绕过合同 |

现行Godot加载器消费迁移保留的manifest/sample/candidate格式。`build.py`的新严格构建不会自动出现在这些suite中；新增评审范围要明确接入和验证消费者，不能直接替换catalog路径后假定兼容。

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
