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


## schema3注册视图与全动作评审（实施中）

多个已verify的同母版、同款式hair_hat部分包可用`recipe_assembly.py <新recipe-id> <新revision> <父build目录...>`汇总登记元数据，再对其输出JSON调用上述`build.py build/verify`。它只创建版本化定义、带父编号的view/mapping目录和明确类型的来源快照，不处理PNG；重复非idle能力拒绝，重复idle须证明同canonical pose/body/geometry及基础、发帽像素一致。能力只取父包真实并集，不补缺帧或继承视觉认可。父制品保留不变，汇总包仍需同Godot消费者和原生验收。

内部资源批次使用`coastal-character-construction-candidate-v1`、明确capabilities及internal-review-only范围；`candidate_preflight`核对实际固定款式严格制品。同一Godot消费者只启用真实动作，内部批次不能通过完整24格preflight。`capture_registered_candidate.gd`仅记录内部GPU明暗停帧、10面板循环与世界一循环的观察；它不替代全包接触、衔接、10世界循环或用户视觉验收。完整范围仍由`all-actions-construction`入口强制检查。

schema3基础配方沿用同一build/verify入口，要求恰好一个与canonical variant逐RGBA一致的完整body。版本化pose annotation绑定真实source/target、人工锚与表面；同一RegisteredAdaptations映射器复算完整源二值ownership、多来源选择、整源统一有理数密度归一或透明补边、真实atlas注册，再核对实际纹理。允许合法整帧整数注册，不支持部件单独缩放/挪动。coverage与occlusion仍须分别证明；半透明前景不能作为二值擦除依据。

schema2带显式adaptations时只支持固定hair_hat并引用schema3父配方，复用同一mapper。帽可为真实near-only或far/body/under-hat/near；近远帽归属并集必须是完整帽，独立typed compatibility记录绑定实际头发与帽的来源身份，允许共享原始atlas而不形成源包SHA环。

真实帽面超出canonical画布时，mapped schema2的clip可显式声明`output_padding_px:[left,top,right,bottom]`（每项0–512整数）。canonical身体、source/target annotation与锚保持原坐标；构建器在所有该clip头层登记与最终base合成时统一添加透明留边，派生交付canvas与root一起增加对应量，world/panel原身体位置不变。此接口仅允许无coverage/occlusion的hair/hat alpha层，不给基础衣体挪缩接口，也不允许裁掉owned alpha。部件纹理本身必须为真实登记后的完整输出画布；使用正常build/verify复算，不能只改manifest尺寸或root。

同姿态手或工具确实位于发帽前方时，mapped schema2的frame可声明`base_foreground`：`mode`为`canonical-rgba-ownership-split`，`target_pose`为当前canonical姿态的typed annotation selector，`surface_id`为`hands-tools-foreground`，`ownership`为`{role:canonical-foreground-ownership,mask:<SHA引用>}`。`target_pose`必须与该帧所有实际hair/near-hat/far-hat映射使用完全相同的annotation selector，禁止另造同姿态head mask sidecar。annotation中同名surface必须属于`base`且绑定同一二值mask；可见`head` surface与它互斥，衣裤鞋实际覆盖不可进入此mask，并须确实与当前头发/近帽相交。层序末尾追加虚拟`base_foreground`，不能添加另一张身体纹理。构建器把已经验证的同一base RGBA按归属分成互斥两片，保留原半透明边缘、只参与一次alpha合成；不把alpha253谎称255，也不重复叠整个人体。透明留边统一作用于该分片，不改变canonical mask坐标。前景归属须沿真实手/工具轮廓并记录前后关系依据，不能仅拿帽交集作mask或默认北向背后工具也在前。

schema3的`pose_id`原样匹配canonical pose token，允许母版既有的`B`等大写字符；路径分隔及非法字符仍拒绝。其他配方、记录、映射和部件ID继续使用既有小写ID合同，不为此改写母版姿态名。

全动作suite schema2要求24 clips、20动作条目、四向canonical idle、一份hair_hat manifest和runtime。runtime v1显式声明走跑世界速度、默认速度因子、stable-idle-v1过渡时长及每clip播放率/pose内事件；走跑时间仍由实际位移驱动。缺字段或事件不属于实际pose时拒绝。农事事件只写隔离评审journal，用instance/event/loop身份去重，无业务事务或存档。

`review.py all-actions-construction`已实现全包预检和既有试玩的全包模式，但真实24格资源尚未齐备，故目前没有正式全包review.json，不能把合成fixture当成可交付美术。原西锄四状态仍从headwear-construction入口回归；当前构建迁移及原Git恢复见 `art/characters/evidence/all-actions-v1/`。全包原生验收工具和实际接触验收仍待完成，旧西锄native入口不认证全包。

全24格原生输入冻结使用`all_actions_capture.py snapshot --suite <全包suite.json> --evidence /private/tmp/coastal-<全新目录> --observer <poses|world|timing|transitions|spatial|locomotion-timing>`。它先严格预检完整hair_hat包，绑定实际源/输出、构建工具、播放与观察脚本的真实资源引用闭包，以及由实际姿态数量推导的采集计划；随后用`verify-inputs --evidence <同目录>`复核。重新计算合同摘要也不能删掉输入或降低计划要求。此入口仅证明输入闭包，尚不产生完整美术/接触/发布回执；不得把输入检查或synthetic观察等同于真实全包验收。

前四种observer分别运行`res://tests/characters/capture_registered_candidate.gd`、`capture_registered_actions_world.gd`、`capture_registered_farm_timing.gd`、`capture_registered_transitions.gd`。传递`--evidence=<冻结目录>`与`--construction-suite=<同一绝对suite路径>`；poses用原港口试玩场景，其余用同一玩家的运动lane。Godot仍须传`--log-file /private/tmp/coastal-*.log`。`spatial`运行`capture_registered_spatial.gd`，保留原港口地形/树/柜台/门与真实碰撞；显式分场景设置起点，路径中使用实际输入和物理。隐藏评审UI只为避开世界截图遮盖，不改变人物或物体层序。原始GPU/物理/时序数据还须独立验证；农事timing观察器覆盖12农事×4情形，locomotion-timing通过`capture_registered_locomotion_timing.gd`另外覆盖8走跑×4情形；其变速调用公开50–100%速度控制，重启为松开到idle再继续原相位，低FPS允许跳过显示姿态。两者合计80情形仍须实际全包采集与原始数据重算；不能据此推导工具合法目标或港口空间通过。
