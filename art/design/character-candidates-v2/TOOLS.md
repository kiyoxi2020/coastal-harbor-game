# 候选目录工具

这组工具只负责候选文件、独立设计计数、版本绑定及原生总览。不会修改 catalog、正式角色、游戏场景或玩家存档，也不会写入用户认可。主代理负责 GPT 生成、分层语义与外观验收。

## 执行范围与计划

已授权设计：`catalog.json` 为唯一目录输入；Python 只读校验，Godot 独立 `SceneTree` 仅加载目录图片。先用临时目录构造失败用例，再实现验证；原生工具先交付源码，由主代理统一运行和检查截图。独占文件为 `verify_catalog.py`、`render_catalog.gd`、本文。没有修改其他脚本或场景。

## 校验目录

在项目根目录执行：

```sh
python3 art/design/character-candidates-v2/verify_catalog.py
python3 art/design/character-candidates-v2/verify_catalog.py --json
python3 art/design/character-candidates-v2/verify_catalog.py --digests
```

退出码：0=本工具覆盖的结构完整且无失效评审；1=数量、文件、兼容声明或版本绑定失败；2=目录读取/参数错误。`--digests` 仅打印当前散列，不执行完整验证，更不会创建通过记录。`--expected` 默认为10，只用于明确的小样诊断；最终全库验收使用默认值。

每类按 `design_id` 去重，未提供时回退到 `id`。四方向、配色、适配版、子层或组合不能增加设计数；同款变体必须共用 `design_id`。工具只能执行已经正确声明的设计归属，不能由图片自动识别“换色充数”。每类报告 `entries`、`unique_designs`、`complete_designs`、独立的 `statuses` 和 `review_states`。缺任一方向透明组件为 incomplete；rejected 不计入完整候选。缺review单独报告pending，候选文件齐全不等于外观通过。

每项必需字段：

- `id`、`design_id`、`template_id`、`template_hash`、`status`。
- `source`、`prompt` 和 `previews.{south,west,east,north}`；preview是完整穿戴图。
- `components.{south,west,east,north}`；body用整帧母版，其他类用原位透明层。单方向可为路径或内部子层路径数组，子层不另计设计。
- `hashes`：所有声明路径到SHA256的映射；所有路径相对项目根，禁止绝对路径和越界。额外声明的遮罩、配方、元数据文件也应写入该映射。
- `compatibility: {body_ids: ["body01"], pose: "standing_0"}`，与候选/拒绝/认可状态分开。所列body必须存在且template_id相同；跨体型应登记单独适配记录，不自动缩放。

`template_hash` 必须与兼容body记录的 `source` 文件当前SHA256相同。一个记录不能用同一个template_hash同时宣称兼容不同源母版。若母版配置或姿态登记另外存于文件，应在 `body_template`、`metadata`、`semantic_masks`、`recipe`、`native_config` 路径字段或 `hashes` 中显式登记，以便进入摘要。仅有template_id字符串不能绑定模板字节。

## 评审与摘要

按项可提供：

```json
{
  "review": {
    "status": "native_checked",
    "artifact_digest": "64位sha256",
    "evidence": {"art/design/.../native/page.png": "64位sha256"}
  }
}
```

`artifact_digest` 对以下对象以UTF-8、键排序、`ensure_ascii=False`、紧凑JSON序列化后取SHA256：`{category, candidate, actual_hashes}`。`candidate` 是排除 `review` 与 `status` 后的完整候选记录；`actual_hashes` 是源图、提示词、preview、component及所有声明文件的当前字节散列。`template_hash`、兼容体型、姿态、显示设置、遮罩及脚本/配置路径由此绑定。变更任一输入后，旧摘要会报stale；不要重新计算摘要后自动保留旧通过结论。

支持的review状态与人体管线一致：selected、registered、geometry_checked、swap_checked、native_checked、user_accepted、unverified、rework_required、rejected。项的 `status` 只允许candidate/rejected/user_accepted。使用user_accepted时，必须另有绑定的user_accepted评审和非空 `user_evidence`，其内容由主代理保存实际用户认可的出处；工具无法代替用户判断。

## 原生总览

以下为执行示例，`/absolute/path/to/godot`替换为本机Godot可执行文件：

```sh
/absolute/path/to/godot --path /Users/wyq/Documents/code/coastal-harbor-game/godot2d --log-file /private/tmp/coastal-catalog-native.log --script /Users/wyq/Documents/code/coastal-harbor-game/art/design/character-candidates-v2/render_catalog.gd -- --root=/Users/wyq/Documents/code/coastal-harbor-game --out=/private/tmp/coastal-catalog-native
```

不能加`--headless`。可追加`--category=hair`或`--per-page=5`定位类别。默认每类10候选一页，每候选四方向固定南/西/东/北；分别输出完整穿戴图页和透明组件页、明暗两背景。多子层组件逐层另出页，不在组件页合成人体，便于目视发现脸、手或肢体误入层。缺失图显示空槽并警告，不生成替代人物。标签仅显示id，模板和状态写日志，不由文字推断外观完成。

图像从磁盘原尺寸加载，nearest纹理过滤；只改变Sprite2D场景尺度，不改写贴图。无显示元数据时，每页采用同一个整画布缩放系数，不能据此比较真实身高或认定游戏尺度。可在候选 `display` 或其 `metadata` JSON的 `display` 提供 `{scale: 0.2371134, root_anchors: {south: [230,707], ...}}`，继承已登记模板的统一尺度/脚底锚点；四向不可各自拉伸。metadata中 `body_template` 用于日志明确模板。`--scale=...`可覆盖显示尺度作诊断，但大于卡片的图可能超出视口，截图不构成原尺寸局部验收。

输出仅限`/private/tmp/coastal-*`，包含PNG和`render-manifest.json`；清单记录目录/渲染脚本SHA256、实际加载文件SHA256、页面ID、背景和显示参数。清单是原生加载证据，不是最终review。主代理应完成明暗背景、东西侧轮廓、四向整体与必要原尺寸局部检查后，将具体证据哈希与配置绑定。总览不执行换装、碰撞或走路动画；也不运行玩法。

## 已验证与边界

Python临时fixture已覆盖10项：完整候选与待评审分离、缺方向组件、同design_id不增计数、rejected排除、文件散列变化、评审配置变更失效、母版源图变化、未知兼容体型、路径越界，以及缺证据的user_accepted拒绝。临时数据仅在`/private/tmp/coastal-*`。Python源码语法检查通过。Godot按分工尚未运行，需主代理做解析与原生截图检查。

结构检查不能判断语义遮罩是否混入眉眼、候选是否改脸、是否只换色或外观是否好看；原生加载截图也不证明可组合或用户认可。完整交付仍由人物管线的几何、视觉、逐槽切换和用户认可各自覆盖。

## 衣裤鞋领口与露踝修订

`build_wearable_candidates.py`使用扩展后的逐方向v3颈部解剖域，保护母版皮肤及低亮度下巴阴影；top05正面领口底与top07正面两侧额外保留小范围可审查patch域。颜色只在这些颈域辅助辨认源皮肤，红色上衣整体及其领口不会执行全局肤色删除。每方向metadata记录`neck_source_skin_leak_pixels`与`neck_dark_patch_leak_pixels`；它们证明所列检查没有残片，不能推导领口外观或用户认可。新源图仍需目视语义复查。

裤02与鞋02原稿在部分脚踝坐标同时露肤，细线有真实设计露踝，不能移动/拉长裤鞋或绘制补丁遮住。两件靛蓝材质仅在各自已限定踝域排除额外暗肤色；牛仔裤暗肤色需与亮肤色连通，保留分离的裤脚缝线。可见皮肤由原母版提供。该规则不泛用于棕皮鞋/工靴，短靴仍使用最高到y620的独立语义轮廓。

本轮临时测试共14项，含36个真实新上衣方向的领口残片回归、真实暗下巴/领口阴影/裤鞋踝皮肤，以及红领口保留、裙装连续性和靴筒保留。工具未运行Godot；改动后的原生总览与交叉换装证据由主代理重新生成，旧截图不能验收新纹理。

实际残片坐标与裤脚缝线保留点已写入`wearables-mask-policy.json.source_bound_regressions`，绑定对应源图SHA256；构造时会自动验证。源图换版后该组逐点回归会明确标为stale_source，不能沿用旧坐标结论。
