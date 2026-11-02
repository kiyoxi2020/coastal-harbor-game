# godot2d旧资源清理分析（2026-11-03）

用户已确认V5主游戏Demo“效果ok”。本轮只分析，不删除、不改运行配置或冻结基线、不提交。

## 方法与边界

以project.godot→harbor.tscn为起点遍历场景/脚本/资源的res引用，得到330项保守依赖（含入口中的验证分支）；再核对tools、测试中的引用、字符串拼接、JSON动态加载、人物冻结基线与导出配置。未读取.godot缓存内容。体积按文件字节统计，含对应.import，不含Git历史、导入缓存或压缩收益。本轮没有删除后的运行或导出验证，因此下面是有引用依据的清理建议，不是已经完成清理的证明。

## A：可优先清理的旧贴图

当前运行与检查过的源码/测试未发现加载引用，共30张PNG及30份.import，2.429MiB。

| 范围 | 内容 | 体积（MiB） |
|---|---|---:|
| assets/farming-polish-v3 | hoe/water/harvest × north/south/east/west，共12旧单帧人物图 | 0.895 |
| assets/farming-polish-v3 | lettuce_young、grass、flowers_yellow、flowers_white、flowers_pink、flower_edge，共6图 | 0.135 |
| assets/visual-polish-v6 | flowers_yellow、flowers_white、flowers_pink、flower_edge，共4图 | 0.006 |
| assets/ui/crafting-v1 | quantity、utility、kitchen_badge、recipe_normal、recipe_selected、background、disabled、confirm，共8图 | 1.393 |

不要整目录删除：farming-polish-v3仍提供土壤、种子、幼苗、成熟作物、石头和工具栏等运行图；visual-polish-v6的grass及三种海产仍在用；crafting-v1的clam_salad、snail_stew、marine_fertilizer是实际物品图标。

`resources/player_action.gdshader`（485字节）是旧人物弯曲变形着色器，未发现引用，可作为旧代码清理项；现行`player_mask.tres`及遮挡shader必须保留。

`assets/farming-polish-v3/pose_registration.json`未发现读取者，属于旧单帧注册；`metadata.json`混合记录现行与旧图及已退役源路径。前者可随旧人物单帧退役，后者建议删旧条目、保留仍有意义的现行布局/锚点数据，而不是整目录或元数据一概删除。

## B：可退役，但须先迁移依赖

### V4运行包：218文件，2.453MiB

`assets/characters/integrations/adult-v4-tank-visible-r001/`（108PNG、108.import、manifest）及`resources/player_body_v4_frames.tres`已经不被默认主角使用，但仍有：

- `tools/characters/tests/runtime_art_fixture.py`：PACKAGE、FRAMES、runtime_png路径白名单仍绑定V4，其他人物测试用它建立真实图像夹具。
- `tests/test_action_registration.gd`：仍校验V4的256×224画布和123/201根点。
- `tools/characters/runtime-baseline.json`：仍冻结110项V4运行文件、SpriteFrames引用及local_integrations。

建议先迁移上述测试到已纳入交付范围的V5运行资源及260×228、125/201几何，保留全部反例与RGBA测试；核对110项旧冻结文件后精确撤销对应基线项，再删除V4运行包。不可只删文件或为过门禁重采基线。本任务不涉及art/characters中的V4制作母版及独立动画档案。

### 32像素花草：8文件，0.009MiB

`assets/flowers-v7/32/`四图及.import仅供旧比较，但`tests/test_flowers_compare_native.gd`循环[32,48]动态加载它们，简单全文路径搜索容易漏掉。需先将一次性32/48评审退役或改为可选入口，保留48版生产回归。

### 室内pilot.json：暂不删除

`assets/house-interior/pilot.json`虽不在默认静态入口闭包，仍被cottage_asset_preview、test_cottage_assets、test_cottage_runtime及cottage_art动态读取，含碰撞与锚点验收信息。保留；如要退役需另迁移测试合同。

## C：过程产物与缓存

- 六个verification目录中仅剩六份测试JSON，共0.007MiB；是测试输出，可清理，生成它们的测试代码不随之删除。
- 排除.godot后发现5个.DS_Store，共0.068MiB；是Finder元数据，可清理，但Finder可能重新生成。
- .godot是可重建缓存，不计作旧资源，也未扫描其内容；不建议在Demo/编辑器运行中为清资源顺带清缓存。
- assets下prompts.md是小型制作文字总结，按项目规则可保留；许可证OFL.txt及licenses不删。

## D：名称旧但仍在使用

- `assets/player.png`→`resources/player_frames.tres`→`scripts/atlas.gd::player_frames()`→`scripts/ui/journal.gd:349`：手账头像仍使用旧人物。若希望头像同步V5，这是独立的小迁移；做完并检查其余引用后才能退役旧图，不在本轮自动修改。
- `assets/player-unified-v4/walk_north_0.png`及`walk_west_0.png`：餐馆顾客的真实纹理，restaurant.tscn直接引用。
- `assets/flowers-v7/48`：当前花草；`environment.png`、environment-v2、tree-set-v4、Noto字体、现行UI等均有主入口依赖，不能凭版本号删除。
- `dev/characters`和`tests/characters`是通用试玩/校验源码，旧名称不代表旧资源；不批量删目录。

## 导出影响与执行建议

export_presets.cfg使用all_resources，仅排除verification目录及少量文档；主入口不使用不代表导出不携带。V4运行包、旧UI贴图等有被导入/导出纳入的可能。具体导出收益必须在清理后检查PCK清单，不能用本次静态依赖分析声称已排除。

建议顺序：先A和C；再迁移V4测试夹具及基线、退役V4运行包；最后处理旧花草比较入口。A+B约4.89MiB，额外过程JSON/Finder元数据约0.076MiB；实际释放工作区字节，不减少Git历史体积。删除后需完成504人物测试、check.py、V5 verify-runtime、主玩家/农事/物品图标/花草/室内相关检查及原生目视检查；导出PCK后用包内入口验证。所有存档均隔离到/private/tmp/coastal-*。

## A组精确文件清单

以下PNG均连同各自`.import`清理，不包含其他同目录文件：

- `assets/farming-polish-v3/hoe_north.png`
- `assets/farming-polish-v3/hoe_south.png`
- `assets/farming-polish-v3/hoe_east.png`
- `assets/farming-polish-v3/hoe_west.png`
- `assets/farming-polish-v3/water_north.png`
- `assets/farming-polish-v3/water_south.png`
- `assets/farming-polish-v3/water_east.png`
- `assets/farming-polish-v3/water_west.png`
- `assets/farming-polish-v3/harvest_north.png`
- `assets/farming-polish-v3/harvest_south.png`
- `assets/farming-polish-v3/harvest_east.png`
- `assets/farming-polish-v3/harvest_west.png`
- `assets/farming-polish-v3/lettuce_young.png`
- `assets/farming-polish-v3/grass.png`
- `assets/farming-polish-v3/flowers_yellow.png`
- `assets/farming-polish-v3/flowers_white.png`
- `assets/farming-polish-v3/flowers_pink.png`
- `assets/farming-polish-v3/flower_edge.png`
- `assets/visual-polish-v6/flowers_yellow.png`
- `assets/visual-polish-v6/flowers_white.png`
- `assets/visual-polish-v6/flowers_pink.png`
- `assets/visual-polish-v6/flower_edge.png`
- `assets/ui/crafting-v1/quantity.png`
- `assets/ui/crafting-v1/utility.png`
- `assets/ui/crafting-v1/kitchen_badge.png`
- `assets/ui/crafting-v1/recipe_normal.png`
- `assets/ui/crafting-v1/recipe_selected.png`
- `assets/ui/crafting-v1/background.png`
- `assets/ui/crafting-v1/disabled.png`
- `assets/ui/crafting-v1/confirm.png`
