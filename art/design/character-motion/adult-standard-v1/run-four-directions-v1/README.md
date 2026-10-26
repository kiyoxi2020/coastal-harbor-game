## 当前试玩：锄地四姿态修订

[打开统一试玩](launch-game-trial.command)，默认西向短袖锄地：预备、抬锄、落锄、收回四个关键姿态，800ms一循环。头部按已认可浇水母版重新生成；左侧站姿可同尺度比较。支持播放、暂停、下一帧。浇水和采收保留现有两姿态，已登记你的[视觉认可](visual-acceptance-farming-2026-10-26.json)。

锄地v4四姿态、头部比例与当前观感已获你认可，见[认可记录](visual-acceptance-hoe-2026-10-26.json)。约11.28%锄柄长度差异保留为测量历史，当前显示无需因此返工；严格接触合同与正式农事行为未验收，目前只提供西向短袖。C开关面板，WASD/Shift走跑，1/2换上衣。

loader43、面板33、启动6项及原生51项通过；十循环754采样/85捕获，已目视四姿态。见[验证](evidence/hoe-v4-review/validation.json)、[原生录像](evidence/hoe-v4-review/hoe-ten-cycles.mp4)、[完整源说明](../hoe-west-proof-v1/revisions/v4/implementation-report.md)。历史证据与下文保持其原版本含义，当前入口以本节为准。连续原始截图已无损归档为各证据目录的tar.xz；原ZIP仍本地保留，恢复说明和逐项核验见[清理清单](../../../../archive/2026-10-26-motion-cleanup.json)。

## 2026-10-26 当前视觉认可结论

当前成年母版的四向站立、走路、奔跑及两套上衣已显示效果均已获你认可。南北长袖的新认可见[记录](visual-acceptance-long-sleeves-2026-10-26.json)，绑定实际八帧、配置与试玩版本。现有比例与细小接口现象按当前画面接受，保留源与测量，不继续为这些已接受画面返工。

南向长袖目前仍以完整帧展示，独立裤鞋/发帽混搭、农事动作、其他体型和正式迁移另行完成。下文待审/诊断表述为当时过程记录，最新视觉状态以本节为准。

## 2026-10-26 当前试玩与认可

你已认可此前可显示的四向走路/站立、四向短袖奔跑、西/东长袖奔跑及现有比例，记录见[认可文件](visual-acceptance-2026-10-26.json)。

[打开更新试玩](launch-game-trial.command)：默认长袖、南向奔跑对照。南北长袖现以**诊断稿**加入港口与面板；南向完整源稿保留第三帧摆臂现象，北向分层稿保留衣体小孔，等待你看当前表现后确认。按2长袖、1短袖；按钮选方向/奔跑，取消播放后可逐帧；WASD/Shift可实际跑动。

新[诊断清单](run-diagnostics.json)由`build_run_diagnostics.py`从既有源登记，显式参数`--trial-run-diagnostics`启用；原有效上衣清单保持不变。两方向的新显示尚未获认可。30项原生诊断通过，见[evidence/long-sleeve-diagnostics/validation.json](evidence/long-sleeve-diagnostics/validation.json)。下文是此前交付范围与历史诊断。

## 用户确认试玩

[打开港口试玩](launch-game-trial.command)。默认显示动作对照：左侧为同向、同上衣的已认可站姿；右侧可选四向站立/走路/奔跑，均2倍原生尺寸。点击方向和动作按钮，取消“播放”可暂停，“下一帧”逐帧查看。WASD/方向键移动，Shift跑步，1/2换衣，C收起/显示对照，R回起点，Esc退出。南北长袖奔跑未提供，会显示提示。

本轮37项对照逻辑、50项走跑回归及原生34项通过，截图与依赖绑定见[evidence/interactive-review/validation.json](evidence/interactive-review/validation.json)。等待你的视觉反馈，不自动登记通过。

# 四向奔跑技术候选

**历史比例待审记录：2026-10-26用户已认可当时可显示部分，见顶部认可文件。** 原生/结构检查只证明技术链路。按实际同向批准 idle、同像素密度比较，南向含耳头部带宽约大13%，北向约大10%；需要视觉复审，可能完整源稿返工。不得局部缩头修复。入口：[港口试玩](launch-game-trial.command)、[离线动态评审](review.html)、[同尺度对照](evidence/scale-comparison.png)、[确切量测](evidence/geometry-audit.json)。

当前可加载范围：短袖 A 四向各四帧；长袖 B 仅西/东向。南向 B 两轮源稿分别出现头/领口漂移及第三帧摆臂丢失，已停止并拒绝。北向 B 有真实 GPT 衣身、袖层及同身体合成，但颈/腰暗边归属、腋下 alpha/遮挡接口仍有孔，**未列入有效换装能力**。[质量诊断](evidence/garment-quality.json)保留172个封闭低 alpha 点，不能将A还原或部件加载等同B通过。

`candidate.json` 保持既有西向候选合同，平铺16帧、方向顺序south/west/east/north、每帧80ms，75%播放率，基准世界速度108（实际81）。画布512×768，根点(256,708)，nearest；原图2048×768，完整格裁切后仅整帧平移(0,+11)。显示比例0.2371134021，单格约121.40×182.10屏幕像素；没有先缩成低分辨率再放大。

西向 A PNG逐字节复制原认可候选。东向固定无工具、裸头、无单侧饰物的当前A/B使用完整帧反射 `x'=511-x`，再整帧+1x把根点255恢复到256，左右解剖标签交换；原x0列alpha恒0，仅其不可见RGB被截去。所有alpha与可见像素可逆。实际查看了当前东向walk高光随侧向翻转的习惯；此决定不推广到持物、帽子、非对称新服装。来源哈希见候选及[GPT源索引](evidence/source-index.json)。

`run-garments.json` 是共享试玩可消费的有效能力清单：`recipes.A/B` 各为方向→四路径字典。缺少的B方向必须拒绝，不借A或旧模型补齐。`parts-manifest.json` 保存西/东/北真实层；北B仅诊断。西/东层来自当前已修所有权的西向真实分层；北A四帧逐RGBA精确还原。完整GPT无臂衣身源与源图、提示词、ownership、coverage、occlusion分别保留，所有层full_frame零偏移。没有通用裸身体，裤鞋仍固定，未完成独立裤鞋或8配方。

## 验证

```sh
python3 art/design/character-motion/adult-standard-v1/run-four-directions-v1/test_candidate.py
python3 art/design/character-motion/adult-standard-v1/run-four-directions-v1/test_parts.py
```

8项完整帧结构/来源测试、7项分层与能力门禁测试通过。测试明确断言北B质量未过、南北B未启用；这不是15项美术验收通过。HTML脚本通过`node --check`，子代理未运行GUI。主代理负责原生采样与同向idle明暗对照，原生证据位于`evidence/native/`（由主代理独占归档）。

`selected`仅表示选作技术评审的源，`registered`为实际登记；南北`geometry_checked`保留待复审/返工风险，精确关节、接触点和轨迹尚未冻结，`motion_checked/dynamic_swap_checked/native_checked/user_accepted`不由本目录结构检查推导。完整四向B、人体隐藏区、独立裤鞋/发帽、世界移动接触和生产迁移均未完成。具体命令、输出哈希与问题见[实施报告](implementation-report.md)。

## 主代理最终原生与独立复查

最终run原生42项、原walk47项通过；六个可用组合十循环共1338采样/663捕获，明暗1x/2x板包含同向批准idle，见[evidence/native/summary.json](evidence/native/summary.json)、[集成记录](evidence/integration-validation.json)。主代理目视确认南北头部带更宽，比例保持待复审，不把技术检查当美术认可。原生失败诊断保留，最终归档校验实际candidate/garment/脚本、六组合完整集合、单调时间与十循环、板脚本/纹理及尺寸后才发布。归档8项失败回归通过，独立复查P2已关闭，见[evidence/review/final-review.md](evidence/review/final-review.md)。

试玩：WASD/方向键移动，Shift跑步，1/2短袖/长袖，R回起点，Esc退出。南北向长袖跑步明确拒绝；该入口不读写存档，仍是比例待复审候选。
