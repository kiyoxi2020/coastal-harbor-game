# 实施报告：锄地西向长袖B两关键姿态

目标是先交付ready/contact完整姿态来确认长袖外观与袖腕/衣摆接口的可审阅性；完成条件为GPT来源齐全、整帧登记、诚实能力清单、尺寸/握点/脚点测量及结构验证。完成此限定交付，不标记阶段4、分层换衣或完整锄地通过。

仅本目录新增；使用内置GPT生图工具，四次调用：ready一次、contact双参考失败一次、单参考重试一次（姿态保留但alpha失败）、针对alpha噪声的背景提取修复一次。后者根据明确透明度证据改变任务，不扩任何姿态；两种失败源与提示词、失败测试及明暗板保留。未脚本绘制、补色、擦除或拆贴旧脸手；未局部缩放/挪动衣鞋或工具。源文件到registered仅整帧整数平移，逐RGBA精确还原。

最终源：sources/ready-attempt1.png、sources/contact-alpha-cleanup.png。候选candidate.json，garment=B、direction=west；1536×1792、root[768,1544]、scale138/1164；ready/contact各180/140ms，events空、loop=false、review_repeat=false、modular=false、native_checked=false。完整源、源/配置/代码/测量哈希绑定，失败稿也在输入清单中。

结构4项通过，详见evidence/validation.json；目视1x/2x明暗对照完成。完整源1024×1536，最终alpha0–254、四角0；画布原生1x182.10×212.45px。头框ready469×476/contact482×495；头身投影、脚底与柄/握点记录在measurements/poses中，±8源像素。柄投影长差1.82%；近后跟对齐由root定义产生，不当作精确支撑通过。透明提取轻微重绘已重测，contact头框较认可A约+1.7%，未按比例局部修正。

无原生Godot、连续动作、支撑/握点批准轨迹、世界遮挡、业务/存档、导出验证。两帧不是完整可执行动作；长袖是完整GPT穿衣图，独立衣物/隐藏身体/覆盖层序仍待制作。无当前技术阻塞；下一步由主代理独立审查/原生停帧，后续同姿态分层接口通过再扩lift/recovery。

本任务由主代理委派的子代理执行，实际调用 model=gpt-6.1-sol、reasoning_effort=high、fork_turns=none（主代理已核实spawn记录），理由为源图/登记/测量可在独立目录交付；未嵌套、未改共享文件、未提交。
