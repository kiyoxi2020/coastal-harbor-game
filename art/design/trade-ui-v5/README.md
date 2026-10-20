# GPT贴图版交易UI（v5，2026-10-20）

用户要求直接使用GPT生成的美术替换v4程序绘制外观。本目录保留两张GPT原图，参考art/design/trade-ui-v4/final-design-original.png生成；不是把程序截图冒充GPT。

- background-original.png：无字无物品的纸面/木框/渔网/浮漂/绳结，RGBA透明边缘。
- controls-original.png：3×3空白控件图集，依次为普通/选中/悬停格、普通/选中标签与确认按钮、小按钮、输入框、金币。
- slice_assets.py：仅RGBA矩形切图，不重绘、不降采样；运行`python3 art/design/trade-ui-v5/slice_assets.py`重建。
- slices.json：源区域与背景框锚点。运行贴图位于godot2d/assets/ui/trade-v5。

实际界面使用原始背景TextureRect和切图StyleBoxTexture；所有数字、中文与交互均为Godot控件。场景海产/作物不在本次重绘范围，继续同源显示。切图不包含文字或示例金额。nearest过滤，未将图集作为一整张静态商店截图。

背景在920×640逻辑面板上对齐：原始frame(112,48,1306,912)，完整贴图Rect(-79,-34,1082,719)，允许渔网绳结伸出面板边缘；操作控件仍使用既有坐标。商品格6列3行不改变容量与交易规则。

runtime-buy.png / runtime-sell.png是当前游戏实际渲染，非GPT设计稿；完整交互证据另见runtime-sell-success.png。
