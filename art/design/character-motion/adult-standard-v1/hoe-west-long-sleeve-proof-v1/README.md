# 西向锄地长袖 B：ready/contact 两姿态诊断

入口：[明暗姿态审阅页](review.html)、[1x A/B对照](evidence/pose-comparison-1x.png)、[2x A/B对照](evidence/pose-comparison-2x.png)、[candidate](candidate.json)、[测量](measurements.json)、[实施报告](implementation-report.md)。

仅交付两张完整 GPT 姿态小样，蓝色长袖延伸到双腕，用于先审阅领肩、袖腕、衣摆及工具握持。**未分层、未用户认可、未接入原生或玩法；缺 lift/recovery，不构成完整动作或独立可组合衣物。** 两姿态分别保留 v4 的 ready/contact 语义与180/140ms参考时长，不把两帧当作320ms循环。

## 来源、尺寸与登记

使用 imagegen 技能内置 GPT 生图工具；工具未返回精确模型版本。ready以认可锄地v4 ready整帧为编辑目标，以认可四向run中的B西向帧为上衣设计参考。contact首稿被ready参考带偏后，改为仅contact原图输入和具体坐标约束。第二稿姿态正常但alpha背景污染，另用一次GPT背景提取修复；所有原稿、提示词、失败对照及理由均保留，见[provenance](provenance.json)。最终透明提取稿有轻微重绘，已重新量测，不宣称与修复前像素相同。

- 完整源：1024×1536；不裁切、不缩放源图。
- registered：1536×1792；root `[768,1544]`；整帧整数平移，全部源RGBA逐像素保留。
- `display_scale=138/1164≈0.118556701`，沿用认可锄地v4的2倍idle源密度。
- 1x画布显示约182.10×212.45屏幕像素；2x约364.21×424.91。明暗板按该密度nearest采样，HTML默认2x；证据板不是Godot原生证据。
- 最终两源alpha范围0–254，四角alpha均0；保留GPT原alpha及低alpha边缘，不强制归一化为255或程序抠图。

| 姿态 | 源 | registered | 头框尺寸 | 冠至root投影 | 柄端投影长 |
|---|---|---|---|---|---|
| ready | sources/ready-attempt1.png | registered/hoe_west_key_0.png | 469×476 | 1226px | 552.76px |
| contact | sources/contact-alpha-cleanup.png | registered/hoe_west_key_2.png | 482×495 | 1175px | 542.86px |

测量为可见轮廓、袖腕、鞋底、柄端和手握中心人工观察，±8源像素。contact头框较认可A同姿态约宽1.69%、高1.64%；ready同口径一致。头颅和四肢没有单独缩放/挪动；髋膝踝等隐藏关节明确null。脚点与握点完整源/registered坐标见[poses](poses.json)。柄长两帧差约1.82%，仅为投影测量；近鞋后缘对齐由root定义产生，不证明脚接触合同通过。远鞋前缘x跨幅14源像素≈1.66屏幕像素，不声称已满足严格1像素支撑轨迹。

## 验证与局限

4项结构检查通过：两姿态与诚实能力范围、完整源RGBA登记保真、依赖/纹理/配置digest、坐标映射与未知关节。已目视明暗1x/2x对照，未见旧奶油袖口、裸前臂、双手/双肢、衣摆断口或透明背景矩形。详细结果[validation](evidence/validation.json)。首次未登记失败测试、contact透明度失败测试及失败板均保留。

没有运行Godot、连续动画、脚/握点批准轨迹、世界遮挡、存档或导出验证，`native_checked=false`。两张完整穿衣GPT图不证明衣身/袖子/身体可拆分或复用。后续先独立审查这两姿态，再补完整隐藏身体、独立衣身/袖视图、pose-map、coverage与实际前后关系，并做A/B同身体精确还原与袖腕/腰接口；通过后再补lift/recovery及连续原生动作。未扩四方向、裤鞋发帽混搭或生产迁移。

复现：

```sh
python3 art/design/character-motion/adult-standard-v1/hoe-west-long-sleeve-proof-v1/register_candidate.py
python3 art/design/character-motion/adult-standard-v1/hoe-west-long-sleeve-proof-v1/test_candidate.py
python3 art/design/character-motion/adult-standard-v1/hoe-west-long-sleeve-proof-v1/build_review.py
```

只修改本独立目录；未改认可素材、共享Godot脚本/catalog、PROJECT_STATE/HANDOFF；未提交、推送或导出。

## 主代理补充的原生静态诊断（2026-10-26）

[Godot明暗1x/2x板](evidence/native-static/native-board.png)及[输入绑定报告](evidence/native-static/report.json)已完成，8项检查通过，参照由认可locomotion清单按同向同上衣自动解析。主代理已目视完整姿态、透明度和源密度；这是静态诊断，不是连续动作、精确接触、独立衣物组合或用户认可。candidate仍保留制作时native_checked=false，以此独立报告解释新增范围。

首张主代理原生对照板曾手动误选东向B idle，保留于evidence/incorrect-idle-reference，仅作失败历史。采集器随后改为从认可manifest按direction/garment自动选同向idle并核验纹理哈希；最终native-static报告与上方静态结论使用修正后的西向B，候选纹理未变。
