# Implementation report

已完成并冻结 harvest-north：原认可蓝长袖 + pants02 深蓝牛仔 + 原鞋，4动作及 matching idle，sample SHA256 `0c5e81663fed72376e11dcec609c41a95df17adabc0540e8773b6cac599020f9`。主代理已明确授权以独立下装组合作为本动作代表性抽样；此组没有宣称 top04 红毛衣适配通过。

4动作200/250/250/300ms（1000ms），1536×1920/root768,1600/scale138/1164/density2；idle512×768/root256,708/scale138/582/density1。原帧source_box、整帧平移、pose_id、时序及alpha全部保持。真正独立top/pants/shoes源、source ownership、coverage、occlusion、shared同pose前景与轮廓俱全。新牛仔裤可见面由完整GPT源提取，ready/reach保留有依据的同坐标隐藏裤面；未用失败重居中unoccluded源。

上游红稿复现为ready81/reach6/pluck85/idle889个peach像素落在原蓝衣覆盖内。定点补图后idle attempt3仍179个，换孤立衣源可补袖；ready收窄合法衣料选择后仍1个，pluck第二孤立collar源明显放大/重居中，依原门禁拒绝。完整源/prompt、各轮诊断和失败配置快照均保留，按范围决定停止扩生图并复用原同pose蓝上衣。未采用透明RGB、局部挪缩、程序涂色、旧pose脸手或放宽门禁。

7项测试通过，覆盖实际manifest验证、源语义失败记录到最终实际槽通过、alpha/非衣RGB变化拒绝、覆盖缺失/槽重叠拒绝、重复pose拒绝、原登记/时序及idle几何、最终仅pants新采样且原top/shoes逐RGB保持。168项inputs哈希及generation-ledger内源哈希均核对。5姿态非裤RGBA变化均0、alpha完全相同、独立槽重建逐RGBA一致，最终上衣槽peach0。最终1×/2×明暗与独立部件板已目视。

未验证：原生GPU连续动作、退出回matching_idle及用户认可，主代理负责。局限：单方向、固定配方、同版型表面适配；共享原黑轮廓/alpha接口是显式范围，不等于任意剪裁、完整隐藏裸体或全部库存混搭能力。上游handoff未附全部生成缓存路径，完整lossless源图和prompt已保留；本代理新增输出路径完整记录。

只修改本目录及其本地helper；没有改共享hoe/water helper、已冻结walk/run、Godot、catalog或旧认可资源；没有嵌套或提交。实际接手模型gpt-6.1-sol，reasoning_effort=high，fork_turns=none。
