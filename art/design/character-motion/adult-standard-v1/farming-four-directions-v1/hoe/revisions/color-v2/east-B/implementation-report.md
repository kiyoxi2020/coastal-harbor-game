# 锄地B颜色修订：east-B

原蓝衣较其他动作偏浅，本次仅以GPT提供的深色衣服RGB修正原衣区。candidate SHA256 `d854afcaa34f6a826a285de1e1a5ca9178465ce41b871b00f88f851bac033cff`，parent `ca529f38594d211a01b93a130823c3d35c49977242c566963a240b9baeab9b26`。四帧时间180/220/140/260ms，共800ms；原画布1536×1792/root[768,1544]/scale138/1164及全部source_root/head/feet/tool/timing完全沿用。

原图1024×1536、GPT完整raw1024×1536、合成源1024×1536；registered仅原整帧平移。手工逐帧声明衣身/袖子及可见衣边polygon，颜色仅在这些表面内辅助选原蓝布；GPT只贡献paint mask内RGB。原alpha全图逐字节一致，mask外RGBA逐字节0差；脸、手、裤鞋及完整工具没有取GPT重画像素。使用主代理只读compose_color.py原样快照，阈值始终5%，未做程序调色或局部变形。

| phase | GPT RGB应用像素 | fallback原边缘保留 | paint区平均RGB亮度（算术均值） |
|---|---|---|---|
| ready | 85639 | 0.399% | 116.18 → 94.11 |
| lift | 79284 | 0.394% | 106.67 → 83.86 |
| contact | 71198 | 0.595% | 109.83 → 85.14 |
| recovery | 76833 | 0.428% | 115.39 → 95.32 |

数据见evidence/color-diagnostics.json，另含Rec709加权luma；平均RGB与luma是不同统计，不混用父级108–123区间。只在同一mask比较前后色调，不把不同姿态的阴影分布强求为同一数值。

4项测试通过：精确非paint/alpha/GPT RGB来源、原配置几何时序、parent/依赖/原登记器validate_data、未偷转新palette认可。完整raw、prompt、原source、paintmask、ownership、compositor快照都进入candidate.inputs；color_revision逐帧提供mask/raw/polygons/info。2x原生密度before/after板及明暗registered板均已目视；颜色回归仍待主代理Godot原生与用户认可。旧姿态认可不等于本新palette认可。

东向四帧首轮全部通过门禁，无被删失败稿。

只写本color-v2独立目录，不改原v1、其他动作/衣服、共享脚本/catalog；未提交、推送或导出。执行模型gpt-6.1-sol high，内置GPT生图，精确生图模型ID工具未返回；未嵌套。
