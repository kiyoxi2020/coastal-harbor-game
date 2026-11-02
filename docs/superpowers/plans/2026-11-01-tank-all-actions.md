# 背心短裤其余动作并行实施计划

**Goal:** 完成walk/run/hoe/water/harvest四向衣物修订，自验后整包交用户验收。

**Architecture:** Q26四向idle为唯一已认可外观；原归档动作只提供同姿态参考。沿既有reference_sheet/pack_sources/build/review工具，不创建批次合成器或播放器。为保持已交付idle与旧全动作严格快照可复核，新完整动作候选使用独立版本化模板身份，仍属于同一unified-composable-character-v1；不切生产或放宽基线。

**Tech Stack:** 内置GPT imagegen、Python/Pillow、统一严格构建与Godot原生观察器。

## 范围与验收

- 保留既有idle4、walk24、run24、hoe24、water16、harvest16，身体共108姿态，农事另外56带工具显示姿态。
- 男性侧胸平直、正背腰腹自然宽；背心短裤、光头赤脚；不拼旧脸手，不改变手脚动作，不以镜像补方向，不任意挪缩部件。
- 源图与prompt/引用SHA保留；只允许整帧登记与实际表格切分。四向时序完整，根点对应原注册与实际新图核验。
- 人物工具全测与check必跑；walk/run至少10循环与转向/停步，农事开始结束、握点和道具轮廓、明暗原尺寸检查；只把实际通过项目列为通过。
- 源/构建不等于动态认可；全部自验后统一提问，不逐方向要求用户认可。尚未完成动态换装、发布和其他体型。
- 保留全部已有未提交修改、不推送、不改runtime-baseline或默认主角。

## 分工与进度

- [x] T01：主代理核源、计划与边界。
- [x] T02：locomotion_art，gpt-6.1-sol high；walk/run48帧源表及源登记自验。独占sources/adult-v3-locomotion-tank-r001与对应审阅子目录。
- [x] T03：farm_body_art，gpt-6.1-sol high；三农事56帧body-only源表及源登记自验。独占sources/adult-v3-farm-body-tank-r001与对应审阅子目录。
- [x] T04：主代理；三农事56带工具源，独占sources/adult-v3-farm-visible-tank-r001。
- [x] T05：主代理集成版本化模板、严格配方、统一评审与原生连续自验。
- [x] T06：复用已完成子代理独立复查具体来源/姿态风险，主代理跑全测/门禁、交接统一验收包。

选择两个sol子代理是因为动作源图判断与注册涉及跨姿态一致性；共用模板和脚本由主代理单写，子代理不嵌套。没有独立工作时等待交付，不重复调查其负责范围。
