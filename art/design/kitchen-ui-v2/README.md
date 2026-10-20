# 厨房 UI v2 实施与验收

2026-10-21：已按批准方案实施，并完成用户九项反馈修正。三列滚动配方、固定详情、料理/加工分类、搜索、批次和逐层返回均接入真实游戏。菜品图标下移10像素；筛选开启显示“仅显示可制作 ✓”，关闭显示“全部菜谱”。

原料使用游戏现有 TradeItem 组件（蛤蜊、生菜等同源），产物使用GPT料理/肥料美术。每批实际产出1份；可制作彩色、不可制作灰色，无可制作/充足/单批产出赘文。扩展测试槽仅空框，无虚构菜名或图标。

## 资源与切分

- [批准概念](expandable-kitchen-concept.png)、[背景原图](background-original.png)、[控件原图](controls-original.png)。
- [切分脚本](slice_assets.py)、[切片元数据](slices.json)；生产资源位于 `godot2d/assets/ui/kitchen-v2`。
- 13个PNG切片；原图保留，矩形切分不重采样，九切边距写入StyleBox；锅从概念图切出并清除连通纸底及边缘碎片。像素资源nearest过滤。

## 原生验收

| 步骤 | 预期 | 实际与结果 |
| --- | --- | --- |
| 实际走入厨房，制作料理、加工肥料、返回背包并重载 | 原子扣料、每批1份、批次/分类/返回正常 | 34/34通过，[流程记录](runtime/flow-checks.json) |
| 查看料理卡、标题、搜索与材料 | 图标顶部留白，彩色/灰色正确，原料同源，无文字重叠 | 原生截图已检查，[料理画面](runtime/09-final-color-gray-and-header.png) |
| 开启加工筛选 | 含义明确，文字完整显示 | [加工画面](runtime/12-processing-available-filter.png) |
| 60空槽、中文搜索、10材料滚动 | 槽位空置、搜索正确、操作固定 | 原生流程通过；仅测试夹具，不增加正式配方 |

自动回归12组共467项通过，摘要见[记录](runtime/headless-summary.json)。布局/滚动后直接回归10和28项通过；最新文案/坐标修改后反馈10项再次通过。原生布局检查12/12通过，另见[布局记录](runtime/layout-checks.json)。

命令：`godot --path godot2d --log-file /private/tmp/coastal-kitchen-last-flow-native.log --script res://tests/test_kitchen_v2_native.gd`；布局脚本 `res://tests/test_kitchen_feedback_native.gd`。测试存档均在 `/private/tmp/coastal-*`，未使用玩家档。

未提交、推送或导出；未做跨平台、真人长时验收。每批1份后P08旧经济测算失效，需重新校准后再开始P10。
