# 动作集成独立只读复查

2026-10-25。复查范围：character_walk_trial.gd四向候选加载/切换改动、新test_character_run_directions.gd、西向build_parts.py/test_parts.py的5像素归属修正。未修改这些文件；未重跑主代理已通过的22新+48西向+28walk测试，也未启动GUI。主代理另报西向原生25、walk实际artifact原生47通过；这里只记录其报告，不冒称独立执行。

## 发现

- P3：godot2d/dev/character_walk_trial.gd:59仍无条件显示“西向跑步小样”“跑步仅西向”。四向候选成功加载后，Scope虽已显示实际方向数，Instructions却继续说仅西向，且加载失败时也会显示该指引。建议按实际clips.run能力更新操作说明，避免四向已可用但用户被提示只可西向。这是文案范围错误，不阻塞加载逻辑或视觉验收。
- 本次未发现P1/P2集成问题。

## 重点风险核对

1. 缺方向与B部分方向拒绝：加载器要求非空合法、无重复directions，每方向四帧，pose_id/direction与方向块顺序一致，当前walk有对应四帧。A缺任何已声明方向立即拒绝；B缺方向插入四个null，与同一全局索引对齐；未知衣物方向拒绝。has_motion_garment在动作/方向不存在、索引越界或null时拒绝，set_garment与run方向切换均先判能力后改变外观/方向。没有缺失B借用A或西向图的分支。
2. 数组对齐：run_clips索引从旧frame_metadata.size()+i构建，textures、metadata、A/B衣物遍历均使用同一directions次序，每方向固定四帧。B缺方向的四null不会让后续有资源方向偏移。没有garment文件时仅A追加，B越界由能力检查拒绝，旧walk/idle的20帧保持可用。
3. 加载失败清除：load_run_candidate开头clear_run_candidate截回run_base_frame_count，去除run clips/policy/digests，并把正在run的状态退到idle。全部新纹理和metadata在本地暂存，通过所有结构/哈希后才追加到共享frames；无半成功残留。新测试覆盖成功→partialB→坏B后run移除、A/B回到20帧。
4. 新测试范围：fixture明确用west图复用测试四向控制/加载语义，不声明新美术通过。覆盖方向切换/相位、真实metadata方向、B仅west可用、B不支持方向切换与换装拒绝、旧walkB可用、坏帧数、错direction及重复direction拒绝。它不能证明四向人体、鞋点、分层或用户视觉认可，主代理另做真实artifact原生验收是必要的。
5. 5裤像素归属：新增规则从near/far臂mask减去已观察pants_waist，再重算arms和base。没有扩大靠全图颜色猜归属的范围，仍依赖每姿态手工腰区。回归测试针对实际零起始pose3的五点，并保留pose2同坐标真手臂，避免把之前误标“第三帧”的描述变成错误修复。
6. A/B结果不变的独立证据：只读提取HEAD的baked/A_0..3、B_0..3，与当前PNG解码RGBA逐字节对比，8/8完全相同（A四True，B四True）。这是历史输出比较，没有重建共享部件、改资源或复跑完整测试。归属变化落在分层数据，原穿戴视觉没有变化。

结论：可继续以候选身份验收与保留，已审加载/拒绝/清理与西向归属补丁没有阻塞级发现。P3操作指引宜同步；不扩大到完整动作集、动态8配方、生产迁移或用户认可。
