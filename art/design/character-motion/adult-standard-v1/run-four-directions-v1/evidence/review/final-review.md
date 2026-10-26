# 人物动作/换衣最终独立复查

2026-10-25。模型由主代理派发记录；职责：跨来源、能力门禁及证据一致性只读复查。读取本轮计划、唯一人体规范、代码包及先前集成复查；未修改生产文件，未启动 GUI，未重跑已报告的逻辑/分层/原生测试。唯一执行的新检查为 `/private/tmp` 中归档门禁的隔离负例，以及 10 个 GPT 原图与 source-index 的来源哈希核对。

## 结论

候选加载能力与资源声明一致：A 四向，B 仅 west/east；south/north B 不得启用。未发现 P1。归档 helper 有一项 P2，修复前不能以它成功退出证明最终六组合证据齐全。没有发现应阻止当前资源作为“待视觉复审候选”保留的其他新增 P2。

此复查不宣布比例、四向动态人体、完整换装、接触轨迹或用户认可通过。实现者补报 south/north 上部轮廓（含耳，y<345、alpha>=128）比已认可同向 idle 宽约 10–13%；应保留待比例复审，主代理拟增加同密度 idle 对照板。农事 water v3/hoe v3/harvest v2 仍未过，不扩大本轮范围。

## P2：最终归档可以接受缺失证据和过期板脚本

位置：`run-four-directions-v1/archive_native_evidence.py:25-35,49,68-78`。

`checks` 只要求非空且现有值为 true；metadata 通过 glob 遍历，没有要求预期组合齐全；boards 只检查 candidate/garment 和每个现有 PNG 的哈希，完全不核验已记录的 `script_sha256` 或板的组合集合。因此空 metadata / 空 boards 同样可成功生成声称 “Real native controls and continuous playback” 的最终 summary。当前先写 checks/ZIP 再验证，也会在后续异常时把旧 summary 与已覆盖的新文件留在同一最终目录。

隔离复现目录：`/private/tmp/coastal-final-review-1mg1y1q7/`。只把 helper 的 SOURCE/OUTPUT 指向隔离目录，输入 `{native_renderer:true}`、当前 candidate/garment 哈希、`script_sha256: deliberately-stale` 与 `boards:[]`，没有 metadata 或 PNG；原 helper 实际成功返回并生成 `clips:{}` 的 summary。未更改候选和真实原生证据，未调用 ffmpeg/Godot。

建议一次修复：

1. 根据 run-garments 的实际 recipes 求预期六组合；metadata 与 boards 都必须完整、唯一、无未知组合。
2. 检查当前验收脚本所有必需 checks 键及其 true 值，不能把子集当完整通过。
3. 校验 boards.script_sha256 对应当前板脚本、renderer 非 headless、板尺寸与声明一致、PNG 文件/哈希匹配。
4. metadata 的四姿态必须是当前方向确切 pose 集合；wall_ms 单调、最后时长达到按候选 duration/playback_rate 计算的十循环，所有 capture_file 存在。现有“>=40 捕获且任意 4 pose”不足以独立检查该范围。
5. 先验证所有输入，再写 staging 并一次发布，或至少验证完整后才修改最终目录，避免失败污染旧 summary；summary 登记归档器自身哈希。

主代理当前真实目录已存在 46 个全部为 true 的 checks。该事实说明上述复现是 helper 防缺失缺陷，不意味着真实检查失败；最终六段、六板仍应由主代理完成实际归档验收。

## P3：证据依赖边界可进一步明确

- native metadata 已绑定 candidate、run-garments、trial.gd 与 native test.gd，能识别这些输入修改；场景 `.tscn` 和继承的原生辅助脚本尚未绑定。当前未观察到这些文件在捕获间变化，不要求为未变文件重新运行视频。最终 summary 可记录其当前哈希及捕获时冻结说明，后续捕获入口直接输出这些依赖，避免将来共享场景变化仍沿用旧证据。
- run-garments inputs 包含 active 烘焙、东西向实际 layer/mask、完整衣身来源及西向 parts-manifest，但不包含本目录 build_parts.py 或精简的 layer/recipe 规则摘要。当前 parts-manifest 自身绑定构建脚本，故制作记录可追溯；不过 runtime garment digest 不能单独表示完整合成规则依赖闭包。若未来改变本目录合成脚本/层序却未重建烘焙，不能只凭旧 runtime digest 宣称新的分层验收仍有效。冻结本次候选后可将该规则哈希纳入下一次资源修订，或在最终证据单列其实际哈希。
- 先前操作指引无条件写“仅西向”的 P3 已修，改为通用指引和实际方向数。

## 已核对的资源与范围

- 10 个 source-index 中的 GPT 原始文件均存在，SHA256 与对应保留源图记录一致；生成来源有原图、提示词、尺寸、状态。south B 两个源版本被登记为姿态漂移拒绝；north B 为真实衣物源但接口失败，没有借静态图或别的身体启用。
- 实际目视查看 south A v3、north A v2 完整四帧源及 baked/B_north_3。可见两侧支撑/腾空轮廓的交替和 north B 腰边/肩部接口风险；这不是比例认可或连续步态验收。反向东西仅整帧翻转后 +1x 根点注册，南北整格 +11y；没有按单独衣鞋缩放或任意位移修接口的代码。
- candidate 16 帧按 south/west/east/north 四组，每向四帧；scope/status 明确 complete-frame proof 和 unapproved。poses 的隐藏关节为 null，接触轨迹未冻结，未把估算点伪装为批准数据。
- run-garments A 四向使用注册完整帧；B 只列东西向实际 baked。parts-manifest 中存在 north A/B 的制作层和烘焙，但运行清单不引用其 B；south 根本没有伪造分层。north A 精确还原仅证明原装重建，不等于 B 或混搭有效。
- garment-quality 保留 north B 四姿态的 9/9/68/86 个封闭低 alpha 像素及具体 ownership/neck/underarm 原因，明确 rework_required_not_enabled；test_parts 的对应检查证明它们仍被拒绝，没有把失败源“修成通过”。
- 加载器校验 walk artifact、候选/衣物依赖哈希、合法唯一方向与严格四帧；B 缺方向对齐为 null，能力查询和方向/上衣切换前拒绝；A 缺声明方向拒绝。加载失败先清理旧 run，并使用暂存数组避免半成功。既有集成审查已覆盖该路径，本轮未重复测试。
- 边界仍为固定裤鞋的 A/B 上衣候选，不是独立裤鞋八配方或发帽动态组合；已认可西向 A 身份不能转移为南北/东向或 B 的用户认可。

README/review/implementation-report 由另一代理补写，最终原生视频和新版对照板由主代理完成；本报告不预判尚未交付的最终文档或最终归档状态。

## P2 修复复查（本轮追加）

主代理修改 helper 后进行了定点只读代码复查，读取新 `archive_native_evidence.py` 与 `test_archive_native_evidence.py`；没有重复执行 8 项窄测试、旧逻辑测试或 GUI。

**原 P2 已在代码层关闭。** 新 `validate_inputs()` 从实际 recipes 构造预期组合，metadata 和板分别要求集合完全一致且无重复；必需 checks 由实际方向/能力生成并要求全部为 true。板校验当前捕获脚本哈希、非 headless renderer、画布/放大/显示比例、candidate/garment/walk 依赖以及实际 PNG 尺寸/哈希。各序列校验当前 trial/test 哈希、确切方向 pose 集合、严格单调采样时间、至少十周期跨度、已捕获的 pose 完整性和文件存在/安全路径。此前“空 metadata、空板、过期板脚本仍成功”的输入无法进入最终写入阶段。

所有校验先于输出目录写入；随后 ZIP、视频、summary 在临时 staging 目录完成，任何构建失败不会改已有最终证据。成功后才 rename；已有交付先保留带摘要哈希的备份，第二次 rename 异常时恢复原目录。summary 登记归档器哈希，并单列原生场景/继承测试辅助脚本及制作规则的当前哈希；说明这些是最终归档时读取且捕获期间未改的依赖，不伪装为进程当时记录。这也以准确限定范围回应了前述 P3。

新增测试对原空集复现、完整六组合、缺 metadata、重复板、过期板脚本、错方向 pose、不足十周期、缺捕获文件设置了直接验收，范围与此修复相称。测试运行通过由主代理报告，本复查只确认用例与实现对应。

没有发现这次修复引入新的 P1/P2。实际六组合归档当时仍由主代理执行；本结论关闭的是 helper 门禁缺陷，不预先宣称尚未完成的 ffmpeg/最终归档成功。南北比例风险、B 南北拒绝与未完成完整混搭的范围限定继续有效。
