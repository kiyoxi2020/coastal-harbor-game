# Implementation report

已完成 walk-west 条纹长袖/牛仔/原鞋真实拆槽小样及 matching idle，sample SHA256 `94f786472c86f5c8225bd9a5e76abd157c0e4fee43f81e5bdd89b590432f2ac6`。原四帧时序、画布、根、scale 完全保持，四帧真实姿态未镜像冒充。7 张 GPT 完整源（5 outfit + 2 完整 torso）及 prompt、所有引用、mask/ownership/工具均保留并绑定 inputs。

236 项结构/能力断言通过。5 帧 alpha 差异均 0，原非衣区域逐 RGBA 差异均 0；三槽拆出后可仅用 shared_body+slot parts+ownership 重建最终图。1×/2×明暗对照及独立部件板已目视。中途鞋口包络误含原裤色，已逐姿态按实际踝口线精修多边形，未挪动部件或程序调色。Python 系统无 numpy，最终工具仅 Pillow；未添加依赖。

未验证：GPU 原生连续运动和切回 matching_idle，主代理负责；用户尚未认可此配方。限制：仅此方向、此配方和5姿态，未验证任意换款/其他体型；现有原姿态 cloth alpha 固定接口是该抽样适配的约束，不宣称可自动适配全部库存设计。

实际执行模型 gpt-6.1-sol，reasoning_effort=high，fork_turns=none。职责为 walk/run 独占抽样资源；无嵌套代理、无提交、未修改共享 Godot/旧认可资源。
