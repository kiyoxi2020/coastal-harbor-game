# V5默认主角接入实施计划

**目标：** 将已认可的adult-v5/r012完整108显示帧接入默认游戏，验证实际导入像素、动作与世界遮挡。
**方案：** 复用godot_integration.py和现有玩家；新包adult-v5-pixel-visible-r010、新SpriteFrames player_body_v5_frames.tres。画布260×228，根点125/201，整体缩放0.25；不改玩法、存档和NPC。用户已明确授权替换，主代理直接实施，不提交或推送。
**技术：** Python严格构建与Godot原生验证。

- [x] 核对parts最终包、r010严格build及认可绑定；Progress记录四步。
- [x] 更新test_unified_player.gd的v5路径、260×228和(-125,-201)预期，确认旧场景失败。
- [x] 执行`python3 tools/characters/godot_integration.py create art/characters/builds/adult-v5-pixel-visible-r010 --package godot2d/assets/characters/integrations/adult-v5-pixel-visible-r010 --frames godot2d/resources/player_body_v5_frames.tres`；player.tscn替换引用和整帧根点，观察器指向新manifest。
- [x] 核对新运行包108帧与源build等价，精确追加110冻结文件及新引用，仅更新player.tscn哈希；旧冻结项不重采、不删除。严格verify和verify-runtime均执行。
- [x] 执行人物unittest全套、check.py、实际玩家469项；使用全新/private/tmp/coastal-v5-*隔离存档，原生test_body_game_native.gd验证走跑十循环、农事和门遮挡，核对输入SHA及截图。
- [x] 同步CURRENT、README、PROJECT_STATE、HANDOFF和文字验收报告。运行包可纳管，制作包继续本地忽略；过程截图留临时目录。Progress完成。
