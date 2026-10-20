# 全镇示意图＋区域详情验收

2026-10-20，基线866cbeb，Godot 4.7.1 / Apple M4 Compatibility。方案已批准并实现，画面已由主代理查看，最终用户美术验收尚未进行。源码未提交/推送/导出。

## 完成内容

左侧连续海湾示意图、同源建筑地标和淡化未来区域；右侧单区域0.6倍真实快照，保持比例/地物与场景同步。地图默认当前区域，屋内映射旧海港；选中区域与玩家实际区域分离。地点/资源信息、方向键/WASD、Tab/Shift+Tab、E、双层Esc/B及M关闭可用。

静态总览美术来源和处理见[ART_PROVENANCE.md](ART_PROVENANCE.md)。代码原生SVG补绘岸线，未重新生成或覆盖已有位图。

## 自动化证据

| 验证 | 结果 |
|---|---:|
| C区域/地点/焦点/资源合同 | 61/61 |
| 真实快照/投影/嵌套变换 | 25/25 |
| 区域旅行/原子存档 | 28/28 |
| 显示 | 18/18 |
| 原有菜单键盘 | 20/20 |
| 场景合同batch=6 | 132/132 |
| C原生键鼠与渲染 | 55/55 |
| 原生跨区往返、重载、进屋 | 29/29 |

前六组共284项。原生结果保留在native-checks.json和travel-native-checks.json；六张整界面截图与独立640×520美术截图位于本目录。

原生入口：
```sh
/Applications/Godot.app/Contents/MacOS/Godot --path godot2d --log-file /private/tmp/coastal-map-c-native-final.log --script res://tests/test_world_map_c_native.gd
/Applications/Godot.app/Contents/MacOS/Godot --path godot2d --log-file /private/tmp/coastal-map-c-travel-native.log --script res://tests/test_region_map_native.gd
```

所有存档固定/private/tmp/coastal-*，真实玩家存档未参与。最终两个原生日志无脚本/引擎错误。部分headless运行出现系统证书初始化提示，与游戏断言无关；美术并行写入期间曾出现未导入SVG的加载错误，导入后已重跑相关检查，无加载错误。

## 原生步骤、预期、实际、结果

| 步骤 | 预期 | 实际 | 结果 |
|---|---|---|---|
| M打开→W选街区→Tab/E选地点→Esc | 当前海港与查看街区分离，先退出地点 | 状态及截图符合；世界状态未变 | 通过 |
| Tab四组循环与Shift+Tab反向 | 总览/地点/资源/关闭可达 | 焦点落点正确，未进入世界UI | 通过 |
| 点击三个未来区 | 显示说明，无实景/资源 | 三者scene_views、markers为空 | 通过 |
| E切资源、鼠标点旧屋、Esc返回 | 六点显示/隐藏；地点选择不传送 | 资源/地点状态正确 | 通过 |
| 真实步行进屋→M→点击旧屋标记 | 默认海港并标屋内，定位针不挡点击 | 定位正确，中心点击可选旧屋 | 通过 |
| 长按Arrow/Tab重复事件 | 不绕过地图自定义焦点导航 | 修复后两项均通过 | 通过 |
| 多次开关及切区 | 只有所选区域一份快照 | 连续三轮无残留快照 | 通过 |
| 旧海港→街区→存档重载→返回→进屋 | 位置/存档正确，门过渡仍可用 | 29项原生检查通过 | 通过 |

独立复查使用gpt-6-astra high；发现echo输入泄漏与屋内定位针拦截，两者均先用原生检查复现（55项中3失败），最小修复后55/55，并复查通过。实现gpt-6.1-sol high，美术gpt-6.1-sol medium，主代理负责集成/原生验收；无用量节省比例声明。

## 边界

没有真人长时试玩、Windows/Intel或新导出验证。三个未来区域仍未开放。以后新增可玩区域须同时登记区域元数据、场景来源映射与美术地标，不能仅修改open标志；大区域缩放/平移和P09不在本轮范围。
