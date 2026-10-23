# P11 餐馆复业实施计划

依据：docs/design/p01-p14/P11.md、共享合同与获批P08单份基线3。用户授权继续下一项；保留全部P10未提交修改，不提交/推送/导出。

目标：通过现有持久化事务开放餐馆供货、注资、开业及营业状态，并完成14日账实和原生交互验证。

架构：life_rules负责开业命令，town_rules按日结指标转换状态，schema接受回执/事件；固定页面使用Journal实例与现有GPT界面贴图。街区餐馆为独立场景，固定美术/底座/交互点随实例移动，表现只读状态。

## 实施检查点

- [x] 后台先失败测试：空库存开业失败、重复请求幂等、两好日营业、两坏日降级/第三坏日关闭、保留资产补货恢复、写盘失败完整快照相等。修改life_rules/town_rules/state_schema；新增test_life_restaurant.gd。
- [x] 正式命令14日路径：day1买种播种、两次浇水睡眠、day3收获/采蛤蜊/供货/开业；源日3..16睡眠，第3/7/10日保存重载，检查精确资金/库存/食品历史、一次性迁移。新增test_life_fourteen_days.gd。
- [x] 界面先失败测试后接入：restaurant_page.tscn/.gd、Journal与harbor边界；供货六物品、数量/金额、个人注资、开业、原因与日报；键鼠逐层返回，失败不丢焦点。
- [x] 场景先建立验收：restaurant.tscn/restaurant_view.gd与街区实例；复用GPT建筑/人物，新增GPT招牌菜单炊烟图集；nearest、锚点、碰撞、交互点元数据；移动实例后相对位置和安全通道有效。
- [x] 主代理集成：相关回归、隔离档原生供货→开业→营业→重载/关闭恢复、截图目视检查，更新P11/总计划/PROJECT_STATE/HANDOFF。

验证命令：`godot --headless --path godot2d --log-file /private/tmp/coastal-P11-<suite>.log --script res://tests/<suite>.gd`；原生测试去掉headless。所有存档/private/tmp/coastal-*，不得触碰默认存档。

## 分工

主代理：场景/素材、集成与原生验收、进度记录。gpt-6.1-sol high（p11_rules）：经济状态机和持久化14日测试，因跨规则一致性需要。gpt-6.1-sol high（p11_ui）：Journal/世界入口/页面及定点测试，因跨模块焦点和空间边界需要。无重叠文件、无嵌套委派。

验收完成：14组1957项＋原生52项；证据见P11任务卡。所有写盘隔离，无提交/推送/导出；下一P12未启动。
