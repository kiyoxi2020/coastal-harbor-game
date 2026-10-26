# 西向农事衔接交付

实现：character_walk_trial.gd新增显式--trial-farming-transitions，F/G/H调用已加载catalog的west/A样例。移动中允许进入，方向冻结，移动速度归零，按原duration一次播放；完成当tick进入同向idle，下一tick才接受移动。换衣只保留最后一个A/B请求，完成时整体切换；R取消清队列，失焦暂停。原始scale/offset恢复，农事显示采用原scale×源密度比及已登记root。对照面板的选择/播放仍独立。原走跑入口默认不启用新行为，新增同目录启动器。

没有新的工具收放过渡图，进入/退出明确硬切。water/harvest仍是两姿态关键帧；尚非完整动作或精确握点/接触通过，不触发真实农事事件、体力或存档。其他方向/长袖缺资源拒绝，两个新美术目录不自动接入。

测试先失败（world_farming_entry_exists），最小实现后45通过；新增直接locomotion setter锁定测试先3项失败，补守卫后48通过。相关回归：farming panel33、catalog43、motion panel37、run directions22、walk28，共163。另命令行入口headless启动成功、zsh -n启动器成功。未重跑生产玩法全部测试、导出应用或跨平台验证。

原生第一次：水/锄各十次通过；采收第4次相位停在483.333ms、后续保持，符合失焦暂停。失败report/checks和代表截图在evidence/failed-native-attempt1，原始PNG留/private/tmp/coastal-farming-transitions-native；未用于成功结论。补测试窗口就绪与焦点采样、超时诊断，不改生产行为。第二次78项通过，三动作各十次、所有8姿态、2715采样/169连续捕获，全程焦点有效、0恢复。实际键盘从run进入、移动/方向锁、排队换衣、完成idle、缺B拒绝均通过。已目视世界锄地、浇水水流、采收蹲姿，未裁图掩盖工具/脚位。evidence/native/report.json绑定实际输入与candidate，验证summary核验哈希及169张无损归档恢复，sequence.mp4为便览。

无已认可candidate/纹理/时序变化，无生产人物或玩家档变化。主代理实现/集成/原生；两个gpt-6.1-sol high分别独立制作南water和西长袖hoe，判断源图身份/比例/姿态需中复杂视觉推理。候选与本状态衔接的认可范围分别记录。不提交、推送或导出。

最终跨合同评审发现P2证据缺项：原native report绑定农事与脚本，但未完整绑定locomotion/run和world/camera/project依赖。已补post-run独立dependency-contract、依赖递归校验及缺项/篡改失败测试，12项通过、1140保守依赖超集当前通过；最终gpt-6-astra high复审关闭P2，无剩余P1/P2。详见dependency-repair-report.md和evidence/final-review.md。补证只证明本次未变输入关联，不冒称当时运行采样；既有原生报告与原脚本哈希保持。
