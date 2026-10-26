# 三类农事 · 四方向 · 短长袖试玩

当前入口使用catalog-color-v2.json；完整24组及锄地长袖衣色修订已于2026-10-26获用户视觉验收，见[最终输入绑定](visual-acceptance-final-2026-10-26.json)。下方待验收描述为生成/交付时历史状态，以最终绑定记录为准。详见[颜色修订](hoe/revisions/color-v2/README.md)。

双击[启动试玩](launch-game-trial.command)。面板直接选四方向和锄地/浇水/采收，1短袖/2长袖；左为同向同衣认可idle，右为完整动作候选，可播放/暂停/下一帧。两侧固定2倍原生源密度显示，画布完整保留工具/水流；源图没有按人物bbox重新缩小。

C收起/打开面板，WASD/方向键走路，Shift奔跑，F浇水、G锄地、H收获，使用世界角色当前朝向和衣服。工具动作锁移动/方向，一次播放后回idle；1/2换衣请求到动作结束后整体应用，R取消回起点。面板独立选号，不改变世界角色朝向；先用WASD转向再按工具键可看世界对应动作。此隔离试玩不读写存档或执行真实农事事务。

catalog.json完整24键：hoe/water/harvest × south/west/east/north × A/B，各4真实姿态，共96。锄地800ms（ready/lift/contact/recovery），浇水1000ms（ready/raise/pour/recovery），采收1000ms（ready/reach/pluck/recovery）。source密度为认可idle两倍，display_scale138/1164；世界实际1x、面板2x。原认可西hoe A四帧RGBA/时序无损复用，西water/harvest已有认可姿态作为真实部分保留；新动作阶段和其他组合待本次用户验收。

每套资源均为固定A/B完整穿衣图，不是独立衣体动态组合；modular=false、accepted=false不因数量齐全而更改。关节隐藏区、精确支撑/握点、无帽有帽/裤鞋混搭与生产人物迁移不在本次交付范围。记录实际投影变化和manual root不等于精确接触通过；不局部缩放头部/鞋子或贴旧脸手掩盖差异。进入/退出依已认可试玩的硬切策略，没有另制工具收放过渡图。

[锄地八组](hoe/implementation-report.md) · [浇水八组](water/implementation-report.md) · [采收说明](harvest/implementation-report.md)。各组candidate绑定GPT源/提示词/登记/测量与实际纹理。四格低密度尝试、透明度失败稿均保留；正式资源采用完整1024×1536单帧，整帧整数登记。

逻辑验证：新目录39项（含schema1错向/错衣RED→GREEN）、面板/世界24组夹具122项、真实目录25项，原schema1/面板/走跑相关211项回归已通过。原生346项全部通过：24组全部96停帧、每组10次连续面板循环及1次世界角色one-shot、走跑进入/排队换衣/取消回idle；62645采样、1096连续捕获。主代理已目视24张原生五列板（idle+四姿态），完整画布、工具/水流均无截断。原生报告与采集前1589保守依赖快照、采集后回执SHA绑定，archive_allowed=true；1193张原始PNG无损归档并逐哈希恢复核验，24段便览视频齐全。最终复审无未关闭P1/P2，限定24组可交用户视觉验收。

证据在原生采集前snapshot所有保守静态/manifest依赖，原生report记录snapshot SHA与UTC时段，采集后必须validate成功并archive_allowed=true才归档。工具与失败测试见[evidence-contract-report](evidence-contract-report.md)。历史试玩/原认可记录保留其原输入绑定，不自动继承到本轮新脚本/布局。

## 未验证与失败记录

真实系统窗口失焦→恢复的独立原生自动补测没有可靠完成：最小化退出焦点后未成功恢复渲染；辅助Window和外部应用激活也未证明预期WM状态切换。三次失败的源脚本、日志/快照与可用截图/报告均保留在evidence/focus-*-attempt*，不计入346通过，不把focus门禁标true。失焦暂停仅有现有逻辑回归通过。该平台窗口自动化限制不改24组动作结论，最终评审已单列；正式跨平台焦点验收仍待完成。没有跑生产玩法事务/新导出或真人长期使用测试。

所有新图保持待用户认可；完整姿态的比例投影变化/精确脚握点仍按实际测量保留，不因数量齐全而继承原视觉认可。独立衣物组合、其他体型、裤鞋发帽及正式生产迁移未完成。
