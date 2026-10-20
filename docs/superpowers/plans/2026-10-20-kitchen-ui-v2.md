# 厨房UI v2实施计划

**Goal:** 落实已批准的可扩展菜谱网格/详情与GPT美术，原料复用现有同源组件。
**Architecture:** RecipeCatalog静态分类 → 浏览模型负责筛选/批数候选 → 可复用RecipeCard/IngredientRow → CraftPage协调真实控件与ActionService；Journal将厨房键盘路由交给页面。
**Tech Stack:** Godot4.7.1、GDScript、.tscn、GPT image_gen、Pillow矩形切图。

## 约束

- 保留现有P09工作，不提交/推送/导出或开始P10。
- 只用实际两料理/一加工；24/60配方与多材料仅测试夹具。
- 1..20批、候选扣料后容量、原子保存/失败不变；不改存档版本。
- 原料使用res://scenes/ui/components/trade_item.tscn，绝不从概念图重切蛤蜊/生菜等原料。
- GPT无字图集切分后连接真实控件；边距不超过目标控件半高，nearest。
- 原生隔离目录/private/tmp/coastal-kitchen-v2-native-save；日志/private/tmp/coastal-kitchen-v2-*.log。

## 执行顺序

- [x] 新建test_craft_browser.gd与test_kitchen_v2.gd，运行失败，覆盖分类/搜索/空结果、最大批数含腾格、60条浏览、动态材料/同源图标、制作与失败、键盘区域/逐层返回。
- [x] 新建craft_browser.gd提供filtered_ids(data,definitions,category,query,only_available)、max_batches(data,recipe_id)；RecipeCatalog加category与all()。仅纯候选查询，不修改库存。
- [x] 新增recipe_card.tscn/.gd、ingredient_row.tscn/.gd，静态节点含TradeItem图标，RecipeCard用recipe_id绑定数据。页面3列GridContainer包ScrollContainer。
- [x] GPT生成背景和控件原图，slice_assets.py与slices.json保存每个裁切矩形/缩放与9切边距，检查透明/边缘/文字安全区。
- [x] 替换craft_page.tscn/.gd，搜索/分类/过滤，右侧动态材料与固定操作区；Journal厨房键盘专用路由，E先进入操作、Esc返回菜谱，输入框隔离WASD。
- [x] 跑browser/UI/crafting/journal/menu/scene合同直接回归；更新旧厨房测试至新页面行为，不保留过期固定按钮断言。
- [x] 原生厨房真实路径制作、缺料/最大批次、加工、背包/工具同源、24/60条滚动、10材料固定按钮、键鼠/中文输入/逐层返回；检查截图并修正切分/拉伸/遮挡。
- [x] 更新规格、P09、证据README、总计划、状态与交接；最后diff/link/切图再现检查。不自动进入下一任务。

## 2026-10-21 厨房 v2 实施与反馈修正（当前有效）

已实施获批的左侧三列滚动菜谱、右侧固定详情、料理/加工分类、搜索、批次与键盘返回。GPT原图已合理切分接入真实控件；原料复用游戏现有图标。恢复透明锅图标，排除标题/搜索/帮助文字重叠；可制作彩色、不可制作灰色，无状态赘文；每批实际产出1份；测试扩展槽仅空框。最新反馈：菜品图标下移10像素，筛选改为“仅显示可制作”。

本轮自动回归467项通过，后续布局/滚动调整的直接回归10/28项通过；原生截图与最终检查见 `art/design/kitchen-ui-v2/README.md`。使用 `/private/tmp/coastal-*` 隔离存档，未提交、推送或导出，未做跨平台或真人长时验收。最新原生完整流程34/34、布局12/12通过，截图已检查。

每批1份使旧P08经济基线失效；下一步先重算P08价格/供给/餐馆收支，再进入P10。本任务不自动启动下一阶段。下文旧状态仅为历史。
