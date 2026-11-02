# 人物资源：当前入口

最终美术实际归档在parts；只保留动画所需数据。制作合同以[唯一规范](../../docs/design/character-art-pipeline.md)为准，执行约定见[AGENTS](../../AGENTS.md)。先读本页、CURRENT及根PROJECT_STATE/HANDOFF，再读具体配方；不要遍历旧历史寻找现行入口。

| 链路 | 当前数据与入口 | 范围 |
|---|---|---|
| 主游戏 | godot2d/scenes/harbor.tscn → player_body_v5_frames.tres → adult-v5-pixel-visible-r010运行包 | V5像素风主角，原餐馆顾客实际两图保留；本地接入，未授予完整发布 |
| V4试玩 | `python3 tools/characters/review.py body-actions` | 完整24方向动作108显示帧；两套严格配方/build r002 |
| V5试玩 | `python3 tools/characters/review.py body-pixel-v5` | 已认可r012像素风；两套严格配方/build r010，已接入主游戏默认主角 |
| 严格构建 | `python3 tools/characters/build.py build <recipe.json> --output <新目录>`及`verify <目录>` | 唯一construction-v1入口，review-only，不另写批次播放器 |

实际图像：[V4](parts/body/adult-v4/r001/atlases/)、[V5](parts/body/adult-v5/r012/atlases/)。身份/锚点/时序见各layout、template和recipe；认可绑定见各animation-equivalence与archive。原稿/生成历史不再是强制输入，sources仅保留独立完整动画快照与source/packing合同。templates为必要canonical/动作定义，recipes/builds为本地严格制品，不能代替parts中的实际PNG。

[CURRENT](CURRENT.md)、[catalog](catalog.json)、[coverage](coverage.json)只列现行V4/V5。旧静态候选、旧衣柜、固定发帽及v1/v2/v3制作链已按用户授权退役，不再提供其试玩资产或承诺动态混搭；通用接口仍按唯一规范扩展。

运行校验：`python3 tools/characters/godot_integration.py verify-runtime godot2d/assets/characters/integrations/adult-v5-pixel-visible-r010/manifest.json`，不需本地制作源；`verify`为包含制作源重建的独立严格操作。必需门禁仍为全套人物unittest与check.py，源码/配方/动画改动后按AGENTS执行；视觉变化须实际原生验收。

本地归档不等于Git纳管；art制作/试玩包默认忽略，只有主游戏实际运行依赖可提交。旧媒体已清理，过程仅留[文字报告](../../docs/reviews/2026-11-02-resource-cleanup-executed.md)。
