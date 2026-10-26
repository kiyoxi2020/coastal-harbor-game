# 锄地长袖颜色修订

用户反馈“锄地的衣服颜色比其他动作浅，其他没问题”。当前原生图和蓝色像素诊断确认hoe B全方向偏浅（约108–123亮度）而water/harvest约84–102；按蓝长袖修正。原反馈与诊断解释分别记录在visual-acceptance-2026-10-26.json，20组其他动作/短袖保留实际输入认可，hoe B只颜色待修。

目标：4方向B共16帧只更新蓝色衣服RGB，几何/姿态/时序/原alpha及非衣RGBA全保持；以认可water/harvest蓝色作参考，GPT生成颜色编辑源，手动衣身/袖子source_ownership限定范围，脚本只提取GPT RGB并合成，禁止程序调色/局部缩放/跨姿态贴旧脸手。保留原v1和所有失败稿。

- [x] hoe_long_sleeve(gpt-6.1-sol high)：color-v2/west-B与east-B，仅各自目录；GPT源/prompt/人工ownership/paintmask/复合源/同几何candidate及证据。
- [x] water_south(同模型)：color-v2/south-B与north-B，同合同，不改其他资源。
- [x] 主代理：颜色合成器4项RED→GREEN，原alpha/非衣不变、尺寸/空owner/错位拒绝；整修订测试先RED。
- [x] 主代理：验证16帧rawGPT RGB实际应用、所有非衣RGBA0差异，24组catalog-color-v2只有4B条目变，更新启动器。
- [x] 原生针对4B/16停帧各10面板循环+1world，参考water比较、采集前后依赖门禁，保留原24组报告；登记20组原认可，修订色仍待用户确认。
- [x] 更新进度/交接并重新启动试玩。无逻辑功能/生产迁移/提交/推送/导出，不重做其他已认可画面。
