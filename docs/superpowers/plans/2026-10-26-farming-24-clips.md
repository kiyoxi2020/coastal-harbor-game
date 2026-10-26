# 三类农事24组试玩 Implementation Plan

> 使用 subagent-driven-development、imagegen、TDD。用户已明确授权持续执行至三动作四向长短袖全部进入试玩，无需逐组暂停确认。

Goal: hoe/water/harvest × south/west/east/north × A/B共24组完整可读待验收序列，同时可在对照面板和隔离世界角色播放。
Architecture: 保持原母版和已认可文件；新资源在farming-four-directions-v1/{action}/{direction}-{garment}/candidate.json。catalog schema2完整覆盖24个action/direction/garment键，原schema1仍支持。复用现有actor权威工具时间轴、移动/方向锁和结束换衣。完整穿衣帧只声明固定A/B外观候选，不冒称独立衣体组合或生产迁移。
Tech: GPT imagegen / Python登记 / Godot4 GDScript。

## 交付合同

每candidate schema_version1/template_id adult-standard-v1/action_id/direction/garment，canvas/root为真实整数登记、source_density_scale_vs_idle2，display_scale138/1164。frames至少4个有序可读姿态，各有唯一pose_id、phase、正整数duration_ms、file/sha256、source/source_sha256；source列入inputs。图像整帧裁切和整数平移，禁止局部缩放/贴旧脸手/镜像代方向/脚本补画正式像素。全部GPT源/prompt/失败稿/登记配置/测量保留。完整动作判定看真实姿态变化与动作意义，不用重复PNG凑帧。已认可西hoe A四帧可原RGBA/时序复用；其他已认可关键姿态可作为完整序列的真实部分。

hoe phases ready/lift/contact/recovery；water ready/raise/pour/recovery；harvest ready/reach/pluck/recovery。约800–1200ms，可按动作必要性增加帧。原有西hoe A180/220/140/260ms不改。采收需看得到接近作物、抓取、提起/恢复过程。北向工具自然被身体遮住时按空间表达，不伪造前面手臂。

## Task 1: hoe美术（hoe_long_sleeve，gpt-6.1-sol high）
- [x] 仅hoe/**；八组完整动作，原源、登记、量测、结构/来源/能力失败检查与报告。
## Task 2: water美术（water_south，gpt-6.1-sol high）
- [x] 仅water/**；八组完整动作，保留完整水流/壶，原源/登记/测试/报告。
## Task 3: harvest美术（主代理先行，空闲子代理可接独立未开始组）
- [x] 仅harvest/**；八组完整动作，同母版固定作物/手部/身体空间一致。
## Task 4: 加载与试玩（主代理）
- [x] 先失败测试schema2完整24键、重复/缺方向/缺衣服、哈希/真实尺寸/时序/原子清空，保留schema1回归。
- [x] character_farming_review.gd支持schema2；character_motion_review.gd与character_walk_trial.gd按实际clip显示，--trial-farming-catalog指定新目录；缺资源明确拒绝。
- [x] 新独立启动器启用24组目录。方向按钮、短长袖、三动作、暂停/逐帧可见；F/G/H当前朝向播放，结束回idle/排队换衣。
## Task 5: 集成与验收（主代理，子代理独立复查）
- [x] 所有24组真实加载、全部姿态停帧截图和目视、原生每组连续10次面板播放及各1次世界one-shot/衔接/键盘/换衣/取消；证据绑定实际资源、时间和世界依赖。失焦逻辑通过，独立原生三策略补测未验证，不记通过（见下）。
- [x] 相关逻辑回归与来源验证；审查修复P1/P2后最终复审；更新进度/交接，启动本轮试玩交用户验收。

只完成本次固定A/B三类农事24组试玩，不扩裤鞋发帽、其他体型或生产玩法。保留已有未提交修改，不提交/推送/导出，不触玩家档。每组成功后继续下一组，不以少量静态小样结束。两次同类失败先分析并改变方案，不能同法机械重试或标假完成。

## 实际验收与保留项

24/96已全入试玩；397逻辑/资源、346原生通过，主采集前后门禁通过及1193PNG逐哈希恢复通过。最终gpt-6-astra high限定规格/质量认可，无未关闭P1/P2。

- [ ] 真实系统窗口失焦/恢复可靠原生自动核验：三策略未证明完整WM链路，失败原样保留，只有既有逻辑暂停回归通过；不扩大346通过范围，不阻断本轮明确24组待用户视觉验收交付。

固定A/B完整穿衣图不是独立组合，accepted/modular/gameplay_available仍false；没有生产/存档/导出变更。
