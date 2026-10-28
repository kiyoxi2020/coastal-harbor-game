# 人物资源目录迁移实施计划

**Goal:** 将当前最终人物资料迁入按身份组织的 `art/characters`，保持现有渲染与能力，精简失败稿/重复证据，历史由固定Git版本恢复。

**Architecture:** 保留已验证动作与样例字段语义；新清单增加 `resource_root: art/characters`，其中资源路径均相对统一库根。Godot加载器显式解析库根，未知根/越界路径拒绝。原样例创建时状态不作为新认可；轻量认可通过旧版本/新纹理与几何时序等价映射绑定。生产角色不切换。

**Tech Stack:** Python标准库/Pillow、现有Godot 4 GDScript试玩。

## 授权与全局约束

- 用户已确认方案B及精简保留策略；普通失败稿与大量重复过程证据在Git可恢复、现行依赖迁出后可移出工作区，不清除Git历史。
- 仅最终资源及必要原图/prompt/部件/mask/注册/配置在新库保留；仍被最终稿引用的失败参考图视为必要输入保留。
- 制作合同仍以docs/design/character-art-pipeline.md为准；仅更改存储附录，不改身份/整帧注册/款式计数/遮挡合同。
- 未提交的两份设计文档保留。基线为379a9bc。未获新提交/推送指令，本次不提交或推送。
- 像素、源尺寸、根点、时序、层序、原认可范围保持；新schema/hash是新artifact，不能改写旧认可再声称旧SHA有效。
- 日志和测试证据用/private/tmp/coastal-*；不读玩家档、不读.godot缓存。

## 责任边界与接口

- 主代理：`tools/characters/`迁移/核验工具、新动态sources/templates/parts/recipes/builds/reviews/evidence/migrations数据、原生集成验收和旧目录清理。
- 静态独立任务：Astra已只读交付/private/tmp/coastal-static-character-inventory.json；后续实现者仅负责静态导入工具与测试，不与主代理共享脚本。
- Godot独立任务：仅godot2d/dev/characters与相关测试迁移、全仓res://角色试玩路径引用更新。不能改art/characters数据或主代理工具。
- 新路径固定：`art/characters/builds/locomotion-r001/manifest.json`、`builds/run-r001/{candidate,run-garments,run-diagnostics}.json`、`reviews/{farming,wardrobe,headwear}/catalog.json`。
- 新rooted manifest的inputs和嵌入file/source/registered_file等路径相对art/characters根；catalog entry的sample/candidate与parent_sample仍为仓库相对路径（现有公共合同）。
- Godot兼容旧格式仅供独立合成fixture测试，活动入口只采用新根。不得运行时找不到就回退旧艺术目录。

## Task 1: 西锄与动态资源迁移工具

- [ ] 建立失败测试：新库缺失时导入/引用核验失败；越界路径、未知根、缺资产和哈希错拒绝；同名不同内容不可合并；普通源重复引用不计新款。
- [ ] 实现 `tools/characters/migrate_layout.py`：从基线Git或核验原文件读取，生成显式旧→新SHA映射，先西锄v3+父配方+必要源，再其余活动样例。源放sources，部件与mask归parts/模板；完整帧归builds；轻量认可归evidence；源码工具不复制入新美术。
- [ ] 为每个源/设计/适配/配方生成可读JSON索引；复用按完整SHA及原身份别名记录，不丢来源。新metadata必须记录旧path/SHA/基线提交，不能暗示原旧JSON已是新合同。
- [ ] 新review catalogs保留scope和样例数：发帽4、衣物5、农事24；walk/idle A/B40帧与run A/B实际帧范围保持，缺资源拒绝。
- [ ] `python3 -m unittest discover -s tools/characters/tests`，旧样例与新样例逐纹理SHA/pose/时长/画布/root/scale核验；旧失败见证六点与修复结果保持。

## Task 2: Godot路径与显式库根解析

- [ ] 新增rooted fixture失败测试，再增加共享资源根解析器；只能接受库根art/characters，不接受绝对根或..。
- [ ] 迁移所有现行character dev .gd/.tscn/.uid到godot2d/dev/characters；仅更新引用/入口路径与加载目录，不改播放行为。
- [ ] 各loader用显式rooted base解析inputs和纹理；locomotion新manifest入口替换原baked定位，run三清单的SHA关联继续验证。
- [ ] 保持旧synthetic fixtures的字段拒绝测试；将依赖历史已退役试验的集成检查改为当前真实资源或明确退役到Git恢复记录，不保留活动失效测试。
- [ ] 实际新库加载、五衣物/四发帽/24农事及走跑回归必须通过。

## Task 3: 静态资源与母版

- [ ] 基于Astra清单建立导入/映射测试，保留60候选的candidate与静态兼容范围，母版selection仍精确指眉毛v3。
- [ ] 必要v2/v3生成参考、授权mask、元数据、pants08真实依赖的skirt-waist参考保留；无动态反向依赖的普通失败图由Git恢复。
- [ ] 迁移最终静态catalog、源与部件到sources/templates/parts，gallery归reviews；不得把完整穿衣候选当隐藏身体或动态适配。

## Task 4: 等价、原生与精简清理

- [ ] 输出migrations/2026-10-resource-layout/{inventory,path-map,verification}.json，旧字节均核对基线blob；非基线内容不自动删除。
- [ ] 在/private/tmp生成采集前新合同，原生检查新入口真正读取新catalog、发帽四状态/动作、衣物与农事/走跑实际显示及切换；检查未受影响生产主角场景加载。
- [ ] 查看原尺寸与面板截图，重点西锄第三帧耳后和发帽切换；新旧像素与配置一致则关联原视觉认可，不重新要求同一外观认可。
- [ ] 全仓扫描活动脚本/场景/入口/规范中的旧制作路径；provenance/迁移记录及明确历史叙述可保留旧字符串，活动输入不能依赖旧根。
- [ ] 所有需移出旧人物制作目录的文件，先核验Git379a9bc可恢复，再移出；不删在用旧生产player-unified-v4，相关顾客引用保留到未来完整发布切换。

## Task 5: 文档与未来覆盖

- [ ] 更新唯一规范第8节、新根README、可运行统一review入口和源/款式/适配导航。
- [ ] 为当前体型×动作×方向×实际配方生成分层覆盖表，区别source/adapted/baked/native/user认可，缺口不填假资源。
- [ ] PROJECT_STATE/HANDOFF/开发计划写本次迁移完成与验证边界；保留现有未验证项；关闭Paseo本次任务，不自动开始补新美术或P12。

## 验收命令

```sh
python3 -m unittest discover -s tools/characters/tests
python3 tools/characters/migrate_layout.py verify
/Applications/Godot.app/Contents/MacOS/Godot --headless --path godot2d --log-file /private/tmp/coastal-character-layout-actual.log --script res://tests/characters/test_character_headwear_actual.gd
/Applications/Godot.app/Contents/MacOS/Godot --path godot2d --log-file /private/tmp/coastal-character-layout-native.log --script res://tests/characters/test_character_layout_native.gd -- --evidence=/private/tmp/coastal-character-layout-native
git diff --check
```

上列待建脚本均由对应任务实际实现后执行，当前不声称存在或通过。原生数据由实施时支持的实际入口采集；测试不使用玩家真实存档。
