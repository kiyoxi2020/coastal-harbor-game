已修复空间观察器把合法idle碰撞恢复一律当角色移动的误拒，仅改tools/characters/all_actions_evidence.py与tests/test_all_actions_evidence.py。普通path/tool idle静止阈值保留，不更改capture、runtime、core、艺术或ground。

窄合同：

- 只对door route、idle且实际位移>=1e-5启用。door0/1只接受HarborExterior/DepthSortedObjects/ExteriorDoor/DoorCollision对应normal，door2只接受House/HouseLintel；colliders/normals逐项等长，全部normal有限unit，4ULP(1)方向误差界。
- requested仅冻结door计划north或release0。motion_delta与实际position差<=1e-6；step<=捕获safe_margin，0<margin<=0.08+1binary32ULP(0.08)。step dot requested<=0.001照原runtime walking clock激活条件，不是phase容差。
- normal-separation：step必须与至少一条对应允许normal平行且同向，walking phase严格等于上一tick或重设0。
- contact-jitter：上述语义/字段/方向平行前提相同（允许反向微抖），每轴step<=2*max(real32ULP(previous_coordinate),real32ULP(current_coordinate))；phase只可相同/0或差<=2*max(binary64ULP(previous_phase),ULP(current_phase))。正常大步恢复不能套这条抖动容差。
- 所有新phase字段先number64有限检查、非负；door另严格小于实际walk-north duration。缺当前字段/前tick phase、错normal、无对应collider、伪大margin、超margin、requested walk推进、phase绕回/任意减小均拒绝。

TDD：14项新增测试先6个assert RED（真实0.072067、reset0、真实2R32ULP/1R64ULP抖动被旧gate拒绝），再最小GREEN。包含缺字段、错normal/对应关系、无collider、非unit、伪大/零margin、motion差、超界、>2R32ULP、>2R64ULP、phase范围/NaN/Inf、普通idle/tool移动拒绝。新14项及整个test_all_actions_evidence模块61项全PASS（110s）。日志/private/tmp/coastal-spatial-idle-recovery-red-04.log、green-01.log、full-targeted.log。

实际spatial04只读API诊断（raw-only，不替代Root官方全closure aggregate）：恢复段全通过，共10tick=9normal-separation+1contact-jitter（door2 frame974，stepY=-3.0517578125e-5）。完整spatial_report仍拒绝既有wallclock预算：tree-around start frame16→waypoint1 frame65，physics interval0.8166666667s，actual wall0.789384s+1tick0.0166666667=0.8060506667s，excess0.010616s。没有把恢复通过谎报为完整raw PASS，也没有改那条独立门禁。详细/private/tmp/coastal-spatial04-idle-recovery-raw-diagnostic.json及同前缀.log。

冻结SHA：all_actions_evidence.py8a046f4ad1a5167b248f28b3bc2dc66e802240232395f8355340d6de95a0df92；test_all_actions_evidence.py303b1174207215ed79e7dfc2f2281987d50840daf3bf0ce6b1771606edd69969。旧spatial03不修改或转正。未重跑native、全量unit/check；主代理统一最终验证。空间艺术/physical contact/user/release仍未由本工具授予认可。
