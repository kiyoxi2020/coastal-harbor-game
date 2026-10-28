# 成年母版动态发帽抽样

本轮沿 adult-standard-v1 同一体系制作栗色短发与草帽。独立入口：`launch-game-trial.command`。本目录为评审候选，视觉认可须以用户实际反馈和另存的输入绑定记录为准。

## 操作

右上选东向跑步、西向锄地、南向浇水或北向收获；右下选裸头、仅头发、仅草帽、头发＋草帽。左侧可播放/暂停/逐帧，对照同配方站姿。世界中按方向键向东跑步；F浇水、G锄地、H收获，仅启用当前样例的动作与方向；R回起点。发帽切换保持当前动作进度，农事结束回同状态站姿。不读写玩家存档。

## 制作范围

四个固定衣物配方×四动作姿态＋匹配idle×四头部状态，共80个显示状态，其中裸头是原衣装图无损复用。hair/hat设计ID及实际姿态视图、注册和source ownership/coverage/occlusion由各样例登记；完整GPT源、prompt及失败稿保留。制作侧拆部件和烘焙，显示侧仍为完整帧与原时间轴。新发帽不会建立另一套人物动画时钟。

每组 `sample.json` 绑定原衣装输入及实际文件SHA；共享 `catalog.json` 只索引这四组。`character_headwear_samples.gd` 拒绝缺状态、缺姿态、原衣装陈旧、非正整数时长、几何不一致和依赖篡改。裸头输出必须与原衣装PNG哈希一致。

## 验证与边界

逻辑fixture只证明加载/切换行为；真实资源集成与GPU原生停帧/连续播放分别记录。原生fixture调用真实控件信号、handler和逻辑Input actions，并由fixture设置focused；不等同OS键鼠投递或系统窗口失焦恢复。`evidence_contract.py` 在采集前记录保守静态依赖及样例完整inputs，采集后核对当前输入、输出截图SHA和UTC顺序。它不是运行时文件访问跟踪。

验证命令（所有Godot入口需带临时log）：

```sh
godot --headless --path godot2d --log-file /private/tmp/coastal-headwear-loader.log --script res://tests/test_character_headwear_samples.gd
godot --headless --path godot2d --log-file /private/tmp/coastal-headwear-trial.log --script res://tests/test_character_headwear_trial.gd
godot --headless --path godot2d --log-file /private/tmp/coastal-headwear-actual.log --script res://tests/test_character_headwear_actual.gd
python3 -m unittest discover -s art/design/character-motion/adult-standard-v1/headwear-sampling-v1 -p test_contract.py
```

这里只声明四组实际适配的方向/动作；其他款式、任意混搭、其他体型、严格脚握接触、系统焦点恢复、生产人物/玩法迁移、跨平台及新导出均不由本轮证据推出。运行中的旧生产人物保持其现有发布状态，未提前退役。

## 本轮技术验收结果

加载34、状态切换90、真实资源98、旧衣物13项Godot检查通过；Python合同10和源格伪影1项通过。真实Apple M4 GPU原生434项通过，18981采样、852捕获，主代理已目视全部明暗停帧和世界合并板。原生报告与SHA回执位于`evidence/native`；独立复查发现的报告完整性P2已由先失败后通过的回归关闭。用户外观认可待反馈。

[实际窗口总览](evidence/native/overview.png) · [东向跑步明背景四状态](evidence/native/review/run-east-light-all-states.png) · [西向锄地明背景四状态](evidence/native/review/hoe-west-light-all-states.png) · [南向浇水明背景四状态](evidence/native/review/water-south-light-all-states.png) · [北向收获明背景四状态](evidence/native/review/harvest-north-light-all-states.png)。16段连续原生裁切VFR录像在`evidence/native/videos`，时间取真实采集间隔。

尺寸记录见[display-measurements.json](display-measurements.json)：走跑输出512×768，西锄1536×1792，南浇/北收1536×1920，idle512×768。整帧登记缩放保持；实际完整发帽动作含工具的世界显示最大约run120×169、hoe114×179、water120×175、harvest120×180像素，面板为两倍。原始GPT源分辨率及每个状态的alpha足迹分别记录，不以这些包围框重新缩放部件。
