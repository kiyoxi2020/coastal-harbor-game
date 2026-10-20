# P05 逐格菜地与背景美术

- `concept-v1.png`：GPT 设计概念板，不是运行截图；原始提示词见 `prompt.md`。
- `production-atlas-v1.png`：内置 GPT imagegen 新生成的 4×4 透明图集；提示词见 `production-prompt.md`。参考概念板的风格，未复制外部游戏素材。
- 游戏素材：`godot2d/assets/farming-grid-v2/*.png`，16张。仅按固定格切图、alpha包围盒裁切和nearest缩放；原图保留。每张图的来源范围、尺寸、底根锚点与非阻挡碰撞元数据见同目录 `metadata.json`。
- 16×16 干湿土壤；种子、幼苗、生菜与番茄阶段；白/黄/粉花丛、草、碎石、苔石。植物统一底根锚点，番茄最高24逻辑像素。
- 土壤共享边缘由 `farm_soil.gdshader` 采样生成瓦片内部，外侧保留土边；不把草边重复拼在已连接的格间。
- 花草碎石共14处固定实例，位置可在 `harbor_exterior.tscn` 编辑；均为低矮非阻挡摆件，避开门口和主要道路。
- `runtime-lettuce.png`、`runtime-tomato.png`：最终 Apple M4 原生运行截图，非概念板。对应验收记录见 `docs/design/p01-p14/P05.md`。

生成方式：内置 GPT imagegen，无CLI/API回退。原始生成文件另保留于 Codex generated_images，游戏与评审不依赖外部路径。
