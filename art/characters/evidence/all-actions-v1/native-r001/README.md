# 全动作统一评审交付（Q2=B）

当前制品 `adult-top03-full-hair-hat-r001`：24动作方向、84姿态，固定top03／原裤鞋／栗短发＋草帽。唯一试玩入口为仓库根 `tools/characters/review-all-actions.command`；[20组动作连续总览](videos/all-actions-native-overview.mp4)按实际时间展示十轮走跑／农事，每组章节之间为声明切口，151.749秒。视频是观看用有损派生，原始PNG和binary64时钟为证据。

## 已完成的技术范围

[六观察器原始证据聚合](raw-observation-set.json)覆盖168明暗停帧（84姿态）、20组世界各十轮／实例、48农事时序、32走跑时序、96转换、14港口空间情形，缺项为0。各自记录实际GPU纹理、位置、物理时钟和输入闭包。地块侧车另验证8个真实锄刃／水花点的几何投影；它不证明土壤冲击、隐藏握点或游戏业务事务。

[接触材质栅格回执](contact-raster/final-summary.md)：102定姿、8407连续适用测量全部最佳偏移[0,0]、无歧义/缺项，固定41×41源ROI、alpha误差界、最少样本和全部等优偏移规则未降；先于读取实际颜色排除固定4ULP边界不确定样本，计数完整保留。

[原生84姿态板图](native-pose-boards/)与[61空间＋8候选板图](native-spatial-boards/)均为原生像素整数裁贴，不缩放，不修改源。Root内部逐帧／空间视觉观察另存JSON，不等于用户认可。355项人物全量测试通过；全库check53严格配方、47构建、9冻结legacy通过，生产未切换。

## 已明确转后续的严格支撑工作

[足底支撑独立审查](foot-support-review/review.md)保留43当前元数据、18历史JSON、26prompt、64材料候选、1373实际PNG和全部328持帧段。制作意图存在，正式实际足点／支撑期／腾空期／批准轨迹缺失；同纹理材料条件漂移walk8–24px、run16–36px。若该材料为固定支撑，则超过1px；没有把此条件值冒称无条件物理误差，也没有把栅格0px冒称脚不滑。

用户已回复 `Q2 (步态验收标准): B`，本轮按当前四关键帧像素步态接收完整统一评审包，交付完成；[范围决定](q2-b-decision.json)绑定实际artifact、manifest及suite。严格支撑／腾空／滑步转后续，原门槛及审查证据保留为未验证，不改为通过。该选择不扩大为所有美术／混搭／生产发布认可；OS级输入、导出和其它平台未测。

## 完整数据与复核

[完整数据索引](lossless-native-dataset-index.json)列出8643个原始PNG路径，所有像素均已无损持久化；标准tar hardlink仅合并相同SHA的payload，每个成员重新读出校验。timing两组按设计无PNG，保存全部原始时钟JSON。每个子目录的persistence.json列原始SHA、压缩SHA及最终回执名；poses旧版回执保留且有角色说明。主原始输入/报告/回执为gzip，PNG为native-pngs.tar.gz。

例如在新建的 `/private/tmp/coastal-native-audit-poses/` 中解压poses目录的数据，再按原记录路径/版本使用官方validator。输入仍绑定采集时仓库及实际绝对suite路径，换路径时不能伪改原报告当新回执。源码由 `frozen-runtime-code-r002.snapshot.json` 和 `final-validator-and-tests.snapshot.json` 保存完整UTF8/SHA；更早快照是修复过程历史。临时完整原路径也保留。所有数据都是review-only，不能继承为动态混搭或生产认可。

提交前格式核对仅清理 `tools/characters/contact_evidence.py` 一个行尾空格，AST与原测量版本完全相同。原实际测量源码和回执不改，原／当前SHA及完整当前文本见 [格式追溯记录](commit-format-only-validator-note.json)。
