# 西向农事衔接隔离试玩

双击 `launch-game-trial.command`。C 收起/打开动作对照面板。WASD/方向键走路，Shift 奔跑；先朝西（A）并按1换短袖，再按 F 浇水、G 锄地、H 采收。动作期间锁移动与方向；1/2换衣请求延后到动作结束。R 取消并回起点；失焦暂停当前工具时间轴。结束先回同向idle，下一物理帧才恢复移动输入。

这里沿用已认可西向短袖 water v3（2姿态，1000ms）、hoe v4（4姿态，800ms）、harvest v2（2姿态，1000ms），原始时序和纹理不变。进入/退出使用硬切，尚无额外工具收放过渡画面。两姿态浇水/采收仍不是完整动作；本轮是状态衔接与实际显示验证，不登记新视觉认可，不触发耕地、耗体力或存档。

只支持catalog已登记的西向短袖；方向/衣服不支持时明确拒绝。南向浇水和长袖锄地新图保存在独立候选目录，不自动启用。旧走跑/对照启动器保持原模式。

源密度与显示：idle 512×768、根(256,708)，场景scale约0.05927835×相机4，源→屏幕约0.2371134；农事2倍源密度，完整画布按登记根点显示，scale减半，源→屏幕约0.1185567。不会按人物bbox缩放、裁掉水流/工具或逐帧挪鞋。验收与实际输入哈希见 evidence/native/report.json；原生截图与连续记录仅证明所列组合。

归档或复用原生证据前，必须运行 `python3 art/design/character-motion/adult-standard-v1/farming-transitions-v1/dependency_contract.py validate`。新增[依赖归因补充说明](dependency-repair-report.md)与[采集后依赖契约](evidence/native/dependency-contract.json)；这是保守静态可达/manifest依赖超集，未改原采集报告，也不是运行时加载列表。门禁失败会清除摘要旧的input_hashes_current=true。
