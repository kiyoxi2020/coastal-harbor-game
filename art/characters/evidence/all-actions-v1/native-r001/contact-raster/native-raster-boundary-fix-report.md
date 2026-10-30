已按root批准的固定算法修复native_raster.py及其tests；未改contact_evidence.py、source70、41ROI、艺术资源、母版、运行时或共同build engine。

算法：每个候选screen pixel center沿原affine逆变换得连续source坐标c；n=round(c)，s=max(1,abs(c),abs(n))。binary32的binade间距为2^(floor(log2(s))-23)，固定guard=4*该ULP。原source/mask/alpha>=250资格满足后，任一轴距整数<=guard即跳过并计数；不读取actual颜色、不选任何相邻source像素。先冻结全部剩余样本并检查min4，再convert/load actual、执行原RGB最优偏移测量。

这是按源坐标量级推导的小范围binary32舍入防护：四个spacing是若干float32顶点/UV舍入的局部保守区间，不是1px容差，也不声称形式证明任意病态affine变换的全局误差。取最近整数的量级可使2^k边界两侧用同一较大spacing。实际1115处4ULP=0.00048828125源像素；源点/ROI不变。

成功结果新增float32_boundary_samples_skipped、eligible_sample_count_before_precision_filter、sampling_precision（固定multiplier4、量级下限1、排除条件与actual-independent规则）。原样本下限4、nearopaque alpha>=250、RGB界256-minimum_source_alpha、radius3、全部等优offset<=1保持不变。低样本仍ValueError，由contact工具保留unverified；多解只有全部最优<=1且RGB合格才可报告有界。

TDD：先加5项边界反例，旧版9tests共6fail（正负eps subcase各fail）；最小实现后9PASS。覆盖界内排除、超过固定界不排、actual颜色不改样本集合、4个资格样本滤至2后拒绝、actual读取发生在样本准入后。contact22项全部PASS。日志/private/tmp/coastal-native-raster-boundary-red.log、coastal-native-raster-boundary-green-01.log、coastal-contact-evidence-after-boundary-green.log。

冻结SHA：native_raster.py c639366bb5e671b0481586d5c47cfebb14548f9deee8d5c9581d39d987309f16；test_native_raster.py409a60c24668a120c26f247354fc632690bcc803c8260fcde65525da449be49c。

旧poses04的102项原始receipt、101通过/1RGB mismatch、源20sample逐点诊断和6处handle文字标签erratum全部保留，不重写或转成PASS。root已明确旧3629原生输入因all_actions_native/UI改动过期，不重测旧数据。等待正式poses06/world04新闭包通知；此修复测试不等于native最终结果或物理接触/soil/support/滑步/用户认可。全量unit/check由root统一。
