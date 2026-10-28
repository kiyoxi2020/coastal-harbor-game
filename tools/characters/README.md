# 人物制作与核验工具

先读[人物库结构与当前使用逻辑](../../art/characters/README.md)。日常只需三类入口：`review.py`查看已登记抽样，`build.py build/verify`构建与复核严格配方，`check.py`检查仓库边界。新构建不会自动替换现行Godot试玩或正式玩家。

## 日常查看

在仓库根执行 `python3 tools/characters/review.py <suite>`；suite为headwear（默认西锄发帽）、wardrobe、farming、locomotion或static-candidates，可加 `--dry-run`。也可双击review.command。场景与加载器导航见[Godot试玩README](../../godot2d/dev/characters/README.md)，测试分类见[Godot测试README](../../godot2d/tests/characters/README.md)。

## 后续构建的统一入口

安装工具依赖：`python3 -m pip install -r tools/characters/requirements.txt`。

```sh
python3 tools/characters/build.py build art/characters/recipes/wardrobe-hoe-west/r002.json --output /private/tmp/coastal-character-build-r002
python3 tools/characters/build.py verify /private/tmp/coastal-character-build-r002
python3 -m unittest discover -s tools/characters/tests
python3 tools/characters/check.py
```

输出也可指定库内全新的 `art/characters/builds/<build-id>`。已有目录即使为空也不能覆盖；修改配方后创建新revision和build目录。输出包含帧和manifest，始终为review-only；此入口没有正式发布命令。

`build_contract.py`实现严格配方合同。真实示例为 `recipes/wardrobe-hoe-west/r002.json`：绑定同一母版/动作集、B姿态、hoe-west+idle-west能力、源包、部件定义、所有实际来源、mask与逐帧层序。它用旧记录作为输入重建，不修改旧sample、认可或迁移JSON。新款或新动作沿相同字段扩展；新增动作的pose数来自模板，不要求四帧。

每层使用完整整帧注册图，不支持本地缩放/挪动。原源帧坐标的层可在整张合成后统一注册：frame.registration绑定确切document/record，source_box和whole_frame_translation须与所选模板variant相同；暂不接受裁剪或构建时密度缩放。正常姿态位移可以烘焙于注册视图。超出这些接口时先扩合同和反例测试，再接资源，不能另写专用构建器。

frame.composition显式选alpha-over或ownership-replace。后者以首个同pose身体参考为底，使用部件二值coverage替换原RGBA，保留源软alpha与透明RGB，不再叠乘一次透明度；coverage/occlusion/ownership仍各自存储及绑定。完整穿衣身体参考仍是有限配方接口，不能冒充隐藏裸身体。

manifest记录配方和实际依赖SHA、构建器/Pillow身份、artifact_digest及输出SHA/RGBA。verify重新验证来源、重算digest并重建逐像素比较；新增无关源不影响旧构建，改已依赖的源/mask/姿态/配方/合成代码则验证失败。不能通过手改输出SHA或user_accepted字段继承验收。

check.py拒绝未登记的旧格式配方、旧构建变动或孤立输出、退役目录/试玩路径恢复、资源目录中的批次代码，以及未评审的生产人物贴图/控制器/引用或新增CharacterBody2D入口。当前九份旧配方只按冻结清单继续评审。runtime-baseline没有自动刷新命令，修改基线本身必须在评审中说明原因及对应验收。

GitHub工作流 `Character construction gates / character-contract`在PR/push运行单元测试、仓库门禁及迁移校验。当前仅配置工作流，未运行远端CI或设置服务端required check；需要在仓库分支保护中将该job设为必需，才能阻止未通过的合并。静态扫描也不能识别任意脚本或判断图像中的人体，代码评审和原生动态验收仍是必要门禁。

## 迁移维护工具（按需读取）

以下条目用于已完成迁移的核验与维护，不是新增资源的一键初始化流程；不得为更新导航随意重跑import/publish、index_library或record_acceptance。

- `migrate_layout.py verify`：核验动态迁移字节、路径与引用；`import --destination /private/tmp/coastal-<stage>`从固定Git基线重建隔离候选，`publish --destination ...`仅用于本次迁移，不用于覆盖未来新版本。
- `import_static.py --verify`：核验60静态候选、必要来源与新引用；静态导入规则持久保存在static-selection.json，旧文件移出后仍可从Git恢复。
- `index_library.py`：按本次已迁移manifest生成导航、动作/pose与69行实际能力表；是现有数据的索引生成器，不虚构新资源。
- `record_acceptance.py`：保存分范围原认可与迁移关系，不制造新用户认可。
- `native_contract.py`：冻结新入口输入、验收真实GPU报告与完整129输出；不把一循环核验当十循环或OS输入测试。
- `cleanup_legacy.py prepare/apply`：先清点Git可恢复性，只有新原生回执通过才移出旧制作目录。非Git资料先临时保全，不修改Git历史。

运行测试：`python3 -m unittest discover -s tools/characters/tests`。

新增资源/动作/适配遵守 `docs/design/character-art-pipeline.md`；此迁移代码不替代GPT制作、真实姿态接口或必要的原生世界验收。版本与能力必须按实际配方声明，禁止改旧认可JSON或缺帧回退旧人物。

## schema2固定头部组合

同一 `coastal-character-construction-v1` 支持schema2：`base_recipe`只引用严格schema1配方，在内存重建父衣装目标帧；所有geometry/pose/timing继承父配方。`head_state`固定为bare/hair/hat/hair_hat之一，clips逐pose声明有界头层操作，不支持任意DAG、多级叠加或局部挪缩。新helper `composition_contract.py` 纳入engine身份，修改实际输入/工具仍使verify失效。

hair-only按alpha>0二值支撑复制原RGBA；hat/hair_hat按far/body/(hair)/near合成后只在真实头层支撑内回贴。第三帧帽下发由两个真实view和互斥来源selection重建验证；source ownership、选择、coverage和可见性诊断不互换。

`review.py headwear-construction [--dry-run]`消费 `art/characters/reviews/headwear-construction/review.json`，先verify四build再进入既有发帽试玩。严格schema2仍沿用原build manifest格式，不能直接替换旧sample路径假定兼容。

新GPU证据入口为 `construction_native.py snapshot --suite <suite.json> --evidence /private/tmp/coastal-<new>`，再运行 `res://tests/characters/test_character_construction_native.gd -- --evidence=<同目录>`；完成后 `construction_native.py verify --evidence <同目录> --receipt <同目录>/receipt.json`。Godot命令必须传 `--log-file /private/tmp/coastal-*.log`。snapshot目录必须全新，native只接受input-contract.json，无其他文件/目录；验证拒绝覆盖旧回执。它认证本小样的四state十面板循环、明暗停帧和世界动作，不认证OS输入/WM焦点、严格接触、导出或用户认可。
