已将空间PNG的墙钟推算改为实际物理tick因果校验；只改all_actions_evidence.py及其test_all_actions_evidence.py，不改capture/GDS、runtime、source、core或ground。

依据：Godot4.4官方文档明确physics_jitter_fix调整物理tick与真实时间的同步程度，较高数值会让游戏时钟更偏离真实时钟。因此由sum(delta)推导“PNG之间wall time+固定1tick”的上界没有该Engine合同保证，本修复直接移除推算，也不改成2tick阈值。这是从文档作出的验证策略选择，非修改物理时钟。见[Engine.physics_jitter_fix](https://docs.godotengine.org/en/4.4/classes/class_engine.html#class-engine-property-physics-jitter-fix)。

新合同：

- report.engine_clock必需：physics_ticks_per_second严格int60、max_physics_steps_per_frame严格int8；time_scale_f64解码严格1；physics_jitter_fix_f64解码有限且非负。所有f64采用既有number64，不接受bool/NaN/Inf。
- 每条physics row的ticks_usec必须正int；沿已校验physics_frame和route顺序全局严格递增，不能route内倒退/重复或跨route复用。
- capture保留原实际physics_frame与position/GPU/state/elapsed/instance绑定、PNG字节/哈希清单、实际pose/worldclock检查。对同tickcapture另核matched_tick_time<=capture_time<下个已记录actual_tick_time（存在时）；不以delta推测间隔。
- setup/初始tool capture仍只允许first_frame-1、真实setup点、idle或tool初始0clock，并要求capture_time<first actual_tick_time。已记录序列没有的引擎tick不造时间；末尾无next记录时只校下界。
- delta依旧用于原运动步长/方向及动画逻辑校验；移除只涉及从game delta到real wall时长的未经保证推断。普通idle和前包normal-separation/contact-jitter边界保持。

TDD：8新测试先20 subcase/assert RED，之后8PASS。包括合法物理累计领先墙钟1.6tick但实际tick因果正确、缺/错Engine header、rowticks缺失/0/bool/倒退/跨route复用、matched tick晚于capture、next tick已在capture前或同刻、setup晚于first tick；旧0/1 collapsed PNG clocks与位置999仍拒绝。14恢复tests继续GREEN。整个evidence模块69项定点全测及正式spatial05 raw-only结果在完成后补记，不以本段预报PASS。

旧spatial04缺header/tick字段，不改旧data、不补造字段，不转PASS。Root官方validate_observation/全closure aggregate与全量unit/check另行完成；本包不授予art/contact/user/release认可。

最终定点结果：8 clock测试PASS，14 idle recovery测试继续PASS；整个test_all_actions_evidence模块69项全PASS（111.746s），日志/private/tmp/coastal-spatial-actual-tick-clock-full-targeted.log。

正式spatial05 raw-only API核对PASS（不替代官方verify_inputs/validate_observation/aggregate）：14route、3045实际physical tick、61PNG；56capture与相同tick绑定并在下个已记录tick前，5setup capture在first tick前。全部实际tick时间全局递增；Engine header为tps60、fix0.5、time_scale1、maxsteps8。恢复分类8 normal-separation+1 contact-jitter，前一窄合同不变。输入contract SHAb1c6701a0a8d8c5b1307b4a9174fb086123c8c8398e7fb427c3fe9803890e2d2；report SHAfc0ac94c5cef16105430ee2d47d7843f944ff8da6350ef5bb403f4ec293743ba。明细/private/tmp/coastal-spatial05-actual-tick-raw-diagnostic.json与.log。旧04不补字段、不转PASS。

冻结：all_actions_evidence.py SHA6a76e0bfc11afbdb5659bd82a79423cd85011b16f437efed735ebd4bdd4379e8；test_all_actions_evidence.py SHAcaed5986a61ae6fbb43efff85cb9b6fb89812ab6ef867040a88a749a15e58cb5。本轮只改这两文件；Root最终全量门禁/官方raw聚合另行执行，未授予艺术/接触/用户/发布认可。
