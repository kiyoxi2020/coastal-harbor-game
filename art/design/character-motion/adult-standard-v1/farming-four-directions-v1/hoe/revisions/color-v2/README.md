# 锄地长袖衣色修订

以用户认可的浇水/采收蓝衣为参考，通过GPT生成同姿态衣色编辑源。四方向16帧仅shirt mask内RGB采用GPT原图；alpha和mask外RGBA、原姿态/锚点/时序完全保留。其他20组不变，原v1和所有失败稿保留。新色已于2026-10-26获用户确认；最终输入绑定见../../../visual-acceptance-final-2026-10-26.json。

通过[启动试玩](../../../launch-game-trial.command)加载catalog-color-v2.json；试玩按2选长袖，面板选择四向锄地/浇水/采收对照。

合成器4测试、完整修订3测试及独立16帧精确像素审计通过。真实Godot渲染fixture69项通过，4组各10面板循环和1次world播放；证据见evidence/native。fixture通过控件signals/动作handler调用，方向直接赋值、focused置true，未证明OS键鼠/转向移动/WM焦点。前两轮系统输入注入失败保留在evidence/input-attempts，不记为通过。旧24组346项报告仍属于原颜色历史。
