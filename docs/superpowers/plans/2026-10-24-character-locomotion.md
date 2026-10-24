# 四向步行与站立实施计划

目标：用户确认75%速度可用并要求继续；本轮沿既有制作规范完成body01四向walk/idle及两套上衣，延续已有西向资源。不宣称五类动作或完整衣裤鞋混搭完成。

速度记录：用户原文“ok 速度可以，继续”，认可范围为游戏体验的0.75倍（54世界单位/秒；源80ms×4以0.75时钟播放），不是自动认可完整人物发布。保持基线源帧80ms，通过playback_rate控制速度。

## 责任与合同

主代理：GPT新源、整帧注册、身体/衣身/袖分层与目标覆盖、姿态合同、真实合成/原生检查和进度。复用gpt-6.1-sol high工具代理：现有合成器schema2兼容扩展和现有游戏体验入口四向/idle支持及测试；独立文件责任，主代理不同时编辑工具/体验脚本。

同一compose.py支持schema1原样与schema2。schema2保留512×768/root[256,708]/display_scale138/582、frames顺序表、recipes.A/B.frames有序layer列表；frames为唯一pose_id/positive integer duration_ms，额外action/direction。actions={idle:{loop:true,directions:{south:[pose_id],west:[pose_id],east:[pose_id],north:[pose_id]}},walk:{loop:true,directions:{south:[4ids],west:[4ids],east:[4ids],north:[4ids]}}。每pose只属一个动作/方向，声明必须全覆盖且无重复/缺失。move_policy={walk:{base_world_speed:72,playback_rate:0.75},idle:{base_world_speed:0,playback_rate:1}}。所有frames/recipes完整映射才允许发布；没有run/hoe/water/harvest不得回退旧资源。层按原规则全帧offset0合成，coverage仍只对指定子层。

schema2导出保留actions/move_policy/frames(含action/direction)/recipes的原姿态列表与实际PNG哈希，额外source_contract(源图、提取脚本、姿态元数据哈希)需读取实际依赖验证并纳入inputs。template_id、motion_set_id保留导出。schema1旧ID和固定四帧继续严格校验，不伪造新字段。

新资源目录art/design/character-motion/adult-standard-v1/locomotion-v1；复用同一godot2d/dev/character_walk_trial入口，由新目录启动器显式传入资源路径；默认旧路径保留兼容历史小样。WASD/方向键归一化移动；停止显示同朝向idle，变方向保持步行相位，换衣同相位；碰撞不推进无效位移。调速50%–100%基线默认75%，R回位；缺动作明确拒绝，不加镜像。旧单侧证据作历史保留，新工具变更后不借其旧哈希称当前工具已验收。

## 步骤

- [x] 保存速度认可范围；GPT完成四向同服装idle，逐方向制作缺失walk；西向原动作复用。
- [x] 完整GPT衣身/两袖长源，按新姿态人工确认归属和可见覆盖，保留完整隐藏衣身；登记实际关节/脚接触及不确定项。
- [x] 工具/体验扩展先失败测试再实现；旧schema1回归、schema2缺动作/缺帧/哈希/时序拒绝、归一化移动/idle/换衣/碰撞通过。
- [x] 同一合成器烘焙2配方×20姿态；真实像素重建及局部分层测试，原生四向行走/停止/衣物切换、明暗检视和连续录像。
- [x] 用户可审交付与未通过事项，更新状态；不提交、推送或导出，不自动制作其他体型。

2026-10-24续作：主代理完成东向抬腿纠正、三向walk各姿态A/B完整衣身补画、20姿态观察草案与原生录像入口；工具代理完成原职责后复用于新ROOT分层提取与烘焙（gpt-6.1-sol high），独立文件责任。新增16姿态背景alpha清理经失败复现与2项检查通过，完整关节冻结/严格脚点误差仍未通过。

2026-10-25用户反馈左右行走不对称，最终美术验收暂停。原37ea2904候选原生42项控制检查通过，但不作为修复后证据；历史记录保存于locomotion-v1/evidence/pre-symmetry-37ea2904。正在以west为动作基准修正east四帧：原高抬膝/前折腿改为低后收、近侧摆臂相位统一；GPT v5完整源统一整帧(-8,0)注册，同姿态B与隐藏衣身同步，不使用runtime flip。其他16姿态保持原样，待重新分层及原生验收。

2026-10-25完成记录：东向v5与两套衣物重新分层并完成原生验收，其他16姿态纹理不变；18项美术检查、20项合成回归、43项港口控制检查通过，40停帧、719连续样本/8段十循环和明暗10张诊断板归档。当前为可评审交付，用户视觉认可、完整关节/接触合同与严格脚点误差仍未通过；其余动作和动态裤鞋另行开发。最终artifact与入口见locomotion-v1/README.md。
