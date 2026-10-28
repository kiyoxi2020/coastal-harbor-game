# 固定候选配方覆盖审计：整体验收独立复查

Spec compliance：PASS（审计内容、导航收尾记录与后续小样建议范围合规）。

Evidence quality：PASS（足以支持现有登记覆盖、合成可行性及统一接口缺口；不构成新小样原生验收或生产发布）。

Critical：无。Important：无。

## Minor

无未解决项。复查期间发现的导航Task 1与Paseo登记来源遗漏已修正：主报告现明确47链接/五suite属于上一导航任务，并记录本轮四步审计与D1/D2登记、子代理连接限制由主代理统一同步；未混写验证轮次。

## 核心复查结果

1. **2/3/19及8/96成立，口径未偷换。** 24衣装行唯一覆盖六动作四向，完整登记仅hoe-west与idle-west，局部仅walk-west/idle-north/harvest-north。四头状态各24行构成96能力单元；候选衣装精确匹配只有上述两行，故8个能力单元对应5 pose×4 state=20实际显示结果。其余父衣装不同的样例未混算。报告明确这既不等于新严格配方支持8格，也不等于8格逐状态用户认可。
2. **bare含义正确。** 头部附件将bare标为`base_clothing_audit_required`，不把“无发无帽”当成缺发帽图，也不据此认定完整身体衣装。Godot加载器实际以bare SHA等于父衣装帧SHA校验，主报告的r002衣装bare重建与之相符。完整穿衣参考、same-pose-reference和隐藏身体未混同。
3. **附件可解析且保留子审计事实。** 760个引用记录、2114次file_ref引用均有有效短ID；修正后的path_base明确区分repository与art/characters。解引用后的headwear与原子报告逐结构一致；衣装除增加path_base/bytes元数据外内容一致。24+24行及96状态齐全。核心输入SHA均与当前文件一致。此复查没有重复主代理已完成的760项全量文件SHA核验。
4. **探针支持可复用图层与现行接口不足，结论边界恰当。** 附件保留标准alpha-over 7/20与精确旧语义20/20两组结果。定点读取Git379a9bc两份旧builder并核对其SHA，与报告一致：hair-only是alpha>0二值支撑上的RGBA paste；hat/hair_hat是far/body/可选hair/near alpha合成，再仅在真实部件支撑内回贴。主报告区分可见hair差异与支撑外透明RGB保全，未把首次不等价错归为缺源。20/20只证明已注册图层可复现旧输出，不声称完整原图提取流程已重建。
5. **混合合成、坐标、多来源和消费者缺口有代码依据。** `tools/characters/build.py:25`每帧只支持一种composition，所有层完成后统一注册；`build_contract.py:138`及后续只用action/direction标能力、绑定单source与source_bundle，非body强制三mask，ownership-replace要求body首层；`character_headwear_samples.gd:49`起固定四旧sample，校验父SHA、四pose和四state。现成目标画布头层不能直接混入r002源画布衣装阶段，新strict manifest也不会自动被消费者接收。报告提出统一入口扩展而非旁路，合理。
6. **源、注册、mask与v3双来源未混淆。** 西锄key2帽下发两个source_views及二值ownership的保全要求明确；source_ownership、coverage、occlusion及diagnostic visible mask分别说明。未以目录名或same-name ID扩大兼容。top03已有静态四向源被保留为待核复用输入，未错误要求全量重画。
7. **认可及原生范围未越界。** 报告分别限定五衣装抽样、东跑v5、西锄key2 v3，南浇/北收未记录新认可。4369旧迁移输入及10项认可原件/subject的主代理复核作为冻结旧范围证据引用，不称新小样原生通过；129图、65面板单循环、16世界报告未扩大为十循环、OS输入、严格接触或导出。75测试/check结果由主代理本轮执行，本复查未重复运行。
8. **后续包可执行且不超本轮授权。** 只建议西向hoe四pose＋idle一pose、四份固定review-only配方；包含反例、统一合同设计、build/verify、20输出等价、消费者实际加载、原生连续播放、头态切换及回idle，完成/停止条件明确。实现均放在后续任务，本次没有新美术、生产切换、基线放宽或第二人物管线。涉及既有已拒绝行为的测试可沿用原测试；新增失败测试应针对本次新接口的真实风险。

## 限制

本次为只读资料及代码定点审查；未重跑75项测试、check、4369迁移输入/10认可核验或两次合成探针，未新构建或GPU采集。审查通过只针对本次审计交付，不替代后续小样的技术与视觉验收。仅写本临时审查文件，未修改工作区或派生子代理。

## 审查快照

- `docs/reviews/character-first-recipe-coverage-audit.md` SHA256：`1420d9981738d1cf6c0d7f5eb7805c6df575c512d9b977d7538c1dd8e1bdc1ce`
- `docs/reviews/character-first-recipe-coverage-audit.json` SHA256：`41b3a299f9d88785f89707ffbe3c1144a059893093184d3bbffeaa6c42bfde2c`
- `docs/superpowers/plans/2026-10-28-character-next-step-audit.md` SHA256：`1fa0ce5e167d4981f53898ae512d488ca4ecfd4de139617ee5ff7041ee3f249e`
