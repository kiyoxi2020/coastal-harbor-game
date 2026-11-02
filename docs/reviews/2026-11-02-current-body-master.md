> 2026-11-02清理说明：所述历史制作媒体和原生过程文件已按用户授权删除，旧数据路径已退役，本文仅保留文字结论；当前数据与验证见[执行报告](2026-11-02-resource-cleanup-executed.md)。

> 后续纠正：此前仅放归档清单，未遵守最终图片位于body的约定。现已补齐 `parts/body/adult-v4/r001/atlases/` 的9张最终PNG与layout/manifest，当前归档升级为archive-r002；164帧原像素/姿态/时长完全等价。下文r001为上一阶段记录。

# 现行人物制作母版归档与替换

按用户“归档当前人物，替换之前的母版”，2026-11-02将Q27=A认可的男性背心短裤设为现行制作母版。

## 入口与归档

- `art/characters/catalog.json.selected_template`：由`adult-standard-v1`改为`adult-standard-v4`。
- `body_source_archive`：[parts/body/adult-v4/archive-r001.json](../../art/characters/parts/body/adult-v4/archive-r001.json)，绑定624项SHA依赖，包括完整源图/提示词、整帧注册、四个pack、两套严格构建、Q27认可及最终r002原生证据。
- [制作入口](../../art/characters/parts/body/adult-v4/README.md)、[CURRENT](../../art/characters/CURRENT.md)、人物库README及唯一制作规范同步。`reviews.body-actions`已列入catalog。
- 四向六动作24能力108身体帧，另56农事带工具表现；身体与带工具两套构建各108帧。

旧v1外观、v2灰色长袖长裤及v3独立idle保留历史来源与冻结依赖。旧灰色归档本身未覆盖，旧README明确已被替代；后续新衣物从v4同姿态身体/注册开始，不继承旧衣物或mask兼容性。

本次修改选择与归档元数据，未改新母版原图、模板、时序、recipe或build字节。其采集时candidate/review-only字段保持，以外部catalog选择和归档表达当前身份，避免重写历史证据。制作母版与默认游戏独立：游戏仍绑定v2；未修改runtime-baseline、生产发布或存档，也未提交/推送。

## 验证

两套严格build及四个pack复核通过；归档624项SHA、归档digest和catalog选择一致。旧归档、runtime-baseline与player_body_frames.tres对HEAD字节一致。

发现原先严格包内新增6个Finder `.DS_Store`（idle源包2个、既有游戏接入包4个），已原样移动到 `/private/tmp/coastal-master-archive-finder-metadata/` 并保存清单，未改艺术资源或放宽校验。

490项人物测试通过（276.701s）；check通过59严格配方、53严格构建、9冻结旧配方、1既有游戏接入。[验证记录](tank-actions-v1/master-replacement-verification.json)。本次无像素/时序变更，沿Q27已绑定的r002原生证据；没有重新生成或录制人物。
