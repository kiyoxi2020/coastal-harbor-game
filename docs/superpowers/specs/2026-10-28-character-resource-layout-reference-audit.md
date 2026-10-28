# 人物资源目录重设计：引用与迁移约束核对

状态：设计输入，未实施迁移。核对基线：`379a9bc`，2026-10-28；统计排除 Python 缓存，不读取 `.godot/`。本文不替代 `docs/design/character-art-pipeline.md` 制作规范。

## 1. 目录现状

仅按文件大小及后缀统计，未重新审美术或逐图判重：

| 现有根目录 | 文件数 | 约 MiB | 当前职责混合情况 |
|---|---:|---:|---|
| art/design/character-motion | 7516 | 3200.7 | 动作母版、衣物/发帽抽样、修订、源、工具、烘焙及原生证据 |
| art/design/character-candidates-v2 | 1164 | 192.3 | body/hair/hat/top/pants/shoes静态候选及第二套交换 |
| art/design/character-bodies | 83 | 29.2 | 已选母版、修订、登记 |
| art/design/character-head-proof-v1 | 46 | 12.7 | 早期头部试验/脚本/原生 |
| art/design/character-clothing-proof-v1 | 88 | 25.8 | 早期衣物试验/分层/原生 |
| art/design/character-library-v1 | 11 | 6.1 | 早期人物库试验 |

`character-motion/adult-standard-v1/` 目前有13个一级制作单元：locomotion、walk/run单侧proof、四向run、三类农事单侧proof、南向浇水/西向长袖proof、农事四向/衔接、wardrobe/headwear sampling。

这既包含现用资源也包含历史失败、已冻结成功候选和工具副本，不能仅按目录名带proof判为可删除历史。

## 2. 实际引用链

- `headwear-sampling-v1/catalog.json` 指向4个不同动作/方向的样例，其中run-east指向v5，hoe-west指向ear-v3，另两组仍在原样例目录。
- headwear sample以`parent_sample`及其SHA引用对应wardrobe样例；每个sample还声明大量相对`inputs`。v5为282项，ear-v3为290项。
- `wardrobe-sampling-v1/catalog.json`有5个样例，而`farming-four-directions-v1/catalog-color-v2.json`有24个clips。它们的结构、scope和能力覆盖不同，不能只改名字就合并成同一能力清单。
- 只按9个活动headwear+wardrobe样例的manifest声明统计：1620条不同输入路径，1311个不同SHA，208组SHA出现在多个路径。该统计含空mask、相同prompt等，不等于208组有价值美术冗余，更不意味着可以删除任何重复文件。
- ear-v3原生快照记录1458项显式sample依赖，并绑定farming/headwear/wardrobe/ear-v3共4个实际校验工具SHA。
- 至少82个动作目录内`.py`或`.command`命中`parents[N]`、`../`或旧目录字符串。例：ear-v3与hoe-v2的`ROOT=P.parents[6]`，启动器沿7层目录定位工程。该数字是文本定位结果，不是完整动态调用图。
- JSON路径、sample/catalog哈希、原生脚本与工具哈希、输出哈希和原生时序构成冻结证据；用户认可还绑定确切sample/native/receipt SHA。

## 3. 正式运行边界

- `godot2d/scenes/actors/player.tscn`使用`godot2d/resources/player_unified_frames.tres`；后者仍引用`res://assets/player-unified-v4/`。
- `godot2d/scripts/player_tool_action.gd`在同一AnimatedSprite2D上播放hoe/water/harvest，依赖明确动画名和完成回调。
- `godot2d/scripts/player.gd`以当前动画纹理集合计算门遮挡范围。目录改造不能悄悄改变纹理尺度/根点/动画名/透明轮廓或绕开门遮挡。
- 餐馆场景还用旧模型两个方向的纹理作为顾客；正式迁移需覆盖这些实际角色，不能只换主角后删除旧模型。

目录整理与正式角色切换是两个验收阶段。当前旧正式资源在新发布全覆盖前仍须可运行；这不构成批准长期维护两套发布模型。

## 4. 必须写入迁移方案的规则

1. 源文件完整保留：GPT原图、prompt、失败稿、锚点、ownership、coverage、occlusion与时间轴分别有出处。ear-v3是两份真实发源的二值选择，其两份ownership不能简化成一个含糊的source字段。
2. 同一动作姿态可以指向相同view；目录不要强迫按动作或帧复制同一服装PNG。保存款式数、视图数、姿态数、配方数的区别。
3. 工具现行实现集中维护；证据中的工具副本仅为冻结追溯，不作为新任务默认调用入口。
4. 不对冻结sample/report/receipt/acceptance执行全局替换。旧证据保持原字节，以历史Git版本/旧布局快照复现；新目录建立单独映射与迁移回执。
5. 新索引和新manifest是新artifact，即使美术像素相同也需明确来源。旧认可保留原范围；通过精确姿态、像素、几何、时序、层序及依赖映射证明迁移关系，不能把旧receipt冒充新合同验证。
6. 原生验证按变化决定：路径/描述迁移先做完整性与等价核验、新入口原生冒烟；尺度/根点/层序/动画/播放逻辑变化则重新验证受影响行为和画面。仅目录迁移不要求重新认可已证明等价的外观，也不宣称全新能力已通过。
7. 迁移失败应可整体回退该批，保留可用入口；缺资源与无法解析的ID显式报错，不运行时回退旧模型。离线旧格式导入器应有边界和退出条件。
8. 正式发布只包含实际声明且验证的角色配方及其依赖；源、失败稿、全部历史原生截图、制作工具不进入正式导出。

## 5. 本轮范围

主代理负责本核对；用户指定的`gpt-6-astra/high`子代理独立设计目标目录与扩展组织，选择理由为跨资源合同、历史证据与运行依赖的一致性设计。仅生成设计文档；实际文件迁移、加载器改造和后续覆盖完善必须等用户确认目录方案后执行。当前不提交或推送。
