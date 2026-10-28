# 人物资源库

这里是现行人物**制作与评审**入口。正式游戏仍使用既有 `player-unified-v4`；当前没有批准的新人体正式发布，不会缺帧时回退或混用两套模型。

唯一制作规范：[character-art-pipeline.md](../../docs/design/character-art-pipeline.md)。当前导航见 [catalog.json](catalog.json)，实际范围见 [coverage.json](coverage.json)。静态60候选仍为候选，不能据此推定动态兼容。

## 查找资源

| 内容 | 位置 |
|---|---|
| 当前成年母版 | [template.json](templates/adult-standard-v1/template.json) 与 [selection.json](templates/adult-standard-v1/selection.json) |
| 动作、方向与姿态 | [motion-set.json](templates/adult-standard-v1/motions/review-motion-v1/motion-set.json)，下设六类action与四向poses |
| 衣裤鞋、头发、帽子 | `parts/<design-id>/design.json`；按体型/动作集的adaptations查view、pose-map和真实接口 |
| 最终原图、提示词、必要参考 | `sources/<source-id>/source.json`；保留完整原分辨率，来源别名与旧SHA在migrations记录 |
| 实际组合和输出 | `recipes/`、`builds/`；完整帧不是可任意拆换的隐藏身体 |
| 静态候选 | [静态图库](reviews/static-candidates/gallery.html) 与 [static-index.json](static-index.json) |
| 分范围原认可 | `evidence/<scope-id>/acceptance.json`，保留原话、范围、Git位置、旧新版本绑定 |
| 迁移与清理核验 | `migrations/2026-10-resource-layout/` |

款式ID、体型ID、pose、view与配方各自独立。`original-*`是保留作用域的旧配方标签，不能仅凭同名推断为一个通用款式；资源ID数量也不是独立生图或新款数量。

## 统一试玩入口

在仓库内运行；也可双击 `tools/characters/review.command`，默认西锄发帽。

```sh
python3 tools/characters/review.py headwear
python3 tools/characters/review.py wardrobe
python3 tools/characters/review.py farming
python3 tools/characters/review.py locomotion
python3 tools/characters/review.py static-candidates
```

headwear为四个动作/方向×裸头/短发/草帽/发帽；wardrobe为五个代表性配方；farming为24组；locomotion为四向走跑与两上衣。新源与贴图路径显式绑定统一库根，缺资源或哈希不符直接拒绝，测试及试玩不读写玩家存档。

## 构建门禁

后续新配方统一使用[严格配方示例](recipes/wardrobe-hoe-west/r002.json)，通过 `tools/characters/build.py build` 构建及 `verify` 复核；完整字段与命令见[工具说明](../../tools/characters/README.md)。旧r001抽样配方保留原范围，不能复制为新的无合同配方。

构建必须绑定真实母版/动作/variant、部件、来源、mask、时序与层序。仅接受已支持的整帧接口和模板一致的整帧注册，缺能力直接报错。结果仅供评审，正式发布仍须完整动态/原生/接触和用户认可；已有迁移回执不能给新构建授予认可。

提交评审前运行 `python3 tools/characters/check.py` 与全套人物工具测试。生产人物依赖冻结在runtime-baseline；不能靠更新白名单绕过失败。详见AGENTS中的人物构建约定。

## 后续扩展

- 新动作放入当前体型动作集的 `actions/<action-id>/<revision>/`，登记真实pose、时序、根点与所需能力。
- 新款放入 `parts/<design-id>/`；只为实际变化的姿态补view，沿pose-map复用相同投影。ownership、coverage、occlusion保持不同含义。
- 新体型建立自身template比例与锚点，仍沿同一合同；不能缩小成人或分叉另一套播放器。
- 新配方先声明required actions与实际部件修订，再生成新build及评审记录；不覆盖已认可源与旧输出。
- 本库包含完整穿衣参考及已完成的部分分层接口。目录可扩展不表示现有范围固定的试玩能零代码执行任意新动作；能力缺口按coverage逐项补齐。

此次没有扩画新动作、遍历全衣柜或切换生产角色。后续先补首个实际生产配方的缺口，再统一迁移全部生产角色，不能只换走路而保留旧模型耕地。

## 留存与恢复

工作区保留最终采用版本、可编辑/可重建所需的源、prompt、部件、mask、注册和配置，以及轻量认可与少量代表图。普通失败稿和重复过程资料移出工作区，历史主要由Git保存，不另建整库archive副本。

旧布局固定在 `379a9bc`，迁移清单记录完整commit与旧路径/SHA。查看单个历史原件：

```sh
git show 379a9bc:art/design/character-motion/adult-standard-v1/headwear-sampling-v1/catalog.json
```

精确重跑旧工具时使用独立历史checkout；不要把旧工具或旧路径恢复到当前活动库。导入迁移工具是对该Git基线的适配器，不是后续美术编辑器，重新运行导入不得覆盖未来新增资源。

未入Git的旧过程资料先暂存在 `/private/tmp/coastal-character-layout-untracked-hold`，清理记录列出原位置与哈希；它们没有被当作最终资源，也未被静默删除。原生完整采集同样留在本次 `/private/tmp/coastal-character-layout-native`，库内只保留其验证回执、范围摘要和代表图。
