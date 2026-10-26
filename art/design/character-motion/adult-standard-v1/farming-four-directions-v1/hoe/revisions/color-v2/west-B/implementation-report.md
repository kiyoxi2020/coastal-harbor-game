# 锄地B颜色修订：west-B

原蓝衣较其他动作偏浅，本次仅以GPT提供的深色衣服RGB修正原衣区。candidate SHA256 `be58b7d2886ac08ef5d34846de67decef77a4b7abe3d825174b3398566c60a77`，parent `5c15bd950e3557beb08b8a612f7866daa2a1b7627a1e5971f97c5667abd746c9`。四帧时间180/220/140/260ms，共800ms；原画布1536×1792/root[768,1544]/scale138/1164及全部source_root/head/feet/tool/timing完全沿用。

原图1024×1536、GPT完整raw1024×1536、合成源1024×1536；registered仅原整帧平移。手工逐帧声明衣身/袖子及可见衣边polygon，颜色仅在这些表面内辅助选原蓝布；GPT只贡献paint mask内RGB。原alpha全图逐字节一致，mask外RGBA逐字节0差；脸、手、裤鞋及完整工具没有取GPT重画像素。使用主代理只读compose_color.py原样快照，阈值始终5%，未做程序调色或局部变形。

| phase | GPT RGB应用像素 | fallback原边缘保留 | paint区平均RGB亮度（算术均值） |
|---|---|---|---|
| ready | 75370 | 0.734% | 112.10 → 95.63 |
| lift | 76345 | 0.114% | 109.10 → 82.19 |
| contact | 74380 | 0.302% | 115.33 → 90.98 |
| recovery | 68849 | 0.293% | 111.28 → 91.35 |

数据见evidence/color-diagnostics.json，另含Rec709加权luma；平均RGB与luma是不同统计，不混用父级108–123区间。只在同一mask比较前后色调，不把不同姿态的阴影分布强求为同一数值。

4项测试通过：精确非paint/alpha/GPT RGB来源、原配置几何时序、parent/依赖/原登记器validate_data、未偷转新palette认可。完整raw、prompt、原source、paintmask、ownership、compositor快照都进入candidate.inputs；color_revision逐帧提供mask/raw/polygons/info。2x原生密度before/after板及明暗registered板均已目视；颜色回归仍待主代理Godot原生与用户认可。旧姿态认可不等于本新palette认可。

西向lift首个GPT输出整帧上移约30px，原衣表面16.2%不再是对应蓝布，已被固定5%门禁拒绝。保留sources/gpt-lift-attempt1.png及失败报告；根据此证据改为仅原图输入、显式原坐标锁定，第二稿fallback0.114%通过，未平移/缩放raw或放宽门槛。

只写本color-v2独立目录，不改原v1、其他动作/衣服、共享脚本/catalog；未提交、推送或导出。执行模型gpt-6.1-sol high，内置GPT生图，精确生图模型ID工具未返回；未嵌套。
