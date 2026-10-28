# 同配方西向行走：素材与适配准备计划

目标：为成年母版、top03条纹上衣、原橄榄裤/棕鞋确定西walk四pose及头部四状态的可复用来源和最小适配任务。完成条件是来源/SHA、身份与坐标证据、可复查诊断、当前合同缺口及独立复查齐全；本阶段不把诊断图登记为正式构建，不改变已交付西锄能力。

## 任务与文件责任

- [x] 主代理检查最新PROJECT_STATE/HANDOFF、AGENTS、git status与上一阶段证据；冻结候选范围。
- [x] gpt-6.1-sol/high衣装代理核原始下身、top03四走、原裤鞋idle像素祖先、完整GPT来源及mask/层序。只写/private/tmp/coastal-walk-west-prep/，不改资源。
- [x] gpt-6.1-sol/high头部代理核实际耳弓锚、头投影、源/target pose映射、完整发/近远帽/帽下发；组合衣装诊断，不创造新脸手或按比例猜锚。
- [x] 主代理核现有strict构建依赖与代码约束，明确新动作登记如何影响既有四构建，禁止刷新基线或覆盖当前交付。
- [x] 汇总docs/reviews/2026-10-29-walk-west-readiness.md及同目录诊断资料。分开说明同配方有限参考、可独立换装、正式构建和原生认可。
- [x] 独立gpt-6-astra/high复查来源、身份、锚点证据和结论边界，处理重要问题。
- [x] 执行必要人物单元测试/check、诊断与来源SHA、文档链接/diff检查；本轮未修改正式美术/代码，不重采GPU。
- [x] 更新PROJECT_STATE/HANDOFF与Paseo；完成素材准备即交付，不自动改合同、重生图或移动旧build。

## 固定决策

1. 新四走帧仅在旧top-visible支撑内使用条纹源，其余保留locomotion B；该结果仅是可复用候选，不可充当新body/source输入。
2. canonical idle直接复用已交付r002精确idle clip，临时walk诊断idle与其top像素不同，不替换。
3. 头部source_view_pose=idle_west_0和target_pose=walk_west_i分别记录；锚点基于实际脸耳轮廓、完整源分辨率，不按身高比例或任意调偏移。
4. 新层需要明确source ownership、target coverage、occlusion/有序层角色；不为满足旧字段虚造mask，不把完整穿衣下身当隐藏裸身体。
5. design或r001适配/共用idle/构建器代码变动会按实际依赖使旧strict构建过期。下一实现需先有明确的新revision与历史制品保全方案；不得通过忽略engine/input hash或baseline例外过关。


## 完成记录

本阶段完成。来源245条SHA核对、114人物测试、check.py(strict5/build4/legacy9)、文档链接/诊断数据/diff通过；两位来源代理及独立复查完成。交付：[素材准备与最小适配包](../../reviews/2026-10-29-walk-west-readiness.md)、[独立复查](../../reviews/2026-10-29-walk-west-readiness-review.md)、同目录walk-west-preparation诊断PNG/APNG与JSON。

现有GPT像素可供有限同配方小样准入，保留exact idle，不等于新增正式walk配方/独立裤鞋/原生能力。本轮未改代码、art资源、旧构建、baseline或认可，未生图/采GPU/提交/推送。下一实现先处理正式身份/多pose注册及构建历史保全，再构建/接入/原生验收。
